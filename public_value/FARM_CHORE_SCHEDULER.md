# Offline Farm Chore Scheduler

A local-first recurring task planner that exports standard iCalendar and CSV files.

## Why it exists

A maintenance schedule is useful only if it reflects the actual farm, equipment, manufacturer guidance, season, and operating system.

So this tool deliberately does **not** contain default maintenance intervals.

The operator supplies:

- task name
- category
- first date
- recurrence
- interval
- optional estimated minutes
- optional notes

## Recurrence options

- one time
- every N days
- every N weeks
- every N months
- every N years

## Outputs

### iCalendar

The `.ics` export can be imported into calendar applications that support the iCalendar format.

Recurring tasks use standard `RRULE` recurrence.

### CSV

The CSV export provides a portable backup and a starting point for spreadsheet workflows.

## Privacy

Schedule data is kept in browser local storage.

The tool has:

- no account
- no analytics
- no server sync
- no network requests

Notes are included in exported files, so users who plan to share a calendar should avoid putting sensitive information in notes.

## Relationship to other CropCircuit tools

The scheduler can be used upstream of the labor log:

```text
plan recurring work
→ perform task
→ record actual labor
→ analyze expensive repetition
→ test improvements
```

This helps separate **what was scheduled** from **what the work actually cost**.
