# CropCircuit Public Value Assets

This directory is the public, reusable core of CropCircuit.

The operating principle is **utility before solicitation**: publish things that are genuinely useful without requiring a sales call, account, subscription, or surrender of raw farm data.

## Start here

### Farm labor operating loop

The current toolchain supports:

```text
schedule
→ observe
→ normalize
→ quantify
→ prioritize
→ model
→ change
→ measure again
→ anonymize
→ aggregate
→ compare
→ improve
```

Key files:

- [Farm Labor Toolkit](FARM_LABOR_TOOLKIT.md)
- [Farm Labor Data Contract](LABOR_DATA_CONTRACT.md)
- [Open Farm Chore Taxonomy](CHORE_TAXONOMY.md)

### Local-first farm tools

- [Labor CSV Import Mapper](labor_csv_import_mapper.html)
- [Offline Farm Labor Log](farm_labor_log.html)
- [Labor Opportunity Analyzer](labor_opportunity_analyzer.html)
- [Equipment Cost Threshold Analyzer](equipment_cost_threshold.html)
- [Schedule Estimate Calibrator](schedule_estimate_calibrator.html)
- [Workflow Experiment Analyzer](workflow_experiment_analyzer.html)
- [Offline Farm Chore Scheduler](farm_chore_scheduler.html)
- [Offline Farm Decision Calculator](farm_decision_calculator.html)
- [Farm Chore Taxonomy Mapper](chore_taxonomy_mapper.html)
- [Anonymous Benchmark Builder](benchmark_builder.html)
- [Private Benchmark Explorer](benchmark_explorer.html)

Most standalone HTML tools do all processing in the browser and do not upload farm data.

## Michigan Farm Funding Radar

The Funding Radar is a source-linked dataset of Michigan farm, food-system, conservation, disaster, and rural-business funding.

Formats:

- [Interactive standalone Funding Explorer](funding_explorer.html)
- [Human-readable Markdown](funding_radar.md)
- [JSON](funding_radar.json)
- [CSV](funding_radar.csv)
- [JSON Feed](funding_feed.json)
- [iCalendar deadlines](funding_deadlines.ics)
- [JSON Schema](funding_radar.schema.json)

Reuse:

- [Embeddable Funding Widget](FUNDING_WIDGET.md)
- [Funding Query CLI](FUNDING_QUERY.md)
- [Integration recipes](FUNDING_INTEGRATIONS.md)

Program status changes. Every record is intended to point back to a primary source so users can verify details before acting.

## Open farm data standards

### Farm Labor Data Contract

Logical labor-row schema:

- [farm_labor_record.schema.json](farm_labor_record.schema.json)
- [CSV validator](validate_labor_contract.mjs)

Synthetic demonstration data:

- [baseline example](examples/synthetic_labor_log_before.csv)
- [after-change example](examples/synthetic_labor_log_after.csv)
- [synthetic chore schedule](examples/synthetic_chore_schedule.csv)

These examples are fabricated demonstration data, not observations from a real farm.

### Open Farm Chore Taxonomy

The taxonomy contains stable canonical task codes while preserving the farmer's own free-text task name.

- [taxonomy JSON](farm_chore_taxonomy.json)
- [taxonomy schema](farm_chore_taxonomy.schema.json)
- [validator](validate_chore_taxonomy.mjs)

### Privacy-first benchmark format

CropCircuit publishes the benchmark specification and tooling, but **does not yet publish a populated benchmark dataset**.

- [Benchmark specification](FARM_BENCHMARK_SPEC.md)
- [Benchmark schema](farm_benchmark.schema.json)
- [Labor-log privacy transform](LABOR_TO_BENCHMARK.md)
- [k-anonymous aggregator](benchmark_aggregate.mjs)

Cohort statistics are suppressed below the default privacy floor of 5 records.

## JavaScript package surface

- [Package usage](PACKAGE_USAGE.md)
- [Module entry point](index.js)
- root `package.json`

The package is prepared for direct GitHub installation but is not claimed as published to npm.

## Reusable code

### CropCircuit Farm Math

[Farm Math](FARM_MATH.md) is a dependency-free ES module for:

- annual task/labor cost
- simple payback
- fence-line estimation
- user-supplied water-storage math
- selling-channel break-even
- rectangular acreage conversion

Source: [farm_math.js](farm_math.js)

### Workflow experiment math

Reusable descriptive before/after labor comparison:

- [workflow_experiment.js](workflow_experiment.js)
- [tests](workflow_experiment.test.mjs)

## Machine discovery

- [Public asset manifest](manifest.json)
- [schema.org DataCatalog JSON-LD](data_catalog.jsonld)
- [Funding Tabular Data Package](funding_datapackage.json)
- [Chore Taxonomy Tabular Data Package](taxonomy_datapackage.json)
- [Chore Taxonomy CSV](farm_chore_taxonomy.csv)
- root `llms.txt`
- [Public Value Changelog](CHANGELOG.md)

## Offline behavior

The repository also includes a Pages-ready offline web-app shell. Once served over HTTPS, core static tools can be cached for repeat offline use while funding data remains network-first.

See [Offline Web App Support](OFFLINE_WEB_APP.md).

## Validation

The repository contains zero-dependency checks for:

- funding structure and freshness
- farm math
- funding-query behavior
- benchmark privacy suppression
- labor-to-benchmark privacy transform
- workflow experiment math
- chore taxonomy integrity
- labor data contract examples
- offline cache asset integrity

GitHub Actions workflow files are present, but automated workflow execution has not yet been independently verified.

## Licensing

- Code under `public_value/`: MIT — [LICENSE-CODE.txt](LICENSE-CODE.txt)
- CropCircuit-authored data structure / metadata intended for broad reuse: CC0 where stated — [LICENSE-DATA.txt](LICENSE-DATA.txt)

Third-party program facts and source material remain subject to their original sources.

## What this is becoming

CropCircuit is exploring a local-first farm operations layer built from small interoperable parts rather than a closed platform.

The useful unit is not a pitch. It is a calculation, record format, dataset, calendar, workflow, or benchmark primitive that someone else can actually use.
