#!/usr/bin/env bash
cd /home/asbelcas/cropcircuit || exit

source .env.grant || true

while true; do
  echo "---- $(date) watchdog tick ----"
  sleep_seconds=600
  if [ -f runtime/call_support_mode.json ] && grep -qi '"active"[[:space:]]*:[[:space:]]*true' runtime/call_support_mode.json; then
    sleep_seconds=120
    echo "call_support_mode active — high-frequency inbox monitoring"
  fi

  # 1) verify DNS + IMAP health
  python3 bin/preflight_imap.py >/dev/null 2>&1

  if [ $? -ne 0 ]; then
      echo "IMAP preflight failed — pausing outbound"
      sleep "$sleep_seconds"
      continue
  fi

  # 2) pull replies
  python3 bin/pull_targets_imap.py >/dev/null 2>&1

  # 3) update email state
  touch runtime/email_state.json

  # 4) notify HA (non-fatal if HA down)
  python3 - << 'PY'
import requests, os
url=os.getenv("HA_BASE_URL")
token=os.getenv("HA_TOKEN")
if url and token:
    try:
        requests.post(
            f"{url}/api/services/persistent_notification/create",
            headers={"Authorization":f"Bearer {token}"},
            json={"title":"CropCircuit Watchdog","message":"Automation heartbeat active"}
        )
    except:
        pass
PY

  sleep "$sleep_seconds"
done
