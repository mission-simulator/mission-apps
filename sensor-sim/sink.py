import json
import queue
import sys
import threading
import urllib.request


class HttpSink:
    """Posts event JSON to the ingest service from a background thread.

    send() only puts the event on a bounded queue, so the main loop never waits
    on the network. If ingest is down or slow, events are dropped.
    """

    def __init__(self, url: str, timeout_s: float = 2.0, max_queue: int = 1000):
        self.url = url
        self.timeout_s = timeout_s
        self.q: queue.Queue = queue.Queue(maxsize=max_queue)
        self.dropped = 0
        threading.Thread(target=self._run, daemon=True).start()

    def send(self, body: str) -> None:
        try:
            self.q.put_nowait(body)
        except queue.Full:
            self._drop("queue_full")

    def _drop(self, reason: str) -> None:
        self.dropped += 1
        if self.dropped == 1 or self.dropped % 100 == 0:
            print(
                json.dumps({"level": "warn", "msg": "ingest_drop",
                            "reason": reason, "dropped_total": self.dropped}),
                file=sys.stderr, flush=True,
            )

    def _run(self) -> None:
        while True:
            body = self.q.get()
            req = urllib.request.Request(
                self.url, data=body.encode(),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s):
                    pass
            except Exception as exc:
                self._drop(type(exc).__name__)