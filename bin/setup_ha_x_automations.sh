#!/usr/bin/env bash
# setup_ha_x_automations.sh — Register X/Twitter automations in Home Assistant.
# Uses HA REST API (no need for root; same pattern as grant automations).
#
# Usage: bash bin/setup_ha_x_automations.sh
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"

# Source env for HA_TOKEN
if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  set -a; source "$ROOT_DIR/.env.grant"; set +a
fi

HA_URL="${HA_URL:-http://localhost:8123}"
HA_TOKEN="${HA_TOKEN:?ERROR: Set HA_TOKEN in .env.grant}"

api() {
  local method="$1" path="$2"
  shift 2
  curl -sS -X "$method" \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" \
    "${HA_URL%/}$path" "$@"
}

echo "=== Creating X/Twitter HA automations ==="

# 1) Morning post (8:30 AM ET) — post from queue
echo "Creating x_morning_post automation..."
api POST "/api/config/automation/config/x_morning_post" -d '{
  "alias": "X Morning Post",
  "description": "Post morning tweet from queue (progress + plan)",
  "mode": "single",
  "trigger": [
    {
      "platform": "time",
      "at": "08:30:00"
    }
  ],
  "condition": [],
  "action": [
    {
      "service": "shell_command.x_post_queue_item",
      "data": {}
    }
  ]
}'
echo " -> done"

# 2) Evening post (6:30 PM ET) — post from queue
echo "Creating x_evening_post automation..."
api POST "/api/config/automation/config/x_evening_post" -d '{
  "alias": "X Evening Post",
  "description": "Post evening tweet from queue (win + ask)",
  "mode": "single",
  "trigger": [
    {
      "platform": "time",
      "at": "18:30:00"
    }
  ],
  "condition": [],
  "action": [
    {
      "service": "shell_command.x_post_queue_item",
      "data": {}
    }
  ]
}'
echo " -> done"

# 3) Daily mentions fetch (12:00 PM and 8:00 PM)
echo "Creating x_fetch_mentions automation..."
api POST "/api/config/automation/config/x_fetch_mentions" -d '{
  "alias": "X Fetch Mentions",
  "description": "Fetch X mentions digest twice daily",
  "mode": "single",
  "trigger": [
    {
      "platform": "time",
      "at": "12:00:00"
    },
    {
      "platform": "time",
      "at": "20:00:00"
    }
  ],
  "condition": [],
  "action": [
    {
      "service": "shell_command.x_fetch_mentions",
      "data": {}
    }
  ]
}'
echo " -> done"

echo ""
echo "=== All X automations registered ==="
echo "Verify in HA: Settings > Automations > search 'X '"
echo ""
echo "IMPORTANT: Run 'sudo bash bin/setup_ha_grant_commands.sh' first to register"
echo "the shell commands, then restart HA Docker to pick them up."
