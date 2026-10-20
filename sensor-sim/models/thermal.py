from typing import Literal

from pydantic import BaseModel, Field

from common import BaseEvent

FRAME_WIDTH_PX = 640
FRAME_HEIGHT_PX = 512
MAX_AREA_PX = FRAME_WIDTH_PX * FRAME_HEIGHT_PX


class ThermalMetrics(BaseModel):
    hotspot_temp_c: float = Field(ge=-50, le=1000)
    ambient_temp_c: float = Field(ge=-50, le=60)
    delta_c: float
    hotspot_area_px: int = Field(ge=0, le=MAX_AREA_PX)

    @classmethod
    def from_readings(
        cls,
        hotspot_temp_c: float,
        ambient_temp_c: float,
        hotspot_area_px: int,
    ) -> "ThermalMetrics":
        """Build metrics so delta_c is always hotspot minus ambient."""
        return cls(
            hotspot_temp_c=round(hotspot_temp_c, 1),
            ambient_temp_c=round(ambient_temp_c, 1),
            delta_c=round(hotspot_temp_c - ambient_temp_c, 1),
            hotspot_area_px=hotspot_area_px,
        )


class ThermalEvent(BaseEvent):
    sensor_type: Literal["thermal_camera"] = "thermal_camera"
    metrics: ThermalMetrics