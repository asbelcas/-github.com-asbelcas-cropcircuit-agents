# CropCircuit Open Farm Utilities

CropCircuit is building small, reusable tools and datasets for practical farm decisions.

**Current principle: utility before solicitation.**  
Instead of leading with a consulting pitch, this repository now exposes useful building blocks that farmers, developers, educators, and AI systems can use directly.

## Public value assets

Everything below lives in [`public_value/`](public_value/).

### Michigan Farm Funding Radar

A source-linked, machine-readable snapshot of Michigan farm, food-system, conservation, and rural-business funding.

Available formats:

- [Human-readable radar](public_value/funding_radar.md)
- [JSON](public_value/funding_radar.json)
- [CSV](public_value/funding_radar.csv)
- [JSON Schema](public_value/funding_radar.schema.json)
- [Funding deadline calendar](public_value/funding_deadlines.ics)

The radar distinguishes open opportunities, continuous-signup programs, paused programs, and closed cycles worth planning for. Every record links back to a primary source.

### CropCircuit Farm Math

A dependency-free JavaScript module for transparent farm calculations:

- repeated-task annual labor cost
- simple payback
- acreage-to-fence-line estimates
- water-storage sizing from user-supplied consumption
- sales-channel break-even transactions
- rectangular acreage conversion

Source:

- [farm_math.js](public_value/farm_math.js)
- [Documentation](public_value/FARM_MATH.md)
- [Tests](public_value/farm_math.test.mjs)

Browser / ES module CDN:

```js
import {
  annualTaskCost,
  simplePayback,
  fenceEstimate,
  waterStorage,
  breakEvenTransactions,
  rectangleAcres
} from "https://cdn.jsdelivr.net/gh/asbelcas/-github.com-asbelcas-cropcircuit-agents@main/public_value/farm_math.js";
```

### Farm Chore Cost & Payback

A smaller standalone module focused on recurring chore economics:

- [Source](public_value/farm_chore_payback.js)
- [Documentation](public_value/FARM_CHORE_PAYBACK.md)

### Offline Farm Decision Calculator

A single HTML file that runs entirely in the browser with no account, analytics, or network dependency after download:

- [farm_decision_calculator.html](public_value/farm_decision_calculator.html)

It combines task cost, simple payback, fence-line estimation, water-storage sizing, and sales-channel break-even in one portable file.

### Embeddable funding radar

Other Michigan agriculture, food-system, nonprofit, or community websites can reuse the radar without copying the data:

- [Widget documentation](public_value/FUNDING_WIDGET.md)
- [Widget source](public_value/funding_widget.js)
- [Demo source](public_value/funding_widget_demo.html)

A website can filter by county, status, tags, count, and theme. The widget contains no analytics or cookies.

### Offline Farm Labor Log

A private local-first time-study tool for discovering where farm labor actually goes:

- [Tool source](public_value/farm_labor_log.html)
- [Documentation](public_value/FARM_LABOR_LOG.md)

It stores entries only in browser storage, calculates worker-hours and labor cost by category/task, and exports CSV for backup or further analysis.

### Funding query CLI

Developers, analysts, and agents can query the radar locally with no API key or dependencies:

- [CLI source](public_value/funding_query.mjs)
- [Documentation](public_value/FUNDING_QUERY.md)
- [Tests](public_value/funding_query.test.mjs)

Examples include county-specific eligibility, open-only results, upcoming deadlines, and machine-readable JSON/TSV output.

### Machine-readable asset manifest

Software can discover the current public assets through:

- [manifest.json](public_value/manifest.json)

## Design rules

1. **Useful before monetized.** An asset should solve a real problem even if nobody pays.
2. **Assumptions stay visible.** Farm Math does not hide biological or financial defaults inside the code.
3. **Primary sources over stale summaries.** Funding records link to the program owner.
4. **Machine-readable by default.** Useful information should be available as data, not trapped in prose.
5. **Small composable pieces.** Build things other people can reuse, link, import, or adapt.

## Licensing

- Public utility code: MIT — see [LICENSE-CODE.txt](public_value/LICENSE-CODE.txt)
- CropCircuit-authored dataset arrangement/metadata: CC0 1.0 dedication to the extent CropCircuit holds rights — see [LICENSE-DATA.txt](public_value/LICENSE-DATA.txt)

Third-party source material remains subject to the original source's terms.

## Legacy agent experiments

This repository contains older autonomous-agent and revenue experiments from earlier CropCircuit phases. They remain for historical continuity and research, but they are **not the current operating strategy**.

The previous repository README has been preserved at [legacy/RM_QPT_README_2026-04-02.md](legacy/RM_QPT_README_2026-04-02.md).

Current work is centered on creating durable internet utility: tools, datasets, APIs, benchmarks, and reusable decision infrastructure.


## Automated quality checks

The repository includes GitHub Actions checks for funding data structure/freshness, JavaScript syntax, Farm Math, and the funding-query CLI on changes and on a daily schedule. This is meant to make stale "open" deadlines fail visibly instead of quietly lingering.
