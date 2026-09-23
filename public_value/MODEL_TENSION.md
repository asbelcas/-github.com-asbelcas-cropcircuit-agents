# Model Tension v0.1

CropCircuit intentionally preserves disagreement between partial farm models.

The purpose of this primitive is **not** to choose a winner. It is to stop a persuasive aggregate score from hiding real tradeoffs.

## What a model position contains

Each partial model records:

- model name
- recommendation
- confidence
- plain-language reason
- evidence references
- hard constraints implicated
- time sensitivity
- reversibility

Examples of models include:

- animal welfare / health
- pasture / forage
- soil
- labor
- finance
- weather
- infrastructure
- customer / market

## States

### BLOCKED

At least one model position reports a failed hard constraint.

The failed boundary remains failed. Other models cannot compensate for it.

### HOLD_FOR_UNKNOWN

No hard constraint is known to fail, but at least one hard constraint is unresolved.

The decision should be reduced, investigated, or delayed until the unknown is handled appropriately.

### HUMAN_ARBITRATION

The hard constraints are clear enough to proceed to tradeoff review, but the models recommend different things.

CropCircuit preserves the disagreement and routes the tradeoff to the authorized human.

### ALIGNED

The recorded model positions point in the same direction.

This still does not constitute an automatic recommendation. Ordinary CropCircuit governance remains in force.

## No magic score

The primitive does not:

- average recommendations
- multiply confidence by ROI
- rank welfare against money on one universal scale
- choose a winning model
- silently suppress a minority position

The record is descriptive.

## Human arbitration

After reviewing the positions, the authorized human may record:

- selected option
- rationale
- decision time
- decision maker
- follow-up

That creates an auditable trail of **who chose the tradeoff and why**.

## Files

- [model_tension.js](model_tension.js)
- [model_tension.test.mjs](model_tension.test.mjs)

## Design principle

**Disagreement is information. Preserve it before resolving it.**
