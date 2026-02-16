#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.grant"
fi

topology="host"
if grep -qaE '(docker|containerd|kubepods)' /proc/1/cgroup 2>/dev/null; then
  topology="container"
elif [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
  topology="wsl"
fi

ha_url="${HA_URL:-<unset>}"
last_run="$(tail -n 1 "$ROOT_DIR/automation_runs.csv" 2>/dev/null || echo '<none>')"

i_sent="<na>"; i_failed="<na>"; f_sent="<na>"; f_failed="<na>"
if [[ "$last_run" != "<none>" ]]; then
  IFS=',' read -r _ts _date _dry i_due i_sent i_failed manual f1_due f2_due f_sent f_failed <<<"$last_run"
fi

log_tail="$(tail -n 3 "$ROOT_DIR/grant_autopilot.log" 2>/dev/null | tr '\n' '|' || true)"
log_tail="${log_tail:-<none>}"

packet=$(
cat <<EOF
review_packet_v1
topology=${topology}
ha_url=${ha_url}
last_run_initial_sent=${i_sent}
last_run_initial_failed=${i_failed}
last_run_followup_sent=${f_sent}
last_run_followup_failed=${f_failed}
last_log_tail=${log_tail}
question=highest ROI reliability/funding tweak with lowest effort?
EOF
)

# Hard caps: <=25 lines and <=1200 chars
packet="$(printf '%s' "$packet" | head -n 25 | head -c 1200)"
printf '%s\n' "$packet"
