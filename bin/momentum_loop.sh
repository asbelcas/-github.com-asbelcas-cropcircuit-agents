#!/usr/bin/env bash
set -euo pipefail
cd /home/asbelcas/cropcircuit

while true; do
  echo "=== $(date) MOMENTUM CYCLE START ==="

  # Pull Gmail targets (IMAP path)
  source /home/asbelcas/cropcircuit/.env.grant
  python3 bin/pull_targets_imap.py || echo "IMAP pull failed, continuing"

  # Refresh email candidate list (includes denylist/holdlist status)
  python3 bin/send_grant_email.py --list || true

  # Score opportunities
  python3 bin/score_opportunities.py || true

  # Watchdog memory + failure prediction
  python3 bin/system_memory_append.py || true
  python3 bin/predict_failure.py || true

  echo "=== $(date) CYCLE DONE. Sleeping 30 min ==="
  sleep 1800
done
