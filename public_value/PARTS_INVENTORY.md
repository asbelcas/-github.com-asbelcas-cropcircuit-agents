# Offline Equipment Parts Inventory

Farm maintenance records are more useful when the parts needed for routine work are also findable.

This tool keeps a small browser-local parts register.

## Fields

- equipment / system
- part name
- OEM / primary part number
- alternate part numbers
- supplier
- storage location
- quantity on hand
- reorder threshold
- preferred order quantity

## Cross-reference boundary

CropCircuit does **not** decide whether two part numbers are equivalent.

Alternate numbers are operator-entered references only.

Before installing a substitute part, verify compatibility with manufacturer/service documentation or a qualified supplier.

## Reorder logic

The tool uses only the values entered by the operator.

```text
reorder when:
  quantity on hand <= reorder threshold
```

If a preferred order quantity is supplied, the reusable math can return that as the order quantity while ensuring it is large enough to move stock above the threshold.

No consumption rate or lead-time assumption is hidden in the calculation.

## Privacy

The browser storage key is:

```text
cropcircuit_parts_inventory_v1
```

The tool exports CSV and JSON backup files.

No account, analytics, or server sync are required.

## Reusable math

- `inventory_math.js`
- `inventory_math.test.mjs`
