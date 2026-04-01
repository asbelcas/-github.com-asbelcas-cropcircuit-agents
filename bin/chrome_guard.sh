#!/usr/bin/env bash
# chrome_guard.sh — Ensure Chrome is running with remote debugging on port 9222.
# If already running and responsive, do nothing. If not, start it.
# Logs all actions to chrome_guard.log.
set -euo pipefail

PROFILE="/home/asbelcas/.chrome-ha"
LOG="/home/asbelcas/cropcircuit/logs/chrome_guard.log"
PORT=9222
DISPLAY="${DISPLAY:-:0}"
export DISPLAY

pick_browser_bin() {
  if [[ -n "${AUTOMATION_BROWSER_BIN:-}" && -x "${AUTOMATION_BROWSER_BIN}" ]]; then
    echo "${AUTOMATION_BROWSER_BIN}"
    return 0
  fi

  local pw
  pw="$(ls -1d "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux64/chrome 2>/dev/null | tail -n 1 || true)"
  if [[ -n "$pw" && -x "$pw" ]]; then
    echo "$pw"
    return 0
  fi

  if command -v chromium-browser >/dev/null 2>&1; then
    command -v chromium-browser
    return 0
  fi

  command -v google-chrome
}

CHROME="$(pick_browser_bin)"

mkdir -p "$PROFILE" "$(dirname "$LOG")"

log() {
  echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$LOG"
}

# Check if Chrome debug port is already responsive
if curl -s --connect-timeout 3 "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
  log "Chrome already running and responsive at port $PORT"
  exit 0
fi

log "Chrome not responsive at port $PORT — checking for stale processes"

# Check if a process is listening on the port but not responding
if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
  # Something is on the port but not responding — wait briefly and retry
  sleep 2
  if curl -s --connect-timeout 3 "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
    log "Chrome became responsive after brief wait"
    exit 0
  fi
  # Still unresponsive — kill the stale process
  log "Killing stale process on port $PORT"
  fuser -k "${PORT}/tcp" 2>/dev/null || true
  sleep 1
fi

# Remove stale lock files (only if Chrome is not running)
if ! pgrep -f "remote-debugging-port=${PORT}" >/dev/null 2>&1; then
  rm -f "$PROFILE/SingletonLock" "$PROFILE/SingletonSocket" "$PROFILE/SingletonCookie"
fi

log "Launching Chrome with remote debugging on port $PORT"
log "Using browser binary: $CHROME"

nohup nice -n 15 "$CHROME" \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE" \
  --headless=new \
  --no-first-run \
  --no-default-browser-check \
  --disable-extensions \
  --disable-notifications \
  --disable-background-networking \
  --disable-sync \
  --disable-gpu \
  --disable-software-rasterizer \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-breakpad \
  --disable-crash-reporter \
  --disable-features=RendererCodeIntegrity,TranslateUI \
  --window-size=1280,900 \
  about:blank \
  >> "$LOG" 2>&1 < /dev/null &

CHROME_PID=$!
log "Chrome launched with PID $CHROME_PID"

# Wait for Chrome to become responsive (up to 15 seconds)
for i in $(seq 1 15); do
  if curl -s --connect-timeout 2 "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
    log "Chrome responsive after ${i}s"
    exit 0
  fi
  sleep 1
done

# Check if Chrome process is still alive
if kill -0 "$CHROME_PID" 2>/dev/null; then
  log "Chrome running (PID $CHROME_PID) but not yet responsive after 15s — continuing anyway"
  exit 0
else
  log "ERROR: Chrome process $CHROME_PID died"
  exit 1
fi
