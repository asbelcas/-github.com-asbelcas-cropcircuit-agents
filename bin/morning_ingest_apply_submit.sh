#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"
INGEST_LOG="$ROOT_DIR/logs/targets_ingest.log"
RUN_LOG="$ROOT_DIR/logs/morning_ingest_apply_submit.log"
TARGETS_JSON="$ROOT_DIR/runtime/morning_targets.json"

mkdir -p "$ROOT_DIR/logs" "$ROOT_DIR/runtime"

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$RUN_LOG"; }

log "morning_ingest_apply_submit_start"

if python3 "$ROOT_DIR/bin/pull_targets_from_gmail.py" >>"$RUN_LOG" 2>&1; then
  log "gmail_ingest_ok"
else
  log "gmail_ingest_failed_fallback_prompt"
  python3 "$ROOT_DIR/bin/targets_prompt.py" --no-submit
fi

if [[ ! -f "$TARGETS_JSON" ]]; then
  log "targets_missing_after_ingest path=$TARGETS_JSON"
  exit 2
fi

bash "$ROOT_DIR/bin/morning_apply_and_submit.sh" >>"$RUN_LOG" 2>&1

log "morning_ingest_apply_submit_complete"
echo "targets_log=$INGEST_LOG"
