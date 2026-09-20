/**
 * CropCircuit equipment maintenance math.
 * Service intervals are always supplied by the operator/manufacturer guidance.
 */

function finiteOrNull(value) {
  if (value === null || value === undefined) return null;
  if (typeof value === "string" && value.trim() === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function round(value, places = 1) {
  const p = 10 ** places;
  return Math.round((value + Number.EPSILON) * p) / p;
}

export function hourServiceStatus({
  currentHours,
  lastServiceHours,
  intervalHours,
}) {
  const current = finiteOrNull(currentHours);
  const last = finiteOrNull(lastServiceHours);
  const interval = finiteOrNull(intervalHours);

  if (
    current === null ||
    last === null ||
    interval === null ||
    current < 0 ||
    last < 0 ||
    interval <= 0
  ) {
    return {
      configured: false,
      nextDueHours: null,
      hoursRemaining: null,
      status: "not-configured",
    };
  }

  const next = last + interval;
  const remaining = next - current;

  return {
    configured: true,
    nextDueHours: round(next),
    hoursRemaining: round(remaining),
    status: remaining < 0 ? "overdue" : remaining === 0 ? "due" : "not-due",
  };
}

function parseDate(value) {
  const text = String(value ?? "");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) return null;
  const d = new Date(text + "T00:00:00Z");
  return Number.isFinite(d.getTime()) ? d : null;
}

function iso(d) {
  return d.toISOString().slice(0, 10);
}

export function dateServiceStatus({
  lastServiceDate,
  intervalDays,
  asOfDate,
}) {
  const last = parseDate(lastServiceDate);
  const asOf = parseDate(asOfDate);
  const interval = finiteOrNull(intervalDays);

  if (!last || !asOf || interval === null || interval <= 0) {
    return {
      configured: false,
      nextDueDate: null,
      daysRemaining: null,
      status: "not-configured",
    };
  }

  const due = new Date(last.getTime());
  due.setUTCDate(due.getUTCDate() + Math.floor(interval));

  const remaining = Math.round((due - asOf) / 86400000);

  return {
    configured: true,
    nextDueDate: iso(due),
    daysRemaining: remaining,
    status: remaining < 0 ? "overdue" : remaining === 0 ? "due" : "not-due",
  };
}

export function combinedServiceStatus(args) {
  const hours = hourServiceStatus(args);
  const date = dateServiceStatus(args);

  const statuses = [hours.status, date.status];
  const overall = statuses.includes("overdue")
    ? "overdue"
    : statuses.includes("due")
      ? "due"
      : statuses.every(x => x === "not-configured")
        ? "not-configured"
        : "not-due";

  return { overall, hours, date };
}
