# Farm Ops Pocket Console

The Pocket Console is a **single HTML file** that combines a small useful subset of CropCircuit's local-first workflow.

It exists for a practical reason: a farmer should be able to save one file and begin using the system without installing a package, running a server, or waiting for CropCircuit's main website deployment.

## Included

### Dashboard

- last 7 days of labor observations
- worker-hours by category
- next 7 days of recurring scheduled chores
- estimated upcoming chore minutes

### Labor log

- date
- category
- free-text task
- optional canonical chore code
- elapsed minutes
- workers
- worker-hours calculation

### Chore scheduler

- task
- optional canonical chore code
- first date
- daily / weekly / monthly / yearly recurrence
- interval
- estimated minutes

### Workspace backup

- export the local labor/schedule workspace as JSON
- replace the workspace from a compatible backup

## Compatibility

When the Pocket Console is opened from the same web origin as the rest of CropCircuit's hosted tools, it uses the same local-storage keys:

- `cropcircuit_farm_labor_log_v1`
- `cropcircuit_farm_labor_settings_v1`
- `cropcircuit_chore_schedule_v1`

That means observations created in the Pocket Console can feed the larger local-first toolkit.

When opened directly as a local `file://` document, browser handling of local storage varies. The JSON backup remains important.

## What is deliberately not included

The Pocket Console is not intended to replace every specialized CropCircuit tool.

Use the larger tools for:

- detailed opportunity analysis
- before/after workflow experiments
- equipment-cost thresholds
- schedule calibration
- benchmark transformation
- funding exploration
- direct-market unit economics

The Pocket Console is the minimum useful operating surface.
