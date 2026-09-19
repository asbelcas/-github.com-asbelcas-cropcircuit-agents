# CropCircuit Local Workspace

CropCircuit's local-first tools intentionally avoid requiring a central farm account.

To make that practical, the Labor Log and Chore Scheduler use stable browser-storage keys, and `workspace.js` provides a shared backup/restore format.

## Workspace schema

Current version: `1.0`

```json
{
  "schema_version": "1.0",
  "exported_at": "ISO timestamp",
  "labor_entries": [],
  "labor_settings": {},
  "chore_schedule": []
}
```

## Browser storage keys

- `cropcircuit_farm_labor_log_v1`
- `cropcircuit_farm_labor_settings_v1`
- `cropcircuit_chore_schedule_v1`

Changing those keys would break compatibility, so they are now part of the local workspace contract.

## Backup tool

[workspace_backup.html](workspace_backup.html) can:

- display current local record counts
- export the workspace as JSON
- restore a workspace
- merge another backup

Merge mode deduplicates records that already have the same non-empty `id`.

## Important privacy distinction

A workspace backup is **not anonymous benchmark data**.

It may contain:

- exact dates
- free-text task names
- notes
- local labor settings

Treat it as a private operational record.

The anonymous benchmark pipeline exists specifically to strip unnecessary identifying detail before aggregation.

## No server dependency

`workspace.js` does not transmit anything.

It operates only on a Storage-compatible object supplied by the caller, usually browser `localStorage`.
