/**
 * CropCircuit Financial Resilience Floor v0.1
 *
 * Evaluates farm-defined financial hard constraints without inventing
 * universal thresholds or collapsing them into a weighted score.
 *
 * Gate semantics:
 * - reject: at least one required constraint fails
 * - hold: no required failures, but at least one required constraint is unknown
 * - pass_to_review: all required constraints can be evaluated and pass
 */

const COMPARATORS = new Set(["gte", "lte"]);

function isText(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isFiniteNumber(value) {
  return Number.isFinite(Number(value));
}

function array(value) {
  return Array.isArray(value) ? value : [];
}

function evaluateComparator(value, comparator, threshold) {
  if (comparator === "gte") return value >= threshold;
  if (comparator === "lte") return value <= threshold;
  throw new TypeError("Unsupported comparator: " + comparator);
}

export function validateFinancialResilienceInput(input = {}) {
  const errors = [];
  const warnings = [];

  if (!isText(input.policy_id)) errors.push("policy_id is required");
  if (!isText(input.as_of)) errors.push("as_of is required");

  if (!input.metrics || typeof input.metrics !== "object" || Array.isArray(input.metrics)) {
    errors.push("metrics must be an object");
  }

  const constraints = array(input.constraints);
  if (!constraints.length) {
    errors.push("at least one farm-defined constraint is required");
  }

  constraints.forEach((constraint, index) => {
    if (!isText(constraint?.id)) errors.push(`constraints[${index}].id is required`);
    if (!isText(constraint?.metric)) errors.push(`constraints[${index}].metric is required`);
    if (!COMPARATORS.has(constraint?.comparator)) {
      errors.push(`constraints[${index}].comparator must be gte or lte`);
    }
    if (!isFiniteNumber(constraint?.threshold)) {
      errors.push(`constraints[${index}].threshold must be numeric`);
    }
    if (typeof constraint?.required !== "boolean") {
      errors.push(`constraints[${index}].required must be true or false`);
    }
    if (!isText(constraint?.source)) {
      warnings.push(`constraints[${index}] has no source note; record who or what defined this floor`);
    }
  });

  if (input.metrics && typeof input.metrics === "object" && !Array.isArray(input.metrics)) {
    for (const [key, value] of Object.entries(input.metrics)) {
      if (value != null && !isFiniteNumber(value)) {
        warnings.push(`metrics.${key} is not numeric and will be treated as unknown`);
      }
    }
  }

  return { valid: errors.length === 0, errors, warnings };
}

export function evaluateFinancialResilienceFloor(input = {}) {
  const validation = validateFinancialResilienceInput(input);
  if (!validation.valid) {
    return {
      gate: "invalid",
      validation,
      evaluations: [],
      failed_required_constraints: [],
      unknown_required_constraints: [],
      advisory_failures: [],
    };
  }

  const metrics = input.metrics || {};
  const evaluations = array(input.constraints).map(constraint => {
    const raw = metrics[constraint.metric];
    const known = raw != null && isFiniteNumber(raw);

    if (!known) {
      return {
        id: constraint.id,
        metric: constraint.metric,
        comparator: constraint.comparator,
        threshold: Number(constraint.threshold),
        value: null,
        required: constraint.required,
        status: "unknown",
        source: constraint.source || "",
        note: constraint.note || "",
      };
    }

    const value = Number(raw);
    const threshold = Number(constraint.threshold);
    const passed = evaluateComparator(value, constraint.comparator, threshold);

    return {
      id: constraint.id,
      metric: constraint.metric,
      comparator: constraint.comparator,
      threshold,
      value,
      required: constraint.required,
      status: passed ? "pass" : "fail",
      source: constraint.source || "",
      note: constraint.note || "",
    };
  });

  const failedRequired = evaluations.filter(x => x.required && x.status === "fail");
  const unknownRequired = evaluations.filter(x => x.required && x.status === "unknown");
  const advisoryFailures = evaluations.filter(x => !x.required && x.status === "fail");

  let gate = "pass_to_review";
  if (failedRequired.length) gate = "reject";
  else if (unknownRequired.length) gate = "hold";

  return {
    gate,
    policy_id: input.policy_id,
    as_of: input.as_of,
    validation,
    evaluations,
    failed_required_constraints: failedRequired.map(x => x.id),
    unknown_required_constraints: unknownRequired.map(x => x.id),
    advisory_failures: advisoryFailures.map(x => x.id),
    summary:
      gate === "reject"
        ? "A required farm-defined financial floor would be crossed."
        : gate === "hold"
          ? "A required farm-defined financial floor cannot be evaluated from the available metrics."
          : "All required farm-defined financial floors pass; continue to wider tradeoff review.",
  };
}

export { COMPARATORS };
