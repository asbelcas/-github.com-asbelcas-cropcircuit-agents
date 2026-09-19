# CropCircuit Farm Labor Data Contract

CropCircuit's local-first labor tools use one small interoperable row format.

## Canonical columns

| Column | Required | Meaning |
| --- | --- | --- |
| `date` | yes | Observation date in `YYYY-MM-DD` |
| `category` | yes | Human-facing broad category |
| `task` | yes | Operator's own task name |
| `chore_code` | no | Canonical CropCircuit Open Farm Chore Taxonomy code |
| `minutes` | yes | Elapsed minutes for the occurrence |
| `workers` | yes | Number of workers involved |
| `worker_hours` | yes | `minutes / 60 × workers` |
| `notes` | no | Local context; stripped before anonymous benchmarking |

## Compatibility rule

**Free text remains authoritative for the operator; the chore code is an interoperability layer.**

A tool must not overwrite the user's task name merely because a `chore_code` exists.

When grouping repeated work:

1. if `chore_code` is present, group by code;
2. otherwise fall back to normalized task name and category.

That lets older uncoded CropCircuit CSVs remain usable.

## Worker-hours invariant

```text
worker_hours = minutes / 60 × workers
```

A validator may allow small rounding differences because CSV exports generally round worker-hours to two decimal places.

## Privacy boundary

The full labor log is **local operational data** and can include exact dates and free-text notes.

Those fields must not automatically flow into the public benchmark layer.

The labor-to-benchmark transform intentionally drops:

- exact date
- task name
- chore code
- notes
- any farm/person identifiers

The benchmark keeps only broad operational bands and category-share percentages.

## Files

- `farm_labor_record.schema.json` — logical record schema
- `validate_labor_contract.mjs` — zero-dependency CSV validator
- `examples/synthetic_labor_log_before.csv` — synthetic demonstration data
- `examples/synthetic_labor_log_after.csv` — synthetic after-change data

The example files are fabricated demonstration data and do not describe a real farm.
