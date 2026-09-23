import assert from "node:assert/strict";
import {
  evaluateReflexes,
  validateObservationEvent,
  validateReflexRule,
} from "./reflex_loop.js";

const event = {
  schema_version: "0.1",
  event_id: "synthetic-water-001",
  recorded_at: "2026-09-23T18:00:00Z",
  source: {
    kind: "sensor_observation",
    ref: "synthetic:tank-sensor-1"
  },
  domain: "water",
  signal_key: "tank_percent",
  summary: "Synthetic tank level reading for reflex-loop test.",
  value: 12,
  unit: "%",
  severity_hint: "watch",
  evidence_refs: ["synthetic:reading-001"],
  privacy: "private"
};

const rules = [
  {
    id: "synthetic-water-low",
    enabled: true,
    domain: "water",
    signal_key: "tank_percent",
    comparator: "<",
    threshold: 20,
    severity: "urgent",
    action: "check_now",
    message: "Synthetic test: tank level is below the farm-defined check threshold."
  },
  {
    id: "synthetic-water-empty",
    enabled: true,
    domain: "water",
    signal_key: "tank_percent",
    comparator: "<=",
    threshold: 0,
    severity: "emergency",
    action: "check_now",
    message: "Synthetic test: tank reports empty."
  }
];

assert.equal(validateObservationEvent(event).valid, true);
assert.equal(validateReflexRule(rules[0]).valid, true);

const result = evaluateReflexes(event, rules);
assert.equal(result.state, "alert");
assert.equal(result.alerts.length, 1);
assert.equal(result.alerts[0].rule_id, "synthetic-water-low");
assert.equal(result.alerts[0].severity, "urgent");
assert.equal(result.alerts[0].authorization, "alert_only");
assert.equal(result.alerts[0].diagnosis, null);
assert.equal(result.alerts[0].human_authority_required, true);
assert.deepEqual(result.alerts[0].evidence_refs, [
  "synthetic:reading-001",
  "synthetic:tank-sensor-1"
]);

const clear = evaluateReflexes({ ...event, value: 50 }, rules);
assert.equal(clear.state, "clear");
assert.equal(clear.alerts.length, 0);

const recordOnly = evaluateReflexes({
  ...event,
  event_id: "synthetic-freeform-001",
  signal_key: undefined,
  summary: "Farmer noticed something unusual but has not structured the signal yet."
}, rules);
assert.equal(recordOnly.state, "record_only");
assert.equal(recordOnly.validation.valid, true);
assert.equal(recordOnly.validation.warnings.length, 1);

const modelInference = validateObservationEvent({
  ...event,
  event_id: "synthetic-inference-001",
  source: { kind: "model_inference" }
});
assert.equal(modelInference.valid, true);
assert.ok(modelInference.warnings.some(x => x.includes("not a direct observation")));

assert.throws(
  () => evaluateReflexes(event, [{ ...rules[0], comparator: "approximately" }]),
  /comparator is not recognized/
);

console.log("PASS: CropCircuit reflex loop v0.1");
