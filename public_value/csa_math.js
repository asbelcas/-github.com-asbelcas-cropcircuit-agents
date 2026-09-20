/**
 * CropCircuit CSA / subscription-share economics.
 * Zero-dependency planning math with user-supplied costs and targets.
 */

function finite(name, value) {
  if (value === null || value === undefined) throw new TypeError(`${name} must be a finite number`);
  if (typeof value === "string" && value.trim() === "") throw new TypeError(`${name} must be a finite number`);
  const n = Number(value);
  if (!Number.isFinite(n)) throw new TypeError(`${name} must be a finite number`);
  return n;
}
function nonnegative(name, value) {
  const n = finite(name, value);
  if (n < 0) throw new RangeError(`${name} must be non-negative`);
  return n;
}
function round(value, places = 2) {
  const p = 10 ** places;
  return Math.round((value + Number.EPSILON) * p) / p;
}

export function csaEconomics({
  plannedShares,
  pricePerShare,
  fixedSeasonCosts = 0,
  seasonLaborHours = 0,
  hourlyLaborCost = 0,
  variableCostPerShare = 0,
  paymentFeePercent = 0,
  targetSeasonSurplus = 0,
}) {
  const shares = nonnegative("plannedShares", plannedShares);
  const price = nonnegative("pricePerShare", pricePerShare);
  const fixed = nonnegative("fixedSeasonCosts", fixedSeasonCosts);
  const laborHours = nonnegative("seasonLaborHours", seasonLaborHours);
  const hourly = nonnegative("hourlyLaborCost", hourlyLaborCost);
  const variable = nonnegative("variableCostPerShare", variableCostPerShare);
  const feeRate = Math.min(nonnegative("paymentFeePercent", paymentFeePercent), 100) / 100;
  const surplusTarget = nonnegative("targetSeasonSurplus", targetSeasonSurplus);

  const laborCost = laborHours * hourly;
  const seasonFixedCost = fixed + laborCost;
  const contributionPerShare = price * (1 - feeRate) - variable;

  const breakEvenShares = contributionPerShare > 0
    ? Math.ceil(seasonFixedCost / contributionPerShare)
    : null;

  const targetShares = contributionPerShare > 0
    ? Math.ceil((seasonFixedCost + surplusTarget) / contributionPerShare)
    : null;

  const grossRevenue = shares * price;
  const paymentFees = grossRevenue * feeRate;
  const variableCosts = shares * variable;
  const modeledSeasonSurplus =
    grossRevenue - paymentFees - variableCosts - seasonFixedCost;

  const denom = shares * (1 - feeRate);
  const requiredPricePerShare = denom > 0
    ? (seasonFixedCost + surplusTarget + shares * variable) / denom
    : null;

  return {
    laborCost: round(laborCost),
    seasonFixedCost: round(seasonFixedCost),
    contributionPerShare: round(contributionPerShare),
    breakEvenShares,
    targetShares,
    grossRevenue: round(grossRevenue),
    paymentFees: round(paymentFees),
    variableCosts: round(variableCosts),
    modeledSeasonSurplus: round(modeledSeasonSurplus),
    requiredPricePerShare:
      requiredPricePerShare === null ? null : round(requiredPricePerShare),
  };
}
