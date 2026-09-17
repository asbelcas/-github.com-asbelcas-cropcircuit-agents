# CLOSED CASH LOOP — experiment ledger (GitHub issue #26, deployed 2026-09-17)
# North star: SETTLED EXTERNAL PAYMENT. Everything else is a weaker signal.
# Fields per candidate: source | payout | eligibility | deliverable | deadline |
# time-to-cash | agent effort | Casey attention | cash spend | payout rail | risk | confidence | status | result | settled
# Score = expected settled value / scarce resource, weighted to time-to-cash + P(accept).

## LIVE EXPERIMENTS
| id | lane | candidate | payout rail | t2cash | P | status | settled |
|----|------|-----------|-------------|--------|---|--------|---------|
| E1 | A | owocki bounty watcher (hourly) | USDC Base | days | med | ARMED (0 open all day) | $0 |
| E2 | C | business ladder $125/$350/$500 (radar-fed) | PayPal | weeks | med | LIVE — 6 warm leads staged; conversion = HUMAN_ACTION (Casey send / Reddit acct) | $0 |
| E3 | A | passive bandwidth containers x6 | fiat dashboards | monthly | high | RUNNING (6+ days) | $? (dashboard login needed) |
| E4 | A | dealwork.ai worker lane | USDC | days | ? | LIVE (agent cropcircuitops onboarded, creds 600) — 0 funded jobs tonight | $0 |
| E5 | A | opentask.ai task scan | USDC | days | ? | SCANNING tonight | $0 |
| E6 | B | ClawTasks free tasks (reputation) | none yet | n/a | n/a | PARKED (paid lane needs stake=money-out) | $0 |
| E7 | D | radar/tool templates as product | fiat | months | low | PARKED until A-C prove | $0 |

## HUMAN_ACTIONS (blocking branches, kept alive otherwise)
- H1: Casey sends 6 drafted lead replies (runtime/demand_intel_table.md)
- H2: Reddit account completion — cron 22:51 (agent); then warm-up posts
- H3: Permies CAPTCHA (10s) / Fiverr session (5 min)
- H4: EIN (10 min IRS) — unlocks federal grant tier
- H5: Unclaimed property — DONE ($0, lane closed)

## KILLED / DEAD (with screening lessons)
- K1: Reddit-archive APIs (PullPush/ArcticShift block agents) → lesson: use RSS+tolerance
- K2: Bounty-hunting INFRA build (owocki 0 open; arms race) → watcher-only, no auto-claimer
- K3: Faucets/mining (negative EV; electricity=money-out) → hard screen: cash-spend>0 kills
- K4: GitHub repo API exploration (rate-limited account) → use token-by-reference sparingly

## KILLED TONIGHT (funding verification — the loop working as designed)
- K5: dealwork/Esmond claim — POSTER WALLET INSUFFICIENT (escrow unfunded; platform caught it)
- K6: dealwork/Bartok claim — job under-funded (budgetMax 40 < 10 x 5 slots; platform caught it)
- K7: dealwork board-wide screen — 0 of ~40 open jobs pass funded-poster filter (totalSpent>0
  or trust>=1). Rule added: check posterBuyerStats.totalSpent + funding math BEFORE any bid/claim.
- K8: opentask micro-tasks ($4-9) — agent-posted, funding unverifiable keyless; parked for
  tomorrow's registration + funding check (Hermes tasks quoted-scope = possible exception).

## GRANT LANE [PARKED 2026-09-17 per D8 — exchange-only doctrine; artifacts kept]
- EV application v2: RED-TEAMED + rewritten (testbed framing, 90-day scorecard, honest
  revenue wording); submission-ready at grants/submissions/ev_draft_2026-09-17.md.
  SUBMIT = Casey (mercatus.org/emergent-ventures, ~10 min).

## SALE-SAFETY FIELDS (from UU audit): per settlement record hold_status
## (settled/held/released_date) + refund_flag + chargeback_flag. >10% refund rate ->
## tighten screening, keep the guarantee.

## SETTLED REVENUE: $0.00 (honest baseline — day 0)
## PROTOCOL v2 AMENDMENTS (ChatGPT, 09-17, from night-1 evidence)
- FUNDING GATE F0-F3: F0 listing-only → F1 math coherent (price x slots <= budget, rail
  exists) → F2 payer evidence (spend history / funded escrow / opened payable contract)
  → F3 executable. NO substantive work before F3. (Kills Esmond/Bartok-class at F1/F2.)
- FUNDED-DEMAND RATE per source: listings scanned | F2+ candidates | contracts | settled
  | agent minutes. Adaptive backoff: 0 F2 in 40 listings → scan frequency -75%.
- MARKETPLACE THEATER ratio: funded jobs / open listings; settled / offers (opentask
  displayed: ~2000 offers vs 2 contracts/30d = economically inert despite busy look).
- SCORE v2: expected settled x P(settle) / (production + verification cost + Casey
  attention + payout latency). Pushes organism toward real buyers (the 6 warm leads).
- Lane A reallocation: 70% payer-verifiable bounties (Algora project pages w/ named
  sponsors, exact issues+rewards) / 20% dealwork funded-poster-only / 10% opentask
  contract-signal-only.

## EMPIRICAL LESSON #1: agent-work boards are full of unfunded listings; the escrow guards
## work. Funded work concentrates where buyers have spending history — screen for it, or go
## where we already have warm buyers (the farm-ladder leads).
## TOKEN SPEND: minimal (deterministic scripts first per protocol)
