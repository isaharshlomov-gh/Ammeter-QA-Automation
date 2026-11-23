"""Greenlee ammeter emulator using Ohm's law."""

from Ammeters.base_ammeter import AmmeterEmulatorBase
from src.utils.Utils import generate_random_float


class GreenleeAmmeter(AmmeterEmulatorBase):
    @property
    def get_current_command(self) -> bytes:
        return b"MEASURE_GREENLEE -get_measurement"

    def measure_current(self) -> float:
        voltage = generate_random_float(1.0, 10.0)
        resistance = generate_random_float(0.1, 100.0)
        return voltage / resistance
