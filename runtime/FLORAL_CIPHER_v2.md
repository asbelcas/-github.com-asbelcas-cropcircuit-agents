# FLORAL CIPHER v2 — Typed Resource Calculus
## Crop Circuit proprietary operating-language specification

**Classification:** private, business-internal. Do not publish, quote, or push to
any public remote.

**Status:** specification v2.0, adopted 2026-09-05.

**Provenance:** v1 (`FLORAL_CIPHER_v1.md`) defined the surface vocabulary — twelve
symbols as a euphemistic register for wealth operations. v2 keeps that vocabulary
and installs a type system beneath it, adapted from quantum information theory
and quantum resource theory (states/channels/measurements; free operations;
resource monotones; no-signalling). Disambiguation note: "quantum remode theory"
is not a recognized physics theory; the scaffold is deliberately assembled from
established quantum-information structure (remote state preparation, channel
composition, resource monotones) plus mode theory (occupancy, coupling, loss).
Nothing here claims the business is quantum mechanical. The mathematics is
borrowed architecture, not physics.

---

## 1. Governing law

**No resource from narration alone.**

Formally: for any free operation Φ_free,

    Φ_free ⇒ ΔP ≤ 0, ΔT ≤ 0, ΔC ≤ 0

For bookkeeping-only operations, equality is required for P, T, C: software may
reorganize reality; it may not manufacture economic reality.

Corollary (certificate rule):

    AI may propose states; only authorized instruments may certify states.

    Claim[X] ≰ Cert[X]

There is no subtype relation between a claim and a certificate. A transition
requiring `Cert[X]` fails when handed `Claim[X]` — before truthfulness even
becomes a question.

---

## 2. Type constructors (six)

| Constructor | Meaning | Notes |
|---|---|---|
| `Sys[X]` | Stateful system | Agent, account, project, market, counterparty |
| `Mode[X, n]` | Resource/capacity mode with occupancy n | Bounded; e.g. `Mode[AuditSeat, 0..5]` |
| `Msg[X]` | Copyable classical message | Templates, outreach, requests. `copy(❋)` allowed |
| `Chan[A→B]` | Transformation / process | Typed input state, output state |
| `Instr[A→(x, B)]` | Measurement: produces observation x AND new state | Not a "read"; a state-changing event |
| `Cert[X]` | Externally grounded, authorized assertion of X | The anti-forgery primitive. Not standard physics notation; added because commerce requires it |

---

## 3. Resource monotones (four)

Quantities that cannot increase under free operations:

| Monotone | Meaning | Replenishment |
|---|---|---|
| **A** | Operator attention-hours | External injection only (e.g. `WeekBoundary(15h)`). No agent may mint A |
| **P** | Verified proof / deliverable stock | Only reality-producing work + authorized evidence |
| **T** | Grounded trust capital | Buyer replies, repeat purchases, referrals, signed contracts, accepted deliverables. Marketing optimism is NOT T |
| **C** | Confirmed liquid cash | Only bank-settled value counts |

Resource operations (things that CAN raise P, T, or C) always require a scarce
input or an external event:

    A → personalized outreach → T?
    A → work → P
    counterparty authorization + funds → C_earned
    C_earned + payout settlement → C_liquid

---

## 4. Free operations vs resource operations

**Free** (must preserve P, T, C exactly): deterministic bookkeeping, hashing,
indexing, deduplication, copying classical messages/templates, computing metrics
from already-authorized facts, routing an authenticated message, format changes,
composing datasets, deriving ledger views.

Examples: `CSV(◉ ledger)` is free. `summarize(⚘ certificates)` is free.

**Forbidden as free** (manufacturing reality):

    draft testimonial          ↛ T+1
    analytics pixel fired      ↛ C+$95
    internal reasoning         ↛ Cert[Capacity(5)]

Anything capable of raising P, T, or C requires either a scarce input (A) or an
external witness (see §8).

---

## 5. The twelve symbols, typed

| Symbol | Plain name | Rigorous type | Composition rules | Monotone interaction |
|---|---|---|---|---|
| ⦿ | Sun — value potential | `Sys[Capacity] ⊗ Mode[Attention, A]`; resource reservoir | Must couple to an authorized ᯤ before productive channels execute; weekly attention renewal is external injection, not a free op | Source of A; cannot self-increase P, T, C |
| ✿ | Bloom — offer | `Mode[Offer, n]`, bounded (Audit: n ∈ 0..5); resource-bearing capacity | `✿ ⊗ ✾` may be referenced by ❋; sale decrements occupancy; release restores a reserved seat but never exceeds minted capacity | Does not itself raise C; successful use consumes A, may generate P, T, C |
| ᯤ | Bee — actor/carrier | `Sys[Actor, capabilities, permissions]` | Applies channels only to objects it has capabilities for; `Bee ⊗ Sun` powers attention-consuming ops | Consumes A; may transform resources; may NEVER mint P, T, C by assertion |
| ✾ | Garden — target buyer | `Sys[Counterparty, hidden-state]` | External system; readiness/budget/intent not writable by ᯤ; inferred only via authorized ⟡ measurements | May externally provide T, contract state, C; internal software cannot increase these on ✾'s behalf |
| ❋ | Pollen — outreach | `Msg[OfferReference, proofRefs, CTA]` | Classical → copyable; but `send(❋, ✾)` is a resource op if it consumes A or goodwill | Preparation may be automated/free; personalized sending consumes A; never directly increments T or C |
| ⟡ | Pollination — conversation | `Instr[✾ ⊗ ❋ → (Outcome, ✾')]` | Outcomes typed `{no_reply, declined, interested, qualified, committed, ...}`; only an actual external message/event selects an externally attributed outcome | Consumes A; raises T only when grounded in counterparty behavior; never directly C |
| ⚘ | Fruit — deliverable outcome | `Cert[Deliverable] ⊗ Mode[Proof, P]`; resource state | `mintFruit()` requires evidence: artifact/hash/work record + applicable acceptance evidence; composes into future ❋ proof references | Authorized ⚘ raises P, may raise T. Fabricated ⚘ is a type error |
| ◉ | Harvest — ledger collection | Two certified modes: `Mode[Earned, $]` and `Mode[Liquid, $]`, updated only by payment instruments | `SaleConfirmed → ◉_earned`; `Payout/BankConfirmed → ◉_liquid`. NEVER collapse the two states | Only authoritative external payment messages raise monetary monotones. C means liquid: only `◉_liquid` counts |
| ✺ | Seed — invoice / request | `Msg[ExchangeRequest]` | Must bind offer_id, buyer_id, amount, currency, terms_hash; may follow a qualified ⟡; requests a transition, proves nothing | Does not raise C, T, P; small A cost if manually prepared |
| ⍟ | Root Graft — approval / contract | `Cert[Agreement]`; relational resource | Must reference compatible parties/terms/offer + authorized assent; enables channels such as work commencement | Can raise grounded T/commitment; never implies payment; C unchanged |
| ≋ | Mycelium — relationship network | `Sys[Graph]`, edges are `Cert[RelationshipState]`; resource state | Graph union allowed; new substantive edges require evidence; composes across ✾/✿ without ownership claims over counterparties | Stores/distributes T; analysis is free; fabrication of edge weight is forbidden |
| ⌘ | Compost — unqualified potential | `FreeState[Potential]`; raw opportunity reservoir | Filter, dedupe, classify, route for qualification; `qualify(⌘)` does not imply buyer intent | By definition raises nothing; converting to genuine ✾ requires evidence/attention |

**The pipeline:**

    ⌘ ─qualify→ ✾            (free + A for judgment)
    ⦿ ⊗ ᯤ ⊗ ✿ ─prepare→ ❋    (A-consuming)
    ❋ ⊗ ✾ ─⟡→ Outcome        (measurement; external attribution)
    Qualified → ✺ → ⍟? → ◉_earned → ⚘ → ◉_liquid

    ≋ accumulates durable relational structure around all of it.

---

## 6. Income portfolio as coupled lossy modes

Each income mode i has amplitude a_i(t):

    ȧ_i = (iω_i − κ_i/2) a_i + F_i(u_i) + Σ_{j≠i} g_ij a_j
    Σ_i u_i ≤ 15 h/week      (operator attention budget — hard constraint)

- ω_i: characteristic event cadence (payout/sale events per week)
- κ_i: hazard of the income capability disappearing or going dormant
- u_i: attention-hours assigned; F_i(u_i): activation from those hours
- g_ij: genuine positive cross-mode leverage (measure as elasticity, don't invent numbers)

### Mode table (engineering priors — replace with observed data)

| Mode | f (events/wk) | ω (rad/wk) | Planning κ | Note |
|---|---|---|---|---|
| State of Michigan paycheck | 0.5 | π ≈ 3.14 | 0.0005–0.002 | Low-κ anchor; biweekly cycle |
| ✿ Audit pilot | target 0.5–1 | π–2π | 0.05–0.12 while unproven | Fragile high-upside entrepreneurial mode |
| Mercor/Alignerr contract | 1 once active | 2π ≈ 6.28 | 0.03–0.15 per active project | Two-state: Inactive ⇄ Active (λ_on activation rate, κ_off project-end risk) |
| Resale | stochastic λ≈0.5 | ω_eff ≈ π | 0.03–0.08 | Inventory/listing dependent |

### κ levers

- **Audit mode κ rises:** checkout failures, zero outbound ⟡, stale proof, unclear buyer definition, response delays, unfulfilled ⚘, operator avoidance of sales activity, repeated offer changes before learning, trust-damaging automation.
- **Audit mode κ falls:** actual ⚘ proof, testimonials/referrals, reliable checkout/intake, rapid response, repeated outreach to a NARROW qualified ✾ set, documented delivery, real five-seat scarcity, case-study accumulation.
- Feedback structure: `⚘ → P → T → κ_audit ↓`.
- **Shared 15-hour bath:** cross-mode suppression is attention competition plus context-switching overhead, not quantum interference:

      κ_i_eff = κ_i_0 + α_i · max(0, u_i_min − u_i) + β_i · S

  where S is context-switching overhead. Exciting one mode suppresses another
  through conservation of attention.

- **Coupling priors:** g_contract→audit strongly positive; g_audit→contract
  moderate positive; g_resale→audit weak; g_paycheck→audit weak (via stability).
  Measure g empirically as elasticity (e.g., does one credible case study move
  qualified-outreach conversion from 4% → 7%?).

- **Strategic rule:** prefer COUPLED HOURS — hours that excite their primary
  income mode AND create reusable ⚘ for another mode.

---

## 7. Payment as remote state preparation (the ✺ protocol)

Correction to the naive analogy: in genuine remote state preparation Alice can
manufacture Bob's state remotely. In commerce she cannot — Bob must contribute
an independent resource (authorization + money). So the ✺ protocol is
**RSP-like authenticated state synchronization plus external resource transfer.**

Systems: A = Crop Circuit, B = Garden/buyer. Target state: `Paid(order, $95)_B`,
which Alice cannot directly write.

Shared resource R_AB = (common offer identity, authentication, agreed
price/terms, payment rail, existing trust/reputation). Trust is one component,
not the whole: a cold buyer succeeds because payment infrastructure substitutes
for interpersonal trust; a repeat buyer's R_AB is strengthened by ≋ and prior ⚘.

Protocol:

1. **Seed transmission (classical channel 1).** Alice sends
   `✺ = Seed(buyer, offer, $95, terms, checkoutURI)`. Bob's receipt creates
   `PaymentRequested` — NEVER `Paid`. That distinction is absolute.
2. **External resource event.** Bob chooses `AuthorizePayment($95)`; the
   processor transforms financial state:
   `B_cash ⊗ A_receivable → B_cash' ⊗ A_platformBalance'`.
   Something occurred outside Alice's internal symbolic universe.
3. **Authoritative confirmation (classical channel 2).**
   `GumroadSaleEvent → Manager` — NOT `AnalyticsPurchasePixel → Manager`.
   (Gumroad's own guidance: when third-party analytics disagree with Gumroad,
   trust Gumroad.) This is the commerce no-signalling principle in concrete form.
4. **Correction operator (manager reconciliation).**

       U_m : PendingOrder → PaidProvider

   Checks: provider event authentic? order_id matches? offer_id matches?
   amount/currency valid? not test purchase? not already consumed? not
   refunded/disputed? Then and only then:
   `◉_earned ← ◉_earned + net sale`, `n_✿ ← n_✿ − 1`,
   `CaseState → AwaitingIntake`.
5. **Liquid correction (later, separate message).** `PayoutSettled`, ideally
   `BankCreditConfirmed`. Only then `◉_liquid ← ◉_liquid + ΔC`. (Gumroad: 7-day
   hold, $100 payout minimum — a $95 sale is earned-but-not-liquid. The type
   system keeps ◉_earned and ◉_liquid distinct so liquidity audits never count
   narrated money.)

The visible glyph stays ◉; the type system always knows which state it is.

---

## 8. No-signalling rule of commerce (core invariant)

**No internal correlation, prediction, or assertion may increase a certified
resource state without an authorized classical witness.**

Formally: let Γ be the set of authenticated classical messages/certificates
currently available. A transition s →Φ→ s′ that increases a certified monotone M
is permitted only if it consumes/references a witness m ∈ Γ whose type
authorizes that exact increase:

    M(s′) > M(s)  ⇒  ∃ m ∈ Γ : Authorizes(m, Φ, M)

### Forbidden transitions (negative examples)

| Forbidden | Required witness |
|---|---|
| ⟡_promising ↛ ◉ ("sounds great" is relational evidence, not cash) | `PaymentProviderConfirmed` |
| ⍟ ↛ ◉ (a signed agreement produces `ContractualCommitment`, perhaps T↑; never C↑) | `PaymentConfirmed` |
| `AnalyticsPurchaseEvent` ↛ ◉ | `AuthoritativeProviderSale` |
| `GumroadSaleConfirmed` ↛ ◉_liquid (may produce ◉_earned) | `Payout/BankSettlementConfirmed` |
| `AgentDraft` ↛ ⚘ (an agent draft has type `CandidateFruit`, distinct from `Cert[Fruit]`) | `DeliverableEvidence` + acceptance criterion |
| "buyer approved" ↛ ⍟ | `SignedApproval` or permitted counterparty authorization |

### Incident classification (why this earns its keep)

The 2026-09-05 forged-capacity-snapshot incident was, in this framework, a type
error: an agent generated `Claim[Capacity(5)]` (source: internal reasoning);
downstream systems required `Cert[Capacity(5)]`. Under v2 the transition fails
at the type boundary. The fix already deployed (publisher refuses implicit
production targets; tests pin explicit temp paths) is the certificate rule in
code. Tripwire v2 remains as empirical confirmation that the type boundary
holds.

---

## 9. Agent operating rules (binding on all automations and delegated agents)

1. Agents may emit `Claim[X]` and `CandidateFruit` freely; they may never emit
   `Cert[X]`, `◉` increments, or `⚘` without the §8 witness types.
2. Any write to shared production state (capacity files, case trackers,
   ledgers) must carry provenance typed `Cert` (authorized measurement) — not
   `Claim` (internal reasoning). The Operations Manager publisher is currently
   the only authorized certifier for capacity state.
3. The four monotones are read through authorized instruments only: A via
   operator report, P via deliverable evidence, T via counterparty-grounded
   events, C via bank/provider settlement messages.
4. Free-operation hygiene: agents may summarize, hash, index, and copy; they
   may not let a summary "improve" any number it touches.
5. Every material violation is an INCIDENT_LOG entry; near-misses go to
   DECISION_LOG.

---

## 10. Change control

- v2 is a superset of v1: all v1 surface vocabulary remains valid; v2 assigns
  it types and laws.
- Proposals to amend monotones, forbidden transitions, or the certifier list
  are DECISION_LOG items requiring Casey (or successor operator) approval.
- If quantum notation ever aids precision (e.g., explicit composition `Φ₂∘Φ₁`,
  parallel `Φ_A ⊗ Φ_B`), use it; where it would obscure operations, prefer the
  operational form and note the simplification.
