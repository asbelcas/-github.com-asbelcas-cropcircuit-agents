/**
 * CropCircuit signal convergence v0.1
 *
 * Detects when independent domains point toward the same provisional
 * hypothesis. This does not diagnose a cause and does not authorize action.
 * It creates an inspectable hypothesis token for investigation.
 */

function isText(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isConfidence(value) {
  return Number.isFinite(Number(value)) && Number(value) >= 0 && Number(value) <= 1;
}

function normalizeSignal(signal, index) {
  if (!isText(signal?.id)) throw new TypeError(`signals[${index}].id is required`);
  if (!isText(signal?.domain)) throw new TypeError(`signals[${index}].domain is required`);
  if (!isText(signal?.hypothesis_key)) {
    throw new TypeError(`signals[${index}].hypothesis_key is required`);
  }
  if (!isConfidence(signal?.confidence)) {
    throw new TypeError(`signals[${index}].confidence must be between 0 and 1`);
  }
  if (!isText(signal?.recorded_at)) {
    throw new TypeError(`signals[${index}].recorded_at is required`);
  }

  return {
    id: signal.id.trim(),
    domain: signal.domain.trim(),
    hypothesis_key: signal.hypothesis_key.trim(),
    confidence: Number(signal.confidence),
    recorded_at: signal.recorded_at,
    evidence_ref: isText(signal.evidence_ref) ? signal.evidence_ref : "",
    note: isText(signal.note) ? signal.note : "",
  };
}

export function detectSignalConvergence(signals = [], options = {}) {
  const minDomains = Number.isInteger(options.min_domains)
    ? Math.max(options.min_domains, 2)
    : 3;
  const minSignalConfidence = isConfidence(options.min_signal_confidence)
    ? Number(options.min_signal_confidence)
    : 0.25;

  const normalized = signals.map(normalizeSignal);
  const groups = new Map();

  for (const signal of normalized) {
    if (signal.confidence < minSignalConfidence) continue;
    const group = groups.get(signal.hypothesis_key) || [];
    group.push(signal);
    groups.set(signal.hypothesis_key, group);
  }

  const tokens = [];

  for (const [hypothesisKey, group] of groups.entries()) {
    const domains = [...new Set(group.map(x => x.domain))].sort();
    if (domains.length < minDomains) continue;

    const meanConfidence = group.reduce((sum, x) => sum + x.confidence, 0) / group.length;
    const minConfidence = Math.min(...group.map(x => x.confidence));
    const maxConfidence = Math.max(...group.map(x => x.confidence));

    tokens.push({
      token_type: "provisional_hypothesis",
      hypothesis_key: hypothesisKey,
      status: "investigate",
      distinct_domains: domains.length,
      domains,
      signal_count: group.length,
      signal_ids: group.map(x => x.id),
      evidence_refs: group.map(x => x.evidence_ref).filter(Boolean),
      confidence_summary: {
        min: Number(minConfidence.toFixed(4)),
        mean: Number(meanConfidence.toFixed(4)),
        max: Number(maxConfidence.toFixed(4)),
      },
      authorization: "none",
      note: "Cross-domain convergence is evidence to investigate, not proof of cause or permission for irreversible action.",
    });
  }

  return tokens.sort((a, b) => {
    if (b.distinct_domains !== a.distinct_domains) {
      return b.distinct_domains - a.distinct_domains;
    }
    return b.signal_count - a.signal_count;
  });
}

export function observationToConvergenceSignal(event = {}, index = 0) {
  if (!isText(event?.hypothesis_key)) return null;
  if (!isText(event?.event_id)) {
    throw new TypeError(`observations[${index}].event_id is required when hypothesis_key is set`);
  }
  if (!isText(event?.domain)) {
    throw new TypeError(`observations[${index}].domain is required when hypothesis_key is set`);
  }
  if (!isText(event?.recorded_at)) {
    throw new TypeError(`observations[${index}].recorded_at is required when hypothesis_key is set`);
  }
  if (!isConfidence(event?.hypothesis_confidence)) {
    throw new TypeError(`observations[${index}].hypothesis_confidence must be between 0 and 1 when hypothesis_key is set`);
  }

  return {
    id: event.event_id,
    domain: event.domain,
    hypothesis_key: event.hypothesis_key,
    confidence: Number(event.hypothesis_confidence),
    recorded_at: event.recorded_at,
    evidence_ref: event.event_id,
    note: isText(event?.summary) ? event.summary : "",
  };
}

export function detectObservationConvergence(observations = [], options = {}) {
  const signals = [];
  observations.forEach((event, index) => {
    const signal = observationToConvergenceSignal(event, index);
    if (signal) signals.push(signal);
  });
  return detectSignalConvergence(signals, options);
}

export function summarizeConvergence(tokens = []) {
  return {
    tokens: tokens.length,
    hypotheses: tokens.map(x => x.hypothesis_key),
    requires_human_review: tokens.length > 0,
  };
}
