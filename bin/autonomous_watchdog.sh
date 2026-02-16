#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"
WORKLOG_GLOB="$ROOT_DIR/logs/autonomous_worklog_*"
TRIGGER_FILE="$ROOT_DIR/runtime/autonomous_self_prompt.txt"
IDLE_SECONDS="${IDLE_SECONDS:-300}"

latest_worklog() {
  ls -1t $WORKLOG_GLOB 2>/dev/null | head -n 1 || true
}

main() {
  local latest
  latest="$(latest_worklog)"
  mkdir -p "$ROOT_DIR/runtime"

  if [[ -z "$latest" ]]; then
    local msg="SELF-PROMPT: resume mission... (no autonomous worklog found)"
    echo "$msg"
    printf '%s | %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$msg" >> "$TRIGGER_FILE"
    return 0
  fi

  local now_ts last_ts delta
  now_ts="$(date +%s)"
  last_ts="$(stat -c %Y "$latest")"
  delta=$((now_ts - last_ts))

  if (( delta > IDLE_SECONDS )); then
    local msg="SELF-PROMPT: resume mission..."
    echo "$msg"
    printf '%s | %s | idle_seconds=%s | worklog=%s\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$msg" "$delta" "$latest" >> "$TRIGGER_FILE"
  else
    echo "watchdog_ok: recent progress detected (idle_seconds=$delta, threshold=$IDLE_SECONDS)"
  fi
}

main "$@"
