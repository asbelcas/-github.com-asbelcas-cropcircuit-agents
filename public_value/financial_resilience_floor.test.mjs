import assert from "node:assert/strict";
import {
  evaluateFinancialResilienceFloor,
  validateFinancialResilienceInput,
} from "./financial_resilience_floor.js";

const policy = {
  policy_id: "synthetic-farm-policy-v1",
  as_of: "2026-09-23T20:00:00Z",
  metrics: {
    unrestricted_cash_after_action: 12000,
    monthly_debt_service_after_action: 1800,
    runway_months_after_action: 4.5,
  },
  constraints: [
    {
      id: "minimum-cash-reserve",
      metric: "unrestricted_cash_after_action",
      comparator: "gte",
      threshold: 10000,
      required: true,
      source: "synthetic farm policy",
    },
    {
      id: "maximum-debt-service",
      metric: "monthly_debt_service_after_action",
      comparator: "lte",
      threshold: 2000,
      required: true,
      source: "synthetic farm policy",
    },
    {
      id: "minimum-runway",
      metric: "runway_months_after_action",
      comparator: "gte",
      threshold: 3,
      required: true,
      source: "synthetic farm policy",
    },
  ],
};

assert.equal(validateFinancialResilienceInput(policy).valid, true);

const pass = evaluateFinancialResilienceFloor(policy);
assert.equal(pass.gate, "pass_to_review");
assert.deepEqual(pass.failed_required_constraints, []);
assert.deepEqual(pass.unknown_required_constraints, []);

const reject = evaluateFinancialResilienceFloor({
  ...policy,
  metrics: {
    ...policy.metrics,
    unrestricted_cash_after_action: 7500,
  },
});
assert.equal(reject.gate, "reject");
assert.deepEqual(reject.failed_required_constraints, ["minimum-cash-reserve"]);

const hold = evaluateFinancialResilienceFloor({
  ...policy,
  metrics: {
    unrestricted_cash_after_action: 12000,
    monthly_debt_service_after_action: 1800,
  },
});
assert.equal(hold.gate, "hold");
assert.deepEqual(hold.unknown_required_constraints, ["minimum-runway"]);

const advisory = evaluateFinancialResilienceFloor({
  ...policy,
  constraints: [
    ...policy.constraints,
    {
      id: "preferred-extra-buffer",
      metric: "unrestricted_cash_after_action",
      comparator: "gte",
      threshold: 15000,
      required: false,
      source: "synthetic farm preference",
    },
  ],
});
assert.equal(advisory.gate, "pass_to_review");
assert.deepEqual(advisory.advisory_failures, ["preferred-extra-buffer"]);

const invalid = evaluateFinancialResilienceFloor({
  policy_id: "bad",
  as_of: "2026-09-23T20:00:00Z",
  metrics: {},
  constraints: [],
});
assert.equal(invalid.gate, "invalid");

console.log("PASS: CropCircuit financial resilience floor v0.1");
