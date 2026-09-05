# POLLINATION PLAYBOOK — v1
## Crop Circuit doctrine for ❋→⟡→✺→◉→⚘ at scale
**Adopted 2026-09-05. Sources: machine recon (Kimi), strategy (ChatGPT), typed
calculus (FLORAL_CIPHER v2). Canonical — all agents brief against this doc.**

---

## 0. Doctrine

The machine is **reach-rich and trust-poor**. The bottleneck is not audience
size. It is the transition:

    P_internal → P_buyer-facing → first ⟡ → first ◉

With T=0 and ◉=0, more broadcast mostly increases impressions, not the state
variable that most lowers κ_audit.

**Phase rule (hard):**

    before first 1–2 customers ⇒ narrow conversion
    after first 1–2 real ⚘     ⇒ broadcast amplification

Broadcast is strongest after there is something worth amplifying.

κ_audit decomposition (which lever acts on which term):

    κ_audit ≈ κ_0 + κ_no-proof + κ_no-conversations + κ_operator-friction

| Lever | Acts on |
|---|---|
| FB repair | reach only — none of the three loss terms |
| Warm-list conversion | all three: ❋→⟡→✺→◉→⚘ |

---

## 1. Asset recon (2026-09-05)

| Asset | State | Play |
|---|---|---|
| Email (SENDER_EMAIL, IMAP) | LIVE, auditable, unsaturated (23 sends ever) | **Primary conversion rail** |
| Warm leads | closer_send_sheet (10) + coop signals (3+) | The narrow Garden — all initial effort |
| LinkedIn bridge | healthy :8787, 153 posts history, 47 queued (Aug 21 vintage) | Maintenance only: 1–2 profile posts/wk + named-prospect DMs |
| 47 vintage queued LI posts | Untargeted product spam, stale | **Do not auto-drain** — positioning review first; noisy channel raises κ |
| Facebook page | DEGRADED (credential_resolution_failed) | Zero strategic attention pre-◉₁; fb-doctor timer left running as-is |
| Sales-pipeline/worker timers | alive (cropcircuit-* units) | Left running; content strategy per phase rule |
| batch_outreach_2026-08-06 | 6 weeks stale | Source material for re-drafting, not for resending as-is |
| Denylist/suppression | small, healthy | Enforced on every ❋ send (v2 §5) |
| Proof stock | deep internal docs, zero buyer-facing ⚘ | Convert (§2) |

**Channel ranking by activation efficiency**
F(u) = Pr(meaningful state transition | u) ÷ Casey attention consumed:

    F_warm-email > F_warm-linkedin ≫ F_cold-broadcast > F_FB-repair

---

## 2. The proof conversion: Annotated Audit Preview

Build ONE artifact (not a case-study library): **"Small Farm Systems Audit —
Annotated Preview"**, 1–2 pages. Proof of METHOD, not customer outcome.
No testimonials, no invented ROI, no client-success claims.

Structure (Input → Diagnosis → Deliverable):
1. **System snapshot** — enterprise type, scale, current workflow, constraint
2. **What the Audit notices** — 3 friction points, one systems map, one
   prioritization table
3. **What the buyer receives** — "fix now / measure next / ignore for now" +
   30-day action sequence

Source material: own farm operation or a clearly-labeled composite. v2 typing:
P_domain-docs → P_buyer-readable-sample is VALID; P_domain-docs →
T_customer-proof is FORBIDDEN until a customer exists.

**Deployment (reply-stage only, never first-touch broadcast):**
- First-touch ❋ stays light: *"I'm opening 5 founding seats for a $95 Small
  Farm Systems Audit. I made a one-page sample showing exactly what the output
  looks like. Want me to send it?"* → "yes" → send Preview (micro-commitment)
- LinkedIn DM on engagement; one pinned/featured LI post as passive
  corroboration
- Budget: 0.75–1.0 agent-hour

---

## 3. Lead state machine

States: `READY → POLLEN_SENT → POLLINATED → INTERESTED → SEED_SENT → PAID →
(CLOSED | FOLLOWUP)`

Transitions (cert-guarded):
- `READY → POLLEN_SENT` only on **successful send receipt**. drafted(❋) ≠
  sent(❋). No narration-counted sends (v2 §8).
- `POLLEN_SENT → POLLINATED` only on **external reply** (the measurement
  event, via IMAP/LinkedIn witness). No reply = no ⟡.
- Reply triage — four classes only:
  - **No** → suppress, close (log to outreach_log + suppression list)
  - **NotNow** → one scheduled follow-up, leave active queue
  - **Interested** → send Annotated Preview + one qualifying question
  - **BuyReady** → prepare ✺ immediately

---

## 4. Agent roles

**Kimi — execution clerk:** pull next 2 warm leads → draft personalized ❋ →
denylist check → send after approval → log receipt → watch IMAP → classify
reply → draft next response → prepare ✺ → update seats ONLY on certified
payment → build Casey's daily review packet. May state only certifiable
machine facts. Never: testimonials, capacity claims, outcomes, invented context.

**Codex — implementation (≤1 sprint):** one lead-state schema; one inbox
classifier; one approval queue; one send/log path; one payment-confirmation
handler; one seat-decrement rule; one exception report. NOT this sprint:
Facebook.

**Casey — social authority, 15 min/day, exactly three approvals:**
1. Today's 2 outbound ❋
2. Replies crossing a commercial boundary (custom scope, nonstandard promise,
   nonstandard price, deadline commitments, anything changing the fixed offer)
3. The ✺ Seed for an interested lead

Goal: 15 min → 2 outbound approvals + qualified exceptions only. Casey does
not answer every DM.

**ChatGPT — strategy/memory/finance:** doctrine reviews, market research,
financial read integration, objection analysis after the first 6 ⟡.

**Manager (automaton) — certifier:** authoritative payment event → ◉_earned,
n_✿−1, LeadState=PAID, Intake=ReadyToSend — one transaction; exception on any
partial failure; never silent retry by inventing ledger state.

---

## 5. Seed protocol

    ✺ = Seed(buyer, offer=SmallFarmSystemsAudit, price=$95, seat, checkout, terms)

Kimi drafts; Casey approves; Kimi sends the approved text verbatim. Fixed
form: *"You're a fit for one of the founding seats. It's $95 and includes
[fixed deliverable]. Here's the checkout link. Once payment confirms, I'll
send intake and reserve your seat."* No negotiation unless the buyer raises
an exception (→ Casey's approval surface).

**Payment certification (machine-hard):**
- ALLOWED: authoritative checkout/webhook confirmation → ◉_earned
- FORBIDDEN: "I paid" email → ◉; checkout-page visit → ◉; analytics event →
  ◉; promising conversation → ◉ (v2 §8 witness types)

After payment: `Paid → IntakeSent → WorkScheduled → ⚘`; delivery evidence →
`⚘: Cert[Deliverable]`. Only then does customer-facing proof stock exist.

---

## 6. The ≤4-agent-hour build

| Hour | Deliverable |
|---|---|
| 1 | Annotated Audit Preview artifact |
| 2 | 13 warm leads normalized into state-machine queue |
| 3 | IMAP reply detection → classifier → Casey approval digest |
| 4 | Approved-Seed → send/log → payment witness → seat decrement + Harvest cert |

Do NOT build: a CRM, channel repair, automated persuasion. Build one narrow
conveyor: 13 warm Gardens → ❋ → ⟡ → ✺ → ◉ → ⚘.

---

## 7. Control target (72 hours)

**Objective: 6 externally-evidenced Pollinations — not 5 sales.**

    2 targeted sends/day + 1 follow-up/day, every event cert-guarded.

Why: the first thing that lowers κ_audit is not revenue alone — it is
learning whether the offer survives contact with actual Gardens. Six ⟡
yield either C+T+P (a sale) or certified information (objections). Broadcast
cannot produce either as efficiently at T=0.

Metrics (dashboard for the daily packet): sends w/ receipts, replies (⟡
count — the 72h target), triage class distribution, Seeds approved/sent,
◉_earned (witness-certified), n_✿ remaining, Casey minutes consumed vs 15
budget, κ_audit lever movements (proof shipped? conversations happening?
friction reduced?).
