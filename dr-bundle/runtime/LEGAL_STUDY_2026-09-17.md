# LEGAL STUDY — 2026-09-17
# Organized per Casey directive ("study law"). Focus: what touches Crop Circuit TODAY.
# Sources cited inline. NOT legal advice — flagged decision points go to Casey/ChatGPT.

## 1. DONATIONS / SOLICITATION — the one live gap found
**Law:** Michigan Charitable Organizations and Solicitations Act, MCL 400.271 et seq.
(Act 169 of 1975), enforced by the AG Charitable Trust Section. Registration required
for orgs soliciting/receiving contributions in MI — aimed at CHARITABLE orgs; threshold
$25,000/yr (or ANY paid fundraising). Source: michigan.gov/consumerprotection/charities.
**Analysis:** Crop Circuit is a private business, NOT a 501(c)(3). Act 169's registration
regime doesn't apply to a for-profit — but the real exposure is DECEPTION LAW: FTC Act §5
and the Michigan Consumer Protection Act (MCL 445.903) both prohibit practices likely to
mislead a reasonable donor. A "Donate" button that implies charity (or deductibility) on
a for-profit site is exactly the kind of thing the AG/FTC call a deceptive practice.
**Current state (verified on live site):**
- /support page: GOOD — transparent ("PayPal may show the recipient as Cassandra
  Armstrong — that's Casey"), no charitable claims, "no contribution is expected."
- GAP 1: no explicit non-deductibility statement anywhere.
- GAP 2: footer/nav still label the link "Donate / Support CropCircuit."
**Staged fix (copy proposal, awaiting approval — NOT deployed):**
  Add to /support after the first paragraph:
  "Crop Circuit is a private family farm business, not a charity — contributions are
  voluntary tips, are not tax-deductible, and fund the farm work described above."
  Change footer label from "Donate / Support" to "Support the farm."
**Long-term option (Casey decision):** real deductible donations require a 501(c)(3)
(6-12 mo, ~$1-3K all-in, ongoing filings) or fiscal sponsorship. Not worth it under
~$10K/yr in contributions. Revisit when donations exceed $200/mo for 3 straight months.

## 2. SPRINT CONTRACT / CONSUMER — already strong
**Law:** Michigan Consumer Protection Act (MCL 445.901 et seq.); common-law service
contracts. **Verified:** /terms exists, is scoped to the audit pilot, disclaims
engineering/vet/legal/tax advice, and labels itself an operational draft. GOOD.
**Small additions worth making when Casey next touches the page (staged):**
  a. Refund mechanics: "refund requested → processed within 5 business days" (the promise
     exists; the timeline makes it enforceable-friendly).
  b. Governing law + venue: "Michigan law; disputes resolved in Calhoun County small
     claims where eligible" ($7,000 MI small-claims limit, MCL 600.8401).
  c. Data line: "intake materials are used only to produce your audit and are deleted on
     request" — the privacy page should say the same (verify at next content pass).
  d. Keep all claim-risk language going through the claim-sheet gate (existing skill).

## 3. LAND / BUILD / RIGHT TO FARM — premature until parcel confirmed
**Law:** Michigan Right to Farm Act, PA 93 of 1981 (MCL 286.471–.474): farms following
MDARD's Generally Accepted Agricultural Practices (GAAMPs) get nuisance/zoning
protections. PLUS local township zoning + MI building code govern the dwelling itself
(Amish construction still needs permits; "agricultural building" exemptions exist but a
primary residence is not one). **Status:** the "7786" parcel identity is still unconfirmed
(PROPERTY_TITLE_FINDINGS doc) — RTF/zoning analysis is EMPTY until Casey confirms which
parcel. **Queued questions for township office once confirmed:** zoning district, minimum
lot/frontage for dwelling, well+septic permitting path (health dept), whether a
farm-business registration (Schedule F intent) changes anything, RTF/GAAMP applicability
to the operations planned.

## 4. UNCLAIMED PROPERTY — the LAWFUL "found money" lane
**Law:** Michigan Uniform Unclaimed Property Act (PA 29 of 1995). Treasury holds ~$2B;
owners/heirs can claim in perpetuity; denial → 90-day circuit-court appeal window.
Portal: unclaimedproperty.michigan.gov (free search, no account needed; free account to
claim). National aggregator: missingmoney.com (covers all states).
**Boundary (important):** only money owed to CASEY (or her heirs) is claimable. "Money
nobody will care about" that belongs to strangers = NOT legal, do not pursue. This is the
clean lane.
**Execution status:** portal API is behind Cloudflare Turnstile — bot search correctly
blocked. This is a 5-MINUTE HUMAN TASK (claims require her identity anyway):
  - Search "Armstrong Cassandra" + "Cassandra Armstrong", Battle Creek ZIPs, plus every
    state she has lived in (national missingmoney.com catches all).
  - Also search old employer residuals: State of Michigan payroll, MSU payroll/refunds.
  - Follow-ups already known: ThredUp $144.99 cancelled-order refund (verify posted);
    any utility deposits from prior addresses.

## 5. BUSINESS STRUCTURE — staged decision (money-OUT)
**Law:** Michigan LLC Act (PA 23 of 1993); sole-prop default. An LLC (~$50 filing +
annual statement ~$25) separates farm/consult liability from personal assets. Given paid
audits + farm visitors eventually + the Amish build, the LLC is the right move WHEN the
first $350 lands or the build starts, whichever first. Registered agent can be Casey
(home address) — privacy tradeoff noted. NOT filing now (money-OUT frozen; also cleaner
to batch with EIN (free, IRS) the same week).

## 6. NEW TOOLS SCAN (from this study's sweep)
- **Gumloop** (hosted visual automation, no API-key management): potential complement to
  n8n for Casey-editable workflows; NOT adopted — n8n local already covers it, avoid
  parallel systems (the "things NOT to do" discipline).
- **Stagehand / Browser Use** (AI browser agents): we already have Playwright+CDP skills;
  note for when we need self-healing selectors on the FB/Meta UIs. Watchlist only.
- **Adobe Workfront AI Collaborators / ABAO agent families**: enterprise-grade, irrelevant
  at our scale. Skipped.
- **CourtListener/RECAP, Google Scholar, Cornell LII** (free legal research): added to
  the research toolkit — useful for verifying statutes without a lawyer (what this doc
  just did).

## 7. PRIORITY ORDER
1. Casey approves the /support non-deductibility copy fix (smallest, closes the only
   live gap). 2. Unclaimed-property self-search (5 min human). 3. Confirm 7786 parcel →
   township question list fires. 4. LLC+EIN when first revenue or build date lands.
