# Equipment Cost Threshold Analyzer

This tool answers a narrower question than "Should I buy this?"

It asks:

**Given my measured labor cost, a chosen time-saving assumption, and a target simple-payback period, what is the maximum upfront price that fits those assumptions?**

## Workflow

1. Track real work with the Offline Farm Labor Log.
2. Annualize and rank it with the Labor Opportunity Analyzer.
3. Export the opportunity-analysis CSV.
4. Load that CSV into `equipment_cost_threshold.html`.
5. Choose:
   - expected time reduction
   - target payback years
   - added annual operating cost
   - expected salvage value

The tool ranks tasks by their modeled capital-cost threshold.

## Formula

```text
gross annual savings
  = annual labor cost × time-reduction fraction

net annual savings
  = gross annual savings − added annual operating cost

maximum upfront cost at target
  = net annual savings × target payback years + salvage value
```

If net annual savings are not positive, the tool does not create a positive threshold beyond any salvage value entered.

## Important omissions

Simple payback is intentionally crude. The threshold does not automatically account for:

- interest or financing
- taxes
- depreciation
- repair uncertainty
- downtime
- training
- safety
- biological effects
- changes in throughput or quality
- opportunity cost

Those can matter more than the arithmetic. The tool is for first-pass screening, not capital-investment advice.


## Value constraints come first

A capital threshold is downstream of the farm's hard boundaries.

If an equipment or automation choice materially affects animal welfare, soil/water, worker safety/capacity, or critical resilience, use the [Right Relationship Decision Gate](right_relationship_gate.html) before treating this financial threshold as actionable.

The rule is non-compensatory:

**a better payback does not erase a failed hard constraint.**

The threshold tool still does the arithmetic; the value gate determines whether an option belongs in the set of acceptable options at all.
