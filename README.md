# CropCircuit Open Farm Utilities

CropCircuit is building small, reusable tools and datasets for practical farm decisions.

**Current principle: utility before solicitation.**  
Instead of leading with a consulting pitch, this repository now exposes useful building blocks that farmers, developers, educators, and AI systems can use directly.

## Start here

Use [Start Here](public_value/START_HERE.md) to choose the smallest useful path. You do not need the whole toolkit.

Temporary runnable previews are listed in [Try CropCircuit Now](public_value/TRY_IT_NOW.md) while GitHub Pages remains disabled.

## Public value assets

### Assisted Farm Data Setup

For operators who already have farm spreadsheets but do not want to clean and map them themselves:

- [Assisted Farm Data Setup — $149 pilot](public_value/farm_data_setup.html)
- [Service scope](public_value/FARM_DATA_SETUP.md)
- [Synthetic example deliverable](public_value/SYNTHETIC_DATA_SETUP_DELIVERABLE.md)
- [Assisted Setup Intake Builder](public_value/assisted_setup_intake.html)
- [Synthetic before → after case study](public_value/examples/assisted_setup_case/README.md)

The free Universal CSV Mapper remains available; the paid pilot is implementation labor, not software access.

### Universal Farm CSV Mapper

Existing spreadsheets can now be mapped into six CropCircuit operational contracts without rewriting the source file:

- [Universal Farm CSV Mapper](public_value/universal_csv_mapper.html)
- [Documentation](public_value/UNIVERSAL_CSV_MAPPER.md)
- [Machine-readable data contracts](public_value/data_contracts.json)

### Spreadsheet Starter Kit

For farms that prefer Excel, Google Sheets, or LibreOffice, CropCircuit now publishes blank portable CSV templates matching the same open data contracts:

- [Spreadsheet Starter Kit](public_value/SPREADSHEET_STARTER_KIT.md)

### One-file Pocket Console

The fastest way into the system is now [Farm Ops Pocket Console](public_value/farm_ops_console.html): one dependency-free HTML file containing a local labor log, recurring chore scheduler, seven-day dashboard, and workspace backup.



Everything below lives in [`public_value/`](public_value/).

### Sales CSV Import Mapper

Existing POS, invoice, or spreadsheet exports can be mapped into CropCircuit's operational sales format without uploading the source file:

- [Sales CSV Import Mapper](public_value/sales_csv_import_mapper.html)
- [Documentation](public_value/SALES_CSV_IMPORT.md)

### Shareable Farm Operations Snapshot

A coarse export bridges private local records to advisor/consultant review without sending the raw Workspace:

- [Operations Snapshot](public_value/operations_snapshot.html)
- [Documentation](public_value/OPERATIONS_SNAPSHOT.md)
- [Reusable summary helper](public_value/ops_snapshot.js)

Sales-dollar summaries are opt-in; notes and raw rows are excluded.

### Offline Farm Sales Log

A local-first sales record separates operational sales arithmetic from accounting claims:

- [Sales Log](public_value/sales_log.html)
- [Documentation](public_value/SALES_LOG.md)
- [Reusable summary math](public_value/sales_math.js)

It summarizes gross amount, payment fees, refunds/discounts, net receipts, and entered direct costs by channel.

### Farm business economics

CropCircuit now includes open unit-economics tools for two common direct-market channels:

- [Farmers Market Break-Even](public_value/market_day_break_even.html)
- [CSA Share Price & Break-Even](public_value/csa_break_even.html)

Both expose the farm's own labor, fee, price, travel, variable-cost, and surplus assumptions rather than hiding them.

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

### Weekly Farm Operations Brief

The local workspace can now generate a private printable report covering recent labor, repeated work, taxonomy coverage, and upcoming recurring chores:

- [Weekly Operations Brief](public_value/weekly_ops_brief.html)
- [Documentation](public_value/WEEKLY_OPS_BRIEF.md)

### Local-first workspace

The local tools now share Workspace 1.2. A dedicated backup tool exports or restores labor, labor settings, chore schedules, equipment maintenance, harvest, and direct-market sales without a server:

- [Workspace backup](public_value/workspace_backup.html)
- [Workspace contract](public_value/LOCAL_WORKSPACE.md)
- [Workspace JSON Schema](public_value/workspace.schema.json)
- [Reusable helpers](public_value/workspace.js)

The Labor Opportunity Analyzer, Chore Load Planner, and Schedule Estimate Calibrator can use that local workspace directly instead of requiring CSV handoffs every time.

### Bring existing spreadsheets with you

The [Labor CSV Import Mapper](public_value/labor_csv_import_mapper.html) converts arbitrary labor spreadsheets into the shared CropCircuit contract without uploading them. A separate [Schedule Estimate Calibrator](public_value/schedule_estimate_calibrator.html) compares planned chore minutes with observed median elapsed time.

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

### Offline Harvest Log

A local-first harvest record tracks quantities without pretending harvest quantity is revenue:

- [Harvest Log](public_value/harvest_log.html)
- [Documentation](public_value/HARVEST_LOG.md)
- [Reusable summary/comparison math](public_value/harvest_math.js)

It keeps unlike units separate and can compare two date ranges by crop/item + unit.

### Equipment Parts Inventory

A local parts register now complements maintenance tracking:

- [Parts Inventory](public_value/parts_inventory.html)
- [Documentation](public_value/PARTS_INVENTORY.md)
- [Reusable stock-status math](public_value/inventory_math.js)

It records operator-entered cross references but does not claim substitute parts are compatible.

### Offline Equipment Checklist

A local checklist recorder lets farms define machine-specific checks from their own manufacturer/employer/service guidance:

- [Equipment Checklist](public_value/equipment_checklist.html)
- [Documentation](public_value/EQUIPMENT_CHECKLIST.md)

CropCircuit deliberately supplies no default safety checklist and does not treat checked boxes as independent verification.

### Equipment Maintenance Log

A local-first equipment service register tracks the intervals the operator chooses, by meter-hours, calendar time, or both:

- [Equipment Maintenance Log](public_value/equipment_maintenance.html)
- [Documentation](public_value/EQUIPMENT_MAINTENANCE.md)
- [Reusable due-status math](public_value/equipment_math.js)

CropCircuit deliberately supplies no default maintenance intervals.

### Farm Chore Load Planner

Recurring schedules can now be expanded into a daily workload view using the operator's own task-duration estimates and daily chore-time capacity:

- [Planner](public_value/chore_load_planner.html)
- [Documentation](public_value/CHORE_LOAD_PLANNER.md)
- [Reusable recurrence math](public_value/schedule_math.js)

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

### JavaScript package surface

The reusable JavaScript layer now has zero-dependency package metadata and an export entry point for direct GitHub installs and future registry publication:

- [Package usage](public_value/PACKAGE_USAGE.md)
- `package.json`
- [Module entry point](public_value/index.js)

No npm registry publication is claimed yet; that remains gated on clean-install verification and evidence of demand.

### Data packages and catalog metadata

The funding radar and chore taxonomy now include Tabular Data Package metadata, and the repository publishes a schema.org `DataCatalog` JSON-LD description for catalog/search reuse:

- [Funding data package](public_value/funding_datapackage.json)
- [Taxonomy data package](public_value/taxonomy_datapackage.json)
- [DataCatalog JSON-LD](public_value/data_catalog.jsonld)
- [Taxonomy CSV](public_value/farm_chore_taxonomy.csv)

### Machine-readable asset manifest

Software can discover the current public assets through:

- [manifest.json](public_value/manifest.json)

## Design rules

1. **Useful before monetized.** An asset should solve a real problem even if nobody pays.
2. **Assumptions stay visible.** Farm Math does not hide biological or financial defaults inside the code.
3. **Primary sources over stale summaries.** Funding records link to the program owner.
4. **Machine-readable by default.** Useful information should be available as data, not trapped in prose.
5. **Small composable pieces.** Build things other people can reuse, link, import, or adapt.

## Privacy and provenance

- [Privacy model](public_value/PRIVACY_MODEL.md)
- [Data provenance and truthfulness policy](public_value/PROVENANCE.md)

CropCircuit's local-first design reduces unnecessary central collection, but the documentation explicitly states the limits of browser storage and k-anonymity.

## Licensing

- Public utility code: MIT — see [LICENSE-CODE.txt](public_value/LICENSE-CODE.txt)
- CropCircuit-authored dataset arrangement/metadata: CC0 1.0 dedication to the extent CropCircuit holds rights — see [LICENSE-DATA.txt](public_value/LICENSE-DATA.txt)

Third-party source material remains subject to the original source's terms.

## Legacy agent experiments

This repository contains older autonomous-agent and revenue experiments from earlier CropCircuit phases. They remain for historical continuity and research, but they are **not the current operating strategy**.

The previous repository README has been preserved at [legacy/RM_QPT_README_2026-04-02.md](legacy/RM_QPT_README_2026-04-02.md).

Current work is centered on creating durable internet utility: tools, datasets, APIs, benchmarks, and reusable decision infrastructure.


## Automated quality checks

The repository includes a GitHub Actions workflow for funding-data freshness and the public validation suite. The workflow file is committed, but GitHub has reported zero workflow runs so far, so automated execution is **not yet verified**. Local/manual validators remain the evidence source until Actions actually runs.


## Stable public-value snapshots

- `release/public-value-0.1.0` → commit `26a6c450742faa56be7b11821c106e1617a7c63b`
- `release/public-value-0.2.0` → commit `2b12a25c123be3755bd1a8dde0048e655143e4a6`
- `release/public-value-0.3.0` → commit `2ef59d315aca655a0ff4329c4b3cf26fd8f4ca86`
- `release/public-value-0.4.0` → commit `00bb29d3a26d308992c7d1f16a6075f86bea7db6`
- `release/public-value-0.5.0` → commit `a2c0b1fe972da0d325ee2c7a98d210ef48ec6845`
- `release/public-value-0.8.0` → commit `f3129795c1f7a44ef0f1f77fc275394f95c34e71`
- `release/public-value-0.10.0` → commit `31b9c0af8a9c9a5c8c82ca2306878a7873aadbfc`
- `release/public-value-0.13.0` → commit `e39d3e2013370a973d99afc2791a0000f2c40823`
- `release/public-value-0.14.0` → commit `aeba8c9756ba21d10be5d16e6fa6fd3623c19844`
- `release/public-value-0.15.0` → commit `3cc0d81e523b72b63213bcbb571d5802470089bb`
- `release/public-value-0.15.1` → commit `55ed09997d00c25af50199def43ccb7e73e9f407`
- `release/public-value-0.16.0` → commit `4a163769aaf7443e93ffe55d74935359b2780319`
- `release/public-value-0.16.1` → commit `21e7368fbc0875b658cbec7549b2a117bb5065fa`

Integration examples pin code by commit SHA for reproducibility, while mutable funding data remains on `main`.
