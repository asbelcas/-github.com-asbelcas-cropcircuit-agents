#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const STATUS_ORDER = { open: 0, continuous: 1, watch: 2, paused: 3, closed: 4 };

export function parseArgs(argv) {
  const out = {
    source: path.join(path.dirname(fileURLToPath(import.meta.url)), "funding_radar.json"),
    status: [],
    county: "",
    tag: [],
    dueWithin: null,
    format: "md",
    asOf: new Date(),
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      if (i + 1 >= argv.length) throw new Error(`Missing value after ${arg}`);
      i += 1;
      return argv[i];
    };

    if (arg === "--source") out.source = next();
    else if (arg === "--status") out.status = next().split(",").map((x) => x.trim().toLowerCase()).filter(Boolean);
    else if (arg === "--county") out.county = next().trim();
    else if (arg === "--tag") out.tag = next().split(",").map((x) => x.trim().toLowerCase()).filter(Boolean);
    else if (arg === "--due-within") out.dueWithin = Math.max(Number(next()), 0);
    else if (arg === "--format") out.format = next().toLowerCase();
    else if (arg === "--as-of") {
      const d = new Date(next());
      if (!Number.isFinite(d.getTime())) throw new Error("Invalid --as-of date");
      out.asOf = d;
    } else if (arg === "--help" || arg === "-h") out.help = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return out;
}

export function countyMatches(item, county) {
  if (!county) return true;
  const scope = Array.isArray(item.county_scope) ? item.county_scope : [];
  if (scope.length === 0) return true;
  return scope.some((x) => String(x).toLowerCase() === county.toLowerCase());
}

export function tagMatches(item, tags) {
  if (!tags.length) return true;
  const itemTags = (item.tags || []).map((x) => String(x).toLowerCase());
  return tags.some((tag) => itemTags.includes(tag));
}

export function filterFunding(radar, options) {
  const statuses = options.status || [];
  const asOfMs = options.asOf instanceof Date ? options.asOf.getTime() : new Date(options.asOf).getTime();
  const maxDueMs = options.dueWithin === null || options.dueWithin === undefined
    ? null
    : asOfMs + (Number(options.dueWithin) * 86400000);

  return (radar.opportunities || [])
    .filter((item) => !statuses.length || statuses.includes(String(item.status).toLowerCase()))
    .filter((item) => countyMatches(item, options.county || ""))
    .filter((item) => tagMatches(item, options.tag || []))
    .filter((item) => {
      if (maxDueMs === null) return true;
      if (!item.deadline) return false;
      const due = Date.parse(item.deadline);
      return Number.isFinite(due) && due >= asOfMs && due <= maxDueMs;
    })
    .sort((a, b) => {
      const sa = STATUS_ORDER[a.status] ?? 99;
      const sb = STATUS_ORDER[b.status] ?? 99;
      if (sa !== sb) return sa - sb;
      const da = a.deadline ? Date.parse(a.deadline) : Number.POSITIVE_INFINITY;
      const db = b.deadline ? Date.parse(b.deadline) : Number.POSITIVE_INFINITY;
      return da - db || String(a.title).localeCompare(String(b.title));
    });
}

function safeCell(value) {
  return String(value ?? "").replaceAll("|", "\\|").replaceAll("\n", " ");
}

export function renderMarkdown(items, radar) {
  const lines = [
    `# ${radar.name || "Funding Radar"}`,
    "",
    `Verified: ${radar.verified_at || "unknown"}`,
    "",
  ];
  if (!items.length) {
    lines.push("No matching opportunities.");
    return lines.join("\n") + "\n";
  }
  lines.push("| Status | Opportunity | Funding | Timing | Source |");
  lines.push("| --- | --- | --- | --- | --- |");
  for (const item of items) {
    lines.push(
      `| ${safeCell(item.status)} | ${safeCell(item.title)} | ${safeCell(item.funding)} | ${safeCell(item.deadline_label)} | [Primary source](${item.source_url}) |`
    );
  }
  return lines.join("\n") + "\n";
}

export function renderTsv(items) {
  const rows = [["status", "title", "provider", "funding", "deadline", "deadline_label", "source_url"]];
  for (const item of items) {
    rows.push([
      item.status,
      item.title,
      item.provider,
      item.funding,
      item.deadline || "",
      item.deadline_label,
      item.source_url,
    ]);
  }
  return rows.map((row) => row.map((x) => String(x ?? "").replaceAll("\t", " ").replaceAll("\n", " ")).join("\t")).join("\n") + "\n";
}

export function helpText() {
  return `CropCircuit funding query

Usage:
  node public_value/funding_query.mjs [options]

Options:
  --status open,continuous   Filter by one or more statuses
  --county Kalamazoo         Show statewide records plus county-scoped matches
  --tag "soil health"        Filter by exact dataset tag; comma-separated allowed
  --due-within 30            Only dated items due in the next N days
  --format md|json|tsv       Output format (default: md)
  --source PATH              Alternate compatible funding JSON
  --as-of DATE               Override today's date for reproducible queries/tests
  -h, --help                 Show help

Examples:
  node public_value/funding_query.mjs --status open --county Kalamazoo
  node public_value/funding_query.mjs --status open --due-within 30 --format json
  node public_value/funding_query.mjs --tag "regenerative agriculture" --format tsv
`;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(helpText());
    return;
  }
  if (!["md", "json", "tsv"].includes(options.format)) {
    throw new Error("--format must be md, json, or tsv");
  }

  const radar = JSON.parse(fs.readFileSync(options.source, "utf8"));
  const items = filterFunding(radar, options);

  if (options.format === "json") {
    process.stdout.write(JSON.stringify({
      name: radar.name,
      verified_at: radar.verified_at,
      count: items.length,
      opportunities: items,
    }, null, 2) + "\n");
  } else if (options.format === "tsv") {
    process.stdout.write(renderTsv(items));
  } else {
    process.stdout.write(renderMarkdown(items, radar));
  }
}

const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  main().catch((error) => {
    console.error(`ERROR: ${error.message}`);
    process.exit(1);
  });
}
