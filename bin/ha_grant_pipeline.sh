#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"
LOG_FILE="$ROOT_DIR/logs/pipeline.log"
STATUS_FILE="$ROOT_DIR/runtime/ha_grant_pipeline_status.json"
FILL_CMD=("python3" "$ROOT_DIR/bin/fill_and_submit.py")

# Ensure DISPLAY is set for Chrome/Playwright access (HA runs without GUI env)
export DISPLAY="${DISPLAY:-:0}"
export HOME="${HOME:-/home/asbelcas}"
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$ROOT_DIR/logs" "$ROOT_DIR/runtime"

# Source environment early so all subsequent commands have HA_URL/HA_TOKEN
if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.grant"
  set +a
fi

# Parse flags
RESUME_MODE=false
DRY_RUN="${DRY_RUN:-false}"
PROGRAM_ID=""
args=("$@")
for i in "${!args[@]}"; do
  case "${args[$i]}" in
    --resume) RESUME_MODE=true ;;
    --dry-run) DRY_RUN=true ;;
    --program-id) PROGRAM_ID="${args[$((i+1))]:-}" ;;
  esac
done

if [[ "$RESUME_MODE" == "true" ]]; then
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ha_grant_pipeline resume_after_captcha" >>"$LOG_FILE"
  FILL_CMD+=("--skip-captcha-check")
else
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ha_grant_pipeline bootstrap" >>"$LOG_FILE"
fi

if [[ "$DRY_RUN" == "true" ]]; then
  FILL_CMD+=("--dry-run")
fi

if [[ -n "$PROGRAM_ID" ]]; then
  FILL_CMD+=("--program-id" "$PROGRAM_ID")
fi

ts_utc() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

log_line() {
  echo "[$(ts_utc)] $*" >>"$LOG_FILE"
}

post_to_ha() {
  local status="$1"
  local screenshot="$2"
  local result_url="$3"
  local payload
  payload="$(cat "$STATUS_FILE")"

  if [[ -z "${HA_URL:-}" || -z "${HA_TOKEN:-}" ]]; then
    log_line "ha_grant_pipeline ha_post skipped reason=missing_ha_url_or_token"
    return 0
  fi

  local ha_url="${HA_URL%/}"
  if [[ "$ha_url" != http* ]]; then
    ha_url="http://$ha_url"
  fi

  local event_rc
  curl -sS -o /dev/null -w "%{http_code}" -X POST \
    -H "Authorization: Bearer ${HA_TOKEN}" \
    -H "Content-Type: application/json" \
    "${ha_url}/api/events/grant_pipeline_status" \
    -d "$payload" 2>/dev/null || true
  event_rc=$?
  log_line "ha_grant_pipeline ha_event_post rc=${event_rc}"

  curl -sS -X POST \
    -H "Authorization: Bearer ${HA_TOKEN}" \
    -H "Content-Type: application/json" \
    "${ha_url}/api/services/persistent_notification/create" \
    -d "$(python3 - <<'PY' "$status" "$screenshot" "$result_url"
import json
import sys
status = sys.argv[1]
screenshot = sys.argv[2]
result_url = sys.argv[3]
if status == "captcha_required":
    title = "CAPTCHA Required — Grant Pipeline"
    msg = (
        "**Action needed:** Solve the CAPTCHA to continue.\n\n"
        "**Steps:**\n"
        "1. Open the form page (link below)\n"
        "2. Solve the CAPTCHA challenge\n"
        "3. Run service `shell_command.grant_pipeline_resume`\n\n"
        f"**Form URL:** {result_url or '<none>'}\n"
        f"**Screenshot:** `{screenshot or '<none>'}`\n"
    )
elif status in ("success", "dry_run_success"):
    title = "Grant Pipeline — Success"
    msg = f"Pipeline completed successfully.\n\nResult URL: {result_url or '<none>'}\nScreenshot: `{screenshot or '<none>'}`"
elif status == "dry_run_captcha_required":
    title = "Grant Pipeline — Dry Run (CAPTCHA present)"
    msg = f"Dry run completed. CAPTCHA is present on the page.\n\nResult URL: {result_url or '<none>'}\nScreenshot: `{screenshot or '<none>'}`"
else:
    title = f"Grant Pipeline — {status}"
    msg = f"Pipeline status: {status}\n\nResult URL: {result_url or '<none>'}\nScreenshot: `{screenshot or '<none>'}`"
print(json.dumps({
    "notification_id": "grant_pipeline_last",
    "title": title,
    "message": msg,
}))
PY
)" >/dev/null 2>&1 || true
}

log_line "ha_grant_pipeline start"

if ! "$ROOT_DIR/bin/chrome_guard.sh"; then
  status="runtime_failure"
  exit_code=2
  screenshot=""
  result_url=""
  python3 - <<'PY' "$STATUS_FILE" "$status" "$exit_code" "$screenshot" "$result_url"
import json
import sys
from datetime import datetime, timezone
path, status, exit_code, screenshot, result_url = sys.argv[1:]
data = {
    "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "status": status,
    "exit_code": int(exit_code),
    "last_screenshot_path": screenshot,
    "result_url": result_url,
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
PY
  log_line "ha_grant_pipeline status=${status} exit_code=${exit_code}"
  post_to_ha "$status" "$screenshot" "$result_url"
  exit "$exit_code"
fi

set +e
run_output="$("${FILL_CMD[@]}" 2>&1)"
run_rc=$?
set -e

json_line="$(printf '%s\n' "$run_output" | tail -n 1)"

if ! python3 - <<'PY' "$json_line" >/dev/null 2>&1
import json
import sys
json.loads(sys.argv[1])
PY
then
  status="runtime_failure"
  exit_code=2
  screenshot=""
  result_url=""
else
  readarray -t parsed < <(python3 - <<'PY' "$json_line"
import json
import sys
obj = json.loads(sys.argv[1])
status = str(obj.get("status", ""))
screenshot = str(obj.get("screenshot", "") or obj.get("post_submit_screenshot", ""))
result_url = str(obj.get("result_url", ""))
selected_page_url = str(obj.get("selected_page_url", ""))
selected_frame_url = str(obj.get("selected_frame_url", ""))
if status == "captcha_required":
    code = 1
    state = "captcha_required"
elif status in ("success", "dry_run_success", "dry_run_captcha_required"):
    code = 0
    state = status
elif status in {"selector_failure", "submit_failed", "submit_rejected"}:
    code = 2
    state = status
else:
    code = 2
    state = "runtime_failure"
print(state)
print(code)
print(screenshot)
print(result_url)
print(selected_page_url)
print(selected_frame_url)
PY
)
  status="${parsed[0]}"
  exit_code="${parsed[1]}"
  screenshot="${parsed[2]}"
  result_url="${parsed[3]}"
  selected_page_url="${parsed[4]}"
  selected_frame_url="${parsed[5]}"
fi

python3 - <<'PY' "$STATUS_FILE" "$status" "$exit_code" "$screenshot" "$result_url" "${selected_page_url:-}" "${selected_frame_url:-}"
import json
import sys
from datetime import datetime, timezone
path, status, exit_code, screenshot, result_url, selected_page_url, selected_frame_url = sys.argv[1:]
data = {
    "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "status": status,
    "exit_code": int(exit_code),
    "last_screenshot_path": screenshot,
    "result_url": result_url,
    "selected_page_url": selected_page_url,
    "selected_frame_url": selected_frame_url,
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
PY

log_line "ha_grant_pipeline selected_page_url=${selected_page_url:-} selected_frame_url=${selected_frame_url:-}"
log_line "ha_grant_pipeline status=${status} exit_code=${exit_code} last_screenshot_path=${screenshot} result_url=${result_url}"

post_to_ha "$status" "$screenshot" "$result_url"
exit "$exit_code"
