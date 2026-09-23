/**
 * CropCircuit Learning Loop v0.1
 *
 * A tiny, inspectable protocol for:
 * prediction -> action -> observation -> contradiction -> update.
 *
 * Design goal: make it cheaper to record uncertainty and failure honestly
 * than to rewrite the story after the outcome is known.
 */

const PROVENANCE_KINDS = new Set([
  "human_observation",
  "sensor_observation",
  "transaction",
  "experiment",
  "external_source",
  "import",
  "model_inference",
  "assumption",
]);

const STOP_STATUSES = new Set(["not_met", "met", "unknown"]);
const CONTRADICTION_STATUSES = new Set(["unresolved", "resolved"]);

function jsonClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function isText(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isConfidence(value) {
  return Number.isFinite(Number(value)) && Number(value) >= 0 && Number(value) <= 1;
}

function array(value) {
  return Array.isArray(value) ? value : [];
}

export function validateLearningCycle(record = {}) {
  const errors = [];
  const warnings = [];

  if (record.schema_version !== "0.1") {
    errors.push("schema_version must equal 0.1");
  }
  if (!isText(record.cycle_id)) errors.push("cycle_id is required");
  if (!isText(record.created_at)) errors.push("created_at is required");
  if (!isText(record.question)) errors.push("question is required");

  if (!isText(record?.prediction?.statement)) {
    errors.push("prediction.statement is required");
  }
  if (!isConfidence(record?.prediction?.confidence)) {
    errors.push("prediction.confidence must be between 0 and 1");
  }
  if (!array(record?.prediction?.falsifiers).some(isText)) {
    errors.push("prediction.falsifiers must contain at least one explicit falsifier");
  }

  if (!isText(record?.action?.description)) {
    errors.push("action.description is required");
  }
  if (typeof record?.action?.reversible !== "boolean") {
    errors.push("action.reversible must be true or false");
  }

  if (!isText(record?.stop_rule?.description)) {
    errors.push("stop_rule.description is required");
  }
  if (!STOP_STATUSES.has(record?.stop_rule?.status)) {
    errors.push("stop_rule.status must be not_met, met, or unknown");
  }

  for (const [index, item] of array(record.provenance).entries()) {
    if (!PROVENANCE_KINDS.has(item?.kind)) {
      errors.push(`provenance[${index}].kind is not recognized`);
    }
    if (!isText(item?.note) && !isText(item?.ref)) {
      errors.push(`provenance[${index}] needs note or ref`);
    }
  }

  for (const [index, item] of array(record.observations).entries()) {
    if (!isText(item?.recorded_at)) {
      errors.push(`observations[${index}].recorded_at is required`);
    }
    if (!isText(item?.result)) {
      errors.push(`observations[${index}].result is required`);
    }
    if (item?.surprise != null) {
      if (!isConfidence(item.surprise?.score)) {
        errors.push(`observations[${index}].surprise.score must be between 0 and 1`);
      }
      if (!isText(item.surprise?.reason)) {
        errors.push(`observations[${index}].surprise.reason is required when surprise is recorded`);
      }
    }
  }

  for (const [index, item] of array(record.contradictions).entries()) {
    if (!isText(item?.statement)) {
      errors.push(`contradictions[${index}].statement is required`);
    }
    if (!CONTRADICTION_STATUSES.has(item?.status)) {
      errors.push(`contradictions[${index}].status must be unresolved or resolved`);
    }
  }

  let previousConfidence = Number(record?.prediction?.confidence);
  for (const [index, item] of array(record.updates).entries()) {
    if (!isText(item?.recorded_at)) {
      errors.push(`updates[${index}].recorded_at is required`);
    }
    if (!isConfidence(item?.confidence_after)) {
      errors.push(`updates[${index}].confidence_after must be between 0 and 1`);
    }
    if (!isText(item?.rationale)) {
      errors.push(`updates[${index}].rationale is required`);
    }
    if (isConfidence(item?.confidence_before) && Number(item.confidence_before) !== previousConfidence) {
      warnings.push(`updates[${index}].confidence_before does not match prior recorded confidence`);
    }
    if (isConfidence(item?.confidence_after)) {
      previousConfidence = Number(item.confidence_after);
    }
  }

  if (!array(record.provenance).length) {
    warnings.push("no provenance recorded yet");
  }
  if (record?.action?.reversible === false && record?.stop_rule?.status === "unknown") {
    warnings.push("irreversible action has an unknown stopping condition");
  }

  return { valid: errors.length === 0, errors, warnings };
}

export function appendObservation(record, observation) {
  const next = jsonClone(record);
  if (!next.prediction) {
    throw new TypeError("A prediction must exist before observations can be appended");
  }
  if (!isText(observation?.recorded_at) || !isText(observation?.result)) {
    throw new TypeError("Observation requires recorded_at and result");
  }
  next.observations = array(next.observations);
  next.observations.push(jsonClone(observation));
  return next;
}

export function appendContradiction(record, contradiction) {
  if (!isText(contradiction?.statement)) {
    throw new TypeError("Contradiction requires statement");
  }
  const next = jsonClone(record);
  next.contradictions = array(next.contradictions);
  next.contradictions.push({
    statement: contradiction.statement,
    status: contradiction.status || "unresolved",
    evidence_refs: array(contradiction.evidence_refs),
    note: contradiction.note || "",
  });
  return next;
}

export function appendConfidenceUpdate(record, update) {
  if (!isConfidence(update?.confidence_after)) {
    throw new TypeError("confidence_after must be between 0 and 1");
  }
  if (!isText(update?.recorded_at) || !isText(update?.rationale)) {
    throw new TypeError("Confidence update requires recorded_at and rationale");
  }

  const next = jsonClone(record);
  const updates = array(next.updates);
  const prior = updates.length
    ? Number(updates[updates.length - 1].confidence_after)
    : Number(next?.prediction?.confidence);

  if (!isConfidence(prior)) {
    throw new TypeError("A valid prediction confidence must exist before confidence can be updated");
  }

  updates.push({
    recorded_at: update.recorded_at,
    confidence_before: prior,
    confidence_after: Number(update.confidence_after),
    rationale: update.rationale,
    model_change: update.model_change || "",
    next_action: update.next_action || "",
  });
  next.updates = updates;
  return next;
}

export function summarizeLearningCycle(record = {}) {
  const validation = validateLearningCycle(record);
  if (!validation.valid) {
    return {
      state: "invalid",
      validation,
      unresolved_contradictions: 0,
      observations: array(record.observations).length,
      confidence_delta: null,
      latest_surprise: null,
    };
  }

  const observations = array(record.observations);
  const contradictions = array(record.contradictions);
  const unresolved = contradictions.filter(x => x?.status !== "resolved");
  const updates = array(record.updates);

  const initialConfidence = Number(record.prediction.confidence);
  const currentConfidence = updates.length
    ? Number(updates[updates.length - 1].confidence_after)
    : initialConfidence;

  const surpriseItems = observations
    .map(x => x?.surprise)
    .filter(x => x && isConfidence(x.score));
  const latestSurprise = surpriseItems.length
    ? {
        score: Number(surpriseItems[surpriseItems.length - 1].score),
        reason: surpriseItems[surpriseItems.length - 1].reason,
      }
    : null;

  let state = "planned";
  if (observations.length) state = "observed";
  if (unresolved.length) state = "contradicted";
  if (record.stop_rule.status === "met") state = "stopped";

  return {
    state,
    validation,
    observations: observations.length,
    unresolved_contradictions: unresolved.length,
    initial_confidence: initialConfidence,
    current_confidence: currentConfidence,
    confidence_delta: Number((currentConfidence - initialConfidence).toFixed(4)),
    latest_surprise: latestSurprise,
    prediction_preserved: true,
  };
}

export function shouldContinueLearning(record = {}) {
  const summary = summarizeLearningCycle(record);

  if (summary.state === "invalid") {
    return { continue: false, reason: "invalid_record", summary };
  }
  if (record.stop_rule.status === "met") {
    return { continue: false, reason: "stop_rule_met", summary };
  }
  if (summary.unresolved_contradictions > 0) {
    return { continue: true, reason: "resolve_or_test_contradiction", summary };
  }
  if (summary.observations === 0) {
    return { continue: true, reason: "await_observation", summary };
  }
  if (record.stop_rule.status === "unknown") {
    return { continue: false, reason: "clarify_stop_rule", summary };
  }
  return { continue: true, reason: "continue_until_stop_rule", summary };
}

export { PROVENANCE_KINDS };
