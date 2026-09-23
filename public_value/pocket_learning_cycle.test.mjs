import assert from "node:assert/strict";
import {
  appendObservation,
  appendContradiction,
  appendConfidenceUpdate,
  summarizeLearningCycle,
  validateLearningCycle,
} from "./learning_loop.js";

const cycle = {
  schema_version: "0.1",
  cycle_id: "synthetic-pocket-cycle-001",
  created_at: "2026-09-23T20:00:00Z",
  question: "Will the flock use the northwest corner after one reversible correction?",
  prediction: {
    statement: "Use of the northwest corner will increase on the next comparable exposure.",
    confidence: 0.6,
    falsifiers: [
      "The flock continues avoiding the area under comparable conditions."
    ]
  },
  action: {
    description: "Inspect the area, make one reversible correction, and observe the next exposure.",
    reversible: true,
    cost_cap: null,
    owner: "farmer"
  },
  stop_rule: {
    description: "Stop after the next comparable exposure or earlier for welfare/safety.",
    status: "not_met",
    evidence: ""
  },
  provenance: [
    {
      kind: "human_observation",
      ref: "synthetic-observation-001",
      note: "Synthetic behavior observation."
    }
  ],
  observations: [],
  contradictions: [],
  updates: []
};

assert.equal(validateLearningCycle(cycle).valid, true);

let next = appendObservation(cycle, {
  recorded_at: "2026-09-24T13:00:00Z",
  result: "The flock still avoided the area.",
  evidence_refs: []
});

next = appendContradiction(next, {
  statement: "Recorded outcome contradicts the original prediction.",
  evidence_refs: [],
  note: "Avoidance persisted after the first reversible correction."
});

next = appendConfidenceUpdate(next, {
  recorded_at: "2026-09-24T13:02:00Z",
  confidence_after: 0.25,
  rationale: "The first suspected cause did not explain the behavior.",
  next_action: "Check footing, shade, fence voltage, and disturbance separately."
});

next.stop_rule.status = "met";
next.stop_rule.evidence = "Comparable exposure observed.";

const summary = summarizeLearningCycle(next);
assert.equal(summary.state, "stopped");
assert.equal(summary.observations, 1);
assert.equal(summary.unresolved_contradictions, 1);
assert.equal(summary.initial_confidence, 0.6);
assert.equal(summary.current_confidence, 0.25);
assert.equal(summary.prediction_preserved, true);
assert.equal(next.prediction.statement, cycle.prediction.statement);

const imported = structuredClone(cycle);
imported.cycle_id = "synthetic-import-cycle-001";
imported.provenance = [{
  kind: "import",
  ref: "synthetic:csv-row-42",
  note: "Synthetic imported record."
}];
assert.equal(validateLearningCycle(imported).valid, true);

console.log("PASS: CropCircuit Pocket Console learning-cycle compatibility");
