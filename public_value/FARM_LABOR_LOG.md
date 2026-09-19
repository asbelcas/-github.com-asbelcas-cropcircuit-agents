# Offline Farm Labor Log

A single-file farm labor time study and cost-analysis tool.

## What it does

- records dated farm tasks
- tracks elapsed minutes and number of workers
- converts entries into worker-hours
- estimates labor cost using a rate you supply
- summarizes labor by category
- identifies the most labor-intensive repeated task names
- exports the raw log as CSV
- prints a clean summary

## Privacy model

The tool is intentionally local-first:

- no account
- no analytics
- no cookies
- no server sync
- no network calls
- data stays in the browser's local storage unless the user exports it

Because browser storage can be cleared, users should export CSV periodically.

## Use

Open `farm_labor_log.html` in a modern browser. It can be saved and used offline.

This is designed to answer a practical question before anyone buys equipment or automation:

**Where is the labor actually going?**

Once a farm has a few weeks of observations, the highest-cost repeated tasks become candidates for layout changes, equipment, automation, or elimination.

The tool does not prescribe wage rates or biological assumptions; the operator supplies their own labor-cost rate.
