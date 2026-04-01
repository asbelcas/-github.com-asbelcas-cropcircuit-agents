#!/usr/bin/env bash
# Setup script to register grant shell commands in Home Assistant.
# Must run as root or with sudo since HA config files are root-owned.
#
# Usage: sudo bash bin/setup_ha_grant_commands.sh
set -euo pipefail

HA_SHELL_CMD="/opt/homeassistant/config/shell_commands.yaml"
SECTION_BEGIN="# === GRANT OUTREACH AUTOMATION (BEGIN) ==="
SECTION_END="# === GRANT OUTREACH AUTOMATION (END) ==="
HA_BASE_URL="${HA_URL:-http://localhost:8123}"

if [[ ! -f "$HA_SHELL_CMD" ]]; then
  echo "ERROR: $HA_SHELL_CMD not found"
  exit 1
fi

tmp_file="$(mktemp)"
MANAGED_KEYS_RE='^(grant_orchestrator_dryrun|grant_orchestrator_live|grant_send_single|grant_submit_dispatch_now|grant_submit_dispatch_watch|grant_live_intake|grant_dispatch_from_session|grant_mark_submitted|grant_pipeline_run|grant_pipeline_resume|grant_pipeline_dryrun|grant_pipeline_status|grant_targets_ingest|grant_pipeline_program|grant_pipeline_program_dryrun|grant_opportunity_scan|grant_donor_intake|grant_donor_write_lead|grant_donor_enqueue|x_post_queue_item|x_fetch_mentions|x_bot_status|ai_liaison_marketplace_run):'
awk -v begin="$SECTION_BEGIN" -v end="$SECTION_END" -v managed="$MANAGED_KEYS_RE" '
  $0 == begin {in_block=1; next}
  $0 == end {in_block=0; next}
  !in_block && $0 !~ managed {print}
' "$HA_SHELL_CMD" > "$tmp_file"

cat >> "$tmp_file" <<'YAML'

# === GRANT OUTREACH AUTOMATION (BEGIN) ===
grant_orchestrator_dryrun: "cd /home/asbelcas/cropcircuit && DRY_RUN=1 /home/asbelcas/cropcircuit/bin/grant_daily_run.sh"
grant_orchestrator_live: "bash -lc 'cd /home/asbelcas/cropcircuit && source /home/asbelcas/cropcircuit/.env.grant && /home/asbelcas/cropcircuit/bin/grant_daily_run.sh'"
grant_send_single: "bash -lc 'cd /home/asbelcas/cropcircuit && source /home/asbelcas/cropcircuit/.env.grant && python3 bin/send_grant_email.py {{ email_id | int }}'"
grant_submit_dispatch_now: "bash -lc 'cd /home/asbelcas/cropcircuit && source /home/asbelcas/cropcircuit/.env.grant && /home/asbelcas/cropcircuit/bin/grant_submission_realtime.sh --program \"USDA FSA Operating Microloan\" --force'"
grant_submit_dispatch_watch: "bash -lc 'cd /home/asbelcas/cropcircuit && source /home/asbelcas/cropcircuit/.env.grant && /home/asbelcas/cropcircuit/bin/grant_submission_realtime.sh --watch --force'"
grant_live_intake: "bash -lc 'cd /home/asbelcas/cropcircuit && source /home/asbelcas/cropcircuit/.env.grant && /home/asbelcas/cropcircuit/bin/grant-live'"
grant_dispatch_from_session: "bash -lc 'cd /home/asbelcas/cropcircuit && source /home/asbelcas/cropcircuit/.env.grant && /home/asbelcas/cropcircuit/bin/ha_dispatch_grant.sh --session /home/asbelcas/cropcircuit/runtime/grant_intake_session.json'"
grant_mark_submitted: "bash -lc 'cd /home/asbelcas/cropcircuit && source /home/asbelcas/cropcircuit/.env.grant && /home/asbelcas/cropcircuit/bin/ha_dispatch_grant.sh --mark-submitted --program \"{{ program }}\" --confirmation \"{{ confirmation }}\" --screenshot \"{{ screenshot }}\" --next-followup \"{{ followup }}\"'"
grant_pipeline_run: 'echo "{\"action\":\"run\"}" > /config/grant_triggers/trigger_run.json'
grant_pipeline_resume: 'echo "{\"action\":\"resume\"}" > /config/grant_triggers/trigger_resume.json'
grant_pipeline_dryrun: 'echo "{\"action\":\"run\",\"dry_run\":true}" > /config/grant_triggers/trigger_dryrun.json'
grant_pipeline_status: "cat /config/grant_results/pipeline_status.json 2>/dev/null || echo '{\"status\":\"unknown\"}'  "
grant_targets_ingest: 'echo "{\"action\":\"ingest\"}" > /config/grant_triggers/trigger_ingest.json'
grant_pipeline_program: "echo '{\"action\":\"run\",\"program_id\":\"{{ program_id }}\"}' > /config/grant_triggers/trigger_program.json"
grant_pipeline_program_dryrun: "echo '{\"action\":\"run\",\"program_id\":\"{{ program_id }}\",\"dry_run\":true}' > /config/grant_triggers/trigger_program_dryrun.json"
grant_opportunity_scan: 'echo "{\"action\":\"scan\"}" > /config/grant_triggers/trigger_scan.json'
grant_donor_intake: 'echo "{\"action\":\"donor_intake\"}" > /config/grant_triggers/trigger_donor.json'
# Keep this command template-free; donor payload should be written via rest_command -> /donor.
grant_donor_write_lead: 'echo "{\"action\":\"donor_webhook_from_file\"}" > /config/grant_triggers/trigger_donor_enqueue.json'
grant_donor_enqueue: 'echo "{\"action\":\"donor_webhook_from_file\"}" > /config/grant_triggers/trigger_donor_enqueue.json'
# --- X/Twitter Bot Commands ---
x_post_queue_item: 'echo "{\"action\":\"x_post_queue\"}" > /config/grant_triggers/trigger_x_post.json'
x_fetch_mentions: 'echo "{\"action\":\"x_fetch_mentions\"}" > /config/grant_triggers/trigger_x_mentions.json'
x_bot_status: "cat /config/grant_results/x_mentions.json 2>/dev/null || echo '{\"status\":\"no data\"}'"
ai_liaison_marketplace_run: 'echo "{\"action\":\"marketplace_liaison\"}" > /config/grant_triggers/trigger_marketplace_liaison.json'
# === GRANT OUTREACH AUTOMATION (END) ===
YAML

cp "$tmp_file" "$HA_SHELL_CMD"
rm -f "$tmp_file"
echo "Grant shell commands refreshed in $HA_SHELL_CMD"

# Reload HA shell commands
HA_TOKEN="${HA_TOKEN:-}"
if [[ -n "$HA_TOKEN" ]]; then
  echo "Reloading HA shell commands..."
  curl -sS -X POST \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" \
    "${HA_BASE_URL%/}/api/services/shell_command/reload" 2>/dev/null || true
  echo "Done. Verify in HA Developer Tools > Services > shell_command.*"
else
  echo "NOTE: Set HA_TOKEN to auto-reload, or restart HA manually."
fi
