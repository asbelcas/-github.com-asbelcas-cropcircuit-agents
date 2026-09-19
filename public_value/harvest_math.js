/**
 * CropCircuit harvest summary math.
 * Quantities are never converted across units automatically.
 */

function inRange(date, startDate, endDate) {
  const d = String(date ?? "");
  return d >= startDate && d <= endDate;
}

function round(value, places = 3) {
  const p = 10 ** places;
  return Math.round((value + Number.EPSILON) * p) / p;
}

export function summarizeHarvest(records, { startDate, endDate } = {}) {
  const groups = new Map();

  for (const record of records ?? []) {
    if (startDate && endDate && !inRange(record.date, startDate, endDate)) continue;

    const item = String(record.item ?? record.crop ?? "").trim();
    const unit = String(record.unit ?? "").trim();
    const quantity = Number(record.quantity);

    if (!item || !unit || !Number.isFinite(quantity) || quantity < 0) continue;

    const key = `${item.toLowerCase()}\u0000${unit.toLowerCase()}`;
    const bucket = groups.get(key) ?? {
      item,
      unit,
      entries: 0,
      quantity: 0,
    };
    bucket.entries += 1;
    bucket.quantity += quantity;
    groups.set(key, bucket);
  }

  return [...groups.values()]
    .map(x => ({ ...x, quantity: round(x.quantity) }))
    .sort((a,b) => a.item.localeCompare(b.item) || a.unit.localeCompare(b.unit));
}

export function compareHarvest(records, {
  periodA,
  periodB,
} = {}) {
  const a = summarizeHarvest(records, periodA);
  const b = summarizeHarvest(records, periodB);
  const map = new Map();

  for (const row of a) {
    const key = `${row.item.toLowerCase()}\u0000${row.unit.toLowerCase()}`;
    map.set(key, {
      item: row.item,
      unit: row.unit,
      quantityA: row.quantity,
      quantityB: 0,
    });
  }

  for (const row of b) {
    const key = `${row.item.toLowerCase()}\u0000${row.unit.toLowerCase()}`;
    const existing = map.get(key) ?? {
      item: row.item,
      unit: row.unit,
      quantityA: 0,
      quantityB: 0,
    };
    existing.quantityB = row.quantity;
    map.set(key, existing);
  }

  return [...map.values()]
    .map(row => {
      const change = row.quantityB - row.quantityA;
      const changePercent = row.quantityA > 0
        ? (change / row.quantityA) * 100
        : null;
      return {
        ...row,
        change: round(change),
        changePercent:
          changePercent === null ? null : round(changePercent, 1),
      };
    })
    .sort((x,y) => Math.abs(y.change) - Math.abs(x.change));
}
