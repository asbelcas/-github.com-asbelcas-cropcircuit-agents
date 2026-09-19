/**
 * CropCircuit direct-market sales summary math.
 * Operational sales records only; not accounting/tax treatment.
 */

function round(value, places = 2) {
  const p = 10 ** places;
  return Math.round((value + Number.EPSILON) * p) / p;
}

function amount(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.max(n, 0) : 0;
}

export function salesRecordEconomics(record) {
  const gross = amount(record?.gross_amount);
  const fees = amount(record?.payment_fees);
  const refunds = amount(record?.refunds_discounts);
  const direct = amount(record?.direct_costs);

  const netReceipts = gross - fees - refunds;
  const contributionAfterDirectCosts = netReceipts - direct;

  return {
    grossAmount: round(gross),
    paymentFees: round(fees),
    refundsDiscounts: round(refunds),
    directCosts: round(direct),
    netReceipts: round(netReceipts),
    contributionAfterDirectCosts: round(contributionAfterDirectCosts),
  };
}

export function summarizeSales(records, {
  startDate = null,
  endDate = null,
  groupBy = "channel",
} = {}) {
  const groups = new Map();

  for (const record of records ?? []) {
    const date = String(record?.date ?? "");
    if (startDate && date < startDate) continue;
    if (endDate && date > endDate) continue;

    const label = String(record?.[groupBy] ?? "Unspecified").trim() || "Unspecified";
    const econ = salesRecordEconomics(record);

    const bucket = groups.get(label) ?? {
      group: label,
      transactions: 0,
      grossAmount: 0,
      paymentFees: 0,
      refundsDiscounts: 0,
      directCosts: 0,
      netReceipts: 0,
      contributionAfterDirectCosts: 0,
    };

    bucket.transactions += 1;
    for (const key of [
      "grossAmount",
      "paymentFees",
      "refundsDiscounts",
      "directCosts",
      "netReceipts",
      "contributionAfterDirectCosts",
    ]) {
      bucket[key] += econ[key];
    }

    groups.set(label, bucket);
  }

  return [...groups.values()]
    .map(row => Object.fromEntries(
      Object.entries(row).map(([k,v]) => [
        k,
        typeof v === "number" && k !== "transactions" ? round(v) : v,
      ])
    ))
    .sort((a,b) => b.netReceipts - a.netReceipts);
}
