/**
 * CropCircuit local-first workspace helpers.
 * Backward-compatible with workspace 1.0 backups.
 * The workspace can contain private operational data and is never transmitted
 * by this module. Callers provide a Storage-compatible object.
 */

export const WORKSPACE_VERSION = "1.1";
export const SUPPORTED_WORKSPACE_VERSIONS = Object.freeze(["1.0","1.1"]);

export const WORKSPACE_KEYS = Object.freeze({
  laborEntries: "cropcircuit_farm_labor_log_v1",
  laborSettings: "cropcircuit_farm_labor_settings_v1",
  choreSchedule: "cropcircuit_chore_schedule_v1",
  equipmentMaintenance: "cropcircuit_equipment_maintenance_v1",
  harvestEntries: "cropcircuit_harvest_log_v1",
  salesEntries: "cropcircuit_sales_log_v1",
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

function arrayOrEmpty(value) {
  return Array.isArray(value) ? value : [];
}

export function readWorkspace(storage) {
  if (!storage || typeof storage.getItem !== "function") {
    throw new TypeError("storage must provide getItem/setItem");
  }

  const laborSettings = getJson(storage, WORKSPACE_KEYS.laborSettings, {});

  return {
    schema_version: WORKSPACE_VERSION,
    exported_at: new Date().toISOString(),
    labor_entries: arrayOrEmpty(getJson(storage, WORKSPACE_KEYS.laborEntries, [])),
    labor_settings:
      laborSettings && typeof laborSettings === "object" && !Array.isArray(laborSettings)
        ? laborSettings
        : {},
    chore_schedule: arrayOrEmpty(getJson(storage, WORKSPACE_KEYS.choreSchedule, [])),
    equipment_maintenance: arrayOrEmpty(getJson(storage, WORKSPACE_KEYS.equipmentMaintenance, [])),
    harvest_entries: arrayOrEmpty(getJson(storage, WORKSPACE_KEYS.harvestEntries, [])),
    sales_entries: arrayOrEmpty(getJson(storage, WORKSPACE_KEYS.salesEntries, [])),
  };
}

export function validateWorkspace(workspace) {
  const errors = [];
  if (!workspace || typeof workspace !== "object") return ["workspace must be an object"];

  const version = String(workspace.schema_version ?? "");
  if (!SUPPORTED_WORKSPACE_VERSIONS.includes(version)) {
    errors.push(`unsupported schema_version ${version || "(missing)"}`);
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

  if (version === "1.1") {
    if (!Array.isArray(workspace.equipment_maintenance)) errors.push("equipment_maintenance must be an array");
    if (!Array.isArray(workspace.harvest_entries)) errors.push("harvest_entries must be an array");
    if (!Array.isArray(workspace.sales_entries)) errors.push("sales_entries must be an array");
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

function setJson(storage,key,value) {
  storage.setItem(key,JSON.stringify(value));
}

export function writeWorkspace(storage, workspace, { mode = "replace" } = {}) {
  if (!storage || typeof storage.getItem !== "function" || typeof storage.setItem !== "function") {
    throw new TypeError("storage must provide getItem/setItem");
  }

  const errors = validateWorkspace(workspace);
  if (errors.length) return { ok:false, errors };

  const current = readWorkspace(storage);
  const version = String(workspace.schema_version);

  let laborEntries = workspace.labor_entries;
  let choreSchedule = workspace.chore_schedule;
  let laborSettings = workspace.labor_settings;
  let equipment = version === "1.1" ? workspace.equipment_maintenance : current.equipment_maintenance;
  let harvest = version === "1.1" ? workspace.harvest_entries : current.harvest_entries;
  let sales = version === "1.1" ? workspace.sales_entries : current.sales_entries;

  if (mode === "merge") {
    laborEntries = mergeById(current.labor_entries, laborEntries);
    choreSchedule = mergeById(current.chore_schedule, choreSchedule);
    laborSettings = { ...current.labor_settings, ...laborSettings };
    equipment = mergeById(current.equipment_maintenance, equipment);
    harvest = mergeById(current.harvest_entries, harvest);
    sales = mergeById(current.sales_entries, sales);
  } else if (mode !== "replace") {
    return { ok:false, errors:[`unsupported import mode ${mode}`] };
  }

  setJson(storage,WORKSPACE_KEYS.laborEntries,laborEntries);
  setJson(storage,WORKSPACE_KEYS.laborSettings,laborSettings);
  setJson(storage,WORKSPACE_KEYS.choreSchedule,choreSchedule);
  setJson(storage,WORKSPACE_KEYS.equipmentMaintenance,equipment);
  setJson(storage,WORKSPACE_KEYS.harvestEntries,harvest);
  setJson(storage,WORKSPACE_KEYS.salesEntries,sales);

  return {
    ok:true,
    errors:[],
    labor_entries:laborEntries.length,
    chore_schedule:choreSchedule.length,
    equipment_maintenance:equipment.length,
    harvest_entries:harvest.length,
    sales_entries:sales.length,
  };
}
