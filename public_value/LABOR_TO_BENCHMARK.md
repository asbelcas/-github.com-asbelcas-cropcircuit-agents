# Labor Log → Anonymous Benchmark Record

This utility converts a CropCircuit farm labor CSV into the coarse benchmark schema.

The transformation is deliberately destructive from a privacy perspective: it **drops details rather than preserving them**.

## Input

A CSV exported from the Offline Farm Labor Log.

The source file may contain:

- date
- category
- task
- minutes
- worker count
- worker-hours
- notes

## Output

The benchmark record keeps only:

- coarse season
- broad region
- acreage band
- enterprise types
- operator-count band
- annual-context weekly worker-hours
- labor-cost band
- percentage of worker-hours by broad category

It does **not** copy:

- dates
- task names
- notes
- farm name
- contact details
- county
- street address
- exact acreage
- exact wage
- exact revenue

## Example

```bash
node public_value/labor_log_to_benchmark.mjs \
  --input cropcircuit-farm-labor-log.csv \
  --days 14 \
  --period summer \
  --region Michigan \
  --acreage-band 5-19.9 \
  --operators 1 \
  --labor-cost-band 20-24.99 \
  --enterprises vegetables,CSA
```

The resulting JSON can be checked against `farm_benchmark.schema.json` and later fed into `benchmark_aggregate.mjs`.

## Why this exists

The benchmark only becomes credible if the data pipeline is transparent. This transformer provides a reproducible path from an operator's actual time study to a coarse comparison record while intentionally discarding operational details that are not needed for benchmarking.
