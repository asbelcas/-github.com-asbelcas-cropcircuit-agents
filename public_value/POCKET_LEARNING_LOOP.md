# Pocket Console Learning Cycles

The Farm Ops Pocket Console now closes the first full slow-loop learning cycle:

**observation → prediction → action → outcome → contradiction → update**

It remains local-first and single-file.

## Start from an observation

A recent observation can be sent into the **Learn** tab with the **Learn** button.

The observation becomes provenance for the new learning cycle. It is not silently converted into a prediction.

A cycle records, before action:

- question
- original prediction
- confidence
- explicit falsifier
- action/test
- reversibility
- stopping rule
- optional source observation

The prediction is preserved after the outcome is known.

## Close the loop

When an outcome is available, the operator records:

- what actually happened
- whether the result broadly supported, contradicted, or remained mixed relative to the prediction
- confidence after the outcome
- what the outcome taught
- optional next action
- whether the cycle should close

A contradicted or mixed outcome creates an unresolved contradiction record rather than rewriting the original prediction.

## Learning memory

The **Learning memory** table preserves:

- cycle state
- question
- original prediction
- current confidence
- number of outcomes
- latest outcome

There is intentionally no prominent delete button for learning cycles in this first version. Failed hypotheses are part of the farm's memory.

## Contract compatibility

Pocket Console cycles use the same v0.1 record shape defined by:

- [Learning Cycle JSON Schema](learning_cycle.schema.json)
- [Learning Loop](learning_loop.js)

A deterministic compatibility test is included in:

- [pocket_learning_cycle.test.mjs](pocket_learning_cycle.test.mjs)

## Provenance consistency

The Learning Loop now accepts `import` as a provenance kind so imported observation events can remain honestly labeled when they seed a learning cycle.

## Safety and authority

A learning cycle records belief, action, evidence, contradiction, and update.

It does not grant authority to:

- diagnose disease
- ignore animal welfare
- bypass safety rules
- spend money outside authorized limits
- perform irreversible actions automatically

The Right Relationship Gate and human authority rules still apply.

## Design principle

**Do not preserve the appearance of being right. Preserve the evidence of how the farm learned.**
