#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/asbelcas/cropcircuit"
RUNTIME="$ROOT/runtime"
LOGS="$ROOT/logs"
HEARTBEAT="$RUNTIME/ops_heartbeat.log"
DECISIONS="$RUNTIME/decision_log.json"
LOOP_PID="$RUNTIME/offline_ops_loop.pid"
LOOP_LOG="$LOGS/offline_ops_loop.log"

mkdir -p "$RUNTIME" "$LOGS"

now_utc() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

log_heartbeat() {
  echo "$(now_utc) mode=codex_primary tick=watchdog status=alive" >> "$HEARTBEAT"
}

log_decision() {
  local decision="$1"
  local details="$2"
  python3 - <<PY
import json
from pathlib import Path
p = Path("$DECISIONS")
entries = []
if p.exists():
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
        if isinstance(data, list):
            entries = data
    except Exception:
        entries = []
entries.append({"timestamp": "$(now_utc)", "decision": "$decision", "details": "$details"})
p.write_text(json.dumps(entries[-1000:], indent=2), encoding='utf-8')
PY
}

load_env() {
  set +u
  for f in "$ROOT/.env" "$ROOT/.env.grant" "$ROOT/.env.donor"; do
    [[ -f "$f" ]] || continue
    set -a
    # shellcheck disable=SC1090
    source "$f"
    set +a
  done
  set -u
  export EXECUTE_SEND=0
}

restart_offline_loop_if_needed() {
  local need_restart=0
  if [[ ! -f "$LOOP_PID" ]]; then
    need_restart=1
  else
    local pid
    pid="$(cat "$LOOP_PID" 2>/dev/null || true)"
    if [[ -z "$pid" ]] || ! ps -p "$pid" >/dev/null 2>&1; then
      need_restart=1
    fi
  fi

  if [[ "$need_restart" -eq 1 ]]; then
    nohup "$ROOT/bin/offline_ops_loop.sh" >> "$LOOP_LOG" 2>&1 &
    echo $! > "$LOOP_PID"
    log_decision "restart_offline_ops_loop" "offline loop missing/crashed; restarted pid=$(cat "$LOOP_PID")"
  fi
}

idle_resume_partner_discovery() {
  local last_ts epoch_now epoch_last idle_sec
  epoch_now=$(date +%s)
  if [[ ! -f "$HEARTBEAT" ]]; then
    python3 "$ROOT/bin/offline_ops_cycle.py" >> "$LOGS/offline_ops_cycle.log" 2>> "$LOGS/ops_errors.log" || true
    log_decision "resume_partner_discovery" "heartbeat_missing; ran offline_ops_cycle"
    return
  fi
  last_ts="$(tail -n 1 "$HEARTBEAT" | awk '{print $1}' || true)"
  if [[ -z "$last_ts" ]]; then
    return
  fi
  epoch_last=$(date -d "$last_ts" +%s 2>/dev/null || echo 0)
  idle_sec=$(( epoch_now - epoch_last ))
  if (( idle_sec > 300 )); then
    python3 "$ROOT/bin/offline_ops_cycle.py" >> "$LOGS/offline_ops_cycle.log" 2>> "$LOGS/ops_errors.log" || true
    log_decision "resume_partner_discovery" "idle>${idle_sec}s; ran offline_ops_cycle"
  fi
}

imap_pull_with_retry() {
  local out rc
  out=$(python3 "$ROOT/bin/pull_targets_imap.py" 2>&1) || rc=$?
  rc=${rc:-0}
  echo "$out" >> "$LOGS/imap_pull.log"
  if [[ $rc -ne 0 ]] || grep -qi 'Temporary failure in name resolution' <<<"$out"; then
    out=$(python3 "$ROOT/bin/pull_targets_imap.py" 2>&1) || rc=$?
    rc=${rc:-0}
    echo "$out" >> "$LOGS/imap_pull.log"
    log_decision "imap_retry" "initial pull failed; retried rc=$rc"
  fi
}

main() {
  load_env
  log_heartbeat
  restart_offline_loop_if_needed
  idle_resume_partner_discovery
  imap_pull_with_retry

  # draft-only classification + queue refresh
  python3 "$ROOT/bin/reply_classifier.py" >> "$LOGS/reply_classifier.log" 2>> "$LOGS/ops_errors.log" || true
  python3 "$ROOT/bin/ha_email_triage.py" >> "$LOGS/email_triage.log" 2>> "$LOGS/ops_errors.log" || true
  python3 "$ROOT/bin/ha_marketplace_liaison.py" >> "$LOGS/ai_liaison.marketplace.log" 2>> "$LOGS/ops_errors.log" || true
  python3 "$ROOT/bin/followup_engine.py" --high-priority-only >> "$LOGS/followup_engine.log" 2>> "$LOGS/ops_errors.log" || true
  timeout 70 python3 "$ROOT/bin/revenue_survival_cycle.py" >> "$LOGS/revenue_survival_cycle.log" 2>> "$LOGS/ops_errors.log" || true

  # default blocked task: partner discovery + enrichment
  python3 "$ROOT/bin/mdard_outreach_pipeline.py" >> "$LOGS/mdard_outreach_pipeline.log" 2>> "$LOGS/ops_errors.log" || true
  log_decision "watchdog_tick_complete" "completed codex tick with draft-only email policy"
}

main "$@"
