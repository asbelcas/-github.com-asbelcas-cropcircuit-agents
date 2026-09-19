import assert from "node:assert/strict";
import {
  median,
  summarizeSample,
  compareSamples,
  annualizeObservedChange,
} from "./workflow_experiment.js";

assert.equal(median([3,1,2]),2);
assert.equal(median([1,2,3,4]),2.5);

assert.deepEqual(
  summarizeSample([0.5, 0.75, 1]),
  { n: 3, medianWorkerHours: 0.75, meanWorkerHours: 0.75, totalWorkerHours: 2.25 }
);

const comparison = compareSamples({
  baseline:[0.5,0.6,0.55,0.7,0.5],
  after:[0.3,0.35,0.4,0.3,0.35]
});
assert.equal(comparison.direction,"less-labor");
assert.equal(comparison.baseline.medianWorkerHours,0.55);
assert.equal(comparison.after.medianWorkerHours,0.35);
assert.equal(comparison.medianChangeWorkerHours,-0.2);
assert.equal(comparison.medianChangePercent,-36.4);

assert.deepEqual(
  annualizeObservedChange({
    baselineMedianWorkerHours:0.55,
    afterMedianWorkerHours:0.35,
    occurrencesPerWeek:14,
    weeksPerYear:52,
    hourlyCost:20,
    interventionCost:750
  }),
  {
    hoursSavedPerOccurrence:0.2,
    annualHoursSaved:145.6,
    annualLaborValue:2912,
    paybackMonths:3.1
  }
);

console.log("PASS: CropCircuit workflow experiment math");
