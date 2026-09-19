# Farm Labor → Decision → Benchmark Toolkit

CropCircuit's labor tools now form one coherent workflow rather than isolated calculators.

## Step 1 — Observe

Use the [Offline Farm Labor Log](farm_labor_log.html) for a real observation period.

Record:

- category
- task
- elapsed minutes
- workers involved

The log stores data locally and exports CSV.

## Step 2 — Find the expensive repetition

Load the CSV into the [Labor Opportunity Analyzer](labor_opportunity_analyzer.html).

It annualizes the observation sample and ranks repeated task names by estimated labor cost.

This identifies where investigation is worth spending attention.

## Step 3 — Model an intervention

Use [CropCircuit Farm Math](farm_math.js) or the [Offline Farm Decision Calculator](farm_decision_calculator.html) to model:

- annual labor cost
- simple payback
- fencing cost scenarios
- water storage
- selling-channel break-even

The calculations expose assumptions rather than hiding them.

## Step 4 — Strip identifying detail

Transform the labor log into the [Anonymous Benchmark schema](farm_benchmark.schema.json) with:

- [labor_log_to_benchmark.mjs](labor_log_to_benchmark.mjs), or
- [benchmark_builder.html](benchmark_builder.html)

Task names, notes, exact dates, county, exact acreage, contact information, and exact wages do not belong in the benchmark record.

## Step 5 — Aggregate with a privacy floor

Use [benchmark_aggregate.mjs](benchmark_aggregate.mjs).

By default, cohort statistics are suppressed until at least **5 records** are available.

## Step 6 — Compare privately

When an aggregate cohort file exists, use the [Private Benchmark Explorer](benchmark_explorer.html) to compare one farm's coarse record against cohort p25 / median / p75 values entirely in the browser.

## Why this matters

The loop is:

```text
observe → quantify → prioritize → model → anonymize → aggregate → compare → improve
```

That creates a reusable operating system for learning from farm work without requiring farmers to surrender raw operational data to a centralized platform.
