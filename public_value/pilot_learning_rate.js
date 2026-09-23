/**
 * CropCircuit Repeated-Decision Pilot v0.1
 *
 * Descriptive instrumentation for comparing how several predictors learn over
 * repeated decisions. It does not choose a winner and does not turn a small
 * pilot into a superiority claim.
 */

const RELATIONS = new Set(["supported", "mixed", "contradicted"]);
const GATES = new Set(["pass", "hold", "reject", "not_run"]);

function isText(value) {
  return typeof value === "string" && value.trim().length > 0;
}
function isConfidence(value) {
  return Number.isFinite(Number(value)) && Number(value) >= 0 && Number(value) <= 1;
}
function array(value) {
  return Array.isArray(value) ? value : [];
}

export function validatePilotDecisionRecord(record = {}) {
  const errors = [];
  const warnings = [];

  if (record.schema_version !== "0.1") errors.push("schema_version must equal 0.1");
  if (!isText(record.record_id)) errors.push("record_id is required");
  if (!isText(record.pilot_id)) errors.push("pilot_id is required");
  if (!isText(record.decision_class)) errors.push("decision_class is required");
  if (!isText(record.created_at)) errors.push("created_at is required");

  if (!GATES.has(record?.governance?.gate)) {
    errors.push("governance.gate is not recognized");
  }

  const predictors = array(record.predictors);
  if (predictors.length < 2) errors.push("at least two predictors are required");

  const predictorIds = new Set();
  predictors.forEach((predictor, index) => {
    if (!isText(predictor?.predictor_id)) {
      errors.push(`predictors[${index}].predictor_id is required`);
    } else if (predictorIds.has(predictor.predictor_id)) {
      errors.push(`duplicate predictor_id: ${predictor.predictor_id}`);
    } else {
      predictorIds.add(predictor.predictor_id);
    }

    if (!isText(predictor?.prediction)) {
      errors.push(`predictors[${index}].prediction is required`);
    }
    if (!isConfidence(predictor?.confidence)) {
      errors.push(`predictors[${index}].confidence must be between 0 and 1`);
    }
  });

  const hasOutcome = record.outcome && isText(record.outcome.description);
  if (hasOutcome && !isText(record.outcome.recorded_at)) {
    errors.push("outcome.recorded_at is required when an outcome is present");
  }

  const evaluations = array(record.evaluations);
  const evaluationIds = new Set();

  evaluations.forEach((evaluation, index) => {
    if (!predictorIds.has(evaluation?.predictor_id)) {
      errors.push(`evaluations[${index}].predictor_id is not present in predictors`);
    } else if (evaluationIds.has(evaluation.predictor_id)) {
      errors.push(`duplicate evaluation for predictor: ${evaluation.predictor_id}`);
    } else {
      evaluationIds.add(evaluation.predictor_id);
    }
    if (!RELATIONS.has(evaluation?.relation)) {
      errors.push(`evaluations[${index}].relation is not recognized`);
    }
    if (!isText(evaluation?.note)) {
      errors.push(`evaluations[${index}].note is required`);
    }
  });

  if (hasOutcome) {
    for (const predictorId of predictorIds) {
      if (!evaluationIds.has(predictorId)) {
        warnings.push(`outcome exists but predictor ${predictorId} has not been evaluated yet`);
      }
    }
  }

  if (record?.governance?.gate === "reject") {
    warnings.push("record shows a rejected governance gate; verify that no prohibited action was executed");
  }

  return { valid: errors.length === 0, errors, warnings };
}

function relationCounts(evaluations) {
  return {
    supported: evaluations.filter(x => x.relation === "supported").length,
    mixed: evaluations.filter(x => x.relation === "mixed").length,
    contradicted: evaluations.filter(x => x.relation === "contradicted").length,
  };
}

function windowStats(items) {
  if (!items.length) {
    return {
      evaluated: 0,
      supported: 0,
      mixed: 0,
      contradicted: 0,
      contradiction_rate: null,
      high_confidence_contradictions: 0,
      mean_confidence: null,
    };
  }

  const counts = relationCounts(items);
  return {
    evaluated: items.length,
    ...counts,
    contradiction_rate: Number((counts.contradicted / items.length).toFixed(4)),
    high_confidence_contradictions: items.filter(
      x => x.relation === "contradicted" && x.confidence >= 0.75
    ).length,
    mean_confidence: Number(
      (items.reduce((sum, x) => sum + x.confidence, 0) / items.length).toFixed(4)
    ),
  };
}

export function summarizePredictorSeries(records = [], predictorId) {
  if (!isText(predictorId)) throw new TypeError("predictorId is required");

  const ordered = [...array(records)].sort((a, b) =>
    String(a.created_at || "").localeCompare(String(b.created_at || ""))
  );

  const evaluated = [];

  ordered.forEach(record => {
    const predictor = array(record.predictors).find(x => x.predictor_id === predictorId);
    const evaluation = array(record.evaluations).find(x => x.predictor_id === predictorId);
    if (!predictor || !evaluation || !RELATIONS.has(evaluation.relation)) return;

    evaluated.push({
      record_id: record.record_id,
      created_at: record.created_at,
      confidence: Number(predictor.confidence),
      relation: evaluation.relation,
      governance_gate: record?.governance?.gate || "not_run",
    });
  });

  const overall = windowStats(evaluated);
  const result = {
    predictor_id: predictorId,
    overall,
    early_window: null,
    late_window: null,
    contradiction_rate_delta: null,
    high_confidence_contradiction_delta: null,
    learning_signal_available: false,
    note:
      "Descriptive pilot summary only. It does not establish superiority or causal benefit.",
  };

  // Require at least 6 evaluated repeated decisions before comparing two windows.
  if (evaluated.length >= 6) {
    const split = Math.floor(evaluated.length / 2);
    const early = windowStats(evaluated.slice(0, split));
    const late = windowStats(evaluated.slice(split));
    result.early_window = early;
    result.late_window = late;
    result.contradiction_rate_delta = Number(
      (late.contradiction_rate - early.contradiction_rate).toFixed(4)
    );
    result.high_confidence_contradiction_delta =
      late.high_confidence_contradictions - early.high_confidence_contradictions;
    result.learning_signal_available = true;
  }

  return result;
}

export function comparePredictorSeries(records = []) {
  const predictorIds = new Set();
  array(records).forEach(record =>
    array(record.predictors).forEach(p => {
      if (isText(p?.predictor_id)) predictorIds.add(p.predictor_id);
    })
  );

  return {
    predictors: [...predictorIds]
      .sort()
      .map(id => summarizePredictorSeries(records, id)),
    record_count: array(records).length,
    note:
      "No winner is selected. Compare evidence, uncertainty, and learning trajectories in context.",
  };
}

export { RELATIONS, GATES };
