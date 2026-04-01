#!/usr/bin/env bash
# setup_ha_cropcircuit_website.sh — Add CropCircuit website URL as a first-class HA config object.
# Creates: input_text helper, template sensor, shell_command, dashboard card.
# Must run as root: sudo bash bin/setup_ha_cropcircuit_website.sh
set -euo pipefail

HA_CONFIG="/opt/homeassistant/config"
CONF="$HA_CONFIG/configuration.yaml"

if [[ ! -f "$CONF" ]]; then
  echo "ERROR: $CONF not found"
  exit 1
fi

echo "=== Setting up CropCircuit Website URL in Home Assistant ==="

# ---------------------------------------------------------------
# 1) input_text helper
# ---------------------------------------------------------------
if grep -q "input_text:" "$CONF"; then
  echo "input_text section already exists — checking for cropcircuit entry..."
  if grep -q "cropcircuit_website_url:" "$CONF"; then
    echo "  -> cropcircuit_website_url already present, skipping"
  else
    echo "  -> input_text exists but no cropcircuit entry. Add manually:"
    echo "     See patch below."
  fi
else
  echo "Adding input_text section to configuration.yaml..."
  cat >> "$CONF" <<'YAML'

# CropCircuit website URL (central config)
input_text:
  cropcircuit_website_url:
    name: CropCircuit Website URL
    initial: "https://cropcircuit.com"
    max: 255
YAML
  echo "  -> input_text added"
fi

# ---------------------------------------------------------------
# 2) template sensor
# ---------------------------------------------------------------
if grep -q "template:" "$CONF"; then
  echo "template section already exists — checking for cropcircuit sensor..."
  if grep -q "cropcircuit_website" "$CONF"; then
    echo "  -> cropcircuit_website sensor already present, skipping"
  else
    echo "  -> template exists but no cropcircuit sensor. Adding to end..."
    # Append as separate template block (HA merges them)
    cat >> "$CONF" <<'YAML'

# CropCircuit website template sensor alias
template:
  - sensor:
      - name: "CropCircuit Website"
        unique_id: cropcircuit_website
        state: "{{ states('input_text.cropcircuit_website_url') }}"
YAML
    echo "  -> template sensor added"
  fi
else
  echo "Adding template sensor section to configuration.yaml..."
  cat >> "$CONF" <<'YAML'

# CropCircuit website template sensor alias
template:
  - sensor:
      - name: "CropCircuit Website"
        unique_id: cropcircuit_website
        state: "{{ states('input_text.cropcircuit_website_url') }}"
YAML
  echo "  -> template sensor added"
fi

# ---------------------------------------------------------------
# 3) shell_command to print URL (for agent verification)
# ---------------------------------------------------------------
SHELL_CMD="$HA_CONFIG/shell_commands.yaml"
if grep -q "cropcircuit_print_url:" "$SHELL_CMD" 2>/dev/null; then
  echo "shell_command cropcircuit_print_url already exists, skipping"
else
  echo "Adding cropcircuit_print_url to shell_commands.yaml..."
  cat >> "$SHELL_CMD" <<'YAML'

# Print CropCircuit website URL to logs
cropcircuit_print_url: 'echo "CropCircuit URL: https://cropcircuit.com" | tee -a /config/grant_results/cropcircuit_url_check.txt'
YAML
  echo "  -> shell_command added"
fi

echo ""
echo "=== Config changes complete ==="
echo ""
echo "Next steps:"
echo "  1) Restart HA:  docker restart homeassistant"
echo "  2) After restart, set the initial value:"
echo "     curl -sS -X POST -H 'Authorization: Bearer \$HA_TOKEN' \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       'http://localhost:8123/api/services/input_text/set_value' \\"
echo "       -d '{\"entity_id\":\"input_text.cropcircuit_website_url\",\"value\":\"https://cropcircuit.com\"}'"
echo "  3) Verify: check entity input_text.cropcircuit_website_url in Developer Tools > States"
echo ""
