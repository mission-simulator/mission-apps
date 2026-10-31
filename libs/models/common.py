import time
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

SensorHealth = Literal["OK", "DEGRADED", "FAULT"]


def now_ms() -> int:
    return time.time_ns() // 1_000_000


class Direction(BaseModel):
    bearing_deg: float = Field(ge=0, lt=360)
    confidence: float = Field(ge=0, le=1)


class Status(BaseModel):
    sensor_health: SensorHealth = "OK"


class BaseEvent(BaseModel):
    schema_version: int = 1
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    node_id: str
    sensor_id: str
    timestamp_epoch_ms: int = Field(default_factory=now_ms)
    direction: Direction
    status: Status