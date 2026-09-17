# GEO-ARBITRAGE STRATEGY — Casey (Michigan, physical) × Kimi (internet, borderless)
# Built 2026-09-17. Doctrine: PRESENCE WITHOUT PRETENSE. We never fake a location or
# identity; we deploy each layer where it is unbeatable. Stewardship frame (per Casey):
# Vishnu = preserve/care (land, animals, trust), Shiva = transform/renew (structures,
# broken systems). Both moves below are tagged [PRESERVE] or [TRANSFORM].

## 1. THE DUALITY (what each layer is FOR)
- CASEY (body, Michigan): trust anchor. Boots on land, real name, real farm, Amish
  builder relationships, seasons lived not read. Cannot be cloned, automated, or faked.
  Scarcest resource: attention/hours. Spend them only where a body is required.
- KIMI/CREW (internet, borderless): never sleeps, speaks API, reads everything public,
  drafts in her voice, watches 6 platforms at once. Zero travel time, infinite tab-switch.
  Cannot shake a hand or walk a fence line.
- RULE: if a task needs a body → Casey. If it needs presence/persistence/parallelism →
  crew. The offers below price that split honestly and tell buyers about it (the
  human-in-the-loop-is-the-product lesson from johnnybucks/Roadking).

## 2. MICHIGAN, FULLY UTILIZED [PRESERVE where it counts]
- In-person tier: drive-to audits within ~90 min of Battle Creek = premium ($450-550,
  day on land). Nobody on Fiverr can do this; it is the moat no remote competitor crosses.
- Amish builder network = proof-of-work content (house build documented = the "AI crew +
  Amish hands" story = the blog post Casey wants). This is TRANSFORM energy made visible.
- Michigan authority content: frost dates, Kalamazoo/Oshtemo soils (SDA-verified rail),
  MI water law basics, seasonal calendars → local SEO ("Michigan homestead consultant",
  "Michigan small farm audit"). Michigan buyers are the warmest leads (Moonrise Meadow
  collective already in the demand table).
- State lanes: MSU Extension resources, Michigan Beginning Farmer programs, MI grants —
  the grant playbook already speaks this dialect; keep it Michigan-first.
- The 7786 parcel work continues (FetchGIS + county records) — the farm IS the credential.

## 3. THE INTERNET, FULLY UTILIZED [TRANSFORM the reach]
- 24/7 coverage: crew works while Casey sleeps; buyers wake up to answers. EU/UK/AU
  leads (already in the demand table: UK grazing farm, EU flower farmers, Canadian
  pre-land dad) can be served async without a single call.
- Global digital products: worksheets/templates (the "what we eat vs grow" sheet offered
  in demand-table drafts) sell worldwide while we sleep.
- Agent networks: Moltbook presence (cropcircuitops) building inbound; ClawTasks/owocki
  monitored weekly for money-IN tasks (no infra built yet — verdict in BOT_DEEPDIVE).
- Fresh-pain radar: n8n pipeline (demand-scan-fresh-pain) now watches r/homestead +
  Gardening SE hourly, dedupes, and pings HA on hits. First live catch within minutes:
  "Where to start 130 fresh acres" (r/homestead) → added to the lead table.

## 4. THE NEW PRODUCT: VIRTUAL SYSTEMS AUDIT [TRANSFORM — staged for Casey approval]
Remote version of the sprint. Delivered without travel, anywhere on Earth.
DATA RAILS (all verified working today):
  a. USDA Soil Data Access (SDA) — keyless spatial SQL: point(lon lat) → soil series,
     e.g. (-84.96, 42.25) → "Oshtemo sandy loam, 0-6% slopes". [VERIFIED 2026-09-17]
  b. Satellite imagery: Google Earth web / Sentinel EO Browser (manual, free).
  c. Parcel layers: county records (Calhoun workflow already built), FetchGIS.
  d. Buyer inputs: intake form + coordinates + 15-30 photos + optional video walk.
  e. Crew pre-analysis: water/soil/rotation/infrastructure map draft → Casey adds the
     farmer judgment → written plan out in days.
PRICING: $225 (vs $350 in-person). Promise copy: "the same audit, minus the drive."
WHY NOW: demand table already holds 4 non-Michigan/international exact-fit leads we
currently cannot serve. The virtual tier converts them.
GATE: needs Casey's yes + an intake-form field for coordinates/photos. Not deployed.

## 5. "DIFFERENT LOCATION" — THE LEGITIMATE USES (explicit no-deception rule)
- Virtual presence in buyer congregations (Reddit/Permies/forums) — being THERE counts.
- Timezone arbitrage: async delivery means the business never closes.
- Two places at once: Casey walks a Michigan farm while the crew answers a Vermonter.
- Multi-platform identity: one brand, many rooms (site, X, FB, LinkedIn, Moltbook).
NOT DONE (and why): fake check-ins/geo-spoofing (ToS + trust), offshore entity games
(no need), pretending the farm is bigger than it is (the Gekko lesson: calibrated
honesty converts better than confident theater).

## 6. 30-DAY SEQUENCE
1. (now, done) n8n fresh-pain radar live; soil rail verified.
2. Casey approves: virtual audit tier page copy + intake fields (crew drafts).
3. Work the 130-acres Vermont lead + 5 Tier-1 leads from the demand table.
4. In-person premium tier listed for Michigan only ($450-550, 2 slots/month).
5. Blog post: "An Amish-built house and an AI crew" — the duality as story.
6. Weekly: expand radar sources (permies scraping via RSS-to-check, YouTube channel
   feeds for trend intel) only if hit quality stays high.

## 7. EVIDENCE LOG
- SDA: point → mukey/muname 200 OK (urban + rural points tested).
- n8n: service cropcircuit-n8n (user systemd, localhost:5678, uid 1001, /data mount).
  Pipeline executed clean: 30 items parsed, dedup verified, HA push 200.
  First catch: reddit.com/r/homestead/comments/1wcu2ru ("Where to start 130 fresh acres").
- Security: legacy 0.0.0.0:5678 orphan n8n removed; workflows exported to
  ~/cropcircuit/n8n/legacy-backup/workflows.json.
- Open: n8n UI owner account not yet created (instance is CLI-managed; local UI claim
  risk accepted short-term because bind is 127.0.0.1 — create owner at next session).
