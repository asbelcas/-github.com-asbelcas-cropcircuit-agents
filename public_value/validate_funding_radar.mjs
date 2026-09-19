import fs from "node:fs";

const path = new URL("./funding_radar.json", import.meta.url);
const radar = JSON.parse(fs.readFileSync(path, "utf8"));

const allowedStatuses = new Set(["open", "continuous", "watch", "paused", "closed"]);
const ids = new Set();
const errors = [];
const warnings = [];
const now = new Date();

function error(message) { errors.push(message); }
function warn(message) { warnings.push(message); }

if (!radar || typeof radar !== "object") error("root must be an object");
if (!/^\d{4}-\d{2}-\d{2}$/.test(radar.verified_at || "")) error("verified_at must be YYYY-MM-DD");
if (!Array.isArray(radar.opportunities)) error("opportunities must be an array");

for (const [index, item] of (radar.opportunities || []).entries()) {
  const prefix = `opportunities[${index}] ${item?.id || "(missing id)"}`;

  if (!item.id || !/^[a-z0-9-]+$/.test(item.id)) error(`${prefix}: invalid id`);
  if (ids.has(item.id)) error(`${prefix}: duplicate id`);
  ids.add(item.id);

  if (!item.title) error(`${prefix}: missing title`);
  if (!item.provider) error(`${prefix}: missing provider`);
  if (!allowedStatuses.has(item.status)) error(`${prefix}: invalid status ${item.status}`);
  if (!item.summary) error(`${prefix}: missing summary`);
  if (!item.deadline_label) error(`${prefix}: missing deadline_label`);
  if (!item.funding) error(`${prefix}: missing funding`);
  if (!item.audience) error(`${prefix}: missing audience`);
  if (!Array.isArray(item.tags)) error(`${prefix}: tags must be an array`);
  if (!item.verification_note) error(`${prefix}: missing verification_note`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(item.verified_at || "")) error(`${prefix}: invalid verified_at`);

  try {
    const source = new URL(item.source_url);
    if (source.protocol !== "https:") error(`${prefix}: source_url must use https`);
  } catch {
    error(`${prefix}: invalid source_url`);
  }

  if (item.deadline !== null && item.deadline !== undefined) {
    const deadline = new Date(item.deadline);
    if (!Number.isFinite(deadline.getTime())) {
      error(`${prefix}: invalid deadline`);
    } else if (item.status === "open" && deadline < now) {
      error(`${prefix}: status is open but deadline is in the past`);
    }
  } else if (item.status === "open") {
    warn(`${prefix}: open item has no machine-readable deadline`);
  }

  const verified = new Date((item.verified_at || "") + "T00:00:00Z");
  if (Number.isFinite(verified.getTime())) {
    const ageDays = Math.floor((now - verified) / 86400000);
    if (ageDays > 30 && ["open", "continuous", "watch", "paused"].includes(item.status)) {
      warn(`${prefix}: verification is ${ageDays} days old`);
    }
  }
}

for (const message of warnings) console.warn("WARN:", message);
if (errors.length) {
  for (const message of errors) console.error("ERROR:", message);
  process.exit(1);
}

console.log(`PASS: ${radar.opportunities.length} funding records validated; ${warnings.length} warning(s)`);
