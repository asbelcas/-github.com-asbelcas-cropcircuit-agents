#!/usr/bin/env bash
set -e

TREND="$(./bin/predict_failure.py)"

if [[ "$TREND" == "failure_likely" ]]; then
  CRON="*/1 * * * *"
else
  CRON="*/5 * * * *"
fi

( crontab -l 2>/dev/null | grep -v ha_health_check.sh ; \
  echo "$CRON cd /home/asbelcas/cropcircuit && /home/asbelcas/cropcircuit/bin/ha_health_check.sh" ) | crontab -
