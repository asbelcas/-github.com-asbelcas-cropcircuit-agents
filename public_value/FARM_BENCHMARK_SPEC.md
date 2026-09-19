# CropCircuit Anonymous Small-Farm Operations Benchmark

## Purpose

Small farms rarely know whether a chore is unusually expensive, a normal part of the system, or a sign that layout and workflow need attention.

CropCircuit's benchmark layer is designed to answer questions like:

- How many worker-hours per week are similar small farms spending?
- What share of labor goes to livestock, harvest, wash/pack, maintenance, or admin?
- Which enterprise mixes have the highest labor concentration in particular categories?
- How does a farm's own time study compare with a coarse peer group?

The system is intentionally designed so the benchmark can become useful **without building a database of identifiable farms**.

## Privacy design

Benchmark records intentionally exclude:

- farm name
- person name
- email or phone
- street address
- county or ZIP code
- exact acreage
- exact revenue
- exact labor wage
- exact dates
- free-text notes
- GPS coordinates
- financial account information

Instead, the record uses coarse bands such as:

- acreage: `1-4.9`, `5-19.9`, etc.
- operator count: `1`, `2`, `3-5`, `6-plus`
- labor cost: broad hourly-cost bands
- region: Michigan / Great Lakes / Midwest / United States / Other
- season instead of exact dates

## Publication rule: k-anonymity floor

CropCircuit should not publish a cohort statistic until at least **5 independent benchmark records** are present in that cohort.

The aggregator therefore has a default `k=5` suppression rule.

If a requested grouping has fewer than 5 records:

- count may be reported as "insufficient sample" or omitted
- median/percentile statistics must not be published
- rare enterprise combinations should be rolled up into broader groups instead of exposed

This is not a guarantee of anonymity, but it reduces the risk of singling out one small operation.

## Current state

The benchmark **specification and tooling are public; there is not yet a real public benchmark dataset**.

That distinction is important. CropCircuit will not fabricate baseline numbers just to make the product look populated.

The next valid milestone is collecting enough genuinely contributed records to publish the first cohorts that meet the k-anonymity threshold.

## Files

- `farm_benchmark.schema.json` — machine-readable record contract
- `benchmark_builder.html` — browser-only builder for creating a coarse benchmark record
- `benchmark_aggregate.mjs` — dependency-free aggregation/suppression utility
- `benchmark_aggregate.test.mjs` — tests for privacy threshold and statistics

## Design principle

**Observe first. Aggregate second. Monetize last.**

If the benchmark becomes useful, future paid layers could include richer cohort filtering, historical trend reports, institutional dashboards, or API access. The underlying privacy floor should remain intact.
