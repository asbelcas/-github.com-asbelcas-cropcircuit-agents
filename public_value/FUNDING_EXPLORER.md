# Michigan Farm Funding Explorer

A standalone human-facing interface for the CropCircuit Funding Radar.

## Features

- filter by status
- filter by county
- filter by tag
- text search
- show dated opportunities due within 14 / 30 / 60 / 90 days
- export filtered CSV
- export filtered JSON
- direct primary-source links
- visible dataset verification date

## Offline behavior

The HTML file embeds the funding snapshot that existed when the file was generated.

That means it remains usable when opened locally with no network connection.

A **Refresh current public data** button attempts to load `funding_radar.json` when network/static-host access is available.

If refresh fails, the embedded snapshot stays available.

## Staleness warning

When the embedded/current dataset verification date is more than 30 days old, the explorer displays a warning.

The warning does not replace source verification. Program details can change before 30 days have elapsed.

## County behavior

A county filter includes:

1. statewide records with no county restriction, and
2. county-scoped records whose `county_scope` contains the requested county.

## Truthfulness rule

The explorer does not relabel a watch, paused, or closed program as open merely because it matches a search.

Every card links to the primary source so the user can verify current eligibility and deadlines.
