import fs from "node:fs/promises";
import Bounty from "@bounty-ai/agent-sdk";

const once = process.argv.includes("--once");
const apiKey = process.env.BOUNTY_AGENT_API_KEY;
if (!apiKey) {
  throw new Error("BOUNTY_AGENT_API_KEY is required; keep it in a server-side secret store.");
}

const policy = JSON.parse(await fs.readFile(new URL("./policy.json", import.meta.url), "utf8"));
const client = new Bounty({ apiKey });

function text(v) {
  return String(v ?? "").toLowerCase();
}

function evaluate(summary) {
  const haystack = text([
    summary.title,
    summary.description,
    ...(summary.categories || []),
    ...(summary.tags || [])
  ].join(" "));

  const payout = Number(summary.payout_cents || 0);
  if (payout < policy.min_payout_cents) {
    return { accept: false, reason: "below_minimum_payout", payout };
  }

  const allowed = policy.allowed_work.some(k => haystack.includes(k));
  if (!allowed) {
    return { accept: false, reason: "outside_ai_worker_scope", payout };
  }

  const blocked = policy.reject_if.find(rule => {
    const needles = rule
      .replace("requires ", "")
      .split(/[\/,-]/)
      .map(x => x.trim())
      .filter(Boolean);
    return needles.some(n => n.length > 5 && haystack.includes(n));
  });
  if (blocked) {
    return { accept: false, reason: `policy_block: ${blocked}`, payout };
  }

  return { accept: true, reason: "candidate", payout };
}

async function scan() {
  const candidates = [];
  for await (const summary of client.bounties.iterate()) {
    const decision = evaluate(summary);
    if (!decision.accept) continue;

    const work = await client.bounties.open(summary._id);
    candidates.push({
      bounty_id: summary._id,
      version: summary.version,
      title: summary.title,
      payout_cents: summary.payout_cents,
      currency: summary.currency,
      decision,
      inspected_at: new Date().toISOString(),
      status: "candidate_not_claimed"
    });
  }

  candidates.sort((a,b) => Number(b.payout_cents) - Number(a.payout_cents));
  await fs.mkdir("runtime", { recursive: true });
  await fs.writeFile(
    "runtime/trybounty_candidates.json",
    JSON.stringify({ generated_at: new Date().toISOString(), candidates }, null, 2)
  );
  console.log(JSON.stringify(candidates, null, 2));
}

do {
  await scan();
  if (once) break;
  await new Promise(r => setTimeout(r, 30_000));
} while (true);
