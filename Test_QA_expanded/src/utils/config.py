"""Configuration loading and validation."""

from pathlib import Path
from typing import Any, Dict

import yaml


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path.resolve()}")
    with path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}
    if not isinstance(config, dict):
        raise ValueError("The YAML configuration root must be a mapping")
    return config
