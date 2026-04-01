#!/usr/bin/env bash
set -euo pipefail

HA_BASE_URL="${HA_BASE_URL:-}"
HA_TOKEN="${HA_TOKEN:-}"

if [[ -z "$HA_BASE_URL" || -z "$HA_TOKEN" ]]; then
  echo "ERROR: HA_BASE_URL and HA_TOKEN are required."
  echo "Set them like:"
  echo "  export HA_BASE_URL='http://192.168.1.120:8123'"
  echo "  export HA_TOKEN='YOUR_LONG_LIVED_TOKEN'"
  exit 1
fi

payload=$(cat <<'JSON'
{
  "title": "HA Notify Test",
  "message": "ha_notify_test.sh succeeded. Persistent notification path is working."
}
JSON
)

code=$(curl -sS -o /tmp/ha_notify_test.out -w '%{http_code}' \
  -X POST \
  -H "Authorization: Bearer ${HA_TOKEN}" \
  -H "Content-Type: application/json" \
  "${HA_BASE_URL%/}/api/services/persistent_notification/create" \
  -d "$payload" || true)

if [[ "$code" == "200" || "$code" == "201" ]]; then
  echo "OK: persistent notification sent (${code})"
  exit 0
fi

echo "ERROR: HA notify failed (HTTP ${code})"
echo "Response:"
cat /tmp/ha_notify_test.out || true
exit 1
