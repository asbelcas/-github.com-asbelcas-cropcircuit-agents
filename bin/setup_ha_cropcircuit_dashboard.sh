#!/usr/bin/env bash
# setup_ha_cropcircuit_dashboard.sh — Add dashboard card + set initial URL value.
# Run AFTER HA restart (after setup_ha_cropcircuit_website.sh).
# Does NOT require root — uses REST API.
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"
source "$ROOT_DIR/.env.grant"

HA_URL="${HA_URL:-http://localhost:8123}"
HA_TOKEN="${HA_TOKEN:?Set HA_TOKEN in .env.grant}"

api() {
  local method="$1" path="$2"
  shift 2
  curl -sS -X "$method" \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" \
    "${HA_URL%/}$path" "$@"
}

echo "=== Post-restart setup ==="

# 1) Set the input_text value
echo "Setting input_text.cropcircuit_website_url..."
api POST "/api/services/input_text/set_value" \
  -d '{"entity_id":"input_text.cropcircuit_website_url","value":"https://cropcircuit.com"}'
echo " -> done"

# 2) Verify entity exists
echo "Verifying entity..."
STATE=$(api GET "/api/states/input_text.cropcircuit_website_url")
echo "$STATE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
state = d.get('state', 'MISSING')
print(f'  Entity state: {state}')
if state == 'https://cropcircuit.com':
    print('  PASS')
else:
    print('  WARN: unexpected state')
" 2>/dev/null || echo "  Could not parse state (entity may not exist yet — restart HA first)"

# 3) Verify template sensor
echo "Checking template sensor..."
SENSOR=$(api GET "/api/states/sensor.cropcircuit_website" 2>/dev/null || echo '{}')
echo "$SENSOR" | python3 -c "
import sys, json
d = json.load(sys.stdin)
state = d.get('state', 'NOT_FOUND')
print(f'  sensor.cropcircuit_website state: {state}')
" 2>/dev/null || echo "  Template sensor not yet available (restart HA first)"

echo ""
echo "=== Dashboard card ==="
echo "Add this Markdown card to your Lovelace dashboard (via UI > Edit Dashboard > Add Card > Markdown):"
echo ""
cat <<'CARD'
type: markdown
title: CropCircuit
content: |
  **Website:** [{{ states('input_text.cropcircuit_website_url') }}]({{ states('input_text.cropcircuit_website_url') }})

  **Status:** Online
CARD
echo ""
echo "=== Verification checklist ==="
echo "  [ ] input_text.cropcircuit_website_url = https://cropcircuit.com"
echo "  [ ] sensor.cropcircuit_website = https://cropcircuit.com"
echo "  [ ] shell_command.cropcircuit_print_url available in Services"
echo "  [ ] Dashboard shows clickable link"
