Ammeter-QA-Automation
Repository navigation
Code
Issues
Pull requests
Actions
Projects
Wiki
Security and quality
Insights
Settings
Files
Go to file
t
T
Test_QA_expanded
Ammeters
Exam
config
examples
results
src
tests
.gitignore
DESIGN_DECISIONS.md
README.md
main.py
requirements.txt
Ammeter-QA-Automation/Test_QA_expanded
/README.md
isaharshlomov-gh
isaharshlomov-gh
Initial Ammeter QA automation solution
85279b4
 · 
4 hours ago
Ammeter-QA-Automation/Test_QA_expanded
/README.md

Preview

Code

Blame
138 lines (100 loc) · 7.2 KB
Ammeter Emulator QA Framework
A Python QA framework for the supplied Greenlee, ENTES, and CIRCUTOR current-meter emulators. It starts each emulator as a TCP server, samples it through one common client API, calculates descriptive statistics, archives every test run as JSON, and can optionally create measurement plots.

Important: The supplied emulators generate independent random values using different formulas and ranges. Comparing their raw means does not prove which device is physically accurate. Accuracy can only be evaluated when a known reference_current_a is configured. Without a reference, the framework reports relative consistency (coefficient of variation), not accuracy.

Requirements
Python 3.9 or newer
Required third-party package: PyYAML
Optional package: matplotlib for plots
Install dependencies:

python -m pip install -r requirements.txt
To enable plots, install Matplotlib separately:

python -m pip install matplotlib
Run the complete demo
From the project root:

python main.py
The command starts the three emulators, waits until they respond, runs the configured QA test against each one, prints a summary, and shuts down the emulator threads cleanly.

Start only the emulator servers:

python main.py --serve-only
Run tests against emulators that are already running:

python examples/run_tests.py
Run the unit tests:

python -m unittest discover -s tests -v
Emulator protocol
Emulator	Default port	Request command	Simulated measurement model
Greenlee	5000	MEASURE_GREENLEE -get_measurement	Ohm's law: I = V / R; V is 1–10 V and R is 0.1–100 Ω
ENTES	5001	MEASURE_ENTES -get_data	Hall-effect model: I = B * K; B is 0.01–0.1 T and K is 500–2000
CIRCUTOR	5002	MEASURE_CIRCUTOR -get_measurement	Simplified integration: sum of sampled V * dt; V is 0.1–1.0 V and dt is 0.001–0.01 s
Each request opens a TCP connection, sends the exact command, and receives a numeric value in amperes. Invalid commands and server-side measurement errors return an ERROR: response, which the client converts to an AmmeterCommunicationError.

Configuration
Edit config/config.yaml to change sampling and device settings. Example:

testing:
  sampling:
    measurements_count: 20       # stop after this many attempts; null disables count limit
    total_duration_seconds: null  # optional time limit; null disables duration limit
    sampling_frequency_hz: 5
  request_timeout_seconds: 3
  simulation:
    failure_probability: 0.0     # set e.g. 0.05 to inject 5% simulated sample failures
At least one of measurements_count or total_duration_seconds must be configured. If both are set, sampling stops when the first limit is reached. The sampling frequency defines the target interval between attempts. A failed attempt is recorded and counts toward the configured attempt count, so the framework does not run indefinitely when the device is unavailable.

Set analysis.reference_current_a to a known test current to calculate absolute and percentage error. Leave it null when no calibrated reference source is available.

Results
Each test run receives a UUID and creates a JSON file under results/. The record includes:

Run ID, device, UTC start/end timestamps, port and command
Sampling configuration and elapsed duration
Each successful measurement and its timestamp
Mean, median, population standard deviation, minimum and maximum
Failed attempts and error messages
Accuracy metrics, when a reference current is configured
Log files are written under results/logs/. When Matplotlib is installed and visualization is enabled, plots are saved under results/plots/. Plot generation is optional and does not prevent measurements from running if Matplotlib is unavailable.

Project structure
Ammeters/                  TCP emulator servers and client
  base_ammeter.py          Shared server lifecycle and protocol handling
  Greenlee_Ammeter.py      Greenlee measurement model
  Entes_Ammeter.py         ENTES measurement model
  Circutor_Ammeter.py      CIRCUTOR measurement model
  client.py                Unified TCP measurement client
config/config.yaml          Runtime configuration
src/testing/test_framework.py
                            Sampling, statistics, comparison and archiving
src/utils/                  Configuration, logging and random-value helper
examples/run_tests.py       Run tests against already-started servers
tests/                      Unit tests
Exam/                       Original exercise specification
results/                    Generated JSON results, logs and plots
Design decisions and known limitations
One common API: AmmeterTestFramework.run_test(ammeter_type) hides device-specific TCP details from the sampling and reporting code.
Monotonic timing: time.monotonic() is used for sampling intervals and duration limits so wall-clock adjustments do not affect scheduling.
Robust communication: Connection errors, timeouts, empty responses, invalid commands and non-numeric values are reported as failed samples rather than crashing the entire run.
Server lifecycle: Emulator servers use a timeout-based accept loop and a stop event, allowing orderly shutdown and reuse of the configured ports.
Minimal dependencies: YAML is the only required external dependency. Statistics, sockets, threading, JSON, UUIDs and timing use the Python standard library. Matplotlib is optional.
Precision versus accuracy: A low standard deviation or coefficient of variation means repeatability/consistency, not closeness to the true current. A calibrated reference is needed to claim accuracy.
Emulator scope: These are software emulators with randomized formulas, not calibrated physical instruments. Results validate the software framework and emulator protocol, not real-world electrical performance.
Fixes applied to the supplied starter project
Aligned ports with the README and specification: 5000, 5001 and 5002 (the starter main.py used 5001–5003).
Corrected the CIRCUTOR request command to match the documented command; the starter emulator expected an extra undocumented -current argument.
Replaced the placeholder run_test implementation and corrected the example caller to pass the ammeter type.
Implemented the missing configuration values and validation.
Changed the client to return a numeric measurement and raise a clear communication exception on errors.
Added clean server shutdown, address reuse, socket timeouts and invalid-command handling.
Removed global random seeding from each emulator instance; Python's module-level random generator is already seeded and shared safely for these simple simulations.
Replaced incomplete logging setup with file and console handlers.
Reduced required packages to PyYAML; NumPy, SciPy, pandas and seaborn were not needed for the implemented functionality.
Sample execution
A sample execution is included at results/sample_runs.json. It contains three runs (one per emulator), with 20 successful samples per run in the environment used to prepare this submission. Random measurement values will differ on each execution.

