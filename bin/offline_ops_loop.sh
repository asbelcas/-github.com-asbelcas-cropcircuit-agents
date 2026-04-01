#!/usr/bin/env bash
# 20-minute autonomous offline operations loop.
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR" || exit 1
mkdir -p "$ROOT_DIR/logs" "$ROOT_DIR/runtime"

LOG_FILE="$ROOT_DIR/logs/offline_ops_loop.log"
ERR_FILE="$ROOT_DIR/logs/ops_errors.log"
PID_FILE="$ROOT_DIR/runtime/offline_ops_loop.pid"

echo "$$" >"$PID_FILE"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { echo "$(ts) $*" >>"$LOG_FILE"; }
err() { echo "$(ts) $*" >>"$ERR_FILE"; }

log "offline_ops_loop started pid=$$"

while true; do
  python3 "$ROOT_DIR/bin/offline_ops_cycle.py" >>"$LOG_FILE" 2>>"$ERR_FILE" || err "offline_ops_cycle_failed rc=$?"
  sleep 1200
done

