"""Configurable measurement, analysis, and result-archiving framework."""

import json
import random
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from Ammeters.client import request_current_from_ammeter
from src.utils.config import load_config
from src.utils.logger import TestLogger


DEFAULT_AMMETERS = {
    "greenlee": {"port": 5000, "command": "MEASURE_GREENLEE -get_measurement"},
    "entes": {"port": 5001, "command": "MEASURE_ENTES -get_data"},
    "circutor": {"port": 5002, "command": "MEASURE_CIRCUTOR -get_measurement"},
}


class AmmeterTestFramework:
    """Run repeatable sampling tests against configured ammeter TCP servers.

    Sampling stops when either the configured measurement count or duration is
    reached. At least one of those limits must be provided.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = load_config(config_path)
        self._validate_config()

    def _validate_config(self) -> None:
        sampling = self.config.get("testing", {}).get("sampling", {})
        count = sampling.get("measurements_count")
        duration = sampling.get("total_duration_seconds")
        frequency = sampling.get("sampling_frequency_hz", 1)
        if count is None and duration is None:
            raise ValueError("Configure measurements_count, total_duration_seconds, or both")
        if count is not None and (not isinstance(count, int) or count <= 0):
            raise ValueError("measurements_count must be a positive integer or null")
        if duration is not None and (not isinstance(duration, (int, float)) or duration <= 0):
            raise ValueError("total_duration_seconds must be positive or null")
        if not isinstance(frequency, (int, float)) or frequency <= 0:
            raise ValueError("sampling_frequency_hz must be positive")

    def _ammeter_config(self, ammeter_type: str) -> Dict[str, Any]:
        name = ammeter_type.strip().lower()
        configured = self.config.get("ammeters", {}).get(name)
        if configured is None:
            configured = DEFAULT_AMMETERS.get(name)
        if configured is None:
            supported = ", ".join(sorted(DEFAULT_AMMETERS))
            raise ValueError(f"Unknown ammeter '{ammeter_type}'. Supported types: {supported}")
        return {**configured, "name": name}

    @staticmethod
    def _statistics(values: List[float]) -> Dict[str, Optional[float]]:
        if not values:
            return {key: None for key in ("mean", "median", "standard_deviation", "minimum", "maximum")}
        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            # Population standard deviation describes the collected run itself.
            "standard_deviation": statistics.pstdev(values) if len(values) > 1 else 0.0,
            "minimum": min(values),
            "maximum": max(values),
        }

    def run_test(self, ammeter_type: str) -> Dict[str, Any]:
        device = self._ammeter_config(ammeter_type)
        sampling = self.config["testing"]["sampling"]
        count_limit = sampling.get("measurements_count")
        duration_limit = sampling.get("total_duration_seconds")
        interval = 1.0 / float(sampling.get("sampling_frequency_hz", 1))
        timeout = float(self.config.get("testing", {}).get("request_timeout_seconds", 3.0))
        fault_probability = float(self.config.get("testing", {}).get("simulation", {}).get("failure_probability", 0.0))
        if not 0.0 <= fault_probability < 1.0:
            raise ValueError("failure_probability must be >= 0 and < 1")

        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        start_clock = time.monotonic()
        deadline = start_clock + float(duration_limit) if duration_limit is not None else None
        values: List[float] = []
        errors: List[Dict[str, str]] = []
        timestamps: List[str] = []
        logger = TestLogger(
            f"{device['name']}_{run_id}",
            self.config.get("result_management", {}).get("logs_directory", "results/logs"),
        )
        logger.info(f"Starting {device['name']} run {run_id}")

        while True:
            now = time.monotonic()
            if count_limit is not None and len(values) + len(errors) >= count_limit:
                break
            if deadline is not None and now >= deadline:
                break

            sample_time = datetime.now(timezone.utc).isoformat()
            try:
                if fault_probability and random.random() < fault_probability:
                    raise RuntimeError("Simulated measurement failure (configured fault injection)")
                measurement = request_current_from_ammeter(
                    int(device["port"]), device["command"],
                    host=device.get("host", "127.0.0.1"), timeout=timeout,
                )
                values.append(measurement)
                timestamps.append(sample_time)
                logger.info(f"Sample {len(values)}: {measurement:.8g} A")
            except Exception as exc:
                errors.append({"timestamp": sample_time, "error": f"{type(exc).__name__}: {exc}"})
                logger.error(errors[-1]["error"])

            if count_limit is not None and len(values) + len(errors) >= count_limit:
                break
            next_sample = start_clock + (len(values) + len(errors)) * interval
            if deadline is not None:
                next_sample = min(next_sample, deadline)
            sleep_for = next_sample - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)

        finished_at = datetime.now(timezone.utc)
        elapsed = time.monotonic() - start_clock
        result: Dict[str, Any] = {
            "run_id": run_id,
            "ammeter_type": device["name"],
            "metadata": {
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "duration_seconds": round(elapsed, 6),
                "port": int(device["port"]),
                "command": device["command"],
                "sampling_frequency_hz": 1.0 / interval,
                "requested_measurements_count": count_limit,
                "requested_duration_seconds": duration_limit,
                "successful_measurements": len(values),
                "failed_measurements": len(errors),
            },
            "measurements": [{"timestamp": ts, "current_a": val} for ts, val in zip(timestamps, values)],
            "statistics": self._statistics(values),
            "errors": errors,
        }

        reference_current = self.config.get("analysis", {}).get("reference_current_a")
        if reference_current is not None and values:
            result["accuracy_assessment"] = {
                "reference_current_a": float(reference_current),
                "mean_absolute_error_a": abs(result["statistics"]["mean"] - float(reference_current)),
                "mean_absolute_percentage_error": (
                    abs(result["statistics"]["mean"] - float(reference_current)) / abs(float(reference_current)) * 100
                    if float(reference_current) != 0 else None
                ),
                "note": "Accuracy is assessed only because a reference current was configured.",
            }

        self._archive_result(result)
        self._create_visualization(result)
        logger.info(f"Finished run {run_id}: {len(values)} successful, {len(errors)} failed")
        return result

    def _archive_result(self, result: Dict[str, Any]) -> Path:
        result_dir = Path(self.config.get("result_management", {}).get("results_directory", "results"))
        result_dir.mkdir(parents=True, exist_ok=True)
        path = result_dir / f"{result['ammeter_type']}_{result['run_id']}.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return path

    def _create_visualization(self, result: Dict[str, Any]) -> Optional[str]:
        visualization = self.config.get("analysis", {}).get("visualization", {})
        if not visualization.get("enabled", False) or not result["measurements"]:
            return None
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            return None

        output_dir = Path(self.config.get("result_management", {}).get("plots_directory", "results/plots"))
        output_dir.mkdir(parents=True, exist_ok=True)
        x_values = list(range(1, len(result["measurements"]) + 1))
        y_values = [sample["current_a"] for sample in result["measurements"]]
        figure, axis = plt.subplots()
        axis.plot(x_values, y_values, marker="o")
        axis.set(title=f"{result['ammeter_type'].upper()} current measurements", xlabel="Sample", ylabel="Current (A)")
        axis.grid(True, alpha=0.3)
        figure.tight_layout()
        output_path = output_dir / f"{result['ammeter_type']}_{result['run_id']}.png"
        figure.savefig(output_path)
        plt.close(figure)
        return str(output_path)

    def compare_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare run distributions; this is not an accuracy ranking without a reference."""
        comparison = {}
        for result in results:
            stats = result.get("statistics", {})
            mean_value = stats.get("mean")
            stddev = stats.get("standard_deviation")
            comparison[result["ammeter_type"]] = {
                "mean_a": mean_value,
                "standard_deviation_a": stddev,
                "coefficient_of_variation_percent": (
                    stddev / abs(mean_value) * 100
                    if mean_value not in (None, 0) and stddev is not None else None
                ),
                "successful_measurements": result.get("metadata", {}).get("successful_measurements", 0),
            }

        # Coefficient of variation is useful for comparing relative spread, not accuracy.
        precision_candidates = {
            name: data["coefficient_of_variation_percent"]
            for name, data in comparison.items()
            if data["coefficient_of_variation_percent"] is not None
        }
        most_consistent = min(precision_candidates, key=precision_candidates.get) if precision_candidates else None
        report = {
            "runs": comparison,
            "most_consistent_by_relative_spread": most_consistent,
            "interpretation": (
                "The lowest coefficient of variation indicates the most consistent output in this run. "
                "It does not establish physical accuracy. Accuracy requires a shared known reference current."
            ),
        }
        reference_current = self.config.get("analysis", {}).get("reference_current_a")
        if reference_current is not None:
            reference_current = float(reference_current)
            accuracy = {}
            for result in results:
                mean_value = result.get("statistics", {}).get("mean")
                if mean_value is not None:
                    accuracy[result["ammeter_type"]] = abs(mean_value - reference_current)
            report["reference_current_a"] = reference_current
            report["absolute_error_by_ammeter_a"] = accuracy
            report["most_accurate_to_reference"] = min(accuracy, key=accuracy.get) if accuracy else None
        return report
