#!/usr/bin/env bash
set -euo pipefail
cd /home/asbelcas/cropcircuit

stamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
preflight="$(source .env.grant >/dev/null 2>&1 || true; python3 bin/preflight_imap.py 2>/dev/null || true)"
watchdog="$(pgrep -af 'automation_watchdog.sh' | grep -v 'offline_checkpoint.sh' | head -n 1 || true)"

{
  echo "[$stamp] CHECKPOINT auto_10m"
  echo "status=Active partner conversation — awaiting call outcome"
  echo "priority=Relationship progression > automated outreach"
  echo "preflight_imap=$preflight"
  if [[ -n "$watchdog" ]]; then
    echo "watchdog_running=$watchdog"
  else
    echo "watchdog_running=not_running"
  fi
  echo "imap_policy=If IMAP fails -> pause inbox-dependent tasks and continue offline prep"
  echo "[$stamp] CHECKPOINT end"
} >> runtime/system_health.log
