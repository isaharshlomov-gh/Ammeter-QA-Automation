"""Small shared utility functions."""

import random


def generate_random_float(min_value: float, max_value: float) -> float:
    """Generate a random float in the inclusive numeric range."""
    if min_value > max_value:
        raise ValueError("min_value must be less than or equal to max_value")
    return random.uniform(min_value, max_value)
