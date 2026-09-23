import assert from "node:assert/strict";
import {
  comparePredictorSeries,
  summarizePredictorSeries,
  validatePilotDecisionRecord,
} from "./pilot_learning_rate.js";

function rec(i, farmerRelation, cropRelation, farmerConfidence, cropConfidence) {
  return {
    schema_version: "0.1",
    record_id: "synthetic-" + i,
    pilot_id: "synthetic-repeat-pilot",
    decision_class: "synthetic-animal-move",
    created_at: `2026-09-${String(10 + i).padStart(2, "0")}T12:00:00Z`,
    context_tags: ["synthetic"],
    governance: {
      gate: "pass",
      hard_constraints: [],
      note: "Synthetic test record."
    },
    predictors: [
      {
        predictor_id: "farmer",
        prediction: "Synthetic farmer prediction " + i,
        confidence: farmerConfidence,
        reason: "Synthetic."
      },
      {
        predictor_id: "cropcircuit",
        prediction: "Synthetic CropCircuit prediction " + i,
        confidence: cropConfidence,
        reason: "Synthetic."
      }
    ],
    outcome: {
      recorded_at: `2026-09-${String(10 + i).padStart(2, "0")}T18:00:00Z`,
      description: "Synthetic outcome " + i,
      evidence_refs: []
    },
    evaluations: [
      {
        predictor_id: "farmer",
        relation: farmerRelation,
        note: "Synthetic evaluation."
      },
      {
        predictor_id: "cropcircuit",
        relation: cropRelation,
        note: "Synthetic evaluation."
      }
    ],
    metrics: {}
  };
}

const records = [
  rec(1, "contradicted", "contradicted", 0.8, 0.8),
  rec(2, "mixed", "contradicted", 0.6, 0.8),
  rec(3, "supported", "mixed", 0.7, 0.6),
  rec(4, "supported", "supported", 0.65, 0.65),
  rec(5, "mixed", "supported", 0.6, 0.7),
  rec(6, "supported", "supported", 0.7, 0.75),
  rec(7, "supported", "supported", 0.75, 0.8),
  rec(8, "supported", "supported", 0.8, 0.8),
];

assert.equal(validatePilotDecisionRecord(records[0]).valid, true);

const crop = summarizePredictorSeries(records, "cropcircuit");
assert.equal(crop.overall.evaluated, 8);
assert.equal(crop.learning_signal_available, true);
assert.ok(crop.late_window.contradiction_rate < crop.early_window.contradiction_rate);
assert.ok(crop.contradiction_rate_delta < 0);

const comparison = comparePredictorSeries(records);
assert.equal(comparison.predictors.length, 2);
assert.equal(comparison.record_count, 8);
assert.match(comparison.note, /No winner is selected/);

const tooSmall = summarizePredictorSeries(records.slice(0, 4), "farmer");
assert.equal(tooSmall.learning_signal_available, false);
assert.equal(tooSmall.early_window, null);

const bad = structuredClone(records[0]);
bad.predictors[1].predictor_id = "farmer";
assert.equal(validatePilotDecisionRecord(bad).valid, false);

console.log("PASS: CropCircuit repeated-decision pilot v0.1");
