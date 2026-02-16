#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p logs

blocking="${BLOCKING_FUNDING:-0}"
funding_idle="${FUNDING_IDLE:-0}"

# Institutional + grant partner bias for outreach.
partner_count="$(python3 - <<'PY'
import csv
import re
from pathlib import Path
p = Path("outreach_log.csv")
if not p.exists():
    print(0); raise SystemExit
count = 0
rx = re.compile(r"(partner|extension|district|university|college|foundation|agency|institute|department)", re.I)
with p.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        t = (row.get("Type") or "")
        org = (row.get("Org_Name") or "")
        if "PARTNER" in t.upper() or rx.search(org):
            count += 1
print(count)
PY
)"

strategy="funding"
reason="primary_vector_funding_acceleration"
if [[ "$blocking" == "1" ]]; then
  strategy="reliability"
  reason="funding_blocked_reliability_unblock"
elif [[ "$partner_count" -gt 0 ]]; then
  strategy="outreach"
  reason="institutional_partner_weighting"
elif [[ "$funding_idle" == "1" ]]; then
  strategy="product"
  reason="funding_idle_product_allowed"
fi

echo "$strategy" > logs/current_strategy.txt
printf '%s strategy=%s reason=%s blocking=%s funding_idle=%s partner_count=%s\n' \
  "$(date '+%Y-%m-%d %H:%M:%S')" "$strategy" "$reason" "$blocking" "$funding_idle" "$partner_count" \
  >> logs/strategy_decisions.log
printf '%s\n' "$strategy"
