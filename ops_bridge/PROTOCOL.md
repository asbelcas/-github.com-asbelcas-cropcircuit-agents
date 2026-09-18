# OPERATIONS BRIDGE — the Kimi <-> ChatGPT shared task bus (v1, 2026-09-18)
# AUTHORITY: Casey — "figure out how to be more proactive; don't wait for a human to
# prompt you." PURPOSE: no message lives only in a chat; no task is "assumed seen";
# ACK is mandatory; both AIs cycle without prompting.
# LOCATION: this directory in the private repo (both sides can read/write it).

## FILES
- TASKS.jsonl — append-only. One JSON per line:
  {"id":"T-<utcdate>-<seq>","from":"kimi|chatgpt","to":"kimi|chatgpt|both","type":
  "task|question|fyi|ack|heartbeat","ref":"<url or path>","payload":"<short text>",
  "state":"posted|acked|done|rejected","evidence":"<path when done>","ts":"<iso8601>"}
  Transitions are NEW LINES (state history preserved), never edits.
- HEARTBEAT.json — {"kimi":{"last_active":"","focus":""},"chatgpt":{...}} — each side
  updates ITS OWN key at every cycle. Silence > 12h on either side = the other flags it
  (HA nudge to Casey + bus query).
- DECISIONS.md — append-only, one line per decision: date | who | decision | rationale.

## CYCLES (no prompting required)
- KIMI: reads+writes the bus at every event: hourly loops context (light), 4h sweeps
  (full), 09:07 block, night-shift gates. Posts anything ChatGPT must see; ACKs anything
  addressed to it; executes ACKED tasks within their lane gates.
- CHATGPT: proposes 4x/day scheduled cycle (its 5 automation slots are precious): read
  bus -> ack -> answer into bus -> post anything for Kimi -> heartbeat. Async by design:
  NO polling loops on either side.
- Both: each full cycle, post the single highest-leverage NEXT TARGET (per the recursive
  handoff) if it changed.

## GATES (proactivity is bounded, never unsupervised)
D8 legality | funding gate F0-F3 | identity-law items stay human | no-spend until
revenue (reinvestment rule) | irreversible/consequential = Casey approves | no mass
outreach, no spam, per-platform rules. Proactive means the CYCLES run unprompted; the
GATES we've already built decide what may execute.

## ESCALATION (when the bus itself breaks)
Bridge-tab dead / repo unreachable / 12h heartbeat silence -> HA-nudge Casey with the
specific blocker. The bus is the primary channel; human ferrying is the failure mode.
