/**
 * CropCircuit Workflow Experiment Math
 * Descriptive before/after labor comparisons for repeated farm tasks.
 * No statistical significance claims are made.
 */

function finite(name, value) {
  const n = Number(value);
  if (!Number.isFinite(n)) throw new TypeError(`${name} must be a finite number`);
  return n;
}

function nonnegative(name, value) {
  return Math.max(finite(name, value), 0);
}

function round(value, places = 2) {
  const p = 10 ** places;
  return Math.round((value + Number.EPSILON) * p) / p;
}

export function median(values) {
  const nums = values.map(Number).filter(Number.isFinite).sort((a,b)=>a-b);
  if (!nums.length) return null;
  const mid = Math.floor(nums.length / 2);
  return nums.length % 2 ? nums[mid] : (nums[mid - 1] + nums[mid]) / 2;
}

export function summarizeSample(workerHoursPerOccurrence) {
  const values = workerHoursPerOccurrence
    .map(Number)
    .filter(Number.isFinite)
    .map(x => Math.max(x, 0));

  if (!values.length) {
    return { n: 0, medianWorkerHours: null, meanWorkerHours: null, totalWorkerHours: 0 };
  }

  const total = values.reduce((a,b)=>a+b,0);
  return {
    n: values.length,
    medianWorkerHours: round(median(values), 4),
    meanWorkerHours: round(total / values.length, 4),
    totalWorkerHours: round(total, 2),
  };
}

export function compareSamples({ baseline, after }) {
  const b = summarizeSample(baseline);
  const a = summarizeSample(after);

  if (!b.n || !a.n) {
    return {
      baseline: b,
      after: a,
      medianChangeWorkerHours: null,
      medianChangePercent: null,
      direction: "insufficient-data",
    };
  }

  const change = a.medianWorkerHours - b.medianWorkerHours;
  const percent = b.medianWorkerHours > 0 ? (change / b.medianWorkerHours) * 100 : null;

  return {
    baseline: b,
    after: a,
    medianChangeWorkerHours: round(change, 4),
    medianChangePercent: percent === null ? null : round(percent, 1),
    direction: change < 0 ? "less-labor" : change > 0 ? "more-labor" : "no-change",
  };
}

export function annualizeObservedChange({
  baselineMedianWorkerHours,
  afterMedianWorkerHours,
  occurrencesPerWeek,
  weeksPerYear = 52,
  hourlyCost,
  interventionCost = 0,
}) {
  const baseline = nonnegative("baselineMedianWorkerHours", baselineMedianWorkerHours);
  const after = nonnegative("afterMedianWorkerHours", afterMedianWorkerHours);
  const frequency = nonnegative("occurrencesPerWeek", occurrencesPerWeek);
  const weeks = Math.min(nonnegative("weeksPerYear", weeksPerYear), 52);
  const hourly = nonnegative("hourlyCost", hourlyCost);
  const cost = nonnegative("interventionCost", interventionCost);

  const hoursSavedPerOccurrence = baseline - after;
  const annualHoursSaved = hoursSavedPerOccurrence * frequency * weeks;
  const annualLaborValue = annualHoursSaved * hourly;
  const paybackMonths = annualLaborValue > 0 && cost > 0
    ? (cost / annualLaborValue) * 12
    : null;

  return {
    hoursSavedPerOccurrence: round(hoursSavedPerOccurrence, 4),
    annualHoursSaved: round(annualHoursSaved, 1),
    annualLaborValue: round(annualLaborValue),
    paybackMonths: paybackMonths === null ? null : round(paybackMonths, 1),
  };
}
