#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"
LOG_FILE="$ROOT_DIR/logs/hit_submit.log"
CDP_URL="${CDP_URL:-http://127.0.0.1:9222}"
CDP_VERSION_ENDPOINT="${CDP_URL%/}/json/version"
TARGET_URL="${TARGET_URL:-}"
SELECTOR_HINT="${SELECTOR_HINT:-}"
TARGETS_FILE="${TARGETS_FILE:-/home/asbelcas/cropcircuit/runtime/morning_targets.json}"
if [[ -z "$TARGET_URL" && -n "${GRANT_TARGET_URL:-}" ]]; then
  TARGET_URL="$GRANT_TARGET_URL"
fi

mkdir -p "$ROOT_DIR/logs"

{
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] grant_hit_submit start"
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] cdp_url=${CDP_URL} target_url=${TARGET_URL:-<unset>} selector_hint=${SELECTOR_HINT:-<unset>} targets_file=${TARGETS_FILE}"
  if ! curl -fsS --max-time 3 "$CDP_VERSION_ENDPOINT" >/dev/null 2>&1; then
    echo "{\"status\":\"error\",\"screenshot\":\"\",\"url\":\"\",\"error\":\"cdp_unreachable: start chrome with --remote-debugging-port=9222 and ensure HA runtime can reach ${CDP_URL}\"}"
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] grant_hit_submit exit_code=3"
    exit 3
  fi
  set +e
  GRANT_TARGET_URL="${GRANT_TARGET_URL:-https://www.fsa.usda.gov/programs-and-services/farm-loan-programs/farm-operating-loans}" \
  SUBMIT_SELECTOR="${SUBMIT_SELECTOR:-}" \
  TARGETS_FILE="$TARGETS_FILE" CDP_URL="$CDP_URL" TARGET_URL="$TARGET_URL" SELECTOR_HINT="$SELECTOR_HINT" \
    python3 "$ROOT_DIR/bin/hit_submit.py" "$TARGETS_FILE"
  rc=$?
  set -e
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] grant_hit_submit exit_code=$rc"
  exit $rc
} >>"$LOG_FILE" 2>&1
