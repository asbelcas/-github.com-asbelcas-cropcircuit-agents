import assert from "node:assert/strict";
import {
  detectSignalConvergence,
  summarizeConvergence,
} from "./signal_convergence.js";

const signals = [
  {
    id: "sensor-1",
    domain: "soil_sensor",
    hypothesis_key: "northwest-paddock-anomaly",
    confidence: 0.55,
    recorded_at: "2026-09-23T12:00:00Z",
    evidence_ref: "synthetic:sensor-1",
  },
  {
    id: "farmer-1",
    domain: "human_observation",
    hypothesis_key: "northwest-paddock-anomaly",
    confidence: 0.8,
    recorded_at: "2026-09-23T12:10:00Z",
    evidence_ref: "synthetic:farmer-1",
  },
  {
    id: "labor-1",
    domain: "labor",
    hypothesis_key: "northwest-paddock-anomaly",
    confidence: 0.45,
    recorded_at: "2026-09-23T13:00:00Z",
    evidence_ref: "synthetic:labor-1",
  },
  {
    id: "finance-1",
    domain: "finance",
    hypothesis_key: "unrelated-input-cost-rise",
    confidence: 0.9,
    recorded_at: "2026-09-23T13:05:00Z",
    evidence_ref: "synthetic:finance-1",
  },
];

const tokens = detectSignalConvergence(signals);
assert.equal(tokens.length, 1);
assert.equal(tokens[0].hypothesis_key, "northwest-paddock-anomaly");
assert.equal(tokens[0].distinct_domains, 3);
assert.deepEqual(tokens[0].domains, ["human_observation", "labor", "soil_sensor"]);
assert.equal(tokens[0].authorization, "none");
assert.equal(tokens[0].status, "investigate");
assert.equal(tokens[0].confidence_summary.mean, 0.6);

const stricter = detectSignalConvergence(signals, { min_domains: 4 });
assert.equal(stricter.length, 0);

const low = detectSignalConvergence([
  {
    id: "low-1",
    domain: "sensor",
    hypothesis_key: "x",
    confidence: 0.1,
    recorded_at: "2026-09-23T14:00:00Z",
  },
  {
    id: "low-2",
    domain: "human",
    hypothesis_key: "x",
    confidence: 0.2,
    recorded_at: "2026-09-23T14:01:00Z",
  },
  {
    id: "strong-1",
    domain: "finance",
    hypothesis_key: "x",
    confidence: 0.9,
    recorded_at: "2026-09-23T14:02:00Z",
  },
]);
assert.equal(low.length, 0);

assert.deepEqual(summarizeConvergence(tokens), {
  tokens: 1,
  hypotheses: ["northwest-paddock-anomaly"],
  requires_human_review: true,
});

assert.throws(
  () => detectSignalConvergence([{ id: "bad" }]),
  /domain is required/
);

console.log("PASS: CropCircuit signal convergence v0.1");
