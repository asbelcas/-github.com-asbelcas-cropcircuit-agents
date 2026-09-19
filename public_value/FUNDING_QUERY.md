# Funding Radar CLI

Query the public funding dataset without a browser or spreadsheet.

No dependencies are required beyond Node.js.

## Examples

Show open opportunities relevant to Kalamazoo County:

```bash
node public_value/funding_query.mjs --status open --county Kalamazoo
```

Show open and continuous opportunities relevant to a county:

```bash
node public_value/funding_query.mjs \
  --status open,continuous \
  --county Kalamazoo
```

Show dated opportunities due in the next 30 days:

```bash
node public_value/funding_query.mjs \
  --status open \
  --due-within 30
```

Return JSON for another program or agent:

```bash
node public_value/funding_query.mjs \
  --status open,continuous,watch \
  --format json
```

Return tab-separated data:

```bash
node public_value/funding_query.mjs \
  --tag "regenerative agriculture" \
  --format tsv
```

## County behavior

A county query includes:

1. statewide records with no county restriction, and
2. county-scoped records that explicitly include the requested county.

That prevents statewide programs from disappearing just because a county filter is active.

## Reproducible queries

Use `--as-of` to make deadline filtering deterministic:

```bash
node public_value/funding_query.mjs \
  --status open \
  --due-within 30 \
  --as-of 2026-09-19
```

This utility reads the same `funding_radar.json` used by CropCircuit's other public funding outputs.
