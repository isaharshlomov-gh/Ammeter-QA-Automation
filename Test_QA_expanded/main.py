"""Start all emulators and execute the configured QA test suite."""

import argparse
import threading
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.client import request_current_from_ammeter
from src.testing.test_framework import AmmeterTestFramework


EMULATORS = [
    ("greenlee", GreenleeAmmeter, 5000, b"MEASURE_GREENLEE -get_measurement"),
    ("entes", EntesAmmeter, 5001, b"MEASURE_ENTES -get_data"),
    ("circutor", CircutorAmmeter, 5002, b"MEASURE_CIRCUTOR -get_measurement"),
]


def start_emulators():
    instances = []
    threads = []
    for name, emulator_class, port, _command in EMULATORS:
        emulator = emulator_class(port)
        thread = threading.Thread(target=emulator.start_server, name=f"{name}-server", daemon=True)
        thread.start()
        instances.append(emulator)
        threads.append(thread)
    return instances, threads


def wait_until_ready(timeout_seconds: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    for name, _class, port, command in EMULATORS:
        while True:
            try:
                request_current_from_ammeter(port, command, timeout=0.5)
                break
            except Exception:
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"{name} emulator did not start on port {port}")
                time.sleep(0.1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ammeter emulator and QA test runner")
    parser.add_argument("--serve-only", action="store_true", help="Start emulators without running QA tests")
    parser.add_argument("--config", default="config/config.yaml", help="Path to YAML configuration")
    args = parser.parse_args()

    instances, threads = start_emulators()
    try:
        wait_until_ready()
        print("All ammeter emulators are ready.")
        if args.serve_only:
            print("Press Ctrl+C to stop the emulators.")
            while True:
                time.sleep(1)
        framework = AmmeterTestFramework(args.config)
        results = [framework.run_test(name) for name, *_ in EMULATORS]
        print("\nTest summary")
        for result in results:
            stats = result["statistics"]
            print(f"{result['ammeter_type']}: {result['metadata']['successful_measurements']} samples, "
                  f"mean={stats['mean']}, stddev={stats['standard_deviation']}")
        print("\nComparison:")
        print(framework.compare_results(results)["interpretation"])
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        for emulator in instances:
            emulator.stop()
        for thread in threads:
            thread.join(timeout=1.0)


if __name__ == "__main__":
    main()
