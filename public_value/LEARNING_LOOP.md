# CropCircuit Learning Loop v0.1

The Learning Loop is the smallest CropCircuit primitive for learning from reality without rewriting the story after the outcome is known.

**prediction → action → observation → contradiction → update**

It is deliberately small. It does not choose goals, invent evidence, or decide what is morally acceptable. Existing CropCircuit governance tools remain responsible for hard ecological, welfare, human, legal, safety, and resilience boundaries.

## Core invariant

> A cycle should gain epistemic value even when the proposed action fails.

A clean failure can update a model. An undocumented or post-hoc-rewritten failure cannot.

## What the record preserves

Each cycle keeps:

- the question being tested;
- a prediction written before the observation;
- an explicit confidence value between 0 and 1;
- at least one falsifier;
- the action and whether it is reversible;
- a stopping rule;
- provenance separated by source type;
- observations, including optional surprise scores and reasons;
- contradictions that remain visible until resolved;
- confidence updates with rationale and model changes.

The original prediction is not overwritten by the helper functions.

## Provenance types

The v0.1 vocabulary distinguishes:

- `human_observation`
- `sensor_observation`
- `transaction`
- `experiment`
- `external_source`
- `model_inference`
- `assumption`

This prevents a model inference from silently becoming "an observation."

## Stopping rules

Every loop must know what would make it stop.

`shouldContinueLearning()` halts when:

- the record is invalid;
- the stop rule is met; or
- the stopping condition itself is unknown and needs clarification.

Unresolved contradictions instead return a reason to investigate or test them.

## Minimal use

```js
import {
  appendObservation,
  appendContradiction,
  appendConfidenceUpdate,
  shouldContinueLearning,
  summarizeLearningCycle
} from "./learning_loop.js";
```

Start with a JSON record conforming to [learning_cycle.schema.json](learning_cycle.schema.json). A synthetic example is available at [examples/synthetic_learning_cycle.json](examples/synthetic_learning_cycle.json).

## Surprise

Surprise is deliberately recorded rather than inferred. A generic utility cannot know whether an outcome is surprising without smuggling in assumptions about the domain.

When recorded, surprise has:

- a score from 0 to 1;
- a plain-language reason.

This makes the quantity inspectable rather than magical.

## Lateral contradiction

Not every model failure appears as a direct prediction/outcome mismatch. Independent signals from different domains can converge on the same possible anomaly.

CropCircuit therefore also supports [Signal Convergence](signal_convergence.js), which can create an explicitly provisional hypothesis token when multiple distinct domains point toward the same hypothesis key.

A convergence token:
- is evidence to investigate;
- carries no action authorization;
- preserves the contributing signal IDs and domains;
- does not claim a diagnosis.

## Hypothesis memory

A failed prediction should not disappear when confidence falls. Preserve it with its conditions, evidence, outcome, contradiction, and update. This makes failure searchable rather than disposable and prevents later operators from rediscovering the same dead end without context.

## Relationship to governed decisions

The Learning Loop does **not** replace:

- [Right Relationship Decision Gate](RIGHT_RELATIONSHIP_GATE.md)
- [High-Impact Decision Record](HIGH_IMPACT_DECISION_RECORD.md)
- [Dharma-Informed Design Doctrine](DHARMA_DESIGN_DOCTRINE.md)

Those tools constrain what may be attempted. The Learning Loop records what was expected, what happened, and what changed in the model.

## Design principle

**Make honesty cheaper than performance, and curiosity cheaper than certainty.**
