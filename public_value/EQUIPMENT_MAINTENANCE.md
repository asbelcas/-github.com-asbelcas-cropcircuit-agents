# Offline Equipment Maintenance Log

Equipment maintenance was added because a recurring farm-management problem is not just "what should be serviced?" but **where is the service history and what is due next?**

CropCircuit keeps this tool intentionally neutral about maintenance intervals.

## The operator supplies

For each equipment/service combination:

- equipment name
- service item
- current meter hours
- last service meter hours
- service interval in hours
- last service date
- calendar interval in days

Either the hour interval, date interval, or both can be used.

## Status

The reusable math reports:

### Meter-hours

```text
next due hours
  = last service hours + interval hours

hours remaining
  = next due hours − current hours
```

### Calendar

```text
next due date
  = last service date + interval days
```

The overall item is marked overdue if either configured clock is overdue.

## Actions

The browser tool can:

- update current meter hours
- mark an item serviced today at the current meter
- delete an item
- export CSV
- export a JSON backup
- restore a JSON backup

## No default service schedule

CropCircuit deliberately does not provide default oil, filter, grease, inspection, or other service intervals.

Those intervals depend on the equipment, usage, environment, regulations, and manufacturer/service guidance.

The tool manages the schedule the operator chooses; it does not invent one.

## Privacy

Data is stored under:

```text
cropcircuit_equipment_maintenance_v1
```

in browser local storage.

No server sync or analytics are required.

## Reusable math

- `equipment_math.js`
- `equipment_math.test.mjs`
