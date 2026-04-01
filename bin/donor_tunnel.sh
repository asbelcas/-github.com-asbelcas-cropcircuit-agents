#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/asbelcas/cropcircuit"
LOG_FILE="$ROOT/logs/donor_tunnel.log"
URL_FILE="$ROOT/runtime/donor_public_url.txt"
TARGET_URL="${DONOR_WEB_PUBLIC_TARGET:-http://127.0.0.1:8788}"

mkdir -p "$ROOT/logs" "$ROOT/runtime"
touch "$LOG_FILE"

log() {
  printf '%s %s\n' "$(date -Is)" "$1" | tee -a "$LOG_FILE"
}

if [[ -n "${DONOR_CLOUDFLARE_TUNNEL_TOKEN:-}" ]]; then
  log "starting cloudflared named tunnel target=$TARGET_URL"
  exec cloudflared tunnel --no-autoupdate run --token "$DONOR_CLOUDFLARE_TUNNEL_TOKEN" 2>&1 | tee -a "$LOG_FILE"
fi

log "starting cloudflared quick tunnel target=$TARGET_URL"

cloudflared tunnel --no-autoupdate --url "$TARGET_URL" 2>&1 | tee -a "$LOG_FILE" | while IFS= read -r line; do
  if [[ "$line" =~ https://[a-z0-9-]+\.trycloudflare\.com ]]; then
    echo "${BASH_REMATCH[0]}" > "$URL_FILE"
    log "public_url=${BASH_REMATCH[0]}"
  fi
done
