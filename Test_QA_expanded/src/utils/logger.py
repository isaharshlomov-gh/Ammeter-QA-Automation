"""Consistent console and file logging for test runs."""

import logging
from pathlib import Path


class TestLogger:
    def __init__(self, test_name: str, log_dir: str = "results/logs"):
        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in test_name)
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"ammeter_test.{safe_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        if not self.logger.handlers:
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            file_handler = logging.FileHandler(Path(log_dir) / f"{safe_name}.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)
