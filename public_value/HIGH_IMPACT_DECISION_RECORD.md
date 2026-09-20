# High-Impact Decision Record

CropCircuit's values layer is useful only if consequential decisions leave an inspectable trail.

The High-Impact Decision Record is a portable JSON format for recording **why** an option was allowed to proceed, held, rejected, or reduced to a reversible experiment.

## Required sections

A record contains:

- decision and purpose;
- hard constraints and evidence;
- financial / operational / legal / technical / biological-ecological viability notes;
- reciprocity;
- enoughness;
- wider-system effects;
- unknowns;
- reversibility;
- gate result;
- decision outcome;
- review trigger.

## Non-compensation logic

The validator enforces three structural rules:

1. If a required hard constraint is `fail`, the gate must be `reject`.
2. If no required constraint fails but a required constraint or important effect is `unknown`, the gate must be `hold`.
3. Only when no required boundary fails or remains unknown may the gate be `pass_to_review`.

A PASS is permission to continue viability/tradeoff review. It is not a universal moral endorsement.

## Validation

```bash
node public_value/validate_decision_record.mjs decision.json
```

Multiple files may be supplied.

## Why this matters for agents

Without a durable record, later agents can see only the action and invent a rationale after the fact.

A decision record preserves:

- what the operator was trying to accomplish;
- which boundaries mattered;
- what evidence existed;
- what remained uncertain;
- what would trigger review.

This makes recursive automation more governable and easier to correct.

## Related

- [Dharma-Informed Design Doctrine](DHARMA_DESIGN_DOCTRINE.md)
- [Right Relationship Decision Gate](RIGHT_RELATIONSHIP_GATE.md)
- [Machine-readable constitution](right_relationship_constitution.json)
- [Decision record JSON Schema](decision_record.schema.json)
