#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${HA_URL:-}" || -z "${HA_TOKEN:-}" ]]; then
  echo "Missing HA_URL or HA_TOKEN env vars."
  echo "Example:"
  echo '  export HA_URL="http://192.168.1.X:8123"'
  echo '  export HA_TOKEN="..."'
  exit 1
fi

METHOD="${1:-}"
PATH_="${2:-}"
BODY="${3:-}"

if [[ -z "$METHOD" || -z "$PATH_" ]]; then
  echo "Usage: $0 METHOD PATH [JSON_BODY]"
  echo "Examples:"
  echo "  $0 GET /api/"
  echo "  $0 GET /api/states"
  echo "  $0 POST /api/services/light/turn_on '{\"entity_id\":\"light.kitchen\"}'"
  exit 1
fi

URL="${HA_URL}${PATH_}"

if [[ -n "${BODY}" ]]; then
  curl -sS -X "$METHOD" "$URL" \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$BODY"
else
  curl -sS -X "$METHOD" "$URL" \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json"
fi
