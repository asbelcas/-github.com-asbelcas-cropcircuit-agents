#!/usr/bin/env bash
# Long-running operations watchdog for CropCircuit.
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR" || exit 1
mkdir -p "$ROOT_DIR/logs" "$ROOT_DIR/runtime"

WATCHDOG_LOG="$ROOT_DIR/logs/ops_watchdog.log"
OPS_ERR_LOG="$ROOT_DIR/logs/ops_errors.log"
STATUS_ROLLUP="$ROOT_DIR/logs/status_rollup.log"
PID_FILE="$ROOT_DIR/runtime/ops_watchdog.pid"
STATE_FILE="$ROOT_DIR/runtime/ops_watchdog_state.env"

echo "$$" >"$PID_FILE"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { echo "$(ts) $*" >>"$WATCHDOG_LOG"; }
err() { echo "$(ts) $*" >>"$OPS_ERR_LOG"; }
rollup() { echo "$(ts) $*" >>"$STATUS_ROLLUP"; }

# restart/backoff state (max 3 restarts per hour per task)
declare -A FAIL_COUNT
declare -A WINDOW_START
declare -A NEXT_ALLOWED

init_task_state() {
  local key="$1"
  FAIL_COUNT["$key"]=0
  WINDOW_START["$key"]=$(date +%s)
  NEXT_ALLOWED["$key"]=0
}

for k in self_check hourly_deep_check email_triage marketplace_liaison casey_briefing; do
  init_task_state "$k"
done

run_with_backoff() {
  local key="$1"
  shift
  local now epoch_delay
  now=$(date +%s)

  if (( now < NEXT_ALLOWED["$key"] )); then
    return 0
  fi

  # reset window every hour
  if (( now - WINDOW_START["$key"] >= 3600 )); then
    FAIL_COUNT["$key"]=0
    WINDOW_START["$key"]=$now
  fi

  "$@" >>"$WATCHDOG_LOG" 2>>"$OPS_ERR_LOG"
  local rc=$?
  if [[ $rc -eq 0 ]]; then
    return 0
  fi

  FAIL_COUNT["$key"]=$(( FAIL_COUNT["$key"] + 1 ))
  if (( FAIL_COUNT["$key"] > 3 )); then
    err "task=$key rc=$rc restart_limit_exceeded window_start=${WINDOW_START[$key]}"
    NEXT_ALLOWED["$key"]=$(( now + 3600 ))
    return 0
  fi

  case "${FAIL_COUNT[$key]}" in
  1) epoch_delay=60 ;;
  2) epoch_delay=300 ;;
  *) epoch_delay=900 ;;
  esac
  NEXT_ALLOWED["$key"]=$(( now + epoch_delay ))
  err "task=$key rc=$rc applying_backoff=${epoch_delay}s fail_count=${FAIL_COUNT[$key]}"
  return 0
}

last_self_check=0
last_hourly_run=-1
last_brief_14=""
last_brief_18=""

log "ops_watchdog started pid=$$"
rollup "watchdog_started pid=$$"

while true; do
  now_epoch=$(date +%s)
  minute=$(date +%M)
  hour=$(date +%H)
  today=$(date +%F)
  hhmm=$(date +%H:%M)

  # heartbeat every 60s
  log "heartbeat alive=1"
  rollup "heartbeat minute=$minute hour=$hour"

  # 15-minute self-check
  if (( now_epoch - last_self_check >= 900 )); then
    run_with_backoff self_check python3 "$ROOT_DIR/bin/watchdog_tasks.py" self_check
    run_with_backoff email_triage python3 "$ROOT_DIR/bin/ha_email_triage.py"
    run_with_backoff marketplace_liaison python3 "$ROOT_DIR/bin/ha_marketplace_liaison.py"
    last_self_check=$now_epoch
  fi

  # hourly deep check at top of hour
  if [[ "$minute" == "00" && "$hour" != "$last_hourly_run" ]]; then
    run_with_backoff hourly_deep_check python3 "$ROOT_DIR/bin/watchdog_tasks.py" hourly_deep_check
    # refresh daily queue progress signal
    rollup "hourly_progress_check done"
    last_hourly_run="$hour"
  fi

  # Casey briefing checkpoints at 14:00 and 18:00 UTC
  if [[ "$hhmm" == "14:00" && "$last_brief_14" != "$today" ]]; then
    run_with_backoff casey_briefing python3 "$ROOT_DIR/bin/watchdog_tasks.py" casey_briefing
    last_brief_14="$today"
  fi
  if [[ "$hhmm" == "18:00" && "$last_brief_18" != "$today" ]]; then
    run_with_backoff casey_briefing python3 "$ROOT_DIR/bin/watchdog_tasks.py" casey_briefing
    last_brief_18="$today"
  fi

  sleep 60
done
