#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/asbelcas/cropcircuit"
LOG="$ROOT/logs/funding_efficiency.log"
DONOR_JSONL="$ROOT/logs/donor_web.log.jsonl"

mkdir -p "$ROOT/logs" "$ROOT/runtime"

log() {
  printf '%s %s\n' "$(date -Is)" "$1" >> "$LOG"
}

cd "$ROOT"

# Keep nurture queue moving every run.
python3 "$ROOT/bin/donor_nurture_runner.py" >> "$LOG" 2>&1 || true

new_leads_30m=0
if [[ -f "$DONOR_JSONL" ]]; then
  new_leads_30m="$(python3 - "$DONOR_JSONL" <<'PY'
import json, sys
from datetime import datetime, timezone, timedelta
p = sys.argv[1]
cut = datetime.now(timezone.utc) - timedelta(minutes=30)
n = 0
with open(p, "r", encoding="utf-8") as f:
    for line in f:
        line=line.strip()
        if not line:
            continue
        try:
            r=json.loads(line)
            if not r.get("accepted"):
                continue
            ts = datetime.fromisoformat(str(r.get("timestamp_utc","")).replace("Z","+00:00"))
            if ts >= cut:
                n += 1
        except Exception:
            pass
print(n)
PY
)"
fi

log "new_leads_last_30m=$new_leads_30m"

if [[ "$new_leads_30m" -eq 0 ]]; then
  log "idle_detected applying_actions=nurture_check+tunnel_check+daily_summary"
  systemctl --user is-active donor-tunnel >/dev/null 2>&1 || systemctl --user restart donor-tunnel || true
  python3 "$ROOT/bin/donor_daily_summary.py" >> "$LOG" 2>&1 || true
  echo "$(date -Is) suggestion: test fresh social-share post with /share copy and one proof screenshot link" >> "$ROOT/logs/funnel_improvements.log"
else
  log "active_flow continuing_nurture"
fi
