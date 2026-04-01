#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/asbelcas/cropcircuit"
LOG="$ROOT/logs/production_outreach.log"
SENT_LOG="$ROOT/runtime/sent_email_ids.log"
STATE_JSON="$ROOT/runtime/production_outreach_state.json"
OFFLINE_MODE_JSON="$ROOT/runtime/offline_mode.json"
HUMAN_MODE_JSON="$ROOT/runtime/human_loop_mode.json"

mkdir -p "$ROOT/logs" "$ROOT/runtime"

now_utc() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

offline_mode_active() {
  if [[ ! -f "$OFFLINE_MODE_JSON" ]]; then
    return 1
  fi
  grep -qi '"active"[[:space:]]*:[[:space:]]*true' "$OFFLINE_MODE_JSON"
}

human_loop_mode_active() {
  if [[ ! -f "$HUMAN_MODE_JSON" ]]; then
    return 1
  fi
  grep -qi '"active"[[:space:]]*:[[:space:]]*true' "$HUMAN_MODE_JSON"
}

log() {
  echo "$(now_utc) $*" | tee -a "$LOG"
}

load_env() {
  set +u
  for f in "$ROOT/.env" "$ROOT/.env.grant" "$ROOT/.env.donor"; do
    if [[ -f "$f" ]]; then
      set -a
      # shellcheck disable=SC1090
      source "$f"
      set +a
    fi
  done
  set -u
}

run_step() {
  local name="$1"
  local cmd="$2"
  local out rc

  log "STEP_START name=$name"
  out=$(timeout 180 bash -lc "cd '$ROOT'; $cmd" 2>&1) || rc=$?
  rc=${rc:-0}
  echo "$out" >> "$LOG"

  if [[ $rc -ne 0 ]] || grep -qi "Temporary failure in name resolution" <<<"$out"; then
    log "STEP_RETRY name=$name reason=dns_or_error rc=$rc"
    sleep 2
    out=$(timeout 180 bash -lc "cd '$ROOT'; $cmd" 2>&1) || rc=$?
    rc=${rc:-0}
    echo "$out" >> "$LOG"
  fi

  if [[ $rc -ne 0 ]]; then
    log "STEP_FAIL name=$name rc=$rc"
    return $rc
  fi

  log "STEP_OK name=$name"
  return 0
}

log_sent_ids() {
  local send_output="$1"
  local ids
  ids=$(grep -oE 'SENT: Email id=[0-9]+' <<<"$send_output" | sed -E 's/.*id=([0-9]+)/\1/' || true)
  if [[ -n "$ids" ]]; then
    while IFS= read -r id; do
      [[ -z "$id" ]] && continue
      echo "$(now_utc),$id" >> "$SENT_LOG"
      log "EMAIL_SENT id=$id"
    done <<< "$ids"
  fi
}

already_sent_today() {
  local id="$1"
  local today
  today="$(date -u +%Y-%m-%d)"
  [[ -f "$SENT_LOG" ]] && grep -q "^${today}T.*,${id}$" "$SENT_LOG"
}

send_today_ids() {
  local ids id out
  ids=$(bash -lc "cd '$ROOT'; python3 bin/send_grant_email.py --list | awk -F: '/day=today/{print \$1}'" || true)
  if [[ -z "$ids" ]]; then
    log "SEND_SKIP reason=no_today_ids"
    return 0
  fi
  while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    if already_sent_today "$id"; then
      log "SEND_SKIP id=$id reason=already_sent_today"
      continue
    fi
    out=$(timeout 180 bash -lc "cd '$ROOT'; SMTP_PORT='${SMTP_PORT:-465}' python3 bin/send_grant_email.py --execute '$id'" 2>&1 || true)
    echo "$out" >> "$LOG"
    if grep -qi "Temporary failure in name resolution\\|unable to resolve SMTP host" <<<"$out"; then
      log "SEND_RETRY id=$id reason=dns"
      out=$(timeout 180 bash -lc "cd '$ROOT'; SMTP_PORT='${SMTP_PORT:-465}' python3 bin/send_grant_email.py --execute '$id'" 2>&1 || true)
      echo "$out" >> "$LOG"
    fi
    log_sent_ids "$out"
  done <<< "$ids"
}

preflight_imap_gate() {
  local out
  out=$(timeout 120 bash -lc "cd '$ROOT'; python3 bin/preflight_imap.py" 2>&1 || true)
  echo "$out" >> "$LOG"
  if grep -q '"ok": true' <<<"$out"; then
    log "PREFLIGHT_OK imap"
    return 0
  fi
  log "PREFLIGHT_BLOCK imap_check_failed output=$(tr '\n' ' ' <<<"$out" | sed 's/  */ /g')"
  python3 - <<'PY' || true
from datetime import datetime, timezone
from email_guard import record_email_event

ts = datetime.now(timezone.utc).isoformat()
record_email_event(
    "block",
    "production_outreach_loop|all_today",
    ts,
    {
        "source": "production_outreach_loop",
        "mode": "preflight_block",
        "reason": "BLOCK: preflight_imap_failed",
    },
)
PY
  return 1
}

write_state() {
  local status="$1"
  local note="$2"
  python3 - <<PY
import json
from pathlib import Path
payload = {
  "timestamp_utc": "$(now_utc)",
  "status": """$status""",
  "note": """$note""",
}
Path("$STATE_JSON").write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY
}

run_cycle() {
  local send_output=""
  local execute_send="${EXECUTE_SEND:-0}"

  load_env
  log "CYCLE_START"

  # 1) Pull morning targets via IMAP (network)
  if offline_mode_active; then
    log "IMAP_SKIP reason=offline_mode_active step=pull_targets_imap"
  elif ! run_step "pull_targets_imap" "python3 bin/pull_targets_imap.py"; then
    log "WARN pull_targets_imap failed; continuing with existing/default targets"
  fi

  # 2) Regenerate map + queue (local)
  run_step "mdard_outreach_pipeline" "python3 bin/mdard_outreach_pipeline.py"

  # 3) Outreach send policy: draft-only unless EXECUTE_SEND=1.
  if human_loop_mode_active; then
    log "SEND_SKIPPED policy=human_loop_mode partnership_conversion_over_volume"
    write_state "human_loop_mode" "Automated outbound paused; stage drafts only unless SAFE_AUTOSEND-tagged human-triggered send"
  elif [[ "$execute_send" != "1" ]]; then
    log "SEND_SKIPPED policy=draft_only execute_send=$execute_send"
    write_state "draft_only_mode" "Send skipped; set EXECUTE_SEND=1 to allow email sends"
  else
    if [[ -z "${GMAIL_APP_PASSWORD:-}" ]]; then
      log "SEND_HALT reason=missing_credentials"
      write_state "send_halted_missing_credentials" "GMAIL_APP_PASSWORD missing"
    else
      if ! preflight_imap_gate; then
        log "SEND_HALT reason=preflight_imap_failed"
        write_state "send_halted_preflight" "IMAP preflight failed; outbound send blocked"
        return 0
      fi
      send_output=$(timeout 180 bash -lc "cd '$ROOT'; python3 bin/send_grant_email.py --list" 2>&1 || true)
      echo "$send_output" >> "$LOG"
      if grep -q "GMAIL_APP_PASSWORD not set" <<<"$send_output"; then
        log "SEND_HALT reason=missing_credentials_runtime"
        write_state "send_halted_missing_credentials" "Runtime missing GMAIL_APP_PASSWORD"
      else
        send_today_ids
        write_state "send_attempted" "send_grant_email per-id today queue executed"
      fi
    fi
  fi

  # 4) Reply check / triage (network: IMAP + optional HA HTTP)
  if offline_mode_active; then
    log "IMAP_SKIP reason=offline_mode_active step=email_triage"
  elif ! run_step "email_triage" "python3 bin/ha_email_triage.py"; then
    log "WARN email triage failed; continuing"
  fi

  # 5) Reply intelligence modules
  if ! run_step "reply_classifier" "python3 bin/reply_classifier.py"; then
    log "WARN reply_classifier failed; continuing"
  fi
  if ! run_step "followup_engine" "python3 bin/followup_engine.py"; then
    log "WARN followup_engine failed; continuing"
  fi
  if ! run_step "referral_expander" "python3 bin/referral_expander.py"; then
    log "WARN referral_expander failed; continuing"
  fi
  if ! run_step "funding_dashboard" "python3 bin/funding_dashboard.py"; then
    log "WARN funding_dashboard failed; continuing"
  fi
  if ! run_step "funding_capture_engine" "python3 bin/funding_capture_engine.py"; then
    log "WARN funding_capture_engine failed; continuing"
  fi

  # 6) Refresh map after triage (local)
  run_step "mdard_outreach_pipeline_post_triage" "python3 bin/mdard_outreach_pipeline.py"

  log "CYCLE_END"
}

if [[ "${1:-}" == "--once" ]]; then
  run_cycle
  exit 0
fi

log "LOOP_START interval_seconds=900"
while true; do
  run_cycle
  sleep 900
done
