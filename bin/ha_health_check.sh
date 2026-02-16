#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p "$ROOT_DIR/logs"

HA_LOG="$ROOT_DIR/logs/ha_health.log"
HA_OK_FILE="$ROOT_DIR/logs/ha_health_last_ok.txt"

if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.grant"
fi

ha_url="${HA_URL:-http://localhost:8123}"
ha_url="${ha_url%/}"

check_ok=0
http_code="000"

if [[ -n "${HA_TOKEN:-}" ]]; then
  http_code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 6 "$ha_url/api/config" -H "Authorization: Bearer ${HA_TOKEN}" || true)"
  if [[ "$http_code" == "200" ]]; then
    check_ok=1
  fi
else
  http_code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 6 "$ha_url/api/" || true)"
  if [[ "$http_code" == "401" || "$http_code" == "200" ]]; then
    check_ok=1
  fi
fi

ts="$(date '+%Y-%m-%d %H:%M:%S')"
if [[ "$check_ok" -eq 1 ]]; then
  echo "$ts" > "$HA_OK_FILE"
  echo "[$ts] HA health OK (code=$http_code url=$ha_url)" >> "$HA_LOG"
  exit 0
fi

echo "[$ts] HA health DOWN (code=$http_code url=$ha_url)" >> "$HA_LOG"
if [[ -x "$ROOT_DIR/bin/ha_event" && -n "${HA_URL:-}" && -n "${HA_TOKEN:-}" ]]; then
  "$ROOT_DIR/bin/ha_event" ha_health_down "ha_health_check failed code=$http_code url=$ha_url" >> "$HA_LOG" 2>&1 || true
fi

exit 0
