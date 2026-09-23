/**
 * CropCircuit Hypothesis Memory v0.1
 *
 * Builds searchable memory entries from learning cycles without rewriting the
 * original prediction or automatically declaring a hypothesis "false."
 */

const DISPOSITIONS = new Set([
  "active",
  "supported",
  "inconclusive",
  "suspended",
  "rejected",
]);

function isText(value) {
  return typeof value === "string" && value.trim().length > 0;
}
function array(value) {
  return Array.isArray(value) ? value : [];
}
function clone(value) {
  return JSON.parse(JSON.stringify(value));
}
function currentConfidence(cycle = {}) {
  const updates = array(cycle.updates);
  return updates.length
    ? Number(updates[updates.length - 1].confidence_after)
    : Number(cycle?.prediction?.confidence);
}

export function createHypothesisMemoryEntry(cycle = {}, metadata = {}) {
  if (!isText(cycle?.cycle_id)) throw new TypeError("cycle_id is required");
  if (!isText(cycle?.prediction?.statement)) {
    throw new TypeError("prediction.statement is required");
  }

  const disposition = metadata.disposition || "active";
  if (!DISPOSITIONS.has(disposition)) {
    throw new TypeError("disposition is not recognized");
  }

  return {
    schema_version: "0.1",
    memory_id: metadata.memory_id || `hypothesis:${cycle.cycle_id}`,
    cycle_id: cycle.cycle_id,
    created_at: metadata.created_at || cycle.created_at || "",
    updated_at: metadata.updated_at || "",
    original_prediction: cycle.prediction.statement,
    initial_confidence: Number(cycle.prediction.confidence),
    current_confidence: currentConfidence(cycle),
    disposition,
    conditions: array(metadata.conditions).filter(isText),
    tags: array(metadata.tags).filter(isText),
    reason: metadata.reason || "",
    question: cycle.question || "",
    action: cycle?.action?.description || "",
    reversible: cycle?.action?.reversible,
    outcomes: array(cycle.observations).map(x => ({
      recorded_at: x.recorded_at || "",
      result: x.result || "",
      evidence_refs: array(x.evidence_refs),
    })),
    contradictions: array(cycle.contradictions).map(x => ({
      statement: x.statement || "",
      status: x.status || "",
      evidence_refs: array(x.evidence_refs),
      note: x.note || "",
    })),
    updates: array(cycle.updates).map(x => ({
      recorded_at: x.recorded_at || "",
      confidence_before: x.confidence_before,
      confidence_after: x.confidence_after,
      rationale: x.rationale || "",
      model_change: x.model_change || "",
      next_action: x.next_action || "",
    })),
    source_refs: array(cycle.provenance)
      .map(x => x.ref)
      .filter(isText),
  };
}

export function updateHypothesisDisposition(entry = {}, update = {}) {
  if (!isText(entry.memory_id)) throw new TypeError("memory_id is required");
  if (!DISPOSITIONS.has(update.disposition)) {
    throw new TypeError("disposition is not recognized");
  }
  if (!isText(update.reason)) {
    throw new TypeError("reason is required when changing disposition");
  }

  const next = clone(entry);
  next.disposition = update.disposition;
  next.reason = update.reason;
  next.updated_at = update.updated_at || "";
  if (Array.isArray(update.conditions)) {
    next.conditions = update.conditions.filter(isText);
  }
  if (Array.isArray(update.tags)) {
    next.tags = update.tags.filter(isText);
  }
  return next;
}

export function searchHypothesisMemory(entries = [], query = "", filters = {}) {
  const q = String(query || "").trim().toLowerCase();
  const dispositions = new Set(array(filters.dispositions));
  const tags = new Set(array(filters.tags).map(x => String(x).toLowerCase()));

  return array(entries).filter(entry => {
    if (dispositions.size && !dispositions.has(entry.disposition)) return false;
    if (tags.size) {
      const entryTags = new Set(array(entry.tags).map(x => String(x).toLowerCase()));
      if (![...tags].every(tag => entryTags.has(tag))) return false;
    }
    if (!q) return true;

    const haystack = [
      entry.original_prediction,
      entry.question,
      entry.reason,
      ...array(entry.conditions),
      ...array(entry.tags),
      ...array(entry.outcomes).map(x => x.result),
      ...array(entry.contradictions).map(x => x.statement + " " + (x.note || "")),
      ...array(entry.updates).map(x => x.rationale + " " + (x.model_change || "") + " " + (x.next_action || "")),
    ]
      .join(" ")
      .toLowerCase();

    return haystack.includes(q);
  });
}

export function graveyard(entries = []) {
  return array(entries).filter(entry =>
    ["inconclusive", "suspended", "rejected"].includes(entry.disposition)
  );
}

export { DISPOSITIONS };
