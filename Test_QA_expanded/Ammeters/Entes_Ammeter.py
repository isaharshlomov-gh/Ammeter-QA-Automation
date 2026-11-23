"""ENTES ammeter emulator using a Hall-effect model."""

from Ammeters.base_ammeter import AmmeterEmulatorBase
from src.utils.Utils import generate_random_float


class EntesAmmeter(AmmeterEmulatorBase):
    @property
    def get_current_command(self) -> bytes:
        return b"MEASURE_ENTES -get_data"

    def measure_current(self) -> float:
        magnetic_field = generate_random_float(0.01, 0.1)
        calibration_factor = generate_random_float(500.0, 2000.0)
        return magnetic_field * calibration_factor
