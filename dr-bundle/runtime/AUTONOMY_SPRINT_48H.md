# 48-HOUR AUTONOMY SPRINT — starts when Casey goes dark — 2026-09-16
Authority: Casey — "set up a full audit and self-led work sprint while im gone
for 48 hours... you have all access and permissions." Boundaries that survive
ANY grant: no SSN/credit/loans, no money movement, no seed/private keys, no
live trading, no mass-DM spam, no new paid commitments.

## OS-LEVEL LANES (run regardless of agent session liveness)
- Lab paper-trade: daily 23:55 (cropcircuit-lab-paper.timer) — 30-day clock.
- Ops health checks: daily 07:45 (7 regression checks, email on failure).
- Daily digest: 08:05 (HA + email to Casey).
- Money radar: Mon 07:15 (plasma rates + best-center alert).
- FB observer: 15-min cycles (page watch + phone push on activity).
- X queue poster: 09:00 + 17:00 daily (cropcircuit-x-queue.timer) — posts ONE
  queued value tweet per run from runtime/x_tweet_queue.json; skips when empty;
  HARD CAP 2/day to protect the account.

## AGENT LANES (when session alive; crons session-scoped)
- 3x daily check: /sprint intakes (data/sprint_intakes.json) — if an intake
  arrives: HA alert + draft personalized reply into runtime/pending_replies/
  (HOLD for Casey; sprint page promises 1-business-day reply).
- Intent-harvest: max 3 genuine replies/day from @CropCircuitHQ, only where a
  real fit; log each to runtime/x_outreach_log.jsonl.
- Moltbook: check replies to sprint post daily; respond helpfully as
  cropcircuitops; log to runtime/moltbook_replies.json (existing watcher).
- Audit sweep: hourly doctor + container health (existing).

## CONTENT BANK (staged NOW, gated, awaiting Casey approval on return)
1. what-my-ai-crew-broke-2 (from incident log: 36 silent HA notifications).
2. ten-papers-that-changed-how-i-think-about-ai-crews (corpus artifact w/ URLs).
3. michigan-winter-readiness-checklist (seasonal, from seasonal_drafts.md).
4. objection-answers article ("can't you just ask ChatGPT?").

## STOP CONDITIONS (abort lane + alert Casey via HA/email)
- X: any rate-limit/lock/ban signal -> stop all X lanes immediately.
- Any payment/site outage -> ops health check emails already cover.
- Any inbound legal/official correspondence -> hold, alert, do not respond.

## ON CASEY'S RETURN
- Approval queue: 4 gated articles, any pending replies, outreach log review,
  lab journal review (walk-forward verdict when 30d hits ~Oct 16).

## CHATGPT REVIEW INTEGRATED (ESC-48H-REVIEW-20260916-001) — preflight adjustments
1. X queue poster PAUSED for the dark window (website-scripting method risks
   permanent suspension per X automation rules; no API budget permitted).
   Queue of 6 tweets preserved for Casey's return. Zero automated outbound
   replies; zero automated follows. Intent-harvest = DRAFT-ONLY review queue.
2. Sprint page promise changed: "slots reviewed in founder rounds twice a
   week" (1-business-day promise unsatisfiable while dark). Deployed.
3. NEW LANE A (highest priority add): Qualified-demand intelligence — private
   table of ~20 best public buyer-pain signals (person|URL|problem|fit|proposed
   reply|CTA?) built during the window; nothing sent.
4. NEW LANE B: synthetic ML-workflow Sprint proof object (fictional composite,
   private) — before map, bottlenecks, redesigned workflow, decision rules,
   7-day plan. Not published; Casey decides on return.
5. Return approval order: (1) outreach expansion from the intent queue
   (best 5-10), (2) proof/content bank in order: synthetic sprint proof ->
   ten-papers -> objection article -> broke-2 -> winter, (3) NO pricing
   changes absent explicit buyer price objections.
6. Engagement rule: any negative/high-attention interaction = observe + draft
   + notify only. Fail-closed on ambiguity, never retry when success is
   uncertain. No cross-account amplification, ever.
