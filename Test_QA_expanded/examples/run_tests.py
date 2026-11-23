"""Run QA tests against already-running ammeter emulators."""

import json
from pathlib import Path

from src.testing.test_framework import AmmeterTestFramework


def main() -> None:
    framework = AmmeterTestFramework()
    results = [framework.run_test(name) for name in ("greenlee", "entes", "circutor")]
    comparison = framework.compare_results(results)
    print(json.dumps(comparison, indent=2))
    print(f"Archived {len(results)} runs under {Path('results').resolve()}")


if __name__ == "__main__":
    main()
