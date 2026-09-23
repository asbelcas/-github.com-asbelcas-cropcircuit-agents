# CropCircuit Farm Nervous System Architecture v0.1

Status: design baseline  
Purpose: turn the regenerative systems constitution into an implementable farm information architecture

## Why this exists

The operating constitution says CropCircuit should behave more like a nervous system than a command center. This document defines what that means technically.

The architecture assumes farm information is incomplete, delayed, noisy, and distributed across people, animals, sensors, records, weather, and financial systems.

It therefore does **not** require complete information before acting.

## 1. Two loops, not one

### Fast loop — reflex

The fast loop exists for time-sensitive signals where waiting for a full model could increase harm.

Examples:
- welfare threshold crossed
- animal missing from an expected process
- water or temperature anomaly
- safety hazard
- equipment state that could damage animals, people, or infrastructure

Fast-loop properties:
- minimal required input
- simple, inspectable rules
- low latency
- conservative escalation
- human-readable reason
- never blocked by slow-loop analysis

A fast-loop alert may say **check now**. It should not pretend to know the full cause.

### Slow loop — deliberation

The slow loop integrates richer context over hours, days, weeks, seasons, or years.

Examples:
- grazing rotation
- labor redesign
- capital purchases
- soil improvement
- recurring animal behavior
- seasonal cash planning
- long-term ecological change

Slow-loop properties:
- relationship mapping
- multiple models
- explicit uncertainty
- prediction before action
- outcome tracking
- contradiction and model update
- reversible probes when possible

The fast loop protects the organism. The slow loop helps it learn.

## 2. Lateral signal convergence

Contradiction does not always arrive as "prediction X was false."

Often signals from different domains converge sideways:

- a sensor value shifts
- the farmer notices unusual behavior
- labor time increases
- production changes
- cash or input use changes

None alone proves the cause.

CropCircuit should create a **provisional hypothesis token** when multiple independent domains begin pointing toward the same possible issue.

A token is:
- lightweight
- explicitly uncertain
- evidence-linked
- easy to dismiss or investigate
- not permission to take an irreversible action

The first implementation is `signal_convergence.js`.

## 3. Farmer-model divergence is a feature

When the farmer and CropCircuit disagree, do not silently override either side.

Record:
- CropCircuit prediction
- farmer prediction or chosen action
- outcome
- repeated pattern, if any

Then surface the divergence as a question.

Example:

> CropCircuit predicted X. You expected Y. We observed Z. This pattern has appeared three times under similar conditions. Want to inspect what each model is weighting differently?

The goal is co-learning, not obedience.

## 4. Dynamic financial resilience floor

Financial survivability is a hard operating constraint.

The floor is farm-defined and dynamic. CropCircuit must not invent a universal threshold.

Possible farm-supplied constraints include:
- minimum unrestricted cash reserve
- maximum monthly debt-service burden
- maximum new cash outlay without review
- minimum runway
- seasonal reserve requirement
- capital-project contingency
- required operating liquidity

The system must distinguish:
- temporary seasonal tightness in a structurally viable operation
- chronic under-capitalization
- acute insolvency risk

A recommendation that would cross a declared financial floor is **HOLD** or **REJECT**, not "high ROI."

The financial resilience floor now has an executable primitive:

- `financial_resilience_floor.js` evaluates farm-defined numeric constraints
- required failures are non-compensatory and produce `reject`
- missing required metrics produce `hold`
- passing the financial floor produces only `pass_to_review`, never an automatic recommendation
- no universal threshold is embedded in the software

See `FINANCIAL_RESILIENCE_FLOOR.md`.

## 5. Model arbitration without one magic score

CropCircuit will contain multiple partial models:
- animal welfare / health
- pasture / forage
- soil
- labor
- finance
- weather / microclimate
- infrastructure
- customer / market

These models can disagree.

Do not collapse them into one opaque weighted score.

Instead produce a tension record:
- model
- recommendation
- evidence
- uncertainty
- hard constraints implicated
- time sensitivity
- reversibility
- authority required

If no hard constraint resolves the tension, route the decision to the authorized human.

Model tension and hypothesis memory now have executable primitives:

- `model_tension.js` preserves each model's recommendation, confidence, evidence, hard constraints, time sensitivity, and reversibility without choosing a winner
- hard-constraint failures block; hard unknowns hold; unresolved model disagreement routes to human arbitration
- `hypothesis_memory.js` creates searchable memory records from learning cycles and never auto-rejects a hypothesis from one contradiction
- the Pocket Console **Memory** tab stores disposition, conditions, tags, reason, outcomes, contradictions, and confidence history locally

## 6. Hypothesis graveyard

A failed hypothesis is not deleted.

Preserve:
- what was believed
- when
- under which conditions
- confidence
- action
- outcome
- contradiction
- why it was rejected or suspended

A failed idea under drought may become useful under wet conditions.

The graveyard is searchable memory, not a trash bin.

### Implemented foundation

The Pocket Console now implements the first capture surface: a local-first **Quick observe** tab that stores source-aware observation events and preserves them in workspace backups. It intentionally allows capture before full structure; signal keys and values are optional.

The first shared fast-loop substrate now exists:

- `observation_event.schema.json` defines a source-aware observation event
- `reflex_loop.js` evaluates inspectable farm-defined reflex rules from sparse observations
- `reflex_loop.test.mjs` verifies alert-only behavior, clear state, record-only freeform observations, and provenance warnings
- `REFLEX_LOOP.md` documents the safety boundary

The Reflex Loop intentionally does not diagnose causes or authorize irreversible actions.

The first full slow-loop path is now implemented in the Pocket Console:

- an observation can seed a learning cycle
- prediction, confidence, falsifier, action, reversibility, and stop rule are recorded before outcome
- outcomes append rather than replace the original prediction
- mixed or contradicted outcomes create unresolved contradiction memory
- confidence updates preserve rationale and next action
- learning cycles persist in local storage and workspace backup

See `POCKET_LEARNING_LOOP.md` and `pocket_learning_cycle.test.mjs`.

Cross-domain convergence is now visible in the Pocket Console:

- observations can optionally carry a user-supplied provisional hypothesis key and support strength
- qualifying observations from at least three distinct domains can surface a provisional convergence token
- the token explicitly carries no action authorization
- **Investigate** moves the contributing observations into a new learning cycle as provenance
- CropCircuit pre-fills a neutral question but does not invent the prediction, falsifier, or action

See `POCKET_CONVERGENCE.md` and `signal_convergence.js`.

## 7. Minimum viable nervous system

Build in this sequence:

1. **Frictionless observation recorder**
   - voice note
   - timestamped photo
   - one-tap event
   - text when convenient
   - structured fields added later, not required at capture

2. **Prediction log**
   - prediction written before action
   - confidence
   - falsifier
   - provenance

3. **Outcome recorder**
   - timestamped
   - linked to prediction/action
   - accepts farmer correction and context

4. **Contradiction + convergence layer**
   - prediction/outcome mismatch
   - cross-domain signal convergence
   - questions rather than accusations

5. **Relationship view**
   - show active flows and dependencies
   - show stress and slack
   - show which evidence supports each connection
   - show unknowns

The relationship view now has an executable primitive and Pocket Console surface:

- `relationship_flow.js` validates recorded nodes and edges, surfaces stressed/unknown areas, and traces local neighborhoods
- non-unknown states without evidence references generate warnings
- the Pocket Console **Relationships** tab stores local nodes, flows, evidence, and unknowns
- connectedness is not treated as proof of causation

See `RELATIONSHIP_FLOW.md`.

Only then should higher-level recommendation systems dominate product development.

## 8. What remains decentralized

Keep final authority local for:
- novel animal-welfare situations
- emergency actions where local physical context dominates
- irreversible interventions
- choices requiring consent
- morally weighty tradeoffs
- decisions where the data model is materially incomplete

Automation may inform these decisions. It should not erase responsibility.

## 9. Human authority

Humans retain responsibility for:
- permission
- accountability
- mercy
- context-sensitive exceptions
- declared values
- acceptance of irreversible downside

This is not because humans are infallible. It is because accountability should not disappear behind automation.

## 10. Time scales

Not all feedback closes at the same rate.

Typical examples:
- seconds/minutes: safety, equipment, acute welfare
- hours/days: milking, water, animal behavior, chores
- days/weeks: grazing, labor redesign, feed or workflow pilots
- months/seasons: soil, forage, enterprise economics
- years: resilience, infrastructure, ecological succession

The system must not delay a fast loop to satisfy a slow one or declare a slow-loop question resolved from one fast observation.

## 11. Validation experiment

The first serious proof should compare **learning rate**, not just initial accuracy.

For one real farm workflow, record in parallel before each decision:
- CropCircuit prediction
- farmer prediction
- conventional software or rule-based recommendation when available

Then record outcomes.

A grazing-season example can measure:
- pasture recovery time
- animal body condition or another appropriate welfare/condition indicator
- labor hours per decision / rotation
- a farmer-selected financial metric

Primary question:

**Which model improves most over repeated decisions without violating hard welfare, ecological, human, legal, or financial constraints?**

Do not claim superiority from a small pilot. The first season is evidence generation.

Repeated-decision pilot instrumentation is now implemented:

- `pilot_decision_record.schema.json` preserves timestamped pre-outcome predictions from two or more predictors
- `pilot_learning_rate.js` reports descriptive supported/mixed/contradicted counts, contradiction rate, high-confidence contradictions, and early/late windows once enough repeated decisions exist
- the summary deliberately selects no winner
- governance gate state remains attached to each record
- predictions are not edited after outcomes

See `REPEATED_DECISION_PILOT.md`.

The Pocket Console now exposes the repeated-decision pilot workflow directly: pre-outcome farmer/CropCircuit predictions, optional conventional comparator, outcome closure, per-predictor relation notes, and descriptive repeated-decision summaries. Pilot records persist in local workspace backup.

## 12. Product consequence

This changes the roadmap.

Priority is not "more calculators."

Priority becomes:
- easier observation capture
- better provenance
- prediction before action
- outcome closure
- contradiction detection
- cross-domain convergence
- relationship visibility
- model arbitration
- memory of failed hypotheses

Domain applications such as cow fetching, grazing, labor automation, irrigation, and farm finance sit on top of this substrate.

## Design shorthand

**Reflex quickly. Deliberate slowly. Preserve disagreement. Keep failed hypotheses. Protect the financial floor. Let many partial models speak. Keep irreversible authority local.**
