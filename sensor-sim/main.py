import random
import sys
import time

from config import load_config
from sensors import SENSOR_CLASSES


def main() -> None:
    cfg = load_config()
    if cfg.sensor_type not in SENSOR_CLASSES:
        sys.exit(f"Unknown SENSOR_TYPE '{cfg.sensor_type}'. "
                 f"Choose from: {', '.join(SENSOR_CLASSES)}")

    interval = 1 / cfg.rate_hz
    sensor = SENSOR_CLASSES[cfg.sensor_type](cfg.node_id, cfg.sensor_id, interval)

    next_tick = time.monotonic()
    while True:
        event = sensor.read()
        if event is not None:
            print(event.model_dump_json(), flush=True)
        next_tick += interval * random.uniform(0.9, 1.1)
        time.sleep(max(0.0, next_tick - time.monotonic()))


if __name__ == "__main__":
    main()