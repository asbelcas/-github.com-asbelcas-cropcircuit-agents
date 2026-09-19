# Offline Web App Support

The repository root contains:

- `site.webmanifest`
- `sw.js`

Once the repository is served from a secure static host such as GitHub Pages, the landing page registers the service worker.

## Caching policy

### Static tools

Core standalone tools and schemas are **cache-first** after the first successful visit.

That means a farmer can revisit the tools during a connectivity outage after they have been loaded once.

### Time-sensitive data

Funding files and the public asset manifest use **network-first** behavior:

- `funding_radar.json`
- `funding_radar.csv`
- `funding_feed.json`
- `funding_deadlines.ics`
- `manifest.json`

If the network works, the newest copy wins.

If the network fails, a previously cached copy can still be used.

This is important because a stale calculator is usually harmless, while a stale funding deadline can waste someone's time.

## Current hosting state

The files are ready, but GitHub Pages is not currently enabled for this repository. Offline web-app behavior therefore remains staged until the static site is served over HTTPS.

Individual standalone HTML tools can still be downloaded and used locally today.
