# Schedule Estimate Calibrator

Farm schedules often begin with guessed task durations.

This tool compares those planned durations with actual elapsed minutes from a CropCircuit-compatible labor log.

## Inputs

### Chore schedule CSV

Expected fields:

- task
- chore_code, optional
- estimated_minutes

The Offline Farm Chore Scheduler already exports these fields.

### Labor log CSV

Expected fields:

- task
- chore_code, optional
- minutes

The Offline Farm Labor Log and canonical import mapper already produce these fields.

## Matching

1. if a canonical `chore_code` exists, match by code;
2. otherwise match by normalized free-text task name.

The export records whether each match used the canonical code or fallback task text.

## Output

For each matched scheduled task:

- planned minutes
- number of actual observations
- median actual elapsed minutes
- difference in minutes
- actual-to-plan ratio
- suggested planning value, equal to the observed median rounded to a whole minute

The suggested value is **not** an efficiency standard.

It is simply a better estimate of how long that farm's observed work has recently taken.

## Why median?

A single interruption or unusual day can distort a mean.

Median is used as a simple robust planning estimate. With small sample sizes, it should still be treated cautiously.

## Privacy

Both CSV files stay in the browser. Nothing is uploaded.
