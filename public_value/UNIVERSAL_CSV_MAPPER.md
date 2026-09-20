# Universal Farm CSV Mapper

The Universal Farm CSV Mapper is the general migration layer for CropCircuit's local-first tools.

It accepts an arbitrary CSV and lets the operator map its columns into one of six open operational contracts.

## Supported targets

- labor log
- recurring chore schedule
- equipment maintenance
- equipment parts inventory
- harvest log
- direct-market sales

The field registry is also published as [data_contracts.json](data_contracts.json).

## Workflow

1. choose a target contract;
2. choose a local CSV file;
3. map each CropCircuit field to a source column;
4. optionally enter a fixed value for fields that are constant across the file;
5. transform and validate;
6. export canonical CSV/JSON or add the valid rows to the browser-local CropCircuit collection.

## Why fixed values matter

Many exports omit context that is known outside the file.

For example:

- a market export may not include a "channel" column because every row came from the same market;
- a maintenance sheet may apply entirely to one equipment unit;
- a harvest sheet may use one unit for every row.

A fixed value avoids modifying the source spreadsheet solely to add repetitive context.

## Validation

The mapper currently checks:

- required fields
- date parsing
- non-negative numeric fields
- supported chore recurrence values

Invalid rows are omitted from the transformed result and counted as warnings.

It does not silently fabricate missing required values.

## Labor convenience

If a labor row has minutes and workers but no worker-hours, the mapper calculates:

```text
worker_hours = minutes / 60 × workers
```

## Sales convenience

Missing optional payment fees, refunds/discounts, and direct costs are normalized to zero.

This is arithmetic normalization only; it is not accounting classification.

## Privacy

The CSV stays in the browser.

No upload, analytics, account, or server-side conversion is required.

## Domain boundaries

Field conversion is not domain verification.

The mapper does not determine:

- whether an accounting field has the correct tax treatment;
- whether a part cross-reference is mechanically compatible;
- whether a maintenance interval is safe;
- whether an agronomic unit or category is appropriate.

Those remain operator/domain decisions.
