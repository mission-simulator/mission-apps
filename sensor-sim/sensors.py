from __future__ import annotations

import math
import random
import uuid
from abc import ABC, abstractmethod

from models.acoustic import (
    FULL_SCALE_DB, AcousticEvent, AcousticMetrics, AcousticStatus,
)
from models.common import BaseEvent, Direction, Status
from models.radar import MAX_RANGE_M, RadarEvent, RadarMetrics
from models.thermal import MAX_AREA_PX, ThermalEvent, ThermalMetrics


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def pick_health() -> str:
    return random.choices(["OK", "DEGRADED", "FAULT"], weights=[98, 1.5, 0.5])[0]


class Sensor(ABC):
    def __init__(self, node_id: str, sensor_id: str, interval_s: float):
        self.node_id = node_id
        self.sensor_id = sensor_id
        self.interval_s = interval_s

    @abstractmethod
    def read(self) -> BaseEvent | None:
        """Return one event, or None if the sensor has nothing to report."""


# ---------- acoustic ----------
BAND_EDGES_HZ = [(0, 125), (125, 250), (250, 500), (500, 1000),
                 (1000, 2000), (2000, 4000), (4000, 8000), (8000, 16000)]
QUIET_RANGES_DB = [(32, 42), (32, 42), (29, 39), (27, 37),
                   (25, 35), (22, 32), (19, 29), (15, 25)]
EVENT_MAX_DB = [85, 90, 95, 100, 100, 90, 80, 65]


class AcousticSensor(Sensor):
    EVENT_START_PROB = 0.02

    def __init__(self, node_id, sensor_id, interval_s):
        super().__init__(node_id, sensor_id, interval_s)
        self.noise_floor = random.uniform(36, 40)
        self.bearing = random.uniform(0, 360)
        self.ticks_left = 0
        self.loud_band = 4

    def _band_powers(self) -> list[float]:
        quiet = [random.uniform(lo, hi) for lo, hi in QUIET_RANGES_DB]
        if self.ticks_left == 0:
            return quiet
        peak = random.uniform(80, EVENT_MAX_DB[self.loud_band])
        powers = []
        for i, base in enumerate(quiet):
            falloff = abs(i - self.loud_band) * random.uniform(8, 14)
            powers.append(min(EVENT_MAX_DB[i], max(base, peak - falloff)))
        return powers

    def read(self) -> AcousticEvent:
        self.noise_floor = clamp(self.noise_floor + random.gauss(0, 0.1), 35, 42)
        if self.ticks_left == 0 and random.random() < self.EVENT_START_PROB:
            self.ticks_left = random.randint(5, 30)
            self.loud_band = random.randint(1, 5)

        powers = self._band_powers()
        if self.ticks_left > 0:
            self.ticks_left -= 1
            self.bearing = (self.bearing + random.gauss(2, 1)) % 360

        lo, hi = BAND_EDGES_HZ[powers.index(max(powers))]
        metrics = AcousticMetrics.from_bands(
            powers, self.noise_floor, random.randint(lo + 1, hi - 1)
        )
        return AcousticEvent(
            node_id=self.node_id,
            sensor_id=self.sensor_id,
            direction=Direction(
                bearing_deg=round(self.bearing, 1) % 360,
                confidence=round(clamp(metrics.snr_db / 50, 0, 1), 2),
            ),
            status=AcousticStatus(
                sensor_health=pick_health(),
                clipping_detected=metrics.spl_db >= FULL_SCALE_DB,
            ),
            metrics=metrics,
        )


# ---------- radar ----------
class RadarSensor(Sensor):
    SPAWN_PROB = 0.05

    def __init__(self, node_id, sensor_id, interval_s):
        super().__init__(node_id, sensor_id, interval_s)
        self.target: dict | None = None

    def _spawn(self) -> dict:
        bearing = random.uniform(0, 360)
        dist = random.uniform(5000, 9500)
        return {
            "track_id": f"trk-{uuid.uuid4().hex[:6]}",
            "x": dist * math.sin(math.radians(bearing)),
            "y": dist * math.cos(math.radians(bearing)),
            "speed": random.uniform(20, 60),
            "heading": (bearing + 180 + random.uniform(-40, 40)) % 360,  # inbound
        }

    def read(self) -> RadarEvent | None:
        if self.target is None:
            if random.random() >= self.SPAWN_PROB:
                return None
            self.target = self._spawn()

        t = self.target
        t["heading"] = (t["heading"] + random.gauss(0, 0.5)) % 360
        t["speed"] = max(1.0, t["speed"] + random.gauss(0, 0.5))
        step = t["speed"] * self.interval_s
        t["x"] += step * math.sin(math.radians(t["heading"]))
        t["y"] += step * math.cos(math.radians(t["heading"]))

        dist = math.hypot(t["x"], t["y"])
        if dist > MAX_RANGE_M or dist < 200:   # left coverage or reached the site
            self.target = None
            return None

        bearing = math.degrees(math.atan2(t["x"], t["y"])) % 360
        metrics = RadarMetrics.from_track(
            t["track_id"], dist, t["speed"], t["heading"]
        )
        return RadarEvent(
            node_id=self.node_id,
            sensor_id=self.sensor_id,
            direction=Direction(
                bearing_deg=round(bearing, 1) % 360,
                confidence=round(clamp(metrics.snr_db / 50, 0, 1), 2),
            ),
            status=Status(sensor_health=pick_health()),
            metrics=metrics,
        )


# ---------- thermal ----------
class ThermalSensor(Sensor):
    EVENT_START_PROB = 0.02

    def __init__(self, node_id, sensor_id, interval_s):
        super().__init__(node_id, sensor_id, interval_s)
        self.ambient = random.uniform(15, 25)
        self.bearing = random.uniform(0, 360)
        self.delta = 0.0
        self.ticks_left = 0

    def read(self) -> ThermalEvent:
        self.ambient = clamp(self.ambient + random.gauss(0, 0.05), -10, 45)
        if self.ticks_left == 0 and random.random() < self.EVENT_START_PROB:
            self.ticks_left = random.randint(5, 30)
            self.delta = random.uniform(20, 35)

        if self.ticks_left > 0:
            self.ticks_left -= 1
            self.delta = clamp(self.delta + random.gauss(0, 1.0), 15, 45)
            area = int(clamp(random.gauss(1500, 300), 100, MAX_AREA_PX))
            self.bearing = (self.bearing + random.gauss(1, 0.5)) % 360
        else:
            self.delta = random.uniform(0, 2)
            area = random.randint(0, 10)

        metrics = ThermalMetrics.from_readings(
            self.ambient + self.delta, self.ambient, area
        )
        return ThermalEvent(
            node_id=self.node_id,
            sensor_id=self.sensor_id,
            direction=Direction(
                bearing_deg=round(self.bearing, 1) % 360,
                confidence=round(clamp(metrics.delta_c / 40, 0, 1), 2),
            ),
            status=Status(sensor_health=pick_health()),
            metrics=metrics,
        )


SENSOR_CLASSES = {
    "acoustic": AcousticSensor,
    "radar": RadarSensor,
    "thermal": ThermalSensor,
}