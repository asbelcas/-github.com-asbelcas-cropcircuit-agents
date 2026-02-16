#!/usr/bin/env bash
# ha_pipeline_watcher.sh — Polls for trigger files from HA and runs the grant pipeline.
# Runs on the HOST (not inside Docker).
# HA shell_command writes a trigger file to /opt/homeassistant/config/grant_triggers/
# This watcher picks it up, runs the pipeline, and writes results back.
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"
TRIGGER_DIR="/opt/homeassistant/config/grant_triggers"
RESULT_DIR="/opt/homeassistant/config/grant_results"
LOG_FILE="$ROOT_DIR/logs/pipeline_watcher.log"
POLL_INTERVAL=3
DONOR_PAYLOAD_FILE="$TRIGGER_DIR/donor_lead_payload.json"

export DISPLAY="${DISPLAY:-:0}"
export HOME="${HOME:-/home/asbelcas}"

# Source environment
if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  set -a
  source "$ROOT_DIR/.env.grant"
  set +a
fi

mkdir -p "$TRIGGER_DIR" "$RESULT_DIR" "$(dirname "$LOG_FILE")"

log() {
  echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$LOG_FILE"
}

log "Pipeline watcher started (PID $$)"

while true; do
  # Auto-bridge donor payload file (webhook/file writers can drop payload here).
  if [[ -s "$DONOR_PAYLOAD_FILE" ]]; then
    log "Detected donor payload file: $(basename "$DONOR_PAYLOAD_FILE")"
    set +e
    python3 "$ROOT_DIR/bin/donor_lead_bridge.py" \
      --input-file "$DONOR_PAYLOAD_FILE" \
      --trigger-donor-intake >> "$LOG_FILE" 2>&1
    rc_payload=$?
    set -e
    if [[ $rc_payload -eq 0 ]]; then
      rm -f "$DONOR_PAYLOAD_FILE"
      log "Donor payload file bridged and cleared"
    else
      log "Donor payload bridge failed rc=$rc_payload (file retained for retry)"
    fi
  fi

  for trigger in "$TRIGGER_DIR"/trigger_*.json; do
    [[ -f "$trigger" ]] || continue

    trigger_name="$(basename "$trigger")"
    log "Processing trigger: $trigger_name"

    # Read trigger contents
    action="run"
    program_id=""
    extra_args=()
    donor_name=""
    donor_email=""
    donor_phone=""
    donor_interest=""
    donor_amount_range=""
    donor_message=""
    donor_source=""
    if command -v python3 >/dev/null; then
      action="$(python3 -c "import json,sys; d=json.loads(open('$trigger').read()); print(d.get('action','run'))" 2>/dev/null || echo "run")"
      dry_run="$(python3 -c "import json,sys; d=json.loads(open('$trigger').read()); print(str(d.get('dry_run',False)).lower())" 2>/dev/null || echo "false")"
      program_id="$(python3 -c "import json,sys; d=json.loads(open('$trigger').read()); print(d.get('program_id',''))" 2>/dev/null || echo "")"
      donor_name="$(python3 -c "import json,sys; d=json.loads(open('$trigger').read()); print(d.get('name',''))" 2>/dev/null || echo "")"
      donor_email="$(python3 -c "import json,sys; d=json.loads(open('$trigger').read()); print(d.get('email',''))" 2>/dev/null || echo "")"
      donor_phone="$(python3 -c "import json,sys; d=json.loads(open('$trigger').read()); print(d.get('phone',''))" 2>/dev/null || echo "")"
      donor_interest="$(python3 -c "import json,sys; d=json.loads(open('$trigger').read()); print(d.get('interest',''))" 2>/dev/null || echo "")"
      donor_amount_range="$(python3 -c "import json,sys; d=json.loads(open('$trigger').read()); print(d.get('amount_range',''))" 2>/dev/null || echo "")"
      donor_message="$(python3 -c "import json,sys; d=json.loads(open('$trigger').read()); print(d.get('message',''))" 2>/dev/null || echo "")"
      donor_source="$(python3 -c "import json,sys; d=json.loads(open('$trigger').read()); print(d.get('source',''))" 2>/dev/null || echo "")"
      if [[ "$dry_run" == "true" ]]; then
        extra_args+=("--dry-run")
      fi
      if [[ -n "$program_id" ]]; then
        extra_args+=("--program-id" "$program_id")
      fi
    fi

    # Remove trigger immediately to prevent re-processing
    rm -f "$trigger"

    # Temporarily disable errexit for pipeline execution (non-zero exit is normal)
    set +e
    case "$action" in
      run)
        log "Running pipeline (args: ${extra_args[*]:-none})"
        "$ROOT_DIR/bin/ha_grant_pipeline.sh" "${extra_args[@]}" >> "$LOG_FILE" 2>&1
        rc=$?
        log "Pipeline completed with exit code $rc"
        ;;
      resume)
        log "Running pipeline in resume mode"
        "$ROOT_DIR/bin/ha_grant_pipeline.sh" --resume "${extra_args[@]}" >> "$LOG_FILE" 2>&1
        rc=$?
        log "Pipeline resume completed with exit code $rc"
        ;;
      ingest)
        log "Running morning targets ingestion"
        python3 "$ROOT_DIR/bin/pull_targets_imap.py" >> "$LOG_FILE" 2>&1
        rc=$?
        log "Ingestion completed with exit code $rc"
        ;;
      scan)
        log "Running opportunity scan"
        python3 "$ROOT_DIR/bin/opportunity_scanner.py" >> "$LOG_FILE" 2>&1
        rc=$?
        log "Opportunity scan completed with exit code $rc"
        ;;
      donor_intake)
        log "Processing donor intake"
        python3 "$ROOT_DIR/bin/donor_intake_handler.py" >> "$LOG_FILE" 2>&1
        rc=$?
        log "Donor intake completed with exit code $rc"
        ;;
      donor_webhook)
        log "Processing donor webhook payload"
        DONOR_NAME="$donor_name" \
        DONOR_EMAIL="$donor_email" \
        DONOR_PHONE="$donor_phone" \
        DONOR_INTEREST="$donor_interest" \
        DONOR_AMOUNT_RANGE="$donor_amount_range" \
        DONOR_MESSAGE="$donor_message" \
        DONOR_SOURCE="$donor_source" \
        python3 "$ROOT_DIR/bin/donor_lead_bridge.py" --trigger-donor-intake >> "$LOG_FILE" 2>&1
        rc=$?
        log "Donor webhook bridge completed with exit code $rc"
        ;;
      donor_webhook_from_file)
        log "Processing donor webhook payload file"
        python3 "$ROOT_DIR/bin/donor_lead_bridge.py" \
          --input-file /opt/homeassistant/config/grant_triggers/donor_lead_payload.json \
          --trigger-donor-intake >> "$LOG_FILE" 2>&1
        rc=$?
        log "Donor webhook file bridge completed with exit code $rc"
        ;;
      status)
        log "Status check requested"
        rc=0
        ;;
      *)
        log "Unknown action: $action"
        rc=99
        ;;
    esac
    set -e

    # Copy status to HA-accessible location
    if [[ -f "$ROOT_DIR/runtime/ha_grant_pipeline_status.json" ]]; then
      cp "$ROOT_DIR/runtime/ha_grant_pipeline_status.json" "$RESULT_DIR/pipeline_status.json"
    fi

    # Copy latest screenshot to HA www for dashboard rendering
    HA_WWW="/opt/homeassistant/config/www/grant_screenshots"
    if [[ -d "$HA_WWW" ]]; then
      latest_screenshot="$(python3 -c "
import json
try:
    d=json.load(open('$ROOT_DIR/runtime/ha_grant_pipeline_status.json'))
    print(d.get('last_screenshot_path',''))
except: pass
" 2>/dev/null)"
      if [[ -n "$latest_screenshot" && -f "$latest_screenshot" ]]; then
        cp "$latest_screenshot" "$HA_WWW/latest.png"
        log "Screenshot copied to $HA_WWW/latest.png"
      fi
    fi

    # Copy morning targets to HA-accessible location
    if [[ -f "$ROOT_DIR/runtime/morning_targets.json" ]]; then
      cp "$ROOT_DIR/runtime/morning_targets.json" "$RESULT_DIR/morning_targets.json"
    fi

    # Copy opportunity queue to HA-accessible location
    if [[ -f "$ROOT_DIR/runtime/opportunity_queue.json" ]]; then
      cp "$ROOT_DIR/runtime/opportunity_queue.json" "$RESULT_DIR/opportunity_queue.json"
    fi

    # Write result file
    python3 -c "
import json
from datetime import datetime, timezone
result = {
    'trigger': '$trigger_name',
    'action': '$action',
    'exit_code': $rc,
    'timestamp_utc': datetime.now(timezone.utc).isoformat(),
}
print(json.dumps(result, indent=2))
" > "$RESULT_DIR/last_result.json" 2>/dev/null || true

    log "Result written to $RESULT_DIR/last_result.json"
  done

  sleep "$POLL_INTERVAL"
done
