import assert from "node:assert/strict";
import {
  evaluateModelTension,
  recordHumanArbitration,
  validateModelTension,
} from "./model_tension.js";

const base = {
  tension_id: "synthetic-paddock-004",
  created_at: "2026-09-23T21:00:00Z",
  decision: "Move the flock to paddock 4 tomorrow?",
  context: "Synthetic example for model-arbitration mechanics.",
  authority: "farm_manager",
  positions: [
    {
      model: "pasture",
      recommendation: "proceed",
      confidence: 0.75,
      reason: "Forage recovery target is met.",
      evidence_refs: ["synthetic:pasture-1"],
      hard_constraints: [{ id: "forage-floor", status: "pass" }],
      time_sensitivity: "today",
      reversibility: "medium",
    },
    {
      model: "animal_welfare",
      recommendation: "investigate",
      confidence: 0.55,
      reason: "Recent avoidance behavior is unresolved.",
      evidence_refs: ["synthetic:behavior-1"],
      hard_constraints: [{ id: "welfare-anomaly-resolved", status: "pass" }],
      time_sensitivity: "today",
      reversibility: "medium",
    },
    {
      model: "labor",
      recommendation: "hold",
      confidence: 0.6,
      reason: "Move timing overlaps with another high-labor chore.",
      evidence_refs: ["synthetic:labor-1"],
      hard_constraints: [],
      time_sensitivity: "today",
      reversibility: "high",
    },
  ],
};

assert.equal(validateModelTension(base).valid, true);

const tension = evaluateModelTension(base);
assert.equal(tension.state, "human_arbitration");
assert.deepEqual(
  tension.record.recommendations_present,
  ["hold", "investigate", "proceed"]
);
assert.equal(tension.record.selected_option, null);

const decided = recordHumanArbitration(tension, {
  selected_option: "Inspect paddock 4 first, then decide whether to move.",
  rationale: "The welfare uncertainty is cheap to investigate before the move.",
  decided_at: "2026-09-23T21:10:00Z",
  decided_by: "farm_manager",
});
assert.equal(
  decided.record.selected_option,
  "Inspect paddock 4 first, then decide whether to move."
);

const blocked = evaluateModelTension({
  ...base,
  tension_id: "synthetic-blocked",
  positions: [
    ...base.positions.slice(0, 2),
    {
      ...base.positions[2],
      model: "finance",
      recommendation: "avoid",
      hard_constraints: [{ id: "cash-floor", status: "fail" }],
    },
  ],
});
assert.equal(blocked.state, "blocked");
assert.equal(blocked.record.failed_hard_constraints.length, 1);

const unknown = evaluateModelTension({
  ...base,
  tension_id: "synthetic-unknown",
  positions: [
    ...base.positions.slice(0, 2),
    {
      ...base.positions[2],
      model: "infrastructure",
      recommendation: "investigate",
      hard_constraints: [{ id: "fence-integrity", status: "unknown" }],
    },
  ],
});
assert.equal(unknown.state, "hold_for_unknown");

const aligned = evaluateModelTension({
  ...base,
  tension_id: "synthetic-aligned",
  positions: base.positions.map((x, i) => ({
    ...x,
    model: ["pasture", "animal_welfare", "labor"][i],
    recommendation: "proceed",
    hard_constraints: [],
  })),
});
assert.equal(aligned.state, "aligned");

console.log("PASS: CropCircuit model tension v0.1");
