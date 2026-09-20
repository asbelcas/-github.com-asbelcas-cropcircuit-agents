/**
 * CropCircuit Farm Labor Data Contract helpers.
 * Zero dependencies. Preserves operator-entered task text while optionally
 * adding canonical chore codes for interoperability.
 */

function finiteOrNull(value) {
  if (value === null || value === undefined) return null;
  if (typeof value === "string" && value.trim() === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function workerHours({ minutes, workers }) {
  const m = finiteOrNull(minutes);
  const w = finiteOrNull(workers);
  if (m === null || w === null || m < 0 || w < 0) return null;
  return (m / 60) * w;
}

export function normalizeLaborIdentity(record) {
  const code = String(record?.chore_code ?? "").trim();
  if (code) {
    return {
      key: `code:${code}`,
      method: "chore_code",
      chore_code: code,
    };
  }

  const category = String(record?.category ?? "").trim().toLowerCase();
  const task = String(record?.task ?? "").trim().toLowerCase();
  if (!task) {
    return { key: "", method: "none", chore_code: "" };
  }

  return {
    key: `text:${category}\u0000${task}`,
    method: "task_text",
    chore_code: "",
  };
}

export function normalizeDate(value) {
  const text = String(value ?? "").trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return text;

  const d = new Date(text);
  if (!Number.isFinite(d.getTime())) return "";
  return d.toISOString().slice(0, 10);
}

export function normalizeLaborRecord(input, {
  calculateWorkerHours = true,
} = {}) {
  const minutes = finiteOrNull(input?.minutes);
  const workers = finiteOrNull(input?.workers);
  let hours = finiteOrNull(input?.worker_hours);

  if (hours === null && calculateWorkerHours) {
    hours = workerHours({ minutes, workers });
  }

  return {
    date: normalizeDate(input?.date),
    category: String(input?.category ?? "").trim(),
    task: String(input?.task ?? "").trim(),
    chore_code: String(input?.chore_code ?? "").trim(),
    minutes: minutes === null ? null : Math.max(minutes, 0),
    workers: workers === null ? null : Math.max(workers, 0),
    worker_hours: hours === null ? null : Math.max(hours, 0),
    notes: String(input?.notes ?? "").trim(),
  };
}

export function validateLaborRecord(record, {
  knownChoreCodes = null,
  workerHourTolerance = 0.011,
} = {}) {
  const errors = [];

  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(record?.date ?? ""))) {
    errors.push("invalid date");
  }
  if (!String(record?.category ?? "").trim()) errors.push("missing category");
  if (!String(record?.task ?? "").trim()) errors.push("missing task");

  const code = String(record?.chore_code ?? "").trim();
  if (code && knownChoreCodes && !knownChoreCodes.has(code)) {
    errors.push(`unknown chore_code ${code}`);
  }

  const minutes = finiteOrNull(record?.minutes);
  const workers = finiteOrNull(record?.workers);
  const hours = finiteOrNull(record?.worker_hours);

  if (minutes === null || minutes <= 0) errors.push("minutes must be > 0");
  if (workers === null || workers <= 0) errors.push("workers must be > 0");
  if (hours === null || hours < 0) errors.push("worker_hours must be >= 0");

  if (minutes !== null && workers !== null && hours !== null) {
    const expected = workerHours({ minutes, workers });
    if (expected !== null && Math.abs(expected - hours) > workerHourTolerance) {
      errors.push(`worker_hours differs from minutes/workers calculation`);
    }
  }

  return errors;
}
