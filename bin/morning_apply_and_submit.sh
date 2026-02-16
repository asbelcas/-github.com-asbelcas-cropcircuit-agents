#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"
SESSION_JSON="$ROOT_DIR/runtime/morning_targets.json"
RUN_LOG="$ROOT_DIR/logs/morning_apply_submit.log"
WAIT_SECONDS="${WAIT_SECONDS:-120}"
WAIT_STEP_SECONDS="${WAIT_STEP_SECONDS:-5}"

mkdir -p "$ROOT_DIR/logs" "$ROOT_DIR/runtime"

if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.grant"
fi

ts() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(ts)] $*" | tee -a "$RUN_LOG"; }

wait_for_session() {
  local waited=0
  while [[ ! -f "$SESSION_JSON" ]]; do
    if (( waited >= WAIT_SECONDS )); then
      log "missing_session_file path=$SESSION_JSON waited=${waited}s"
      return 1
    fi
    sleep "$WAIT_STEP_SECONDS"
    waited=$(( waited + WAIT_STEP_SECONDS ))
  done
  return 0
}

program_count() {
  python3 - "$SESSION_JSON" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
d = json.loads(p.read_text(encoding='utf-8'))
arr = d.get('programs', [])
print(len(arr) if isinstance(arr, list) else 0)
PY
}

main() {
  log "morning_apply_submit_start session=$SESSION_JSON"
  wait_for_session || exit 2

  local n i rc any_fail out
  n="$(program_count)"
  if [[ "$n" -eq 0 ]]; then
    log "no_programs_in_session"
    exit 3
  fi

  any_fail=0
  for (( i=0; i<n; i++ )); do
    log "program_index_start index=$i"
    set +e
    out="$(python3 "$ROOT_DIR/bin/apply_and_submit.py" --session "$SESSION_JSON" --program-index "$i" 2>&1)"
    rc=$?
    set -e
    log "program_index_result index=$i rc=$rc result=$out"
    if [[ "$rc" -ne 0 ]]; then
      any_fail=1
    fi
  done

  if [[ "$any_fail" -ne 0 ]]; then
    log "morning_apply_submit_complete status=failed"
    exit 1
  fi
  log "morning_apply_submit_complete status=ok"
}

main "$@"
