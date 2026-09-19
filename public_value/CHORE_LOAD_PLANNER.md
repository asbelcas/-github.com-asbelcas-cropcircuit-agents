# Farm Chore Load Planner

The Farm Chore Load Planner expands a recurring CropCircuit chore schedule into daily estimated work.

It answers a simple planning question:

**Given my own task-duration estimates, where does the recurring schedule bunch too much work into the same day?**

## Inputs

- chore schedule CSV
- planning start date
- number of days to view
- user-defined available chore minutes per day

The scheduler's own CSV format works directly.

## Outputs

For every day in the planning window:

- number of scheduled tasks
- estimated scheduled minutes
- percentage of entered daily capacity
- a simple within / near / above-capacity flag
- task list with canonical chore codes when present

## Capacity is not a work recommendation

The tool does not decide how much someone should work.

The operator enters the number of chore minutes they want to make available.

This lets the tool expose schedule bunching without embedding a labor expectation.

## Recurrence semantics

The planner supports the recurrence forms produced by CropCircuit's Offline Farm Chore Scheduler:

- one time
- daily
- weekly
- monthly
- yearly
- interval N for recurring events

For monthly and yearly recurrence, invalid calendar dates are skipped rather than shifted. For example, a monthly task beginning on January 31 does not silently move to February 28.

## Estimate calibration

Planned minutes can be improved over time with the [Schedule Estimate Calibrator](SCHEDULE_CALIBRATION.md), which compares schedule estimates with observed labor-log durations.
