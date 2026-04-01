#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"
LOG_DIR="$ROOT_DIR/logs"
RUNTIME_DIR="$ROOT_DIR/runtime"
LOG_FILE="$LOG_DIR/system_update_workflow.log"
STATUS_FILE="$RUNTIME_DIR/system_update_status.json"

SERVICES=(
  "cropcircuit-chrome-cdp.service"
  "cropcircuit-morning-targets.service"
  "cropcircuit-targets-receiver.service"
  "grant-pipeline-watcher.service"
  "grant-submission-relay.service"
  "donor-web.service"
  "donor-tunnel.service"
)

mkdir -p "$LOG_DIR" "$RUNTIME_DIR"
cd "$ROOT_DIR"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG_FILE"
}

ha_notify() {
  local msg="$1"
  if [[ -x "$ROOT_DIR/bin/ha_event" && -n "${HA_URL:-}" && -n "${HA_TOKEN:-}" ]]; then
    "$ROOT_DIR/bin/ha_event" system_update "$msg" >> "$LOG_FILE" 2>&1 || true
  fi
}

if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.grant" || true
fi

SUDO_CMD=("sudo")
INTERACTIVE_SUDO="false"
if sudo -n -l /usr/bin/apt-get update >/dev/null 2>&1; then
  SUDO_CMD=("sudo" "-n")
elif [[ ! -t 0 ]]; then
  log "System update skipped: sudo password required but no interactive terminal is available."
  ha_notify "System update skipped: sudo password required."
  cat > "$STATUS_FILE" <<EOF
{"timestamp":"$(date -Is)","status":"skipped","reason":"sudo_password_required_non_interactive"}
EOF
  exit 2
else
  INTERACTIVE_SUDO="true"
fi

log "Starting system update workflow."
"$ROOT_DIR/bin/ha_health_check.sh" || true

for unit in "${SERVICES[@]}"; do
  state="$(systemctl --user is-active "$unit" 2>/dev/null || true)"
  log "Pre-check $unit=$state"
done

log "Running apt-get update."
if [[ "$INTERACTIVE_SUDO" == "true" ]]; then
  "${SUDO_CMD[@]}" apt-get update
else
  "${SUDO_CMD[@]}" apt-get update >> "$LOG_FILE" 2>&1
fi

log "Running apt-get upgrade."
if [[ "$INTERACTIVE_SUDO" == "true" ]]; then
  "${SUDO_CMD[@]}" apt-get -y upgrade
else
  "${SUDO_CMD[@]}" apt-get -y upgrade >> "$LOG_FILE" 2>&1
fi

log "Running apt-get autoremove."
if [[ "$INTERACTIVE_SUDO" == "true" ]]; then
  "${SUDO_CMD[@]}" apt-get -y autoremove
else
  "${SUDO_CMD[@]}" apt-get -y autoremove >> "$LOG_FILE" 2>&1
fi

for unit in "${SERVICES[@]}"; do
  state="$(systemctl --user is-active "$unit" 2>/dev/null || true)"
  if [[ "$state" != "active" ]]; then
    log "Restarting $unit (state=$state)."
    systemctl --user restart "$unit" >> "$LOG_FILE" 2>&1 || log "Restart failed for $unit"
  fi
  state_after="$(systemctl --user is-active "$unit" 2>/dev/null || true)"
  log "Post-check $unit=$state_after"
done

"$ROOT_DIR/bin/ha_health_check.sh" || true

reboot_required="false"
if [[ -f /var/run/reboot-required ]]; then
  reboot_required="true"
fi

cat > "$STATUS_FILE" <<EOF
{"timestamp":"$(date -Is)","status":"ok","reboot_required":$reboot_required}
EOF

log "System update workflow complete (reboot_required=$reboot_required)."
ha_notify "System update workflow complete. reboot_required=$reboot_required"
