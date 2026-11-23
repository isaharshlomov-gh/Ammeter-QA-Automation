# Design Decisions

## Architecture

The solution separates device emulation, transport, test orchestration, analysis, and persistence:

- **Emulators** implement a shared abstract server contract and retain their original measurement formulas.
- **Client** owns TCP connection handling and returns a float in amperes regardless of emulator type.
- **Test framework** owns sampling schedule, failure accounting, statistics, optional reference comparison, visualization, and archival.
- **Configuration** keeps ports, commands, sampling controls, fault-injection probability, and output paths outside the Python implementation.

## Sampling semantics

`measurements_count` and `total_duration_seconds` are optional limits. At least one must be set. If both are set, the first reached limit ends the run. `sampling_frequency_hz` is converted to a target interval. Scheduling uses a monotonic clock to avoid time-of-day changes affecting elapsed-time calculations. The count limit includes failed attempts so a disconnected device cannot cause an endless count-based run.

## Statistical definitions

- Mean: arithmetic average of successful samples.
- Median: middle value (or average of the two middle values).
- Standard deviation: population standard deviation (`statistics.pstdev`) because the report describes the complete set collected in that test run.
- Minimum/maximum: smallest/largest successful sample.
- Coefficient of variation: population standard deviation divided by absolute mean, expressed as a percentage. It is used as a normalized repeatability indicator, not as an accuracy metric.

## Accuracy

The three supplied emulators use different randomized input ranges and mathematical models. There is no common known current supplied by the exercise. Therefore, cross-emulator mean comparison alone cannot identify the most accurate ammeter. If a calibrated `reference_current_a` is supplied in configuration, the framework reports absolute and percentage error and can identify the closest mean to that reference.

## Error handling and fault injection

The TCP client converts socket failures, timeouts, empty replies, invalid numeric responses, and emulator error replies into `AmmeterCommunicationError`. The framework records individual failed attempts and continues sampling. Optional `failure_probability` in configuration injects synthetic failures to exercise the reporting path; it is disabled by default.

## Dependencies

PyYAML is required to read the supplied YAML configuration. Matplotlib is optional for PNG plots. All other functionality uses the Python standard library.
