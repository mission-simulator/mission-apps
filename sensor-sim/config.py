import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    sensor_type: str
    node_id: str
    sensor_id: str
    rate_hz: float


def load_config() -> Config:
    sensor_type = os.environ["SENSOR_TYPE"]
    return Config(
        sensor_type=sensor_type,
        node_id=os.getenv("NODE_ID", "edge-sensor-node-01"),
        sensor_id=os.getenv("SENSOR_ID", f"{sensor_type}-01"),
        rate_hz=float(os.getenv("RATE_HZ", "1")),
    )