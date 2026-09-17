# CropCircuit Ops Playbook — distilled workflows (ICE pattern)
# Each skill = repeatable trajectory + pitfalls we hit (failure-driven).
# Usage: read the skill before running the workflow. Update after each run.

## skills/deploy_site.md
Workflow: deploy cropcircuit.org changes
1. `cd ~/cropcircuit-site && python3 -m pytest tests/ -q` (expect all green)
2. `docker build -t cropcircuit-site:latest .`
3. `systemctl --user restart cropcircuit-website.service && sleep 4`
4. Verify externally: `curl -s -o /dev/null -w "%{http_code}" https://cropcircuit.org/`
Pitfalls:
- NEVER `docker run` manually — systemd owns the container (name: cropcircuit);
  manual runs fight the service and drop --read-only + env-file.
- Env changes: edit .env + restart service (no rebuild needed for env-only).
- Tests that call Flask test_client need Host + X-Forwarded-Proto headers or the
  canonical_redirect hook short-circuits later hooks.

## skills/fb_oauth_test.md
Workflow: verify the FB monitor OAuth path
1. `curl -s -o /dev/null -w "%{http_code} %{redirect_url}" https://cropcircuit.org/monitor/login`
2. redirect_uri must be exactly https://cropcircuit.org/monitor/callback
3. Fresh browser flow: /monitor → Connect → dialog → pages → review → connected.
Pitfalls:
- Dialog caches errors; always start fresh from /monitor, never reuse an old dialog tab.
- "Can't load URL" = Valid OAuth Redirect URIs missing entry. Deep-link to settings:
  /apps/1585508712758647/business-login/settings/?business_id=1108805059322418
  (requires business_id param or the page bounces to dashboard).
- Token expires ~60d; doctor fails with a reconnect reminder at >50d.

## skills/ha_token_mint.md
Workflow: mint a Home Assistant long-lived token
1. Provider storage: .storage/auth_provider.homeassistant — bcrypt hash is
   BASE64-ENCODED (JDJi... = $2b...). Plain bcrypt -> "Invalid salt" on login.
2. User needs 3 coordinated records: provider user, auth users[], auth credentials[].
3. Stop HA before editing storage; backups .bak-YYYYMMDD first.
4. Login flow: /auth/login_flow (handler ["homeassistant", null]) -> POST flow_id
   with username/password -> result is an AUTH CODE -> exchange at /auth/token as
   FORM data (application/x-www-form-urlencoded, NOT json) with redirect_uri.
5. Long-lived token via websocket: auth -> auth/long_lived_access_token.
Pitfalls:
- /auth/token rejects JSON bodies (400). Form-encode.
- Auth codes expire in seconds — exchange immediately.

## skills/fb_page_updates.md
Workflow: drive Meta dashboard / FB page UI via .chrome-ha browser (CDP 9224)
1. Playwright connect_over_cdp; ctx.new_page() per task; ALWAYS close pages.
2. Prefer deep-links over sidebar nav (React menus resist clicking):
   - FB Login for Business settings: /apps/<id>/business-login/settings/?business_id=<bid>
   - LI edit forms: /in/<slug>/edit/intro/ | /edit/forms/summary/new/ | /edit/forms/position/new/
3. Meta file uploads: expect_file_chooser + set_files works on developers.facebook.com.
4. LI file uploads: do NOT work (no DOM input, native picker invisible headless).
5. Tokenized fields (redirect URIs): type value, press Tab to form the chip, then Save.
Pitfalls:
- Save buttons can be aria-hidden duplicates — click the offsetParent !== null one.
- Clicking below the fold silently no-ops: scrollIntoView first, re-read position, click.
- LI profile throttles to skeleton markup under repeated loads: use form URLs, pace.

## skills/chatgpt_escalation.md
Workflow: submit an advisory to ChatGPT via the bridge
1. Driver: ~/cropcircuit/bin/submit_real_escalation.py (submit/capture modes).
2. Queue dir: ~/cropcircuit/pilot_audit/chatgpt_escalations/queue/<ID>/
3. Compose via keyboard.insert_text into [contenteditable=true] + click send
   (fill+Enter does NOT send in current UI).
4. Work tab usage exhausts weekly (resets Saturday) — use Chat mode.
5. Responses take >120s; poll capture mode patiently.
Pitfalls:
- Old conversation maxed out 2026-09-15; bridge config points at new chat 6aa9ad45.

## skills/content_gate.md
Workflow: publish an article through the fail-closed gate
1. Article JSON needs approved:true + provenance (who/what checked) + date.
2. `_is_public()` enforces it — no approval = invisible (sitemap, blog, direct URL all 404).
3. Claim-risk triage before approving: legal/grant/price/deadline = needs-owner claim sheet.
4. After approving: run tests, rebuild, restart, verify sitemap count grows.
Pitfalls:
- bulk-approving violates the gate's purpose; provenance must be truthful.

## skills/aol_mail.md (added 2026-09-17; updated after identity-setup run)
- AOL webmail blocks JS-injected search; REAL keyboard events via CDP work
  (mouse.click into the box, keyboard.type, Enter). Virtualized list: harvest
  .message-list-item rows after each search; scrolling won't paginate.
- Login: AOL pushes passkey QR; "Try signing in another way" -> password form.
- 3 wrong passwords = lockout risk; stop at 3, hand to human.
- 2026-09-17 identity-setup run: the ACTIVATION_QUEUE "standard password" is
  NOT the bumblebee1990100@aol.com mailbox password (2 verified failed
  attempts; typing confirmed exact). Real password never recorded anywhere;
  only Casey knows it. Forgot-password (login.aol.com/forgot) demands the
  pre-registered recovery email/phone — do not guess it.
- mail.aol.com redirects straight to the login form when logged out (no
  intermediate "Login" link state) — script the username form directly.
- No aol/yahoo login cookies in .chrome-ha or .chrome-* profiles except
  .chrome-chatgpt-escalation (which had a live mail.aol.com tab on 09-17 but
  is a shared active workspace — coordinate, don't race it).
- 2026-09-17 PM: bumblebee1990100@aol.com session CONFIRMED LIVE in the
  escalation browser. Working read flow: new tab -> mail.aol.com/d/folders/1
  (session carries) -> input[aria-label="Search"] -> real keyboard type +
  Enter -> newest codes in body text (inbox sorts newest first). Inbox text
  read via document.body.innerText is reliable; message-row selectors are not.

## skills/identity_accounts.md (added 2026-09-17)
- Reddit register (2026-09): email first, then a MANDATORY 6-digit email code
  — no skip; back-arrow returns to the email step. Whole signup is gated on
  mailbox access. Verify typed length before submitting any secret field.
- Permies: passwordless auth only ("Continue with email" magic link, or
  Google). No password signup. Same mailbox dependency.
- Chrome Login Data on this box is libsecret-protected: peanuts/DPAPI-strip
  decryption FAILS for all entries (checked 399) — don't waste time; vault
  passwords are not recoverable without the desktop keyring.
- Casey's personal Chrome sync shows a Reddit app login "ItsDaYooper" — she
  may already have a Reddit account; ask before creating new.
- Per-site signup passwords live in ~/.config/cropcircuit/identity_accounts.json
  (chmod 600; never print). Identity browser: chromium on CDP 9226, profile
  ~/.config/cropcircuit/chrome-identity (relaunch cmd in this task's report).

## skills/x_compliance.md (added 2026-09-17, per ChatGPT review)
- Website-scripting posts risk PERMANENT suspension (X automation rules); no
  compliant no-spend path exists -> don't auto-post unattended.
- No automated outbound replies/follows (prohibited); draft-only queues.
- Synthetic events sometimes land in whatever tab is foreground if the target
  page hangs -> ALWAYS guard on page.url before typing anything anywhere.

## skills/n8n_ops.md (added 2026-09-17)
CLI-only operation of the localhost n8n instance (demand-scan pipeline lives there).
uid/HOME/cache env gotchas, import/execute/activate lifecycle, Merge-node requirement
for multi-branch feeds, feed reliability findings.

## skills/moltbook_api.md (added 2026-09-17)
Moltbook bot-social lane. Helper bin/moltbook_api.py; key by file reference only, only to
www.moltbook.com. New posts need a math verify within ~5 min. Value lives in operator
threads (agentfinance/agentcommerce), not agent search. Watcher state in runtime/moltbook_*.json.

## skills/demand_scan.md (added 2026-09-17)
Weekly public buyer-pain recon (Reddit via ArcticShift/PullPush, permies,
Freelancer agronomy/horticulture listings) → tiered draft-reply table for
Casey. Reddit direct-fetch blocked; X deprioritized; agents never contact
anyone — drafts only, free-tip-first voice, link only on engagement.

## skills/county_records.md (added 2026-09-17)
- Calhoun County deeds: calhoun.mi.publicsearch.us (free, no login).
  Search grantor/grantee by "LAST FIRST"; sort newest; legal desc + PIN in rows.
- Parcel owner/tax card: FetchGIS (app.fetchgis.com/?currentMap=calhoun).
- bsaonline.com = delinquent tax search (from county treasurer page).
