# CropCircuit Local Workspace

CropCircuit's local-first tools intentionally avoid requiring a central farm account.

To make that practical, compatible tools use stable browser-storage keys, and `workspace.js` provides one backup/restore format.

## Workspace schema

Current version: **1.1**

```json
{
  "schema_version": "1.1",
  "exported_at": "ISO timestamp",
  "labor_entries": [],
  "labor_settings": {},
  "chore_schedule": [],
  "equipment_maintenance": [],
  "harvest_entries": [],
  "sales_entries": []
}
```

## Browser storage keys

- `cropcircuit_farm_labor_log_v1`
- `cropcircuit_farm_labor_settings_v1`
- `cropcircuit_chore_schedule_v1`
- `cropcircuit_equipment_maintenance_v1`
- `cropcircuit_harvest_log_v1`
- `cropcircuit_sales_log_v1`

These keys are now part of the local interoperability contract.

## Backward compatibility

Workspace **1.0** contained only labor entries, labor settings, and the chore schedule.

`workspace.js` continues to accept 1.0 backups.

When an old 1.0 backup is imported in **replace** mode, CropCircuit replaces the three fields present in that backup but deliberately preserves any newer equipment-maintenance, harvest, and sales records already stored in the browser.

A 1.1 backup can replace or merge the full workspace.

## Backup tool

[workspace_backup.html](workspace_backup.html) can:

- display record counts for all workspace collections
- export the full workspace as JSON
- restore a compatible workspace
- merge another backup

Merge mode deduplicates records that share the same non-empty `id`.

## What belongs in the workspace

### Private operational records

The workspace can contain:

- exact dates
- free-text task names
- labor notes
- equipment service history
- harvest quantities
- direct-market sales records
- locally chosen labor-rate settings

A workspace backup is therefore **not anonymous benchmark data**.

Treat it as a private farm record.

## Benchmark boundary

The anonymous benchmark pipeline exists specifically to discard operational detail before aggregation.

Do not publish a raw workspace as benchmark input.

Use the documented labor-to-benchmark transform instead.

## No server dependency

`workspace.js` does not transmit anything.

It operates on a Storage-compatible object supplied by the caller, normally browser `localStorage`.

That design reduces central data collection, but browser storage is not an encrypted vault. See [Privacy Model](PRIVACY_MODEL.md).
