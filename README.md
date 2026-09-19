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
} from "https://cdn.jsdelivr.net/gh/asbelcas/-github.com-asbelcas-cropcircuit-agents@26a6c450742faa56be7b11821c106e1617a7c63b/public_value/farm_math.js";
```

### Farm Chore Cost & Payback

A smaller standalone module focused on recurring chore economics:

- [Source](public_value/farm_chore_payback.js)
- [Documentation](public_value/FARM_CHORE_PAYBACK.md)

### Offline Farm Decision Calculator

A single HTML file that runs entirely in the browser with no account, analytics, or network dependency after download:

- [farm_decision_calculator.html](public_value/farm_decision_calculator.html)

It combines task cost, simple payback, fence-line estimation, water-storage sizing, and sales-channel break-even in one portable file.

### Copy-paste funding integrations

The same funding data can be pulled into Google Sheets, Excel/Power Query, JavaScript, Python, curl, calendar clients, and feed readers:

- [Integration recipes](public_value/FUNDING_INTEGRATIONS.md)

### Embeddable funding radar

Other Michigan agriculture, food-system, nonprofit, or community websites can reuse the radar without copying the data:

- [Widget documentation](public_value/FUNDING_WIDGET.md)
- [Widget source](public_value/funding_widget.js)
- [Demo source](public_value/funding_widget_demo.html)

A website can filter by county, status, tags, count, and theme. The widget contains no analytics or cookies.

### Offline-first static app shell

The repository root now includes a Pages-ready web manifest and service worker. Once served over HTTPS, core calculators/tools can be revisited offline while time-sensitive funding data stays network-first:

- [Offline web-app policy](public_value/OFFLINE_WEB_APP.md)
- `site.webmanifest`
- `sw.js`

GitHub Pages is not enabled yet, so this capability is staged rather than claimed live.

### Shared Farm Labor Data Contract

The labor tools now share one explicit interoperable row format. It keeps the farmer's free-text task name and optionally adds a canonical chore code:

- [Data contract](public_value/LABOR_DATA_CONTRACT.md)
- [Logical row schema](public_value/farm_labor_record.schema.json)
- [CSV validator](public_value/validate_labor_contract.mjs)
- [Synthetic baseline demo](public_value/examples/synthetic_labor_log_before.csv)
- [Synthetic after-change demo](public_value/examples/synthetic_labor_log_after.csv)

### Offline Farm Labor Log

A private local-first time-study tool for discovering where farm labor actually goes:

- [Tool source](public_value/farm_labor_log.html)
- [Documentation](public_value/FARM_LABOR_LOG.md)

It stores entries only in browser storage, calculates worker-hours and labor cost by category/task, and exports CSV for backup or further analysis.

### Offline Farm Chore Scheduler

A local-first recurring task planner lets farms define their own maintenance/chore intervals and export them as standard iCalendar or CSV:

- [Scheduler](public_value/farm_chore_scheduler.html)
- [Documentation](public_value/FARM_CHORE_SCHEDULER.md)

It deliberately contains no default maintenance intervals; the operator supplies timing appropriate to the farm and equipment guidance.

### Open Farm Chore Taxonomy

CropCircuit now publishes a CC0 controlled vocabulary for repeated farm work so logs from different operators can become interoperable instead of remaining trapped in inconsistent free text:

- [Taxonomy JSON](public_value/farm_chore_taxonomy.json)
- [Schema](public_value/farm_chore_taxonomy.schema.json)
- [Documentation](public_value/CHORE_TAXONOMY.md)
- [Private browser mapper](public_value/chore_taxonomy_mapper.html)

The first version contains stable human-readable codes across livestock, crops, wash-pack, fencing, water, maintenance, sales, admin, and general farm work.

### Workflow Experiment Analyzer

Farm improvements can now be checked against a second observation period instead of being assumed successful:

- [Browser analyzer](public_value/workflow_experiment_analyzer.html)
- [Reusable math](public_value/workflow_experiment.js)
- [Tests](public_value/workflow_experiment.test.mjs)
- [Documentation](public_value/WORKFLOW_EXPERIMENT.md)

It compares baseline and after-change labor by task, shows sample sizes and median worker-time changes, and can model annual labor value/payback without claiming causation or statistical significance.

### Equipment Cost Threshold Analyzer

Once a task's annualized labor cost is known, a local-first screening tool calculates the maximum upfront capital cost consistent with a chosen time-reduction assumption and simple-payback horizon:

- [Tool source](public_value/equipment_cost_threshold.html)
- [Documentation](public_value/EQUIPMENT_COST_THRESHOLD.md)

It is a first-pass threshold, not a purchase recommendation.

### Labor Opportunity Analyzer

Pair the Offline Farm Labor Log with a browser-only analyzer that annualizes a real time-study sample and ranks repeated work by estimated labor cost:

- [Analyzer source](public_value/labor_opportunity_analyzer.html)
- [Documentation](public_value/LABOR_OPPORTUNITY_ANALYZER.md)

The analysis remains local to the browser and can export its ranked opportunity table as CSV.

### Funding query CLI

Developers, analysts, and agents can query the radar locally with no API key or dependencies:

- [CLI source](public_value/funding_query.mjs)
- [Documentation](public_value/FUNDING_QUERY.md)
- [Tests](public_value/funding_query.test.mjs)

Examples include county-specific eligibility, open-only results, upcoming deadlines, and machine-readable JSON/TSV output.

### Privacy-first Farm Operations Benchmark

CropCircuit now has the public specification and tooling for a small-farm operations benchmark without publishing identifiable farm records:

- [Benchmark specification](public_value/FARM_BENCHMARK_SPEC.md)
- [JSON Schema](public_value/farm_benchmark.schema.json)
- [Browser-only record builder](public_value/benchmark_builder.html)
- [k-anonymous aggregator](public_value/benchmark_aggregate.mjs)
- [Privacy/statistics tests](public_value/benchmark_aggregate.test.mjs)

The public benchmark dataset is **not populated yet**. CropCircuit will not manufacture baseline numbers. Cohort statistics are suppressed until at least 5 records are present.

### Labor Log → Anonymous Benchmark

A dependency-free transformer converts real labor-log CSV into the coarse benchmark schema while deliberately discarding exact dates, task names, notes, county, exact acreage, and contact information:

- [Transformer](public_value/labor_log_to_benchmark.mjs)
- [Documentation](public_value/LABOR_TO_BENCHMARK.md)
- [Privacy tests](public_value/labor_log_to_benchmark.test.mjs)

This makes the path from real observation to a privacy-preserving benchmark record reproducible.

### Farm Labor → Decision → Benchmark workflow

The tools now form an end-to-end local-first workflow:

**observe → quantify → prioritize → model → anonymize → aggregate → compare → improve**

- [Workflow guide](public_value/FARM_LABOR_TOOLKIT.md)
- [Private Benchmark Explorer](public_value/benchmark_explorer.html)
- [Benchmark Explorer documentation](public_value/BENCHMARK_EXPLORER.md)

The explorer respects cohort suppression and will not expose statistics from a group that is below the privacy floor.

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


## Stable public-value snapshots

- `release/public-value-0.1.0` → commit `26a6c450742faa56be7b11821c106e1617a7c63b`
- `release/public-value-0.2.0` → commit `2b12a25c123be3755bd1a8dde0048e655143e4a6`
- `release/public-value-0.3.0` → commit `2ef59d315aca655a0ff4329c4b3cf26fd8f4ca86`

Integration examples pin code by commit SHA for reproducibility, while mutable funding data remains on `main`.
