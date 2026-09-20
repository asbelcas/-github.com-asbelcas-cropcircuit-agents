# Synthetic Data QA Work Sample

This sample demonstrates a small but complete spreadsheet-cleanup workflow:

**preserve raw data → normalize deterministic fields → flag ambiguous records → detect duplicates → reconcile totals → document changes**

No real customer or employer data is used.

## What this proves

- structured spreadsheet cleanup
- deterministic normalization
- duplicate detection without silently deleting evidence
- exception handling for ambiguous or incomplete values
- formula-based reconciliation
- documented QA and change rules
- human-review gates instead of invented values

## Files

- `raw_data.csv` — intentionally messy synthetic source data
- `cleaned_data.csv` — normalized output with duplicate/review flags
- `exceptions.csv` — records that should not be auto-corrected
- `qa_summary.csv` — before/after metrics and reconciliation checks

A formatted XLSX version is maintained separately for application use.

## Design rule

If a value is ambiguous, missing, or invalid, the workflow flags it for review rather than guessing. The source evidence is preserved.

This is a portfolio proof asset for Casey Armstrong / CropCircuit operations and data-quality work.
