/**
 * CropCircuit local-first workspace helpers.
 * The workspace contains private operational data and is never transmitted by
 * this module. Callers provide a Storage-compatible object (usually localStorage).
 */

export const WORKSPACE_VERSION = "1.0";

export const WORKSPACE_KEYS = Object.freeze({
  laborEntries: "cropcircuit_farm_labor_log_v1",
  laborSettings: "cropcircuit_farm_labor_settings_v1",
  choreSchedule: "cropcircuit_chore_schedule_v1",
});

function safeParse(value, fallback) {
  try {
    const parsed = JSON.parse(value);
    return parsed ?? fallback;
  } catch {
    return fallback;
  }
}

function getJson(storage, key, fallback) {
  const raw = storage.getItem(key);
  if (raw === null || raw === undefined) return fallback;
  return safeParse(raw, fallback);
}

export function readWorkspace(storage) {
  if (!storage || typeof storage.getItem !== "function") {
    throw new TypeError("storage must provide getItem/setItem");
  }

  const laborEntries = getJson(storage, WORKSPACE_KEYS.laborEntries, []);
  const laborSettings = getJson(storage, WORKSPACE_KEYS.laborSettings, {});
  const choreSchedule = getJson(storage, WORKSPACE_KEYS.choreSchedule, []);

  return {
    schema_version: WORKSPACE_VERSION,
    exported_at: new Date().toISOString(),
    labor_entries: Array.isArray(laborEntries) ? laborEntries : [],
    labor_settings:
      laborSettings && typeof laborSettings === "object" && !Array.isArray(laborSettings)
        ? laborSettings
        : {},
    chore_schedule: Array.isArray(choreSchedule) ? choreSchedule : [],
  };
}

export function validateWorkspace(workspace) {
  const errors = [];
  if (!workspace || typeof workspace !== "object") return ["workspace must be an object"];
  if (workspace.schema_version !== WORKSPACE_VERSION) {
    errors.push(`unsupported schema_version ${workspace.schema_version ?? "(missing)"}`);
  }
  if (!Array.isArray(workspace.labor_entries)) errors.push("labor_entries must be an array");
  if (!Array.isArray(workspace.chore_schedule)) errors.push("chore_schedule must be an array");
  if (
    !workspace.labor_settings ||
    typeof workspace.labor_settings !== "object" ||
    Array.isArray(workspace.labor_settings)
  ) {
    errors.push("labor_settings must be an object");
  }
  return errors;
}

function mergeById(existing, incoming) {
  const out = [];
  const seen = new Set();

  for (const item of [...existing, ...incoming]) {
    const id = String(item?.id ?? "").trim();
    if (id) {
      if (seen.has(id)) continue;
      seen.add(id);
    }
    out.push(item);
  }
  return out;
}

export function writeWorkspace(storage, workspace, { mode = "replace" } = {}) {
  if (!storage || typeof storage.getItem !== "function" || typeof storage.setItem !== "function") {
    throw new TypeError("storage must provide getItem/setItem");
  }

  const errors = validateWorkspace(workspace);
  if (errors.length) return { ok: false, errors };

  let laborEntries = workspace.labor_entries;
  let choreSchedule = workspace.chore_schedule;
  let laborSettings = workspace.labor_settings;

  if (mode === "merge") {
    const current = readWorkspace(storage);
    laborEntries = mergeById(current.labor_entries, laborEntries);
    choreSchedule = mergeById(current.chore_schedule, choreSchedule);
    laborSettings = { ...current.labor_settings, ...laborSettings };
  } else if (mode !== "replace") {
    return { ok: false, errors: [`unsupported import mode ${mode}`] };
  }

  storage.setItem(WORKSPACE_KEYS.laborEntries, JSON.stringify(laborEntries));
  storage.setItem(WORKSPACE_KEYS.laborSettings, JSON.stringify(laborSettings));
  storage.setItem(WORKSPACE_KEYS.choreSchedule, JSON.stringify(choreSchedule));

  return {
    ok: true,
    errors: [],
    labor_entries: laborEntries.length,
    chore_schedule: choreSchedule.length,
  };
}
