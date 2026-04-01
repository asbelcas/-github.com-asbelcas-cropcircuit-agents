#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p "$ROOT_DIR/logs" "$ROOT_DIR/patches/pending"

LOCK_FILE="$ROOT_DIR/.grant_autopilot.lock"
LOG_FILE="$ROOT_DIR/grant_autopilot.log"
CLAUDE_LOG="$ROOT_DIR/logs/claude_reviews.log"
FUNDING_LOG="$ROOT_DIR/logs/funding_moves.log"
CAPITAL_LOG="$ROOT_DIR/logs/capital_events.log"
ADAPT_LAST="$ROOT_DIR/logs/adaptive_last.json"
AUTOPILOT_DRY_RUN="${AUTOPILOT_DRY_RUN:-0}"
HA_POLL_INTERVAL_SECONDS="${HA_POLL_INTERVAL_SECONDS:-30}"
HA_POLL_ATTEMPTS="${HA_POLL_ATTEMPTS:-3}"

if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.grant"
fi

# Ensure user-local bin is in PATH (needed when running from cron)
export PATH="$PATH:/home/asbelcas/.local/bin"

if [[ "$AUTOPILOT_DRY_RUN" != "0" && "$AUTOPILOT_DRY_RUN" != "1" ]]; then
  echo "ERROR: AUTOPILOT_DRY_RUN must be 0 or 1" >&2
  exit 2
fi

if [[ "$AUTOPILOT_DRY_RUN" == "0" && -z "${GMAIL_APP_PASSWORD:-}" ]]; then
  echo "ERROR: live autopilot requires GMAIL_APP_PASSWORD in environment or .env.grant" >&2
  exit 2
fi

normalize_url() {
  local raw="${1%/}"
  if [[ "$raw" =~ ^https?:// ]]; then
    printf '%s\n' "$raw"
  else
    printf 'http://%s\n' "$raw"
  fi
}

check_ha_reachable() {
  local base_url
  base_url="$(normalize_url "${HA_URL:-}")"
  [[ -z "$base_url" ]] && return 1
  curl -sS --max-time 4 "${base_url}/api/" >/dev/null 2>&1
}

latest_failures() {
  python3 - <<'PY'
import csv
from pathlib import Path
p=Path('automation_runs.csv')
if not p.exists():
    print(0)
    raise SystemExit
last=None
with p.open(newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f):
        last=r
if not last:
    print(0)
    raise SystemExit
initial=int((last.get('initial_failed') or '0').strip() or 0)
follow=int((last.get('followup_failed') or '0').strip() or 0)
print(initial+follow)
PY
}

latest_run_date() {
  python3 - <<'PY'
import csv
from pathlib import Path
p=Path('automation_runs.csv')
if not p.exists():
    print('<none>')
    raise SystemExit
last=None
with p.open(newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f):
        last=r
print((last or {}).get('run_date','<none>'))
PY
}

ha_state() {
  local f="$ROOT_DIR/logs/ha_health.log"
  if [[ ! -f "$f" ]]; then
    echo "unknown"
    return
  fi
  local line
  line="$(tail -n 1 "$f" 2>/dev/null || true)"
  if [[ "$line" == *"HA health OK"* ]]; then
    echo "ok"
  elif [[ "$line" == *"HA health DOWN"* ]]; then
    echo "down"
  else
    echo "unknown"
  fi
}

funding_idle_recent() {
  local c
  c="$(grep -c '\"event\":\"capital_move_selected\"' "$CAPITAL_LOG" 2>/dev/null || true)"
  if [[ "${c:-0}" -eq 0 ]]; then
    echo 1
  else
    echo 0
  fi
}

is_channel_overconcentrated() {
  local ch="$1"
  python3 - "$CAPITAL_LOG" "$ch" <<'PY'
import json, sys
from pathlib import Path
log = Path(sys.argv[1])
target = (sys.argv[2] or "").strip().lower()
if not log.exists() or not target:
    print(0); raise SystemExit
rows = []
for ln in log.read_text(encoding="utf-8", errors="replace").splitlines():
    try:
        j = json.loads(ln)
    except Exception:
        continue
    if j.get("event") == "capital_move_selected":
        c = str(j.get("channel", "")).lower()
        if c:
            rows.append(c)
if len(rows) < 3:
    print(0); raise SystemExit
from collections import Counter
ctr = Counter(rows)
dominant_channel, dominant_count = ctr.most_common(1)[0]
unique = len(ctr)
over = 1 if (target == dominant_channel and dominant_count / len(rows) >= 0.8 and unique <= 2) else 0
print(over)
PY
}

generate_status() {
python3 - <<'PY'
import csv, json, os
from pathlib import Path
from datetime import datetime

root = Path('.').resolve()
runs = root / 'automation_runs.csv'
outreach = root / 'outreach_log.csv'
status_file = root / 'grant_autopilot_status.md'
ha_ok_file = root / 'logs' / 'ha_health_last_ok.txt'
claude_log = root / 'logs' / 'claude_reviews.log'
adapt_last = root / 'logs' / 'adaptive_last.json'
funding_metrics = root / 'logs' / 'funding_metrics.jsonl'

latest = None
if runs.exists():
    with runs.open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            latest = row

counts = {}
if outreach.exists():
    with outreach.open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            s = (row.get('Status') or 'UNKNOWN').strip()
            counts[s] = counts.get(s, 0) + 1

lines = []
lines.append("# Grant Autopilot Status\n")
lines.append(f"Updated: {datetime.utcnow().replace(microsecond=0).isoformat()}Z\n")
if latest:
    lines.append("## Latest Run")
    lines.append(f"- run_date: {latest.get('run_date','')}")
    lines.append(f"- initial_sent: {latest.get('initial_sent','0')}")
    lines.append(f"- initial_failed: {latest.get('initial_failed','0')}")
    lines.append(f"- followup_sent: {latest.get('followup_sent','0')}")
    lines.append(f"- followup_failed: {latest.get('followup_failed','0')}")
    lines.append("")

lines.append("## Outreach Status Counts")
for k in sorted(counts):
    lines.append(f"- {k}: {counts[k]}")
lines.append("")

ha_url = (os.environ.get('HA_URL') or '').strip()
ha_fallbacks = (os.environ.get('HA_URL_FALLBACKS') or '').strip()
lines.append("## HA Connectivity Config")
lines.append(f"- HA_URL: {ha_url if ha_url else '<unset>'}")
lines.append(f"- HA_URL_FALLBACKS: {ha_fallbacks if ha_fallbacks else '<unset>'}")
lines.append("")

lines.append("## Thin Status Dashboard")
if ha_ok_file.exists():
    lines.append(f"- last_successful_ha_check: {ha_ok_file.read_text(encoding='utf-8').strip()}")
else:
    lines.append("- last_successful_ha_check: <none>")
if latest:
    lines.append(f"- last_autopilot_run: {latest.get('run_date','<unknown>')}")
else:
    lines.append("- last_autopilot_run: <none>")
snippet = "<none>"
if claude_log.exists():
    last = ""
    with claude_log.open(encoding='utf-8') as f:
        for row in f:
            if "[review]" in row:
                last = row
    if last:
        snippet = last.split("[review]", 1)[1].strip()[:140]
lines.append(f"- last_claude_review: {snippet}")
lines.append("")

lines.append("## Funding KPI")
metric_now = {}
metric_prev = {}
if funding_metrics.exists():
    rows = [ln for ln in funding_metrics.read_text(encoding='utf-8', errors='replace').splitlines() if ln.strip()]
    if rows:
        try:
            metric_now = json.loads(rows[-1])
        except Exception:
            metric_now = {}
    if len(rows) > 1:
        try:
            metric_prev = json.loads(rows[-2])
        except Exception:
            metric_prev = {}
score_now = metric_now.get('funding_probability_score', 0)
score_prev = metric_prev.get('funding_probability_score', score_now)
trend = "flat"
if score_now > score_prev:
    trend = "up"
elif score_now < score_prev:
    trend = "down"
lines.append(f"- funding_probability_score: {score_now}")
lines.append(f"- funding_probability_score_trend: {trend}")
lines.append(f"- partner_count: {metric_now.get('partner_count', 0)}")
lines.append(f"- capital_events: {metric_now.get('capital_events', 0)}")
lines.append(f"- channel_diversity: {metric_now.get('channel_diversity', 0)}")
lines.append(f"- recurring_revenue_signals: {metric_now.get('recurring_revenue_signals', 0)}")
lines.append(f"- infrastructure_capital_events: {metric_now.get('infrastructure_capital_events', 0)}")
lines.append(f"- single_source_dependency: {metric_now.get('single_source_dependency', 0)}")
lines.append("")

lines.append("## Last Adaptive Change")
if adapt_last.exists():
    try:
        data = json.loads(adapt_last.read_text(encoding='utf-8'))
    except Exception:
        data = {}
    lines.append(f"- improvement: {data.get('improvement','<none>')}")
    lines.append(f"- risk: {data.get('risk','<none>')}")
    lines.append(f"- applied_or_staged: {data.get('action','<none>')}")
    lines.append(f"- outcome_delta: {data.get('outcome_delta','<none>')}")
else:
    lines.append("- improvement: <none>")
    lines.append("- risk: <none>")
    lines.append("- applied_or_staged: <none>")
    lines.append("- outcome_delta: <none>")
lines.append("")

status_file.write_text("\n".join(lines), encoding='utf-8')
print(status_file)
PY
}

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] autopilot already running; exiting" >> "$LOG_FILE"
  exit 0
fi

{
  ts_start="$(date '+%Y-%m-%d %H:%M:%S')"
  run_start_epoch="$(date +%s)"
  echo "[$ts_start] starting grant autopilot (dry_run=$AUTOPILOT_DRY_RUN)"

  if [[ "$AUTOPILOT_DRY_RUN" == "1" ]]; then
    DRY_RUN=1 "$ROOT_DIR/bin/grant_daily_run.sh"
  else
    "$ROOT_DIR/bin/grant_daily_run.sh"
  fi

  # HA callback path (non-fatal)
  if [[ -x "$ROOT_DIR/bin/ha_event" && -n "${HA_URL:-}" && -n "${HA_TOKEN:-}" ]]; then
    if "$ROOT_DIR/bin/ha_event" grant_autopilot "batch completed; see grant_autopilot_status.md"; then
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] ha_event callback delivered"
    else
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] ha_event callback failed; switching to polling fallback"
      i=1
      while (( i <= HA_POLL_ATTEMPTS )); do
        if check_ha_reachable; then
          echo "[$(date '+%Y-%m-%d %H:%M:%S')] polling fallback: HA reachable on attempt $i"
          break
        fi
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] polling fallback: HA still unreachable (attempt $i/$HA_POLL_ATTEMPTS)"
        sleep "$HA_POLL_INTERVAL_SECONDS"
        ((i+=1))
      done
    fi
  fi

  # Failure prediction before reviewer loop
  AUTOPILOT_SAFE_MODE="${AUTOPILOT_SAFE_MODE:-0}"
  if [[ -x "$ROOT_DIR/bin/predict_failure.py" ]]; then
    TREND="$("$ROOT_DIR/bin/predict_failure.py" 2>/dev/null || echo stable)"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] prediction_trend=$TREND"
    if [[ "$TREND" == "failure_likely" ]]; then
      AUTOPILOT_SAFE_MODE=1
      export AUTOPILOT_SAFE_MODE=1
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] [adaptive] switching to conservative mode"
    fi
  else
    TREND="unknown"
  fi

  CURRENT_FAILURES="$(latest_failures)"
  CURRENT_HA_STATE="$(ha_state)"
  BLOCKING_FUNDING=0
  if [[ "${CURRENT_FAILURES:-0}" -gt 0 || "$CURRENT_HA_STATE" != "ok" ]]; then
    BLOCKING_FUNDING=1
  fi
  FUNDING_IDLE="$(funding_idle_recent)"
  export BLOCKING_FUNDING FUNDING_IDLE
  CURRENT_STRATEGY="funding"
  if [[ -x "$ROOT_DIR/bin/select_strategy.sh" ]]; then
    CURRENT_STRATEGY="$("$ROOT_DIR/bin/select_strategy.sh" 2>/dev/null | tail -n 1 || echo funding)"
  fi
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] policy_vector=stability blocking_funding=$BLOCKING_FUNDING funding_idle=$FUNDING_IDLE strategy=$CURRENT_STRATEGY"

  # Adaptive reviewer + patch engine (optional, non-fatal)
  if [[ -x "$ROOT_DIR/bin/build_review_packet.sh" && -x "$ROOT_DIR/bin/claude_review.sh" && -x "$ROOT_DIR/bin/adaptive_patch_engine.py" ]]; then
    reviewer_packet="$($ROOT_DIR/bin/build_review_packet.sh 2>/dev/null || true)"
    if [[ -n "$reviewer_packet" ]]; then
      review_out="$(printf '%s\n' "$reviewer_packet" | "$ROOT_DIR/bin/claude_review.sh" 2>&1 || true)"
      ts="$(date '+%Y-%m-%d %H:%M:%S')"
      echo "[$ts] [packet] $(printf '%s' "$reviewer_packet" | tr '\n' ' ' | head -c 220)" >> "$CLAUDE_LOG"
      echo "[$ts] [review] $(printf '%s' "$review_out" | tr '\n' ' ' | head -c 700)" >> "$CLAUDE_LOG"

      if [[ "${AUTOPILOT_SAFE_MODE:-0}" == "1" ]]; then
        apply_out=$'action=log_only\nrisk=high\nnote=conservative_mode_active'
      else
        review_patch_type="$(printf '%s\n' "$review_out" | awk '/^PATCH_TYPE:/{getline; print tolower($0); exit}' | tr -d '[:space:]')"
        if [[ "$review_patch_type" != "funding" && "$BLOCKING_FUNDING" != "1" ]]; then
          apply_out=$'action=log_only\nrisk=medium\nnote=policy_block_non_funding_patch'
        else
          review_tmp="$(mktemp)"
          printf '%s\n' "$review_out" > "$review_tmp"
          apply_out="$($ROOT_DIR/bin/adaptive_patch_engine.py apply --root "$ROOT_DIR" --review-file "$review_tmp" 2>/dev/null || true)"
          rm -f "$review_tmp"
        fi
      fi

      action="$(printf '%s\n' "$apply_out" | awk -F= '/^action=/{print $2}')"
      risk="$(printf '%s\n' "$apply_out" | awk -F= '/^risk=/{print $2}')"
      note="$(printf '%s\n' "$apply_out" | awk -F= '/^note=/{sub(/^note=/,""); print}')"

      if [[ "$action" == "auto_patch_applied" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] auto_patch_applied risk=$risk note=$note"

        before_failures="$(latest_failures)"
        before_latency="$(( $(date +%s) - run_start_epoch ))"
        ha_before="$(ha_state)"

        eval_start="$(date +%s)"
        DRY_RUN=1 "$ROOT_DIR/bin/grant_daily_run.sh" >/dev/null 2>&1 || true
        eval_end="$(date +%s)"
        after_latency="$(( eval_end - eval_start ))"

        "$ROOT_DIR/bin/ha_health_check.sh" >/dev/null 2>&1 || true
        ha_after="$(ha_state)"
        after_failures="$(latest_failures)"

        eval_out="$($ROOT_DIR/bin/adaptive_patch_engine.py evaluate --root "$ROOT_DIR" --before-failures "$before_failures" --after-failures "$after_failures" --before-latency "$before_latency" --after-latency "$after_latency" --ha-before "$ha_before" --ha-after "$ha_after" 2>/dev/null || true)"
        delta="$(printf '%s\n' "$eval_out" | awk -F= '/^delta=/{sub(/^delta=/,""); print}')"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] adaptive_delta ${delta:-<none>}"

      elif [[ "$action" == "staged" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] adaptive_patch_staged risk=$risk note=$note"
      else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] adaptive_log_only risk=$risk note=$note"
      fi
    fi
  fi

  # Funding intelligence (second Claude call, non-fatal)
  if [[ -x "$ROOT_DIR/bin/funding_packet.sh" ]]; then
    FUNDING_PACKET="$("$ROOT_DIR/bin/funding_packet.sh" 2>/dev/null || true)"
    if [[ -n "$FUNDING_PACKET" ]]; then
      funding_out="$(
        timeout 30s claude -p "
You are assisting an automation system that manages a regenerative agriculture project.

This is NOT creative writing.
This is operational decision support.
PRIMARY OBJECTIVE: STABILITY
TARGET: reliable monthly baseline income without dependence on a single source.
OPTIMIZE FOR: recurring revenue, diversified channels, low maintenance cash flow, infrastructure-strengthening capital.
AVOID: short-term spikes with no repeatability, constant manual attention, single partner/platform/grant dependency.

Context:
$FUNDING_PACKET

Goal:
Recommend ONE operational move with strongest expected financial impact.

Respond ONLY:

MOVE:
<one concrete action>

CHANNEL:
(grant|donor|partnership|product)

NEXT_STEP:
<immediate executable step>
" || echo "CLAUDE_FUNDING:TIMEOUT"
      )"

      ts="$(date '+%Y-%m-%d %H:%M:%S')"
      {
        echo "[$ts] [funding-packet] $(printf '%s' "$FUNDING_PACKET" | tr '\n' ' ' | head -c 260)"
        printf '%s\n' "$funding_out"
      } >> "$FUNDING_LOG" 2>&1 || true

      move="$(printf '%s\n' "$funding_out" | awk '/^MOVE:/{getline; print; exit}')"
      channel="$(printf '%s\n' "$funding_out" | awk '/^CHANNEL:/{getline; print; exit}' | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
      next_step="$(printf '%s\n' "$funding_out" | awk '/^NEXT_STEP:/{getline; print; exit}')"

      funding_accepted=1
      if [[ "$channel" == "product" && "$FUNDING_IDLE" != "1" ]]; then
        funding_accepted=0
      fi
      if [[ "$CURRENT_STRATEGY" == "outreach" && ! "$channel" =~ ^(grant|donor|partnership)$ ]]; then
        funding_accepted=0
      fi
      if printf '%s %s\n' "$move" "$next_step" | tr '[:upper:]' '[:lower:]' | grep -qE '(vanity|social growth|experimental|experiment)'; then
        funding_accepted=0
      fi
      if printf '%s %s\n' "$move" "$next_step" | tr '[:upper:]' '[:lower:]' | grep -qE '(manual|constant attention|daily hand|one-off spike|short-term)'; then
        funding_accepted=0
      fi
      if [[ "$(is_channel_overconcentrated "$channel" 2>/dev/null || echo 0)" == "1" ]]; then
        funding_accepted=0
      fi

      if [[ "$funding_accepted" == "1" && -n "${move// }" ]]; then
        printf '{"ts":"%s","event":"capital_move_selected","channel":"%s","move":"%s","next_step":"%s"}\n' \
          "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$channel" "$(printf '%s' "$move" | tr '"' "'")" "$(printf '%s' "$next_step" | tr '"' "'")" \
          >> "$CAPITAL_LOG"
      else
        printf '{"ts":"%s","event":"capital_move_rejected","channel":"%s","reason":"policy_filter"}\n' \
          "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$channel" >> "$CAPITAL_LOG"
      fi
    fi
  fi

  # Write runs.jsonl for predictors (non-fatal)
  python3 - <<'PY' 2>/dev/null || true
import json
from datetime import datetime
from pathlib import Path
root = Path('.')
log = root / 'grant_autopilot.log'
ha = root / 'logs' / 'ha_health.log'
runs = root / 'logs' / 'runs.jsonl'
last_autop = ''
if log.exists():
    lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
    last_autop = '\\n'.join(lines[-3:])
last_ha = ''
if ha.exists():
    lines = ha.read_text(encoding='utf-8', errors='replace').splitlines()
    last_ha = lines[-1] if lines else ''
payload = {
    'ts': datetime.utcnow().replace(microsecond=0).isoformat() + 'Z',
    'last_autopilot': last_autop,
    'last_ha': last_ha,
}
runs.parent.mkdir(parents=True, exist_ok=True)
with runs.open('a', encoding='utf-8') as f:
    f.write(json.dumps(payload) + '\\n')
PY

  # Adaptive scheduler (non-fatal)
  if [[ -x "$ROOT_DIR/bin/adaptive_scheduler.sh" ]]; then
    "$ROOT_DIR/bin/adaptive_scheduler.sh" 2>&1 | sed 's/^/[scheduler] /' || true
  fi

  # Funding KPI snapshot (non-fatal)
  if [[ -x "$ROOT_DIR/bin/funding_metrics.py" ]]; then
    metrics_out="$("$ROOT_DIR/bin/funding_metrics.py" 2>/dev/null || true)"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] funding_metrics ${metrics_out:-<none>}"
  fi

  generate_status >/dev/null 2>&1 || true
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] grant autopilot complete"
} >> "$LOG_FILE" 2>&1

echo "[adaptive] prediction:"
./bin/predict_failure.py >> logs/adaptive_state.json 2>&1 || true

echo "[adaptive] funding:"
timeout 30s claude -p "
You are assisting an automation system that manages a regenerative agriculture project.

This is NOT creative writing.
This is operational decision support.
PRIMARY OBJECTIVE: STABILITY
TARGET: reliable monthly baseline income without dependence on a single source.
OPTIMIZE FOR: recurring revenue, diversified channels, low maintenance cash flow, infrastructure-strengthening capital.
AVOID: short-term spikes with no repeatability, constant manual attention, single partner/platform/grant dependency.

Context:
$(./bin/funding_packet.sh)

Goal:
Recommend ONE operational move that increases funding probability.

Respond ONLY:

MOVE:
<one concrete action>

CHANNEL:
(grant|donor|partnership|product)

NEXT_STEP:
<immediate executable step>
" >> logs/funding_moves.log 2>&1 || true

echo "[adaptive] scheduling:"
./bin/adaptive_scheduler.sh || true
