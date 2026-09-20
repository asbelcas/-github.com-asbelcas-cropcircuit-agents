# Shareable Farm Operations Snapshot

The Shareable Farm Operations Snapshot is the bridge between a private local Workspace and a coarse summary that can be reviewed without exporting raw operational rows.

## Default privacy behavior

The snapshot does **not** include:

- raw labor rows
- raw harvest rows
- raw sales rows
- free-text notes
- exact transaction dates

Sales dollar totals are excluded by default.

The user must explicitly opt in to include sales-dollar summaries.

## Included summaries

The snapshot can contain:

- labor entry count
- worker-hours by category
- labor category shares
- number of recurring chore templates
- equipment maintenance-item counts
- parts-stock threshold counts
- harvest totals by item + unit
- sales record counts by channel
- optional sales dollar totals by channel

## Why this exists

A local-first farm tool is useful partly because raw records can stay local.

But farms may still want to share a **summary** with:

- an advisor
- a consultant
- a collaborator
- an extension professional
- a lender or planning partner
- their own future self

The snapshot provides a smaller disclosure surface than sending the raw Workspace.

## Not anonymous by guarantee

A coarse summary can still be identifying in context.

CropCircuit does not claim this output is anonymous.

Users should review the JSON/PDF before sharing.

## Reusable helper

`ops_snapshot.js` contains the zero-dependency summary logic.

`ops_snapshot.test.mjs` checks that:

- period filtering works
- labor aggregation works
- harvest aggregation works
- sales dollar fields remain absent by default
- free-text notes are not copied into the snapshot
- optional sales-dollar summaries are calculated correctly
