import assert from "node:assert/strict";
import {
  appendObservation,
  appendContradiction,
  appendConfidenceUpdate,
  shouldContinueLearning,
  summarizeLearningCycle,
  validateLearningCycle,
} from "./learning_loop.js";

const base = {
  schema_version: "0.1",
  cycle_id: "synthetic-fetch-queue-001",
  created_at: "2026-09-21T14:30:00Z",
  question: "Will a shared digital fetch queue reduce handoff ambiguity in a milking workflow?",
  prediction: {
    statement: "A shared queue will reduce ambiguous handoffs compared with a handwritten list.",
    confidence: 0.65,
    falsifiers: [
      "The queue creates equal or more ambiguous handoffs during the pilot.",
      "Workers cannot reliably access or update the queue during normal work."
    ]
  },
  action: {
    description: "Run a reversible one-shift synthetic pilot with a shared queue.",
    reversible: true,
    cost_cap: 0,
    owner: "operator"
  },
  stop_rule: {
    description: "Stop after one pilot shift or immediately if the workflow adds safety risk.",
    status: "not_met",
    evidence: ""
  },
  provenance: [
    {
      kind: "assumption",
      note: "This is a synthetic example, not evidence from a real farm."
    }
  ],
  observations: [],
  contradictions: [],
  updates: []
};

assert.deepEqual(validateLearningCycle(base), {
  valid: true,
  errors: [],
  warnings: []
});

const originalPrediction = structuredClone(base.prediction);
const observed = appendObservation(base, {
  recorded_at: "2026-09-21T16:00:00Z",
  result: "Pilot exposed one new handoff ambiguity not represented in the initial model.",
  evidence_refs: ["synthetic:shift-note-1"],
  surprise: {
    score: 0.6,
    reason: "The failure mode was not included in the original falsifiers."
  }
});

assert.deepEqual(base.prediction, originalPrediction);
assert.equal(base.observations.length, 0);
assert.deepEqual(observed.prediction, originalPrediction);
assert.equal(summarizeLearningCycle(observed).state, "observed");
assert.equal(summarizeLearningCycle(observed).latest_surprise.score, 0.6);

const contradicted = appendContradiction(observed, {
  statement: "Shared state did not guarantee shared interpretation.",
  evidence_refs: ["synthetic:shift-note-1"]
});
assert.equal(summarizeLearningCycle(contradicted).state, "contradicted");
assert.equal(shouldContinueLearning(contradicted).reason, "resolve_or_test_contradiction");

const updated = appendConfidenceUpdate(contradicted, {
  recorded_at: "2026-09-21T16:05:00Z",
  confidence_after: 0.4,
  rationale: "The pilot revealed a missing coordination mechanism.",
  model_change: "Separate visibility from acknowledgment of responsibility.",
  next_action: "Test explicit claim/acknowledge state in the next reversible pilot."
});
const summary = summarizeLearningCycle(updated);
assert.equal(summary.initial_confidence, 0.65);
assert.equal(summary.current_confidence, 0.4);
assert.equal(summary.confidence_delta, -0.25);

const stopped = structuredClone(updated);
stopped.stop_rule.status = "met";
stopped.stop_rule.evidence = "Synthetic pilot shift complete.";
assert.equal(shouldContinueLearning(stopped).continue, false);
assert.equal(shouldContinueLearning(stopped).reason, "stop_rule_met");

const invalid = structuredClone(base);
invalid.prediction.falsifiers = [];
assert.equal(validateLearningCycle(invalid).valid, false);

console.log("PASS: CropCircuit learning loop v0.1");
