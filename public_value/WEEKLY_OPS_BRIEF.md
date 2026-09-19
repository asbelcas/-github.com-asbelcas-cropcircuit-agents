# Weekly Farm Operations Brief

A browser-local report that combines CropCircuit's Labor Log and recurring Chore Scheduler.

## Purpose

The tool provides a simple weekly operating picture without sending farm data to a server.

It shows:

- labor entry count
- total worker-hours
- share of labor entries carrying canonical chore codes
- worker-hours by category
- highest-time repeated work
- upcoming scheduled chores after the report window

## Data source

The brief reads the shared [Local Workspace](LOCAL_WORKSPACE.md):

- local labor entries
- local recurring chore schedule

Because all compatible tools use the same browser-local keys, the brief can be generated without exporting and re-importing CSV files.

## Privacy

The brief is built in the browser.

Free-text notes from the labor log and schedule are deliberately not displayed in the report.

Printing or saving the brief can still create a file outside the browser, so users should treat exported reports according to their own recordkeeping/privacy needs.

## Interpretation

The report is descriptive.

"Highest-time repeated work" means only that the observed entries consumed the most worker-hours inside the selected window.

It is not an efficiency score and does not imply the work should take less time.

## Upcoming work

The upcoming schedule is expanded with the same recurrence semantics as [schedule_math.js](schedule_math.js).
