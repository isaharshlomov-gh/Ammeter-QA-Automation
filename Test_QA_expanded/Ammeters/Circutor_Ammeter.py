"""CIRCUTOR ammeter emulator using a simplified Rogowski integration model."""

from Ammeters.base_ammeter import AmmeterEmulatorBase
from src.utils.Utils import generate_random_float


class CircutorAmmeter(AmmeterEmulatorBase):
    @property
    def get_current_command(self) -> bytes:
        # Keep the command aligned with the README/specification.
        return b"MEASURE_CIRCUTOR -get_measurement"

    def measure_current(self) -> float:
        sample_count = 10
        time_step = generate_random_float(0.001, 0.01)
        voltages = [generate_random_float(0.1, 1.0) for _ in range(sample_count)]
        return sum(voltage * time_step for voltage in voltages)
