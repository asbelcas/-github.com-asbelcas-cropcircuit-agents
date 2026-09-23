# Repeated-Decision Pilot Protocol v0.1

CropCircuit now needs evidence, not additional architectural enthusiasm.

The first real pilot should test a **repeated decision class** and ask whether each participating model becomes less wrong, less overconfident, and more useful over time without violating hard constraints.

The pilot is not designed to prove that CropCircuit is "better than farmers."

## Core comparison

For the same repeated decision, record predictions **before the outcome** from:

1. farmer / operator
2. CropCircuit
3. conventional software or a fixed rule when one is genuinely available

A two-predictor pilot is valid when no conventional comparator exists.

Then record the real outcome and evaluate each prior prediction as:

- supported
- mixed
- contradicted

The evaluation must include a note.

## What the pilot measures

The first instrumentation focuses on descriptive signals:

- number of evaluated repeated decisions
- supported / mixed / contradicted counts
- contradiction rate
- high-confidence contradictions
- mean confidence
- early-window versus late-window contradiction rate
- change in high-confidence contradictions

These are **learning signals**, not proof of causal superiority.

The code refuses to report early-versus-late learning windows until there are at least six evaluated repeated decisions.

Six is only a minimum to avoid comparing tiny one- or two-event windows. It is not a statistical sufficiency claim.

## Governance stays outside the contest

Every record carries the current governance gate.

A predictor does not earn credit for proposing an action that violates:

- animal welfare
- safety
- law
- financial hard floors
- consent
- another declared hard boundary

The pilot is subordinate to normal CropCircuit governance.

## Recommended first pilot classes

Choose a workflow that:

- repeats often enough to generate evidence
- has observable outcomes
- has low-cost or reversible decisions
- already matters to farm operations
- does not require unsafe experimentation

Good candidates include:

- cow fetch / overdue milking prioritization on a participating dairy
- grazing move timing
- recurring water-system checks
- labor scheduling / chore handoff
- another repeated workflow with clear outcome signals

Do **not** create experimental risk to generate data.

## Minimum record

Each decision stores:

- decision class
- context tags
- governance gate
- predictor identities
- prediction text
- confidence
- reason / evidence where available
- outcome
- evidence references
- relation of each prediction to the outcome
- optional operational metrics

## First proof standard

Do not publish:

> CropCircuit outperformed the farmer.

from a tiny pilot.

A responsible first claim is closer to:

> In N repeated decisions on one workflow, CropCircuit's recorded contradiction rate changed from X in the early window to Y in the later window, while the farmer / rule-based comparator showed Z. This is pilot evidence only and may not generalize.

The repo's default summary deliberately selects **no winner**.

## Data quality rules

- predictions must be timestamped before outcomes
- do not edit old predictions after results are known
- keep mixed outcomes mixed
- record missing evaluations rather than inventing them
- preserve governance holds/rejections
- do not exclude failures because they make a predictor look bad
- label synthetic data as synthetic

## Files

- [pilot_learning_rate.js](pilot_learning_rate.js)
- [pilot_learning_rate.test.mjs](pilot_learning_rate.test.mjs)
- [pilot_decision_record.schema.json](pilot_decision_record.schema.json)
- [Synthetic example](examples/synthetic_pilot_decision.json)

## Design principle

**Compare learning trajectories, not egos.**
