from contextlib import asynccontextmanager
from typing import Annotated, Union

from fastapi import FastAPI
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield
    db.pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/events", status_code=201)
def post_event(event: Event):
    db.store_event(event)
    return {"event_id": event.event_id}