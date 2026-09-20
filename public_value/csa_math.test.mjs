import assert from "node:assert/strict";
import { csaEconomics } from "./csa_math.js";

const r = csaEconomics({
  plannedShares: 40,
  pricePerShare: 600,
  fixedSeasonCosts: 4000,
  seasonLaborHours: 500,
  hourlyLaborCost: 20,
  variableCostPerShare: 180,
  paymentFeePercent: 3,
  targetSeasonSurplus: 3000,
});

assert.equal(r.laborCost,10000);
assert.equal(r.seasonFixedCost,14000);
assert.equal(r.contributionPerShare,402);
assert.equal(r.breakEvenShares,35);
assert.equal(r.targetShares,43);
assert.equal(r.grossRevenue,24000);
assert.equal(r.paymentFees,720);
assert.equal(r.variableCosts,7200);
assert.equal(r.modeledSeasonSurplus,2080);
assert.equal(r.requiredPricePerShare,623.71);

const impossible=csaEconomics({
  plannedShares:10,
  pricePerShare:100,
  variableCostPerShare:100,
  paymentFeePercent:5
});
assert.equal(impossible.breakEvenShares,null);

assert.throws(
  () => csaEconomics({ plannedShares:"", pricePerShare:600 }),
  TypeError
);

assert.throws(
  () => csaEconomics({ plannedShares:40, pricePerShare:-1 }),
  RangeError
);

console.log("PASS: CropCircuit CSA economics");
