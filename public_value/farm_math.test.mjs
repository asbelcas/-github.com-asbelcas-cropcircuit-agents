import assert from "node:assert/strict";
import {
  annualTaskCost,
  simplePayback,
  fenceEstimate,
  waterStorage,
  breakEvenTransactions,
  rectangleAcres,
} from "./farm_math.js";

assert.deepEqual(
  annualTaskCost({
    minutes: 15,
    occurrencesPerWeek: 14,
    workers: 1,
    hourlyCost: 20,
    weeksPerYear: 52,
  }),
  { annualHours: 182, annualLaborCost: 3640 }
);

assert.deepEqual(
  simplePayback({ upfrontCost: 750, annualSavings: 2184 }),
  { netAnnualSavings: 2184, netCapitalAtRisk: 750, paybackMonths: 4.1 }
);

assert.equal(
  fenceEstimate({ acres: 1, installedCostPerFoot: 2 }).baselinePerimeterFeet,
  834.6
);

assert.deepEqual(
  waterStorage({
    animals: 10,
    gallonsPerAnimalPerDay: 4,
    autonomyDays: 3,
    reservePercent: 25,
  }),
  { dailyDemandGallons: 40, baseStorageGallons: 120, recommendedStorageGallons: 150 }
);

assert.deepEqual(
  breakEvenTransactions({
    fixedCosts: 500,
    averageSale: 30,
    variableCostPerTransaction: 10,
  }),
  { contributionPerTransaction: 20, breakEvenTransactions: 25, breakEvenGrossRevenue: 750 }
);

assert.deepEqual(
  rectangleAcres({ lengthFeet: 435.6, widthFeet: 100 }),
  { squareFeet: 43560, acres: 1 }
);

console.log("PASS: CropCircuit Farm Math");
