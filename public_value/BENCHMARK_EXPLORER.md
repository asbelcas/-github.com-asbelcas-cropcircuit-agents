# Private Benchmark Explorer

This single-file browser tool compares:

1. one coarse CropCircuit benchmark record, and
2. one aggregate cohort JSON file produced by `benchmark_aggregate.mjs`.

Nothing is uploaded.

## Privacy behavior

The explorer respects the aggregator's suppression flag.

If a matching cohort has fewer records than the configured privacy floor, the explorer displays the sample size but **does not reveal or infer median/percentile statistics**.

## Current limitation

The first version expects cohorts grouped by:

```text
region,acreage_band
```

That grouping is intentionally coarse.

## Interpretation

The explorer compares:

- weekly worker-hours
- labor share by broad category

It shows whether the farm falls below p25, inside the middle 50%, or above p75 for a cohort.

Those positions are **descriptive, not evaluative**. Higher or lower labor can be appropriate depending on farm goals, production stage, weather, enterprise mix, mechanization, animal-care requirements, and many other factors.

## Current data state

CropCircuit does not yet publish a populated benchmark dataset. The explorer exists now so the infrastructure is ready before data collection and so other organizations can use the open specification with their own privacy-suppressed aggregates.
