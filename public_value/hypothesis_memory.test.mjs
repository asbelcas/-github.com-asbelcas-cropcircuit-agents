import assert from "node:assert/strict";
import {
  createHypothesisMemoryEntry,
  graveyard,
  searchHypothesisMemory,
  updateHypothesisDisposition,
} from "./hypothesis_memory.js";

const cycle = {
  schema_version: "0.1",
  cycle_id: "synthetic-hypothesis-001",
  created_at: "2026-09-23T20:00:00Z",
  question: "Does fence voltage explain northwest-corner avoidance?",
  prediction: {
    statement: "Correcting low fence voltage will reduce avoidance on the next comparable exposure.",
    confidence: 0.65,
    falsifiers: ["Avoidance continues after voltage is corrected."],
  },
  action: {
    description: "Correct voltage and observe one comparable exposure.",
    reversible: true,
  },
  stop_rule: {
    description: "Stop after one comparable exposure.",
    status: "met",
    evidence: "Synthetic exposure completed.",
  },
  provenance: [
    { kind: "human_observation", ref: "synthetic:obs-1", note: "Synthetic observation." },
  ],
  observations: [
    {
      recorded_at: "2026-09-24T12:00:00Z",
      result: "Avoidance continued after voltage was corrected.",
      evidence_refs: ["synthetic:obs-2"],
    },
  ],
  contradictions: [
    {
      statement: "The recorded outcome contradicted the prediction.",
      status: "unresolved",
      evidence_refs: ["synthetic:obs-2"],
      note: "Avoidance persisted.",
    },
  ],
  updates: [
    {
      recorded_at: "2026-09-24T12:05:00Z",
      confidence_before: 0.65,
      confidence_after: 0.2,
      rationale: "Fence voltage alone did not explain the behavior.",
      model_change: "Separate fence voltage from footing and disturbance hypotheses.",
      next_action: "Inspect footing under similar weather.",
    },
  ],
};

const entry = createHypothesisMemoryEntry(cycle, {
  disposition: "inconclusive",
  conditions: ["dry weather", "same flock", "daylight"],
  tags: ["paddock-4", "animal-behavior"],
  reason: "The first mechanism lost support, but the broader anomaly remains unexplained.",
  updated_at: "2026-09-24T12:06:00Z",
});

assert.equal(entry.original_prediction, cycle.prediction.statement);
assert.equal(entry.initial_confidence, 0.65);
assert.equal(entry.current_confidence, 0.2);
assert.equal(entry.outcomes.length, 1);
assert.equal(entry.contradictions.length, 1);

const rejected = updateHypothesisDisposition(entry, {
  disposition: "rejected",
  reason: "Repeated comparable tests did not support this mechanism.",
  updated_at: "2026-09-25T12:00:00Z",
});
assert.equal(rejected.disposition, "rejected");
assert.equal(entry.disposition, "inconclusive");

assert.equal(searchHypothesisMemory([entry], "footing").length, 1);
assert.equal(searchHypothesisMemory([entry], "voltage").length, 1);
assert.equal(
  searchHypothesisMemory([entry], "", { tags: ["paddock-4"] }).length,
  1
);
assert.equal(
  searchHypothesisMemory([entry], "", { dispositions: ["rejected"] }).length,
  0
);
assert.equal(graveyard([entry, rejected]).length, 2);

console.log("PASS: CropCircuit hypothesis memory v0.1");
