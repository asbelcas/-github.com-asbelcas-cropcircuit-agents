#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/asbelcas/cropcircuit"
LOG="$ROOT/logs/reliability_check.log"
SERVICES=("donor-web" "grant-pipeline-watcher" "cropcircuit-morning-targets" "donor-tunnel")
BRIDGE="$ROOT/bin/donor_lead_bridge.py"
STATUS="ok"

mkdir -p "$ROOT/logs"

log() {
  printf '%s %s\n' "$(date -Is)" "$1" >> "$LOG"
}

notify_ha() {
  local msg="$1"
  if [[ -f "$ROOT/.env.grant" ]]; then
    # shellcheck disable=SC1091
    source "$ROOT/.env.grant" || true
  fi
  if [[ -n "${HA_TOKEN:-}" ]]; then
    curl -sS -X POST \
      -H "Authorization: Bearer $HA_TOKEN" \
      -H "Content-Type: application/json" \
      "${HA_URL:-http://localhost:8123}/api/services/persistent_notification/create" \
      -d "{\"title\":\"CropCircuit Reliability Alert\",\"message\":\"$msg\"}" >/dev/null 2>&1 || true
  fi
}

for svc in "${SERVICES[@]}"; do
  if systemctl --user is-active "$svc" >/dev/null 2>&1; then
    log "service_ok $svc"
  else
    STATUS="degraded"
    log "service_down $svc restarting"
    if systemctl --user restart "$svc"; then
      log "service_restart_ok $svc"
      notify_ha "Service restarted automatically: $svc"
    else
      log "service_restart_failed $svc"
      notify_ha "Service restart failed: $svc"
    fi
  fi
done

if [[ -f "$BRIDGE" ]]; then
  log "bridge_ok donor_lead_bridge.py"
else
  STATUS="degraded"
  log "bridge_missing donor_lead_bridge.py"
  notify_ha "Missing donor bridge script: $BRIDGE"
fi

echo "{\"timestamp\":\"$(date -Is)\",\"status\":\"$STATUS\"}"
