# Right Relationship Decision Gate

The Right Relationship Gate is a CropCircuit decision primitive for choices where a single ROI number is not enough.

It is built around one structural idea:

**Hard boundaries should not be silently traded away by a weighted score.**

The design is inspired by the Dharma-Informed Design Doctrine.

## It does not decide morality for the farm

The operator defines:
- purpose;
- hard constraints;
- which constraints pass, fail, or remain unknown;
- enoughness;
- uncertainties;
- reversibility;
- descriptive effects.

CropCircuit does not contain a universal animal-welfare score, biodiversity score, or moral conversion factor.

## Gate states

### PASS
No required hard constraint is marked failed or unresolved.

This means only that the option may proceed to viability/tradeoff review. It is not a moral endorsement.

### HOLD
No hard constraint is known to fail, but an important hard constraint or effect remains unknown.

Recommended response:
- gather evidence;
- reduce the size of the decision;
- run a reversible test where practical.

### REJECT
At least one required hard constraint fails.

Higher profit, yield, or labor savings do not override the failed boundary.

## Why there is no total score

A weighted total can allow a severe water-quality failure to disappear inside a large financial gain.

CropCircuit treats declared hard constraints differently: a failed hard constraint stays failed.

## Reusable module

right_relationship.js exports evaluateRightRelationship(input).

The module returns a gate state plus failed/unresolved constraints and a plain-language summary.

## Related policy
- Dharma-Informed Design Doctrine
- Machine-readable right relationship constitution


## Decision record export

After evaluation, the browser tool can download a local JSON decision record containing:

- decision / option;
- purpose;
- enoughness note;
- reciprocity note;
- who/what bears costs;
- hard-constraint states;
- important unknowns;
- reversibility;
- the PASS / HOLD / REJECT gate result.

Nothing is uploaded. The record exists so a later operator or agent can inspect **why** a decision passed, held, or failed instead of seeing only the final outcome.
