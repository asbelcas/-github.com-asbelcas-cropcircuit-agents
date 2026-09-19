# Offline Harvest Log

The Harvest Log addresses a basic farm-recordkeeping need without requiring a cloud account.

## Records

Each entry contains:

- date
- crop / item
- quantity
- unit
- optional destination

The current destination list includes CSA, farmers market, farm stand, wholesale, restaurant, home, donation, and other.

## Unit rule

CropCircuit does **not** automatically convert unlike harvest units.

Examples:

- pounds remain pounds
- bunches remain bunches
- count remains count

A crop harvested partly by weight and partly by count will appear as separate summary rows.

This avoids inventing conversion factors that depend on grading and pack style.

## Summaries

A selected date range can be summarized by crop/item + unit.

The tool reports:

- entry count
- total quantity

## Period comparison

Two date ranges can be compared.

For each crop/item + unit combination:

- period A quantity
- period B quantity
- absolute change
- percentage change when period A is nonzero

## Revenue boundary

Harvest quantity is not sales revenue.

CropCircuit deliberately does not infer sale price or dollar value from the harvest log.

Sales-channel economics are handled separately by tools such as:

- Farmers Market Break-Even
- CSA Share Price & Break-Even

## Privacy and backup

The browser storage key is:

```text
cropcircuit_harvest_log_v1
```

The tool can export CSV and a JSON backup.

No server sync or analytics are required.

## Reusable math

- `harvest_math.js`
- `harvest_math.test.mjs`
