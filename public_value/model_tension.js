/**
 * CropCircuit Model Tension v0.1
 *
 * Preserves disagreement between partial farm models without collapsing them
 * into one weighted score or selecting a winner.
 */

const RECOMMENDATIONS = new Set(["proceed", "hold", "avoid", "investigate", "monitor", "no_position"]);
const TIME_SENSITIVITY = new Set(["now", "today", "days", "weeks", "seasonal", "long_term", "unknown"]);
const REVERSIBILITY = new Set(["high", "medium", "low", "irreversible", "unknown"]);
const HARD_CONSTRAINT_STATES = new Set(["pass", "fail", "unknown"]);

function isText(value) {
  return typeof value === "string" && value.trim().length > 0;
}
function isConfidence(value) {
  return Number.isFinite(Number(value)) && Number(value) >= 0 && Number(value) <= 1;
}
function array(value) {
  return Array.isArray(value) ? value : [];
}
function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

export function validateModelTension(input = {}) {
  const errors = [];
  const warnings = [];

  if (!isText(input.tension_id)) errors.push("tension_id is required");
  if (!isText(input.created_at)) errors.push("created_at is required");
  if (!isText(input.decision)) errors.push("decision is required");

  const positions = array(input.positions);
  if (positions.length < 2) errors.push("at least two model positions are required");

  positions.forEach((position, index) => {
    if (!isText(position?.model)) errors.push(`positions[${index}].model is required`);
    if (!RECOMMENDATIONS.has(position?.recommendation)) {
      errors.push(`positions[${index}].recommendation is not recognized`);
    }
    if (!isConfidence(position?.confidence)) {
      errors.push(`positions[${index}].confidence must be between 0 and 1`);
    }
    if (!isText(position?.reason)) errors.push(`positions[${index}].reason is required`);
    if (!TIME_SENSITIVITY.has(position?.time_sensitivity)) {
      errors.push(`positions[${index}].time_sensitivity is not recognized`);
    }
    if (!REVERSIBILITY.has(position?.reversibility)) {
      errors.push(`positions[${index}].reversibility is not recognized`);
    }

    array(position?.hard_constraints).forEach((constraint, cIndex) => {
      if (!isText(constraint?.id)) {
        errors.push(`positions[${index}].hard_constraints[${cIndex}].id is required`);
      }
      if (!HARD_CONSTRAINT_STATES.has(constraint?.status)) {
        errors.push(`positions[${index}].hard_constraints[${cIndex}].status is not recognized`);
      }
    });

    if (!array(position?.evidence_refs).length) {
      warnings.push(`positions[${index}] has no evidence_refs`);
    }
  });

  return { valid: errors.length === 0, errors, warnings };
}

export function evaluateModelTension(input = {}) {
  const validation = validateModelTension(input);
  if (!validation.valid) {
    return {
      state: "invalid",
      validation,
      record: null,
    };
  }

  const positions = clone(input.positions);
  const hardConstraints = positions.flatMap(position =>
    array(position.hard_constraints).map(constraint => ({
      ...constraint,
      model: position.model,
    }))
  );

  const failed = hardConstraints.filter(x => x.status === "fail");
  const unknown = hardConstraints.filter(x => x.status === "unknown");
  const recommendationSet = [...new Set(positions.map(x => x.recommendation))];

  let state = "aligned";
  if (failed.length) state = "blocked";
  else if (unknown.length) state = "hold_for_unknown";
  else if (recommendationSet.length > 1) state = "human_arbitration";

  return {
    state,
    validation,
    record: {
      schema_version: "0.1",
      tension_id: input.tension_id,
      created_at: input.created_at,
      decision: input.decision,
      context: input.context || "",
      positions,
      recommendations_present: recommendationSet.sort(),
      failed_hard_constraints: failed,
      unknown_hard_constraints: unknown,
      authority: input.authority || "authorized_human",
      selected_option: null,
      rationale: "",
      note:
        state === "blocked"
          ? "At least one model position reports a failed hard constraint. Do not trade it away with a weighted score."
          : state === "hold_for_unknown"
            ? "At least one hard constraint remains unknown. Resolve or reduce the decision before proceeding."
            : state === "human_arbitration"
              ? "Models disagree without a hard-constraint resolution. Preserve the disagreement and route the tradeoff to the authorized human."
              : "The recorded model positions are directionally aligned. Continue ordinary governed review.",
    },
  };
}

export function recordHumanArbitration(evaluation, decision = {}) {
  if (!evaluation?.record || evaluation?.state === "invalid") {
    throw new TypeError("A valid model-tension evaluation is required");
  }
  if (!isText(decision.selected_option)) {
    throw new TypeError("selected_option is required");
  }
  if (!isText(decision.rationale)) {
    throw new TypeError("rationale is required");
  }

  const next = clone(evaluation);
  next.record.selected_option = decision.selected_option;
  next.record.rationale = decision.rationale;
  next.record.decided_at = decision.decided_at || "";
  next.record.decided_by = decision.decided_by || "authorized_human";
  next.record.follow_up = decision.follow_up || "";
  return next;
}

export {
  RECOMMENDATIONS,
  TIME_SENSITIVITY,
  REVERSIBILITY,
  HARD_CONSTRAINT_STATES,
};
