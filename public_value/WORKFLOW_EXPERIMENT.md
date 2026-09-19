# Workflow Experiment Analyzer

A workflow improvement should be measured after it is installed.

CropCircuit's Workflow Experiment Analyzer compares two labor-log periods:

- **baseline** — before the change
- **after** — after the change

Matching is based on task name.

## Outputs

For each matching task it reports:

- baseline sample size
- after-change sample size
- baseline median worker-minutes per occurrence
- after-change median worker-minutes per occurrence
- descriptive percentage change
- estimated baseline occurrences per week when dated observations are available
- modeled annual labor value of the observed median change
- simple payback when an intervention cost is supplied

## What it does not claim

The analyzer does **not** calculate statistical significance and does not claim the intervention caused the observed change.

A before/after comparison can be distorted by:

- weather
- season
- herd or crop stage
- staffing
- learning effects
- changing task definitions
- equipment downtime
- different volumes or throughput

The right response to a surprising result is usually another observation period, not certainty.

## Reusable math

The descriptive calculations are also available in:

- `workflow_experiment.js`
- `workflow_experiment.test.mjs`

This keeps the core comparison math reusable outside the standalone HTML tool.

## Evidence loop

This closes an important part of the CropCircuit operating loop:

```text
observe baseline
→ identify expensive repetition
→ model a possible intervention
→ change the workflow
→ observe again
→ compare actual labor
→ keep, revise, or reverse
```

That is more useful than assuming a purchase or automation saved time simply because it was installed.
