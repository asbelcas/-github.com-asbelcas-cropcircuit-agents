#!/usr/bin/env bash
# config_sanity_check.sh — Verify grant pipeline prerequisites are met.
# Run: bash bin/config_sanity_check.sh
set -euo pipefail

ROOT="/home/asbelcas/cropcircuit"
PASS=0
FAIL=0
WARN=0

check() {
  local label="$1" result="$2"
  if [[ "$result" == "ok" ]]; then
    echo "  [OK]   $label"
    PASS=$((PASS+1))
  elif [[ "$result" == "warn" ]]; then
    echo "  [WARN] $label"
    WARN=$((WARN+1))
  else
    echo "  [FAIL] $label — $result"
    FAIL=$((FAIL+1))
  fi
}

echo "=== Grant Pipeline Sanity Check ==="
echo ""

# Environment
echo "--- Environment ---"
if [[ -f "$ROOT/.env.grant" ]]; then
  check ".env.grant exists" "ok"
  source "$ROOT/.env.grant"
  [[ -n "${HA_URL:-}" ]] && check "HA_URL set" "ok" || check "HA_URL set" "missing in .env.grant"
  [[ -n "${HA_TOKEN:-}" ]] && check "HA_TOKEN set" "ok" || check "HA_TOKEN set" "missing in .env.grant"
  [[ -n "${GMAIL_APP_PASSWORD:-}" ]] && check "GMAIL_APP_PASSWORD set" "ok" || check "GMAIL_APP_PASSWORD set" "warn"
else
  check ".env.grant exists" "not found"
fi

# Files
echo ""
echo "--- Required Files ---"
for f in bin/ha_grant_pipeline.sh bin/fill_and_submit.py bin/chrome_guard.sh bin/ha_pipeline_watcher.sh runtime/field_map.json; do
  [[ -f "$ROOT/$f" ]] && check "$f" "ok" || check "$f" "not found"
done

# Runtime
echo ""
echo "--- Runtime State ---"
[[ -f "$ROOT/runtime/ha_grant_pipeline_status.json" ]] && check "Status file exists" "ok" || check "Status file exists" "will be created on first run"
[[ -f "$ROOT/runtime/morning_targets.json" ]] && check "Morning targets file" "ok" || check "Morning targets file" "warn"

# Chrome
echo ""
echo "--- Chrome ---"
if curl -s --connect-timeout 3 "http://127.0.0.1:9222/json/version" >/dev/null 2>&1; then
  check "Chrome CDP on port 9222" "ok"
else
  check "Chrome CDP on port 9222" "not running — run: bin/chrome_guard.sh"
fi

# HA connectivity
echo ""
echo "--- Home Assistant ---"
if [[ -n "${HA_URL:-}" && -n "${HA_TOKEN:-}" ]]; then
  ha_resp=$(curl -sS -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $HA_TOKEN" "${HA_URL}/api/" 2>/dev/null || echo "000")
  [[ "$ha_resp" == "200" ]] && check "HA API reachable" "ok" || check "HA API reachable" "HTTP $ha_resp"
else
  check "HA API reachable" "skipped (no HA_URL/HA_TOKEN)"
fi

# Watcher service
echo ""
echo "--- Pipeline Watcher ---"
if pgrep -f "ha_pipeline_watcher.sh" >/dev/null 2>&1; then
  check "Watcher process running" "ok"
else
  check "Watcher process running" "not running — run: systemctl --user start grant-pipeline-watcher"
fi

# Trigger/Result directories
echo ""
echo "--- Trigger Bridge ---"
[[ -d "/opt/homeassistant/config/grant_triggers" ]] && check "Trigger dir" "ok" || check "Trigger dir" "missing: sudo mkdir -p /opt/homeassistant/config/grant_triggers"
[[ -d "/opt/homeassistant/config/grant_results" ]] && check "Results dir" "ok" || check "Results dir" "missing: sudo mkdir -p /opt/homeassistant/config/grant_results"

echo ""
echo "=== Summary: $PASS passed, $FAIL failed, $WARN warnings ==="
[[ $FAIL -eq 0 ]] && echo "Pipeline is ready." || echo "Fix the FAIL items above before running."
exit $FAIL
