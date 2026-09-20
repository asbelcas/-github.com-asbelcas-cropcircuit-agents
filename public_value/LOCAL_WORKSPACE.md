# CropCircuit Local Workspace

CropCircuit's local-first tools intentionally avoid requiring a central farm account.

Compatible tools use stable browser-storage keys, and `workspace.js` provides one portable backup/restore format.

## Workspace schema

Current version: **1.2**

```json
{
  "schema_version": "1.2",
  "exported_at": "ISO timestamp",
  "labor_entries": [],
  "labor_settings": {},
  "chore_schedule": [],
  "equipment_maintenance": [],
  "harvest_entries": [],
  "sales_entries": [],
  "parts_inventory": []
}
```

## Browser storage keys

- `cropcircuit_farm_labor_log_v1`
- `cropcircuit_farm_labor_settings_v1`
- `cropcircuit_chore_schedule_v1`
- `cropcircuit_equipment_maintenance_v1`
- `cropcircuit_harvest_log_v1`
- `cropcircuit_sales_log_v1`
- `cropcircuit_parts_inventory_v1`

These keys are part of the local interoperability contract.

## Backward compatibility

Workspace **1.0** contained labor, labor settings, and the chore schedule.

Workspace **1.1** added equipment maintenance, harvest, and sales.

Workspace **1.2** adds equipment-parts inventory.

`workspace.js` accepts all three versions.

In replace mode, an older backup replaces only the collections that existed in that version and deliberately preserves collections introduced later. That prevents an old backup from silently deleting newer operational records.

## Backup tool

[workspace_backup.html](workspace_backup.html) can:

- display record counts across the workspace
- export the full current workspace as JSON
- restore a compatible workspace
- merge another backup

Merge mode deduplicates records that share the same non-empty `id`.

## Private operational data

A workspace can contain exact dates, free-text tasks, labor notes, service history, part numbers and stock levels, harvest quantities, sales records, and local rate settings.

A workspace backup is therefore **not anonymous benchmark data**.

Treat it as a private farm record.

## Benchmark boundary

The anonymous benchmark pipeline is intentionally separate from the raw workspace.

Do not publish a raw workspace as benchmark input.

## No server dependency

`workspace.js` does not transmit anything.

It operates on a Storage-compatible object supplied by the caller, normally browser `localStorage`.

That reduces central data collection, but browser storage is not an encrypted vault. See [Privacy Model](PRIVACY_MODEL.md).
