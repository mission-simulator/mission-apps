import math
from typing import Literal

from pydantic import BaseModel

from .common import BaseEvent, Status

BAND_NAMES = [
    "0-125Hz", "125-250Hz", "250-500Hz", "500-1000Hz",
    "1000-2000Hz", "2000-4000Hz", "4000-8000Hz", "8000-16000Hz",
]
FULL_SCALE_DB = 120.0  # reference level for rms_amplitude and clipping


class FFTBin(BaseModel):
    band: str
    power_db: float


class AcousticMetrics(BaseModel):
    spl_db: float
    peak_frequency_hz: int
    rms_amplitude: float
    noise_floor_db: float
    snr_db: float
    fft_bins_hz: list[FFTBin]

    @classmethod
    def from_bands(
        cls,
        band_powers_db: list[float],
        noise_floor_db: float,
        peak_frequency_hz: int,
    ) -> "AcousticMetrics":
        """Build metrics from the band powers so derived fields stay consistent."""
        spl = 10 * math.log10(sum(10 ** (p / 10) for p in band_powers_db))
        return cls(
            spl_db=round(spl, 1),
            peak_frequency_hz=peak_frequency_hz,
            rms_amplitude=round(10 ** ((spl - FULL_SCALE_DB) / 20), 4),
            noise_floor_db=round(noise_floor_db, 1),
            snr_db=round(spl - noise_floor_db, 1),
            fft_bins_hz=[
                FFTBin(band=b, power_db=round(p, 1))
                for b, p in zip(BAND_NAMES, band_powers_db, strict=True)
            ],
        )


class AcousticStatus(Status):
    clipping_detected: bool
    gain_db: float = 12.0


class AcousticEvent(BaseEvent):
    sensor_type: Literal["acoustic_array"] = "acoustic_array"
    metrics: AcousticMetrics
    status: AcousticStatus