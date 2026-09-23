# Hypothesis Memory v0.1

CropCircuit keeps failed, suspended, and inconclusive hypotheses as **searchable memory**.

The goal is not to create a cemetery of "wrong ideas." It is to preserve what was believed, under what conditions, what happened, and why confidence changed.

## Why this matters

A farm can encounter the same pattern months or years later under different conditions.

If the old hypothesis simply disappeared, a future worker or model might repeat the same failed reasoning from scratch.

A useful memory entry preserves:

- original prediction
- initial confidence
- current confidence
- question
- action
- outcomes
- contradictions
- model updates
- source references
- conditions
- tags
- human-assigned disposition
- reason for that disposition

## Dispositions

### ACTIVE

Still under investigation.

### SUPPORTED

Current evidence supports continued use of the hypothesis.

This is not the same as universal truth.

### INCONCLUSIVE

The cycle did not resolve the hypothesis cleanly.

### SUSPENDED

The hypothesis is not currently being pursued, often because the required conditions or evidence are unavailable.

### REJECTED

The authorized operator has decided the hypothesis should not guide current decisions under the recorded conditions.

CropCircuit does **not** automatically set a hypothesis to rejected merely because one outcome contradicts it.

## The graveyard

The `graveyard()` helper returns:

- inconclusive
- suspended
- rejected

entries.

They stay searchable.

That means an old idea can be rediscovered with context rather than resurrected as if nobody tested it before.

## Conditions matter

A hypothesis can fail under:

- drought
- winter
- one animal group
- one soil type
- one equipment state
- one labor configuration

and behave differently elsewhere.

Conditions therefore belong in the memory record.

## Search

`searchHypothesisMemory()` can search across:

- original predictions
- questions
- conditions
- tags
- reasons
- outcomes
- contradictions
- model changes
- next actions

## Files

- [hypothesis_memory.js](hypothesis_memory.js)
- [hypothesis_memory.test.mjs](hypothesis_memory.test.mjs)

## Design principle

**Do not delete a failed idea. Preserve the conditions under which reality disagreed with it.**
