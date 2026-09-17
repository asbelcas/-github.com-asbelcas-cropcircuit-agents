# UNKNOWN UNKNOWNS — pre-mortem + assumption inversion + adversary pass
# Built 2026-09-17 (Casey directive). Method: (1) pre-mortem — it's Sep 2027 and the
# operation failed, write the story; (2) every load-bearing assumption, inverted;
# (3) adversary pass by domain. Triaged by probability x impact x detectability.

## VERIFIED LIVE DURING THIS AUDIT
- Linger=yes: user services survive reboot. Power-loss auto-start SAFE.
- Backups rotate daily (17:22 today) but live on the SAME nvme as everything else.
  Disk death = total loss. -> Decision D-01 executed (offsite DR bundle).
- All 8 money/tool/docker layers confirmed running this session.

## THE PRE-MORTEM STORY (abridged)
"Sep 2027: Crop Circuit never got a settled dollar. The leads were real but the replies
went out under a Reddit account that had been silently shadowbanned — six weeks of
sends into the void. The one $350 that did arrive sat in a 21-day PayPal hold while the
buyer's refund clock ran out; the dispute closed against us and the account got
limited. A power flicker killed the disk; the backups were on the same disk. Casey got
pulled away for a month and nobody knew what 'keep the lights on' meant without her.
The AI-farm-advice market flooded with free tools and our $125 tier looked like a
premium wrapper on free. The bridge to ChatGPT died quietly and the strategy context
died with it. Nothing killed us. Everything did."

Every sentence above maps to a real, currently-unguarded failure mode. That is the
point of the exercise: none of these were on any todo list this morning.

## SURFACED UNKNOWN-UNKNOWNS + DECISIONS

### TIER 1 — act now
- UU-1 Shadowbanned outreach (Reddit fresh-account heuristics silently eat posts).
  DECISION: warm-up protocol — first 3 posts are pure-value (no CTA, no link); after
  each post, verify visibility in a logged-out session; only then send lead replies.
  Owner: agent-11 flow. Trigger: any post with 0 views after 2h = pause and diagnose.
- UU-2 PayPal new-service holds (funds held up to 21 days vs refund clock; dispute
  risk with no shipping proof). DECISION: (a) PayPal-hold playbook written; (b)
  confirmation email template sets expectations + offers BTC/stablecoin alternative;
  (c) delivery-evidence packet per ops policy is mandatory from sale #1; (d) track
  holds in the loop ledger. Owner: agent. See PAYPAL_HOLD_PLAYBOOK.md.
- UU-3 Single-disk total loss (site+HA+bots+DBs+backups on one nvme). DECISION D-01:
  non-secret disaster-recovery bundle (MEMORY, ledgers, playbooks, docs — NO secrets,
  NO .env, NO customer data) pushed to the private GitHub repo on every material change;
  restore test quarterly. Secrets stay local per policy. Partial mitigation only —
  a second physical location (Casey's USB drive) remains a Casey task.
- UU-4 Casey-dark >2 weeks (no human in the loop; everything idles; leads rot).
  DECISION: continuity mode doc — what the organism does with zero Casey: keep
  radars/watchers running, keep replies DRAFTED (never sent), hold all approvals,
  monthly HA digest. See CONTINUITY_MODE.md.

### TIER 2 — instrument + watch
- UU-5 Free-AI flood undercuts the $125 tier (probability rising through 2027).
  Decision: differentiation = verification + real-farm ground truth + signed
  deliverables (doctrine already); quarterly price-position review; bandit tests only
  when traffic exists. Trigger: competitor scan in demand radar keywords.
- UU-6 Bridge death (ChatGPT session flagged/UI change kills advisory lane).
  Decision: all bridge outputs archived locally (done — queue dirs); MEMORY +
  doctrine docs make the strategy model-independent. Trigger: bridge failure at next
  use = switch to local Chat-mode alternatives.
- UU-7 Refund-guarantee abuse + chargebacks (bad-faith buyers).
  Decision: intake screening (existing), delivery-evidence packet, track refund/
  chargeback rate in ledger once sales exist; >10% = tighten screening, never drop
  the guarantee (signal value exceeds abuse cost below that rate).
- UU-8 Customer PII in plaintext JSON on a single machine.
  Decision: perms 600 (done); machine-disk encryption is a Casey decision; minimize
  retention (delete intake files on request — already in terms plan).
- UU-9 Model/vendor dependency (this CLI's availability).
  Decision: the docs are the continuity — any capable agent can resume from
  MEMORY.md + playbook README (proven by today's compaction). Annual export of
  ledgers to plain formats (done by design: JSON/MD).

### TIER 3 — accepted risks (documented, not mitigated)
- UU-10 X account takeover via machine compromise (inherent to local sessions).
- UU-11 Crypto invoice volatility (policy: price invoices in USD, convert same-day —
  noted in MONEY docs; binding when first crypto invoice goes out).
- UU-12 Platform ToS drift on agent-operated human-named accounts (bounded by honest
  bios, business-owned mailbox plan, human sign-off; kill-switch = stop that lane).

## SCREENING ADDITIONS (permanent)
- Funding gate F0-F3 now includes: poster spend history (already), PLUS refund/chargeback
  tracking on our own sales, PLUS visibility-verification for any platform post.
- Quarterly pre-mortem rerun (this doc's method) — next: 2026-12-17.
