# Pocket Console Cross-Domain Convergence

The Pocket Console can now surface a **provisional pattern** when observations from different farm domains begin pointing toward the same possible hypothesis.

This is the first user-facing implementation of CropCircuit's lateral-inference idea.

## What the farmer records

Quick Observe remains frictionless. A plain-language observation is still enough.

Optionally, the farmer can add:

- a **possible pattern** key, such as `northwest-paddock-anomaly`
- a **pattern support** percentage describing how strongly this observation appears to support that provisional pattern

The key is normalized locally so repeated labels can converge consistently.

Pattern tagging is deliberate in v0.1. CropCircuit does not automatically invent a common cause from unrelated records.

## When a convergence token appears

A provisional token is surfaced when:

- qualifying tagged observations share the same hypothesis key
- at least **three distinct domains** contribute
- each qualifying observation meets the current minimum support threshold used by the convergence primitive

The default shared primitive uses a minimum support value of 0.25 unless explicitly configured otherwise.

Examples of distinct domains include:

- animal welfare
- water
- labor
- pasture
- soil
- finance
- weather
- infrastructure

Three observations from the same domain do not count as three independent domains.

## What a token means

A convergence token means:

> Multiple parts of the farm are pointing toward the same possible pattern. It may be worth investigating.

It does **not** mean:

- the pattern is true
- CropCircuit knows the cause
- the observations are statistically independent
- an intervention is authorized
- an irreversible action should be taken

Every token remains `authorization: "none"`.

## Investigate

The **Investigate** button moves the token into the Learn workflow.

CropCircuit:

- carries all tagged source observations into the new learning cycle as provenance
- pre-fills only a neutral question about the pattern
- does **not** invent the prediction
- does **not** invent the falsifier
- does **not** invent the action

The operator still has to state what they think is happening before acting.

That preserves the core discipline:

**observation → provisional convergence → explicit hypothesis/prediction → action → outcome → contradiction → update**

## Why pattern tagging is manual first

Automatic relationship discovery is attractive, but it creates a serious epistemic risk: the software may manufacture a persuasive story from coincidental correlations.

The first implementation therefore favors legibility over automation.

Manual tags give us real data about:

- which relationships farmers actually suspect
- whether cross-domain patterns recur
- which tags become useful
- where automatic suggestions might eventually be safe and valuable

A future version may suggest candidate relationships, but suggestions should remain distinguishable from human-observed links.

## Relationship to the shared convergence primitive

The reusable implementation lives in:

- [signal_convergence.js](signal_convergence.js)
- [signal_convergence.test.mjs](signal_convergence.test.mjs)

Observation records now support:

- `hypothesis_key`
- `hypothesis_confidence`

The shared helper maps those tagged observation events into convergence signals and applies the same distinct-domain rule used by the Pocket Console.

## Design principle

**Notice convergence early. Claim causation late.**
