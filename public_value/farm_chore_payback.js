/**
 * CropCircuit Farm Chore Cost & Payback Calculator
 * Pure JavaScript utility. No dependencies.
 *
 * Inputs:
 * - minutes: minutes per occurrence
 * - occurrences: occurrences per week
 * - workers: workers involved each occurrence
 * - hourlyCost: fully loaded labor cost per hour
 * - weeks: weeks per year the chore occurs
 * - fixCost: one-time cost of the proposed improvement
 * - reductionPercent: expected percentage reduction in chore time
 */
export function calculateChorePayback({
  minutes,
  occurrences,
  workers = 1,
  hourlyCost,
  weeks = 52,
  fixCost = 0,
  reductionPercent = 0,
}) {
  const values = { minutes, occurrences, workers, hourlyCost, weeks, fixCost, reductionPercent };

  for (const [key, value] of Object.entries(values)) {
    if (!Number.isFinite(Number(value))) {
      throw new TypeError(`${key} must be a finite number`);
    }
  }

  const m = Math.max(Number(minutes), 0);
  const o = Math.max(Number(occurrences), 0);
  const w = Math.max(Number(workers), 0);
  const h = Math.max(Number(hourlyCost), 0);
  const y = Math.min(Math.max(Number(weeks), 0), 52);
  const f = Math.max(Number(fixCost), 0);
  const r = Math.min(Math.max(Number(reductionPercent), 0), 100) / 100;

  const annualHours = (m / 60) * o * y * w;
  const annualLaborCost = annualHours * h;
  const annualSavings = annualLaborCost * r;
  const paybackMonths = annualSavings > 0 && f > 0 ? (f / annualSavings) * 12 : null;
  const threeYearNetSavings = annualSavings * 3 - f;

  const round = (n, places = 2) => {
    const p = 10 ** places;
    return Math.round((n + Number.EPSILON) * p) / p;
  };

  return {
    annualHours: round(annualHours, 1),
    annualLaborCost: round(annualLaborCost),
    annualSavings: round(annualSavings),
    paybackMonths: paybackMonths === null ? null : round(paybackMonths, 1),
    threeYearNetSavings: round(threeYearNetSavings),
  };
}
