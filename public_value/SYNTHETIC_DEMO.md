# Synthetic Demo Workspace

The demo workspace lets someone test CropCircuit's local-first workflow without entering a real farm record.

Every record is fictional and every record ID begins with:

```text
demo-
```

## Included

- 6 labor entries
- 3 recurring scheduled chores
- 2 equipment-maintenance items
- 2 equipment-parts records
- 3 harvest entries
- 2 sales records

## Files

- [Synthetic Workspace 1.2 JSON](examples/synthetic_workspace_1_2.json)
- [Demo loader](demo_workspace.html)

## Demo loader behavior

The loader uses Workspace merge mode.

That means it can add the demo records without replacing normal local records.

A separate **Remove demo records** action removes only records whose IDs begin with `demo-`.

## What to test

After loading the demo from the same web origin, try:

- Weekly Farm Operations Brief
- Labor Opportunity Analyzer
- Schedule Estimate Calibrator
- Farm Chore Load Planner
- Equipment Maintenance Log
- Equipment Parts Inventory
- Harvest Log
- Farm Sales Log

## Browser-origin caveat

Local storage belongs to the web origin.

If the demo is loaded under a temporary preview host, it will not automatically appear under a different future GitHub Pages or cropcircuit.org origin.

Workspace JSON export/restore is the portability mechanism.

## Not evidence

Synthetic demo output must never be counted as:

- farm performance
- customer usage
- earned revenue
- benchmark input
- product validation

It exists only for testing and demonstration.
