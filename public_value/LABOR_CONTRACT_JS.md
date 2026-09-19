# Farm Labor JavaScript Helpers

`labor_contract.js` exposes the shared Farm Labor Data Contract as reusable zero-dependency JavaScript.

## Functions

### `workerHours({ minutes, workers })`

Calculates:

```text
minutes / 60 × workers
```

### `normalizeLaborIdentity(record)`

Returns the stable grouping identity:

1. canonical `chore_code` when present;
2. otherwise normalized category + task text.

This is the same compatibility rule used across CropCircuit's labor tools.

### `normalizeDate(value)`

Preserves ISO `YYYY-MM-DD` dates and attempts to normalize other browser-parseable dates.

### `normalizeLaborRecord(input)`

Creates the standard labor-record shape and can calculate worker-hours when missing.

### `validateLaborRecord(record, options)`

Checks the basic labor contract and optionally validates the chore code against a supplied set of known codes.

## Example

```js
import {
  normalizeLaborRecord,
  validateLaborRecord
} from "./labor_contract.js";

const record = normalizeLaborRecord({
  date: "2026-09-19",
  category: "Fencing",
  task: "Move portable fence",
  chore_code: "fencing.move",
  minutes: 30,
  workers: 1
});

console.log(record.worker_hours); // 0.5
console.log(validateLaborRecord(record)); // []
```

The helpers do not upload data and contain no biological or wage assumptions.
