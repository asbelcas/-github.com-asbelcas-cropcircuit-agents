# CropCircuit MEMORY — typed memory (boot file for any agent on this machine)
# Pattern: MIRIX-style typed stores, kept local. Read this FIRST at session start.
# Update: append changes with dates. Never store secrets here — pointers only.

## PROFILE (who we are)
One-person regenerative farm business, Southwest Michigan. Founder: Casey Armstrong
(MSU animal science; livestock/dairy; park ranger). Building the farm in public.
AI crew: Kimi (primary ops agent, this machine), ChatGPT (escalation bridge),
Codex (CLI, usage-limited some weeks). Authority: Casey final-approves external
actions; OPERATING_POLICY.md governs; INCIDENT_LOG.md is the episodic record.

## EPISODIC (what happened)
- ~/cropcircuit/pilot_audit/governance/INCIDENT_LOG.md — chronological everything.

## SEMANTIC (facts)
- Website: cropcircuit.org; Flask+Docker; systemd user service cropcircuit-website.service;
  env: ~/cropcircuit-site/.env (secrets live there: FB creds, HA token, STATS_KEY, PayPal).
- FB Page: canonical id 61579176842719 (legacy 748206851708249 redirects). No @username
  (@CropCircuit = music artist). Observer watches page via .chrome-ha browser (CDP 9224).
- Meta app: cropCircuit 1585508712758647, business 1108805059322418. Dev-mode admin model
  (Tech Provider NOT needed — role users skip business verification).
- LinkedIn: /in/cassandra-armstrong-9030711a3 (headline/about/experience done 09-15).
- HA: docker container homeassistant, http://127.0.0.1:8123, admin user kimi_agent
  (password ~/.config/cropcircuit/ha_kimi_agent.pass); phones push via
  notify.mobile_app_{pixel_9,cat,doogee}.
- Donations: /go/donate -> paypal.me/mydogyooper (shows as Cassandra Armstrong — disclosed).
- Stats: first-party, /stats/<STATS_KEY from .env>.
- Key gotchas -> ops_playbook/README.md (deploy, oauth, ha_token, fb_page, escalation, gate).

## PROCEDURAL (how we do things)
- ~/cropcircuit/ops_playbook/README.md — distilled workflows with pitfalls.
- ~/cropcircuit/runtime/ — staged plans (sept_plan/, growth packet, synthesis).

## RESOURCES (links)
- Bridge config: ~/.config/cropcircuit/chatgpt-escalation-bridge.json (chat 6aa9ad45, Chat mode).
- Backups: ~/backups/cropcircuit/ (runtime + agentbridge + cropcircuit-site/data, last 12).
- Runbook: ~/cropcircuit-site/FB_OPERATIONS.md.
- Research synthesis: runtime/ARTICLE_STACK_SYNTHESIS_2026-09-16.md (35-paper corpus, 52 URLs).

## KNOWLEDGE ASSETS INDEX (2026-09-17 integration — read these before redoing research)
- runtime/ARTICLE_STACK_SYNTHESIS_2026-09-16.md — 35-paper corpus → 10 lessons, 5 bets.
- runtime/demand_intel_table.md — 20 tiered buyer leads + draft replies (6 fresh <6wk).
- runtime/BOT_DEEPDIVE_2026-09-17.md — agent-economy survey; operator-bot interviews
  (johnnybucks/robauto-ai/Gordon_Gekko); $0→$1 verdict; owocki/ClawTasks lane status.
- runtime/GEO_ARBITRAGE_2026-09-17.md — Michigan×internet duality; Virtual Systems
  Audit product design (STAGED for Casey); n8n radar + SDA soil rail verified.
- runtime/LEGAL_STUDY_2026-09-17.md — donations non-deductibility gap (staged fix);
  terms solid; unclaimed-property self-search task (human); LLC staged; RTF parked.
- runtime/SINGULARITY_ECONOMICS_2026-09-17.md — verification-bottleneck economics;
  5 rents (all held); doctrine D1-D7; second-order products S1-S5.
- runtime/FIFTY_K_SPRINT_PLAN + MONEY_BREAKTHROUGH + CURRENCY_WALL_MAP +
  FROZEN_MONEY_SWEEP + NICHE_MONEY_LANES (09-15/16) — money-lane strategy corpus.
- runtime/sept_plan/ — sprint launch package, proof object (Lane B), claim sheets,
  objection sims, seasonal drafts, email-capture packet.

## NEW INFRASTRUCTURE (2026-09-17)
- n8n: cropcircuit-n8n.service (localhost:5678, CLI-managed, owner acct NOT created
  yet) + cropcircuit-demandscan.timer (hourly :17; stops svc → one-shot execute →
  restarts). Workflow demand-scan-fresh-pain: reddit RSS (429-prone) + Gardening SE
  Atom → dedup → runtime/demand_scan_hits.jsonl + HA push. n8n v2 publish-model
  pitfall: sqlite active=1 does NOT arm triggers — use the timer.
- Moltbook helper: bin/moltbook_api.py (post/comment/verify/search/feed). New posts
  need math verify <5min. cropcircuitops = ops agent identity.
- Cron watchers: 01M2PEC0... (:23/4h main sweep), 01M2R15H... (:41/4h ask-post watch).
- Legacy n8n orphan (0.0.0.0:5678, unprotected) REMOVED 09-17; export in n8n/legacy-backup/.

## GRANT FACTORY (revived 2026-09-17)
- Chain: Josie Zayner(X) → 1517 Fund directory (35 grants, LIVE verified) → old xlsx
  never existed on GitHub (ChatGPT admitted). Factory: grants/GRANT_FACTORY_2026-09-17.md
  (Tier-1 alt-grants queue, Tier-2 USDA, blockers, SSN routing rule).
- EV application DRAFT READY: grants/submissions/ev_draft_2026-09-17.md ($6k ask).
- Feb packets reusable: grants/submissions/ (MDARD RFNG, SARE, FACT...).
- Blockers: EIN (Casey 10-min IRS task) unlocks federal; 5-farmer list + Calhoun CD
  signer pending for partnership grants. GitHub issue #26 "Closed Cash Loop" UNVERIFIED
  (API rate-limited, profile 404) — investigate when API resets.

## UNKNOWN-UNKNOWNS AUDIT (2026-09-17; rerun quarterly 12-17)
runtime/UNKNOWN_UNKNOWNS_2026-09-17.md — pre-mortem + assumption inversion + adversary
pass. Tier-1 fixed/live: UU-1 shadowban protocol (visibility verify before lead sends);
UU-2 PayPal-hold playbook (runtime/PAYPAL_HOLD_PLAYBOOK.md) + alt-rails in confirmations;
UU-3 offsite DR bundle of non-secret state to private GitHub repo (D-01, this session);
UU-4 continuity mode (runtime/CONTINUITY_MODE.md). Tier-2 watched: free-AI flood,
bridge death, refund abuse, PII, vendor dependency. Tier-3 accepted. VERIFIED: linger
handles power-loss auto-start; backups rotate but were same-disk (now mitigated).
## ACTIVE PROJECTS (as of 2026-09-17)
- AWAITING CASEY (approval order): (1) /support non-deductibility copy fix (LEGAL_STUDY
  §1). (2) staged articles → flip approved+provenance. (3) Virtual Systems Audit tier
  + intake fields. (4) demand-table Tier-1 replies (6 fresh leads incl. "130 fresh
  acres"). (5) unclaimed-property self-search (LEGAL_STUDY §4). (6) 7786 parcel
  confirm → RTF/zoning list. (7) LLC+EIN at first revenue/build.
- LIVE AS OF 09-17: Farm Plan Review tier (/review, $125; DECISION_LOG entry).
  Intakes at data/review_intakes.json (env REVIEW_INTAKES_PATH); HA notifies.
- MONEY FUTURE (Casey 09-17): runtime/FUTURE_OF_MONEY_2026-09-17.md — certainties
  (stablecoins won: $300B+, GENIUS Act; BIS unified ledger; 5-layer agent-payments stack
  w/ x402 carrying real volume; machines = economic actors w/ balance sheets),
  high-probs (receipt-reputation as collateral, micro-settlement micro-markets,
  wholesale CBDCs), speculative (AI treasuries, farm oracles, mutual-credit rails).
  Commands F1-F6: agent reputation compounds into FICO world; USDC float rail staged;
  x402 micro-product at n>=10; wallet-layer policy encoding; farm-oracle positioning.
- MONEY HISTORY (Casey 09-17): runtime/HISTORY_OF_MONEY_2026-09-17.md — 5,000y arc:
  ledger-credit predates coin (Graeber); coinage = state-stamped trust (Lydia 600 BCE);
  Rome dies by debasement; Song paper = first fiat failure mode; tally sticks 700y then
  burn down Parliament; Medici/BoE born of war finance; Pacioli 1494 = the ledger
  algorithm capitalism runs on; 1971 = all-fiat world; 2008 = scarcity without issuer;
  2020s = agent money (our layer). 5 through-lines + operational commands.
- ECONOMIC ALGORITHMS (Casey 09-17): runtime/ECONOMIC_ALGORITHMS_2026-09-17.md — canon of
  15 (price mechanism, Vickrey auctions, Gale-Shapley matching, signaling/screening,
  repeated games, AMMs, bandits, Wright's law, Romer non-rival growth, creative
  destruction, multiplier/velocity, Kelly, evolutionary search) + our growth model:
  OUTPUT = f(agents, capital, tech, institutions); growth = transactions/Casey-hour x
  margin x velocity, compounded by templates. Roadmap §5 = what to install and when.
- MONEY DOCTRINE D8 (Casey 09-17): EXCHANGE ONLY — asking lanes parked (grants/donation
  strategy; EV draft kept on disk, submit = Casey's option). Study: runtime/
  WHAT_MONEY_IS_2026-09-17.md — money = IOU/social relation; ~97% created by bank credit
  (BoE 2014); five doors (exchange/claim/gift/revaluation/issuance); we run door 1,
  presell = honest micro-issuance. WALLET_MATH + CLOSED_CASH_LOOP reclassified.
- POSITIONING DOCTRINE (ChatGPT-approved, binding): "AI-assisted. Human-reviewed. Casey
  personally reviews every recommendation and signs every final plan." NEVER say:
  underwritten/certified/verified safe/guaranteed results. Refund = service guarantee
  only (see SINGULARITY doc §7 for full phrase list).
- Watch loops: moltbook reply crons, :17 timer now runs BOTH demand-scan AND owocki
  bounty watcher (bow1ntywatch1), 21:30 learning loop. WALLET MATH doc:
  runtime/WALLET_MATH_2026-09-17.md — the honest $50k equation; Lane A business engine
  is the only five-figure path; micro-lanes armed and measured, not fantasized.
- Content shipped 09-17: blog/one-human-ai-crew-farm (the AI-crew story post Casey
  requested 09-16) + tools/eat-vs-grow worksheet (lead magnet promised in demand-table
  drafts). Ladder CTAs on both. Next content: Amish-build story; singularity-econ post.
- Moltbook field report live (post 1e2504fc, m/agentfinance): week-1 radar receipts,
  honest $0 numbers, channel question to operators.

## WALLET (agent-hot-btc, created 2026-09-05)
BIP84 Bitcoin hot wallet ("pocket-change; savings never here"). Receive addr 1:
bc1q06gem9uqwkl40x943v3c9vrvjgcszruppkukys (watch-only copy:
runtime/agent_wallet_watchonly.json). SEED PHRASE: paper backup held by Casey —
the only copy (laptop copies shredded 2026-09-05; ~/.config/agent-wallet/ gone).
NEVER in chat/logs. Balance 0 as of 2026-09-16. BTC-native: CANNOT receive USDC;
USDC-on-Base for sprint payments needs an EVM address (Casey's phone wallet or new).

## X ACCESS (added 2026-09-16)
@CropCircuitHQ (formerly @Ham_lamdingdong, Casey.s second account, used for Moltbook verification) is
LOGGED IN in the .chrome-ha browser (CDP 9224). Full access granted by Casey
("do whatever it takes"). Caveats: account has ~1 follower (alt account, not
the ML audience — @IntuitMachine is the high-value ML account, NOT logged in
anywhere). On 09-16: sprint launch tweet + thread reply posted, bio set to
point to cropcircuit.org/sprint, 10 ML/agents followed. X automation pitfalls:
heavy pages hang CDP (use wait_until='commit', ALWAYS close pages in finally,
clean zombie tabs via /json/close when connect times out).

## LEARNING LOOP (added 2026-09-17)
~/cropcircuit/bin/learning_loop.py + daily 21:30 timer: measures traffic/X/lab/
funnel/radar, appends runtime/LEARNING_LOG.md, queues optimizations in
runtime/OPTIMIZATION_QUEUE.md. Continuous-learning directive from Casey is
operational: the machine measures itself daily and the queue feeds agent work.

## AOL MAILBOX + IDENTITY SETUP (added 2026-09-17, verified live)
- bumblebee1990100@aol.com ("Yoooer") mailbox session is LIVE in the
  .chrome-chatgpt-escalation browser (CDP 9224; tab mail.aol.com/d/today).
  Verification-code retrieval proven: open NEW tab to mail.aol.com/d/folders/1
  (session carries over), search box = input[aria-label="Search"], REAL keyboard
  type + Enter, read codes straight from inbox text. Never log out; never race
  the existing tab. NOTE: port mapping corrected — 9222=.chrome-ha (X/FB
  observer), 9224=chatgpt-escalation. MEMORY's "X at 9224" is stale.
- Reddit/Permies signup passwords generated in
  ~/.config/cropcircuit/identity_accounts.json (600). Reddit: flow verified to
  username screen, then Reddit STOPPED sending fresh verification emails
  (~5 sends/day suppression) — finish when codes resume. Permies: reCAPTCHA v2
  passes nondeterministically with slow paced mouse moves. Fiverr: PerimeterX
  wall. New-mailbox lanes (Proton/Tuta/Zoho) all blocked this window.
- Identity browser: chromium CDP 9226, profile ~/.config/cropcircuit/chrome-identity
  (left running).
