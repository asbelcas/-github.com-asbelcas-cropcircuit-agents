/**
 * CropCircuit recurring farm schedule math.
 * Implements the recurrence forms produced by the Offline Farm Chore Scheduler.
 * Monthly/yearly recurrences skip invalid calendar dates rather than silently
 * moving them to another day.
 */

function assertIsoDate(value, name) {
  const text = String(value ?? "");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) {
    throw new TypeError(`${name} must be YYYY-MM-DD`);
  }
  const d = new Date(text + "T00:00:00Z");
  if (!Number.isFinite(d.getTime())) throw new TypeError(`${name} is invalid`);
  return d;
}

function iso(d) {
  return d.toISOString().slice(0, 10);
}

function addUtcDays(d, days) {
  const out = new Date(d.getTime());
  out.setUTCDate(out.getUTCDate() + days);
  return out;
}

function daysInMonth(year, monthZeroBased) {
  return new Date(Date.UTC(year, monthZeroBased + 1, 0)).getUTCDate();
}

function monthlyCandidate(first, stepMonths) {
  const y0 = first.getUTCFullYear();
  const m0 = first.getUTCMonth();
  const day = first.getUTCDate();

  const absoluteMonth = y0 * 12 + m0 + stepMonths;
  const year = Math.floor(absoluteMonth / 12);
  const month = absoluteMonth % 12;

  if (day > daysInMonth(year, month)) return null;
  return new Date(Date.UTC(year, month, day));
}

function yearlyCandidate(first, stepYears) {
  const year = first.getUTCFullYear() + stepYears;
  const month = first.getUTCMonth();
  const day = first.getUTCDate();
  if (day > daysInMonth(year, month)) return null;
  return new Date(Date.UTC(year, month, day));
}

export function expandScheduleItem(item, {
  startDate,
  endDate,
  maxOccurrences = 10000,
} = {}) {
  const first = assertIsoDate(item.first_date ?? item.date, "first_date");
  const start = assertIsoDate(startDate, "startDate");
  const end = assertIsoDate(endDate, "endDate");
  if (end < start) throw new RangeError("endDate must be on or after startDate");

  const frequency = String(item.frequency ?? item.freq ?? "ONCE").toUpperCase();
  const interval = Math.max(1, Math.floor(Number(item.interval) || 1));
  const out = [];

  function maybePush(d) {
    if (!d) return;
    if (d >= start && d <= end) out.push(iso(d));
  }

  if (frequency === "ONCE") {
    maybePush(first);
    return out;
  }

  if (frequency === "DAILY" || frequency === "WEEKLY") {
    const stepDays = frequency === "DAILY" ? interval : interval * 7;
    let d = first;
    let guard = 0;
    while (d <= end && guard < maxOccurrences) {
      maybePush(d);
      d = addUtcDays(d, stepDays);
      guard += 1;
    }
    return out;
  }

  if (frequency === "MONTHLY") {
    let step = 0;
    let guard = 0;
    while (guard < maxOccurrences) {
      const candidate = monthlyCandidate(first, step);
      const comparison = candidate ?? monthlyCandidate(
        new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth(), 1)),
        step
      );
      if (comparison && comparison > end) break;
      maybePush(candidate);
      step += interval;
      guard += 1;
    }
    return out;
  }

  if (frequency === "YEARLY") {
    let step = 0;
    let guard = 0;
    while (guard < maxOccurrences) {
      const candidate = yearlyCandidate(first, step);
      const year = first.getUTCFullYear() + step;
      if (Date.UTC(year, 0, 1) > end.getTime()) break;
      maybePush(candidate);
      step += interval;
      guard += 1;
    }
    return out;
  }

  throw new RangeError(`Unsupported frequency: ${frequency}`);
}

export function buildDailyLoad(items, {
  startDate,
  endDate,
} = {}) {
  const days = new Map();

  for (const item of items) {
    const dates = expandScheduleItem(item, { startDate, endDate });
    const minutes = Math.max(Number(item.estimated_minutes ?? item.minutes) || 0, 0);

    for (const date of dates) {
      const bucket = days.get(date) ?? {
        date,
        total_estimated_minutes: 0,
        tasks: [],
      };

      bucket.total_estimated_minutes += minutes;
      bucket.tasks.push({
        task: String(item.task ?? ""),
        chore_code: String(item.chore_code ?? ""),
        category: String(item.category ?? ""),
        estimated_minutes: minutes,
      });
      days.set(date, bucket);
    }
  }

  return [...days.values()]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map(day => ({
      ...day,
      total_estimated_minutes: Math.round(day.total_estimated_minutes * 100) / 100,
    }));
}
