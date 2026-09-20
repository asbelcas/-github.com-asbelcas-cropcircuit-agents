/**
 * CropCircuit Right Relationship Gate.
 * Transparent non-compensatory decision logic.
 * The caller defines hard constraints and descriptive judgments.
 * No universal moral score is assigned.
 */
export function evaluateRightRelationship(input = {}) {
  const hardConstraints = Array.isArray(input.hard_constraints) ? input.hard_constraints : [];
  const unknowns = Array.isArray(input.unknowns) ? input.unknowns : [];
  const failed = hardConstraints.filter(x => x && x.required !== false && x.status === "fail");
  const unresolved = hardConstraints.filter(x => x && x.required !== false && (x.status === "unknown" || !x.status));

  let gate = "pass";
  if (failed.length) gate = "reject";
  else if (unresolved.length || unknowns.length) gate = "hold";

  return {
    gate,
    failed_hard_constraints: failed.map(x => x.id || x.label || "unnamed"),
    unresolved_hard_constraints: unresolved.map(x => x.id || x.label || "unnamed"),
    unknowns: unknowns.map(x => typeof x === "string" ? x : (x.id || x.label || "unnamed")),
    enoughness_met: input.enoughness_met === true,
    reversible: input.reversible === true,
    summary: gate === "reject"
      ? "At least one required hard constraint fails. Do not use higher performance on another dimension to override it."
      : gate === "hold"
        ? "No required hard constraint is known to fail, but important constraints or effects remain unresolved."
        : "No required hard constraint is marked failed or unresolved. Continue with viability and tradeoff review; this is not a moral endorsement."
  };
}
