/**
 * CropCircuit Reflex Loop v0.1
 *
 * Fast-loop primitive for inspectable threshold / state alerts from sparse input.
 * It does NOT diagnose causes and does NOT authorize irreversible actions.
 */

const SOURCE_KINDS = new Set([
  "human_observation",
  "sensor_observation",
  "transaction",
  "import",
  "external_source",
  "model_inference",
]);

const DOMAINS = new Set([
  "animal_welfare",
  "livestock",
  "water",
  "infrastructure",
  "safety",
  "pasture",
  "soil",
  "crop",
  "labor",
  "finance",
  "weather",
  "market",
  "other",
]);

const SEVERITY_ORDER = {
  emergency: 4,
  urgent: 3,
  watch: 2,
  info: 1,
};

const ALLOWED_SEVERITIES = new Set(Object.keys(SEVERITY_ORDER));
const ALLOWED_ACTIONS = new Set(["check_now", "review_soon", "log_only"]);
const COMPARATORS = new Set(["<", "<=", ">", ">=", "==", "!="]);

function isText(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function jsonClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function isDateTime(value) {
  return isText(value) && !Number.isNaN(Date.parse(value));
}

export function validateObservationEvent(event = {}) {
  const errors = [];
  const warnings = [];

  if (event.schema_version !== "0.1") errors.push("schema_version must equal 0.1");
  if (!isText(event.event_id)) errors.push("event_id is required");
  if (!isDateTime(event.recorded_at)) errors.push("recorded_at must be a valid date-time");
  if (!SOURCE_KINDS.has(event?.source?.kind)) errors.push("source.kind is not recognized");
  if (!DOMAINS.has(event.domain)) errors.push("domain is not recognized");
  if (!isText(event.summary)) errors.push("summary is required");

  if (event.signal_key != null && !isText(event.signal_key)) {
    errors.push("signal_key must be non-empty when provided");
  }
  if (event.severity_hint != null && !new Set(["normal", "watch", "urgent", "emergency"]).has(event.severity_hint)) {
    errors.push("severity_hint is not recognized");
  }
  if (!isText(event.signal_key)) {
    warnings.push("no signal_key: event can be recorded but deterministic reflex rules cannot match it");
  }
  if (event.source?.kind === "model_inference") {
    warnings.push("model_inference is not a direct observation");
  }

  return { valid: errors.length === 0, errors, warnings };
}

function compare(actual, comparator, expected) {
  if (comparator === "==") return actual === expected;
  if (comparator === "!=") return actual !== expected;

  const a = Number(actual);
  const b = Number(expected);
  if (!Number.isFinite(a) || !Number.isFinite(b)) return false;

  if (comparator === "<") return a < b;
  if (comparator === "<=") return a <= b;
  if (comparator === ">") return a > b;
  if (comparator === ">=") return a >= b;
  return false;
}

export function validateReflexRule(rule = {}, index = 0) {
  const errors = [];
  if (!isText(rule.id)) errors.push(`rules[${index}].id is required`);
  if (!isText(rule.signal_key)) errors.push(`rules[${index}].signal_key is required`);
  if (rule.domain != null && !DOMAINS.has(rule.domain)) errors.push(`rules[${index}].domain is not recognized`);
  if (!COMPARATORS.has(rule.comparator)) errors.push(`rules[${index}].comparator is not recognized`);
  if (!("threshold" in rule)) errors.push(`rules[${index}].threshold is required`);
  if (!ALLOWED_SEVERITIES.has(rule.severity)) errors.push(`rules[${index}].severity is not recognized`);
  if (!ALLOWED_ACTIONS.has(rule.action)) errors.push(`rules[${index}].action is not recognized`);
  if (!isText(rule.message)) errors.push(`rules[${index}].message is required`);
  return { valid: errors.length === 0, errors };
}

export function evaluateReflexes(event = {}, rules = []) {
  const validation = validateObservationEvent(event);
  if (!validation.valid) {
    return { state: "invalid_event", validation, alerts: [] };
  }

  if (!isText(event.signal_key)) {
    return { state: "record_only", validation, alerts: [] };
  }

  const alerts = [];

  rules.forEach((rawRule, index) => {
    const ruleValidation = validateReflexRule(rawRule, index);
    if (!ruleValidation.valid) {
      throw new TypeError(ruleValidation.errors.join("; "));
    }
    const rule = jsonClone(rawRule);
    if (rule.enabled === false) return;
    if (rule.signal_key !== event.signal_key) return;
    if (rule.domain && rule.domain !== event.domain) return;
    if (!compare(event.value, rule.comparator, rule.threshold)) return;

    alerts.push({
      alert_type: "reflex_alert",
      rule_id: rule.id,
      event_id: event.event_id,
      recorded_at: event.recorded_at,
      domain: event.domain,
      signal_key: event.signal_key,
      severity: rule.severity,
      action: rule.action,
      message: rule.message,
      evidence_refs: [...new Set([
        ...asArray(event.evidence_refs),
        ...(isText(event?.source?.ref) ? [event.source.ref] : []),
      ])],
      diagnosis: null,
      authorization: "alert_only",
      human_authority_required: rule.action !== "log_only",
      note: "Fast-loop alert from an inspectable rule. Check the real-world condition; this is not a diagnosis or authorization for irreversible action.",
    });
  });

  alerts.sort((a, b) => SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity]);

  return {
    state: alerts.length ? "alert" : "clear",
    validation,
    alerts,
  };
}

export { SOURCE_KINDS, DOMAINS, SEVERITY_ORDER };
