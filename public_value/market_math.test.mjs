import assert from "node:assert/strict";
import { marketDayEconomics } from "./market_math.js";

const r = marketDayEconomics({
  boothFee: 40,
  roundTripMiles: 50,
  vehicleCostPerMile: 0.5,
  travelHours: 1.5,
  setupHours: 1,
  sellingHours: 4,
  teardownHours: 0.5,
  workers: 1,
  hourlyLaborCost: 20,
  otherFixedCosts: 15,
  averageSale: 25,
  variableCostPerSale: 8,
  cardFeePercent: 3,
  expectedTransactions: 20,
});

assert.equal(r.totalWorkerHours, 7);
assert.equal(r.vehicleCost, 25);
assert.equal(r.laborCost, 140);
assert.equal(r.fixedDayCost, 220);
assert.equal(r.cardFeePerSale, 0.75);
assert.equal(r.contributionPerSale, 16.25);
assert.equal(r.breakEvenTransactions, 14);
assert.equal(r.breakEvenGrossRevenue, 350);
assert.deepEqual(r.forecast, {
  transactions: 20,
  grossRevenue: 500,
  estimatedDayMargin: 105,
});

const impossible = marketDayEconomics({
  averageSale: 10,
  variableCostPerSale: 11,
});
assert.equal(impossible.breakEvenTransactions, null);

console.log("PASS: CropCircuit market day math");
