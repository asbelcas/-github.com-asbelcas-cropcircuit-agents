# Recovery Runbook

1. Read `OPERATING_POLICY.md`, `CURRENT_STATE.md`, `TASK_BOARD.md`, and the
   relevant recent rows in `DECISION_LOG.md`.
2. Check `../05_APPROVAL_QUEUE.md` and `../manager/approvals.jsonl`; do not
   execute a queued action without its required approval.
3. Verify live state from `../manager/state.json`, `../manager/digest.md`,
   `../manager/service.log`, the case tracker, and active timer status when a
   user-bus-capable session is available. Treat customer data as need-to-know.
4. Confirm the pause flag and budget state before any manager work. Prefer the
   existing deterministic script or test configuration before an agent call.
5. Resume only the next bounded task. Record evidence and material decisions;
   use fictional cases for new workflow/restore tests.
6. On suspected exposure, duplicate processing, payment discrepancy, or delivery
   risk: pause the manager, preserve logs/state, create an approval item, and do
   not contact customers or change payment state.

Backup and retention policy is still awaiting Casey approval. Do not claim a
working backup until a versioned, encrypted backup restoration has passed on
fictional data.

For a genuine unresolved technical blocker, follow the concise queue, browser,
sanitization, response-capture, and stop rules in
`CHATGPT_ESCALATION_BRIDGE.md`; never substitute a new conversation or browser
profile.

## HA long-lived token recovery (verified 2026-09-05, HA core 2026.2.1)

Credential semantics (implementation-dependent — re-verify against the running
HA version before reuse; internals can change across upgrades):

- Home Assistant 2026.2 validates `Authorization: Bearer` tokens as SIGNED
  JWTs, not as the raw token shown in the profile UI or stored in auth state.
  Claims: `iss` = the refresh-token entry's `id`; `iat`/`exp` in seconds;
  signed HS256 with the entry's `jwt_key` (`auth/__init__.py`
  `async_create_access_token` / `async_validate_access_token`).
- The 128-hex `token` field in `/config/.storage/auth` refresh-token entries is
  a REFRESH token (login flow only). Presenting it as a bearer always 401s.
  The 2026-08-17 rotation planted a raw refresh token in every `.env`; every
  HA notification path has been failing with 401 since that date until fixed.
- Refresh-token entries in the auth store require key `token` (not
  `access_token`); `token_type` must be lowercase `long_lived_access_token`;
  long-lived entries use `access_token_expiration: 315360000.0` (10 years)
  and one entry per `client_name`.

Non-secret recovery procedure (token minted via container-side script, never
printed to logs):

1. Stop the container (`docker stop homeassistant`) so the auth store is not
   rewritten mid-edit; the store is a root-owned bind mount writable only via
   the container.
2. Run a python script inside the container that loads
   `/config/.storage/auth`, removes entries with the target `client_name`,
   appends a fresh entry shaped exactly like an existing working long-lived
   entry (id `secrets.token_hex(16)`, `token`/`jwt_key` `token_hex(64)`,
   fields per above), and writes the store back with `indent=2`.
3. Restart the container, wait for `GET /` to return 200/302. If it
   crash-loops on `KeyError: 'token'` or a token_type `ValueError`, the entry
   shape is wrong — compare against a working entry and fix before restart.
4. Mint the bearer JWT inside the container (PyJWT is bundled):
   `jwt.encode({'iss': entry_id, 'iat': now, 'exp': now+exp_sec}, jwt_key,
   algorithm='HS256')`. Write it to a mode-600 staging file, `docker cp` it
   out, delete the in-container copy.
5. Verify `GET /api/` with the JWT returns 200 BEFORE editing any `.env`;
   only then rewrite `HA_TOKEN=` (regex, exactly one match per file, chmod
   600). Delete the staging file only after all `.env` updates succeed.
6. Verify end-to-end with a `persistent_notification/create` (and dismiss)
   against `/api/services/...`; expect 200.

Operational notes: prefer creating tokens via the HA profile UI whenever an
interactive session is available (it produces the JWT automatically); the
store-edit path is the headless fallback. Never echo or log token values —
verify in memory, print booleans/counts only.
