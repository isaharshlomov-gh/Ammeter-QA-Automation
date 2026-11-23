import tempfile
import unittest
from pathlib import Path

from src.testing.test_framework import AmmeterTestFramework


class StatisticsTests(unittest.TestCase):
    def test_statistics(self):
        self.assertEqual(
            AmmeterTestFramework._statistics([1.0, 2.0, 3.0]),
            {"mean": 2.0, "median": 2.0, "standard_deviation": 0.816496580927726,
             "minimum": 1.0, "maximum": 3.0},
        )

    def test_empty_statistics(self):
        self.assertIsNone(AmmeterTestFramework._statistics([])["mean"])

    def test_unknown_ammeter_is_rejected(self):
        framework = AmmeterTestFramework()
        with self.assertRaises(ValueError):
            framework._ammeter_config("unknown")

    def test_comparison_reports_consistency_not_accuracy(self):
        framework = AmmeterTestFramework()
        report = framework.compare_results([
            {"ammeter_type": "greenlee", "statistics": {"mean": 10.0, "standard_deviation": 1.0},
             "metadata": {"successful_measurements": 5}},
            {"ammeter_type": "entes", "statistics": {"mean": 20.0, "standard_deviation": 1.0},
             "metadata": {"successful_measurements": 5}},
        ])
        self.assertEqual(report["most_consistent_by_relative_spread"], "entes")
        self.assertNotIn("most_accurate_to_reference", report)


if __name__ == "__main__":
    unittest.main()
