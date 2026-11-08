import time
from contextlib import asynccontextmanager
from typing import Annotated, Union

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import Field

import db
from models.acoustic import AcousticEvent
from models.radar import RadarEvent
from models.thermal import ThermalEvent

# Pydantic reads "sensor_type" first and validates the rest against the matching model.
Event = Annotated[
    Union[AcousticEvent, RadarEvent, ThermalEvent],
    Field(discriminator="sensor_type"),
]

HTTP_REQUESTS = Counter(
    "ingest_http_requests_total",
    "HTTP requests by path, method and status code",
    ["path", "method", "status"],
)
EVENTS_STORED = Counter(
    "ingest_events_stored_total",
    "Events written to Postgres, by sensor type",
    ["sensor_type"],
)
DB_INSERT_SECONDS = Histogram(
    "ingest_db_insert_seconds",
    "Time spent inserting one event into Postgres",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield
    db.pool.close()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def count_requests(request: Request, call_next):
    response = await call_next(request)
    # Use the route template, not the raw URL, so labels stay few.
    route = request.scope.get("route")
    path = route.path if route else "unmatched"
    HTTP_REQUESTS.labels(path, request.method, str(response.status_code)).inc()
    return response


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/events", status_code=201)
def post_event(event: Event):
    start = time.perf_counter()
    db.store_event(event)
    DB_INSERT_SECONDS.observe(time.perf_counter() - start)
    EVENTS_STORED.labels(event.sensor_type).inc()
    return {"event_id": event.event_id}