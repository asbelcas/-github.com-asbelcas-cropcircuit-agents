# Crop Circuit LLC — Launch Packet (Michigan)
**Prepared 2026-09-05 by the agent workforce. Status: READY FOR CASEY'S 3 STEPS.**

Decision: Michigan single-member LLC. Filing $50, annual statement $25 (due
Feb 15), no Michigan franchise tax. Registered agent: Casey (Michigan street
address required — her home address becomes public record; at this scale that
is normal, and the address can be changed later if she moves or hires an RA
service).

Entity: **CropCircuit Operations LLC** — the name already chosen in the prior
launch plan (workforce/src/app/entity_launch_packet.py, status "planned";
never filed). Fallbacks if taken at filing time:
1. Crop Circuit Farm Systems LLC, 2. Crop Circuit LLC.
The LARA filing system checks name availability in real time at submission —
the definitive check, no pre-search needed.

---

## STEP 1 — File Articles of Organization (CASEY, ~10 min, $50)

1. Go to https://mibusinessregistry.lara.state.mi.us and sign in (or create
   an account with your email).
2. Choose "File Articles of Organization" (domestic LLC). Use the online form
   (form CSCL/CD-700).
3. Enter exactly:

| Field | Value |
|---|---|
| Entity name | CropCircuit Operations LLC |
| Entity type | Limited Liability Company |
| Purpose | Farm systems consulting and digital product sales |
| Registered agent | Casey Armstrong (herself) |
| Registered office | [her Michigan home street address — public record] |
| Organizer | Casey Armstrong |
| Management | Member-managed |
| Duration | Perpetual |
| Members at formation | 1 (Casey Armstrong, 100%) |

4. Pay $50 by card. Standard processing: a few business days (approval email
   arrives; Articles come back stamped as PDF).

## STEP 2 — Get the EIN (CASEY, ~5 min, free)

1. https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online
   (Mon–Fri 7am–10pm ET).
2. Entity type: Limited Liability Company → single member → state Michigan.
3. Responsible party: Casey Armstrong, SSN required — **enter it herself;
   never share it with any agent or store it in this repo.**
4. Submit → EIN issued instantly on screen. Download/save the PDF (CP-575).

## STEP 3 — Open the business bank account (CASEY, ~30 min at a branch)

Recommended: **Advia Credit Union business checking** (existing membership,
keeps business money beside personal for easy transfers, local branch).
Bring: stamped Articles of Organization, EIN letter (CP-575), government ID.
Alternative if Advia's business accounts are weak: Relay (free online business
banking).
Opening deposit can be small ($25–$100). **This separation is the point:** the
ChatGPT finances audit showed household and business money mixing — the
business account ends that.

---

## AGENT WORKFORCE — everything after Step 3 lands (no Casey time needed)

1. Update Gumroad: payout settings → business bank account (Casey logs in
   once, or authorizes a supervised browser session).
2. Manager config: add `business_account_note` so sale records tag
   ◉_earned/◉_liquid (business) distinctly from household money.
3. Bookkeeping scaffold: runtime ledger file for business ◉ per v2 §7
   (◉earned on Gumroad webhook witness; ◉liquid on bank settlement witness —
   the cert-guard witness discipline applies to money too).
4. Compliance calendar: annual statement reminder (Feb 15, $25) via HA
   notification; tax-year summary prep for the Schedule C.
5. Website/payment pages: update footer/contact to "Crop Circuit LLC" once
   the entity is stamped.

## Cost & timeline

| Item | Cost | When |
|---|---|---|
| Articles of Organization | $50 | Step 1 |
| EIN | $0 | Step 2 (same day) |
| Bank account | $0–$25 opening | Step 3 (within a week) |
| Annual statement | $25/yr | every Feb 15 |
| Registered agent | $0 (self) | ongoing |
| **Total to exist properly** | **~$50 + one afternoon** | |

## What the agents deliberately did NOT do

Not distrust — legal design: a state filing attested under her name, an IRS
SSN entry, and a card payment must be performed by the human they legally
belong to. Everything else — research, worksheets, templates, banking plan,
post-formation automation — is done or ready.
