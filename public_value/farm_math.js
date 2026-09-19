/**
 * CropCircuit Farm Math
 * Dependency-free farm decision utilities.
 *
 * These functions expose the arithmetic, not prescriptions. Operators choose
 * their own biological, labor, cost, and safety assumptions.
 */

const ACRE_SQ_FT = 43560;

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

/**
 * Annual cost of a repeated task.
 */
export function annualTaskCost({
  minutes,
  occurrencesPerWeek,
  weeksPerYear = 52,
  workers = 1,
  hourlyCost,
}) {
  const m = nonnegative("minutes", minutes);
  const o = nonnegative("occurrencesPerWeek", occurrencesPerWeek);
  const y = Math.min(nonnegative("weeksPerYear", weeksPerYear), 52);
  const w = nonnegative("workers", workers);
  const h = nonnegative("hourlyCost", hourlyCost);

  const annualHours = (m / 60) * o * y * w;
  const annualLaborCost = annualHours * h;

  return {
    annualHours: round(annualHours, 1),
    annualLaborCost: round(annualLaborCost),
  };
}

/**
 * Simple payback for a change that saves money each year.
 */
export function simplePayback({
  upfrontCost,
  annualSavings,
  annualAddedCost = 0,
  salvageValue = 0,
}) {
  const upfront = nonnegative("upfrontCost", upfrontCost);
  const savings = nonnegative("annualSavings", annualSavings);
  const added = nonnegative("annualAddedCost", annualAddedCost);
  const salvage = nonnegative("salvageValue", salvageValue);

  const netAnnualSavings = savings - added;
  const netCapitalAtRisk = Math.max(upfront - salvage, 0);
  const paybackMonths = netAnnualSavings > 0
    ? (netCapitalAtRisk / netAnnualSavings) * 12
    : null;

  return {
    netAnnualSavings: round(netAnnualSavings),
    netCapitalAtRisk: round(netCapitalAtRisk),
    paybackMonths: paybackMonths === null ? null : round(paybackMonths, 1),
  };
}

/**
 * Approximate outer fence line from acreage.
 *
 * A square is the minimum-perimeter rectangle for a given area.
 * shapeFactor lets the caller increase that baseline for irregular parcels,
 * lanes, setbacks, or other geometry. Add internalFenceFeet separately.
 */
export function fenceEstimate({
  acres,
  installedCostPerFoot,
  shapeFactor = 1,
  internalFenceFeet = 0,
  gateCost = 0,
}) {
  const a = nonnegative("acres", acres);
  const cost = nonnegative("installedCostPerFoot", installedCostPerFoot);
  const shape = Math.max(nonnegative("shapeFactor", shapeFactor), 1);
  const internal = nonnegative("internalFenceFeet", internalFenceFeet);
  const gates = nonnegative("gateCost", gateCost);

  const squareSideFeet = Math.sqrt(a * ACRE_SQ_FT);
  const baselinePerimeterFeet = 4 * squareSideFeet;
  const outerFenceFeet = baselinePerimeterFeet * shape;
  const totalFenceFeet = outerFenceFeet + internal;
  const estimatedCost = (totalFenceFeet * cost) + gates;

  return {
    squareSideFeet: round(squareSideFeet, 1),
    baselinePerimeterFeet: round(baselinePerimeterFeet, 1),
    outerFenceFeet: round(outerFenceFeet, 1),
    totalFenceFeet: round(totalFenceFeet, 1),
    estimatedCost: round(estimatedCost),
  };
}

/**
 * Water storage sized from user-entered consumption and desired autonomy.
 * No species defaults are embedded; callers supply their own current values.
 */
export function waterStorage({
  animals,
  gallonsPerAnimalPerDay,
  autonomyDays,
  reservePercent = 20,
}) {
  const n = nonnegative("animals", animals);
  const g = nonnegative("gallonsPerAnimalPerDay", gallonsPerAnimalPerDay);
  const days = nonnegative("autonomyDays", autonomyDays);
  const reserve = Math.min(nonnegative("reservePercent", reservePercent), 500) / 100;

  const dailyDemandGallons = n * g;
  const baseStorageGallons = dailyDemandGallons * days;
  const recommendedStorageGallons = baseStorageGallons * (1 + reserve);

  return {
    dailyDemandGallons: round(dailyDemandGallons, 1),
    baseStorageGallons: round(baseStorageGallons, 1),
    recommendedStorageGallons: round(recommendedStorageGallons, 1),
  };
}

/**
 * Transaction break-even for a stand, market, CSA add-on, or other sales lane.
 */
export function breakEvenTransactions({
  fixedCosts,
  averageSale,
  variableCostPerTransaction = 0,
}) {
  const fixed = nonnegative("fixedCosts", fixedCosts);
  const sale = nonnegative("averageSale", averageSale);
  const variable = nonnegative("variableCostPerTransaction", variableCostPerTransaction);
  const contributionPerTransaction = sale - variable;

  if (contributionPerTransaction <= 0) {
    return {
      contributionPerTransaction: round(contributionPerTransaction),
      breakEvenTransactions: null,
      breakEvenGrossRevenue: null,
    };
  }

  const transactions = Math.ceil(fixed / contributionPerTransaction);

  return {
    contributionPerTransaction: round(contributionPerTransaction),
    breakEvenTransactions: transactions,
    breakEvenGrossRevenue: round(transactions * sale),
  };
}

/**
 * Convert rectangular dimensions to acreage.
 */
export function rectangleAcres({ lengthFeet, widthFeet }) {
  const length = nonnegative("lengthFeet", lengthFeet);
  const width = nonnegative("widthFeet", widthFeet);
  const squareFeet = length * width;

  return {
    squareFeet: round(squareFeet, 1),
    acres: round(squareFeet / ACRE_SQ_FT, 4),
  };
}
