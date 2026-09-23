# CropCircuit Reflex Loop v0.1

The Reflex Loop is the first executable piece of the fast side of the Farm Nervous System.

Its job is narrow:

**observation event → inspectable rule → alert**

It is deliberately not a diagnosis engine.

## Why this exists

Farm information often arrives sparse and late. A time-sensitive welfare, water, safety, or infrastructure signal should not have to wait for the slow relationship model to finish reasoning.

The Reflex Loop therefore accepts a minimal observation event and evaluates simple farm-defined rules.

## Observation contract

The shared observation shape is defined in [observation_event.schema.json](observation_event.schema.json).

An observation may come from:
- a human
- a sensor
- a transaction
- an import
- an external source
- a model inference

The source kind remains explicit so a model inference cannot silently become a direct observation.

A free-form observation does not need a `signal_key`. It can still be recorded. It simply cannot trigger deterministic reflex rules until the signal is structured.

## Reflex rule

A rule specifies:
- optional domain
- signal key
- comparator
- threshold
- severity
- action
- human-readable message

Supported actions are:
- `check_now`
- `review_soon`
- `log_only`

The engine returns `authorization: "alert_only"`.

That is a hard design choice. An alert may request attention. It does not authorize an irreversible intervention.

## Safety boundary

The Reflex Loop must not:
- diagnose a disease
- invent veterinary, engineering, financial, or agronomic thresholds
- convert a model inference into an observation
- perform an irreversible action
- silently override the authorized human

Thresholds must come from a farm-defined rule, validated domain guidance, or another explicitly governed source.

## Example

The tests use a **synthetic** water-level threshold solely to verify mechanics. It is not a real-world recommendation.

## Relationship to the slow loop

The fast loop can fire first.

Later, the slow loop may:
- link the alert to other observations
- generate a provisional cross-domain hypothesis
- compare the farmer's interpretation with the model
- update a learning cycle
- preserve failed hypotheses
- revise a farm-defined rule when evidence supports doing so

The slow loop may explain a reflex later. It should not block an appropriate reflex now.

## Test

```bash
node public_value/reflex_loop.test.mjs
```

Expected output:

```
PASS: CropCircuit reflex loop v0.1
```

## Design principle

**Fast enough to protect. Simple enough to inspect. Humble enough not to diagnose.**
