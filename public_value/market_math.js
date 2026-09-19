/**
 * CropCircuit Market Day Math
 * Zero-dependency farm-market unit economics.
 * No mileage, wage, fee, or margin assumptions are embedded.
 */

function finite(name, value) {
  const n = Number(value);
  if (!Number.isFinite(n)) throw new TypeError(`${name} must be a finite number`);
  return n;
}
function nonnegative(name, value) { return Math.max(finite(name, value), 0); }
function round(value, places = 2) {
  const p = 10 ** places;
  return Math.round((value + Number.EPSILON) * p) / p;
}

export function marketDayEconomics({
  boothFee = 0,
  roundTripMiles = 0,
  vehicleCostPerMile = 0,
  travelHours = 0,
  setupHours = 0,
  sellingHours = 0,
  teardownHours = 0,
  workers = 1,
  hourlyLaborCost = 0,
  otherFixedCosts = 0,
  averageSale,
  variableCostPerSale = 0,
  cardFeePercent = 0,
  expectedTransactions = null,
}) {
  const booth = nonnegative("boothFee", boothFee);
  const miles = nonnegative("roundTripMiles", roundTripMiles);
  const vehicleRate = nonnegative("vehicleCostPerMile", vehicleCostPerMile);
  const hours =
    nonnegative("travelHours", travelHours) +
    nonnegative("setupHours", setupHours) +
    nonnegative("sellingHours", sellingHours) +
    nonnegative("teardownHours", teardownHours);
  const workerCount = nonnegative("workers", workers);
  const laborRate = nonnegative("hourlyLaborCost", hourlyLaborCost);
  const other = nonnegative("otherFixedCosts", otherFixedCosts);
  const sale = nonnegative("averageSale", averageSale);
  const variable = nonnegative("variableCostPerSale", variableCostPerSale);
  const cardRate = Math.min(nonnegative("cardFeePercent", cardFeePercent), 100) / 100;

  const vehicleCost = miles * vehicleRate;
  const laborCost = hours * workerCount * laborRate;
  const fixedDayCost = booth + vehicleCost + laborCost + other;
  const cardFeePerSale = sale * cardRate;
  const contributionPerSale = sale - variable - cardFeePerSale;

  const breakEvenTransactions = contributionPerSale > 0
    ? Math.ceil(fixedDayCost / contributionPerSale)
    : null;
  const breakEvenGrossRevenue = breakEvenTransactions === null
    ? null
    : breakEvenTransactions * sale;

  let forecast = null;
  if (expectedTransactions !== null && expectedTransactions !== undefined) {
    const tx = nonnegative("expectedTransactions", expectedTransactions);
    const grossRevenue = tx * sale;
    const transactionContribution = tx * contributionPerSale;
    forecast = {
      transactions: round(tx, 1),
      grossRevenue: round(grossRevenue),
      estimatedDayMargin: round(transactionContribution - fixedDayCost),
    };
  }

  return {
    totalWorkerHours: round(hours * workerCount, 1),
    vehicleCost: round(vehicleCost),
    laborCost: round(laborCost),
    fixedDayCost: round(fixedDayCost),
    cardFeePerSale: round(cardFeePerSale),
    contributionPerSale: round(contributionPerSale),
    breakEvenTransactions,
    breakEvenGrossRevenue:
      breakEvenGrossRevenue === null ? null : round(breakEvenGrossRevenue),
    forecast,
  };
}
