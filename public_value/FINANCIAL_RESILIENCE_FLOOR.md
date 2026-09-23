# Financial Resilience Floor v0.1

CropCircuit treats financial survivability as a **hard operating constraint**, not as a soft dashboard score.

This module evaluates **farm-defined** financial floors before a recommendation proceeds to broader tradeoff review.

## Important: CropCircuit does not invent the thresholds

There is no universal CropCircuit rule such as:

- every farm must keep a particular cash balance
- debt service must stay below one fixed percentage
- every farm needs the same number of runway months

Those numbers depend on the farm, season, debt structure, enterprise mix, risk tolerance, lender obligations, and household/business context.

The operator supplies the policy.

## Input

The evaluator takes:

- a `policy_id`
- an `as_of` timestamp
- projected or current numeric `metrics`
- one or more constraints

Each constraint specifies:

- `id`
- metric name
- comparator: `gte` or `lte`
- threshold
- whether the constraint is required
- source describing who or what defined the floor
- optional note

Example metrics might include:

- unrestricted cash after an action
- debt service after an action
- runway months after an action
- seasonal reserve after an action
- new cash outlay
- operating liquidity

The evaluator does not calculate those projections for the farm. It evaluates supplied numbers against supplied constraints.

## Gate states

### REJECT

At least one **required** farm-defined floor fails.

A high projected ROI does not compensate for that failure.

### HOLD

No required floor is known to fail, but at least one required floor cannot be evaluated from available data.

Unknown is not silently treated as pass.

### PASS_TO_REVIEW

Every required floor can be evaluated and passes.

This does **not** mean the action is recommended.

It means only that the action may proceed to the wider CropCircuit review of:

- animal welfare
- ecology
- labor
- legal/safety constraints
- reversibility
- trust
- resilience
- other system effects

## Advisory constraints

A farm may also define non-required preferences.

An advisory failure is surfaced but does not change the hard gate.

## Why this is separate from ROI

A weighted score can hide fragility.

For example, a project can have attractive long-term payback and still create an immediate cash condition the farm has explicitly declared unacceptable.

CropCircuit therefore keeps the financial floor **non-compensatory**.

## Dynamic means re-evaluated, not guessed

The same action may pass in one season and fail in another because the farm's actual metrics change.

The policy can also change when the authorized human changes the farm's declared floor.

CropCircuit should record both the metrics and the policy version used for each consequential decision.

## Files

- [financial_resilience_floor.js](financial_resilience_floor.js)
- [financial_resilience_floor.test.mjs](financial_resilience_floor.test.mjs)

## Design principle

**A regenerative recommendation must survive the farm's explicitly declared financial reality before it earns the right to be considered further.**
