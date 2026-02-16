#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"
QUEUE_DIR="$ROOT_DIR/runtime/queue"
PENDING_FILE="$QUEUE_DIR/pending.jsonl"
HISTORY_FILE="$QUEUE_DIR/history.jsonl"
LOG_FILE="$ROOT_DIR/logs/pipeline.log"

mkdir -p "$QUEUE_DIR" "$ROOT_DIR/logs"
touch "$PENDING_FILE" "$HISTORY_FILE"

log_line() {
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" >>"$LOG_FILE"
}

if [[ ! -s "$PENDING_FILE" ]]; then
  log_line "grant_queue_run queue_empty"
  exit 0
fi

tmp_pending="$(mktemp)"
head -n 1 "$PENDING_FILE" > "$tmp_pending.job"
tail -n +2 "$PENDING_FILE" > "$tmp_pending"
mv "$tmp_pending" "$PENDING_FILE"
job_line="$(cat "$tmp_pending.job")"
rm -f "$tmp_pending.job"

readarray -t parsed < <(python3 - <<'PY' "$job_line"
import json
import sys
line = sys.argv[1]
try:
    obj = json.loads(line)
except Exception:
    print("")
    print("false")
    print("invalid_job_json")
    raise SystemExit(0)
program_id = str(obj.get("program_id", "")).strip()
dry_run = bool(obj.get("dry_run", False))
job_id = str(obj.get("job_id", "")).strip()
print(program_id)
print("true" if dry_run else "false")
print(job_id)
PY
)

program_id="${parsed[0]}"
dry_run="${parsed[1]}"
job_id="${parsed[2]}"

if [[ -z "$program_id" ]]; then
  log_line "grant_queue_run invalid_job missing_program_id"
  python3 - <<'PY' "$HISTORY_FILE" "$job_line"
import json
import sys
from datetime import datetime, timezone
hist, line = sys.argv[1], sys.argv[2]
entry = {
    "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "job_raw": line,
    "status": "invalid_job",
    "reason": "missing_program_id",
}
with open(hist, "a", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")
PY
  exit 2
fi

log_line "grant_queue_run start program_id=${program_id} dry_run=${dry_run} job_id=${job_id:-<none>}"

set +e
if [[ "$dry_run" == "true" ]]; then
  PROGRAM_ID="$program_id" DRY_RUN=1 "$ROOT_DIR/bin/ha_grant_pipeline.sh"
  rc=$?
else
  PROGRAM_ID="$program_id" "$ROOT_DIR/bin/ha_grant_pipeline.sh"
  rc=$?
fi
set -e

state_file="$ROOT_DIR/runtime/programs/$program_id/state.json"
if [[ ! -f "$state_file" ]]; then
  state_file="$ROOT_DIR/runtime/ha_grant_pipeline_status.json"
fi

readarray -t state_parsed < <(python3 - <<'PY' "$state_file"
import json
import sys
p = sys.argv[1]
try:
    obj = json.load(open(p, "r", encoding="utf-8"))
except Exception:
    obj = {}
print(str(obj.get("status", "")))
print(str(obj.get("last_screenshot_path", "")))
print(str(obj.get("result_url", "")))
PY
)
status="${state_parsed[0]}"
screenshot="${state_parsed[1]}"
result_url="${state_parsed[2]}"

python3 - <<'PY' "$HISTORY_FILE" "$job_line" "$program_id" "$status" "$rc" "$screenshot" "$result_url"
import json
import sys
from datetime import datetime, timezone
hist, job_line, program_id, status, rc, screenshot, result_url = sys.argv[1:]
entry = {
    "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "job": json.loads(job_line),
    "program_id": program_id,
    "status": status,
    "runner_exit_code": int(rc),
    "last_screenshot_path": screenshot,
    "result_url": result_url,
}
with open(hist, "a", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")
PY

log_line "grant_queue_run done program_id=${program_id} status=${status} rc=${rc}"

if [[ "$status" == "captcha_required" || "$status" == "dry_run_captcha_required" ]]; then
  log_line "grant_queue_run stop_on_captcha program_id=${program_id} screenshot=${screenshot}"
  exit 1
fi

if [[ "$status" == "success" || "$status" == "dry_run_success" ]]; then
  exit 0
fi

exit 2
