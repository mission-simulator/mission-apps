import math
from typing import Literal

from pydantic import BaseModel, Field

from .common import BaseEvent

MAX_RANGE_M = 10_000.0
REF_RANGE_M = 1_000.0
REF_SNR_DB = 50.0  # simulated SNR at the reference range


class RadarMetrics(BaseModel):
    track_id: str
    range_m: float = Field(ge=0, le=MAX_RANGE_M)
    speed_mps: float = Field(ge=0)
    heading_deg: float = Field(ge=0, lt=360)
    snr_db: float

    @classmethod
    def from_track(
        cls,
        track_id: str,
        range_m: float,
        speed_mps: float,
        heading_deg: float,
    ) -> "RadarMetrics":
        """Build metrics from the track so snr_db stays consistent with range."""
        # Return power falls off with range to the fourth power, i.e. 40*log10.
        snr = REF_SNR_DB - 40 * math.log10(max(range_m, 1.0) / REF_RANGE_M)
        return cls(
            track_id=track_id,
            range_m=round(range_m, 1),
            speed_mps=round(speed_mps, 1),
            heading_deg=round(heading_deg, 1) % 360,
            snr_db=round(snr, 1),
        )


class RadarEvent(BaseEvent):
    sensor_type: Literal["radar"] = "radar"
    metrics: RadarMetrics