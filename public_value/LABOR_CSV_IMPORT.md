# Labor CSV Import Mapper

CropCircuit should not require a farm to start over just because its existing spreadsheet uses different column names.

The Labor CSV Import Mapper converts an arbitrary labor CSV into the CropCircuit [Farm Labor Data Contract](LABOR_DATA_CONTRACT.md).

## What it maps

A source column can be mapped to:

- date
- category
- task
- chore code
- elapsed minutes
- workers involved
- worker-hours
- notes

The tool attempts conservative header-name guesses, but the operator confirms the mapping.

## Worker-hours

If the source file does not contain a worker-hours column, the mapper calculates:

```text
worker_hours = minutes / 60 × workers
```

## Dates

ISO dates such as `2026-09-19` pass through unchanged.

Other date strings are parsed by the browser when possible and normalized to `YYYY-MM-DD`.

Ambiguous or invalid dates are flagged.

## Privacy

All parsing and transformation happens in the browser.

- no upload
- no account
- no analytics
- no network request

## Why this matters

Interoperability is more valuable when adoption does not require abandoning an existing recordkeeping workflow.

The canonical export can feed:

- Labor Opportunity Analyzer
- Equipment Cost Threshold Analyzer
- Workflow Experiment Analyzer
- taxonomy mapper
- labor-to-benchmark transform

without requiring farms to use the CropCircuit logger itself.
