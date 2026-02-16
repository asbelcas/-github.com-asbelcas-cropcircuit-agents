#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

partner_count="$(python3 - <<'PY'
import csv, re
from pathlib import Path
p = Path("outreach_log.csv")
if not p.exists():
    print(0); raise SystemExit
rx = re.compile(r"(partner|extension|district|university|college|foundation|agency|institute|department)", re.I)
n = 0
with p.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        t = (row.get("Type") or "")
        org = (row.get("Org_Name") or "")
        if "PARTNER" in t.upper() or rx.search(org):
            n += 1
print(n)
PY
)"

capital_events="$(python3 - <<'PY'
import json
from pathlib import Path
p = Path("logs/capital_events.log")
if not p.exists():
    print(0); raise SystemExit
n = 0
for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
    try:
        j = json.loads(ln)
    except Exception:
        continue
    if j.get("event") == "capital_move_selected":
        n += 1
print(n)
PY
)"
current_strategy="$(cat logs/current_strategy.txt 2>/dev/null || echo funding)"

echo "funding_context:"
echo "recent_failures=$(grep fail logs/runs.jsonl 2>/dev/null | wc -l)"
echo "partner_count=$partner_count"
echo "capital_events=$capital_events"
echo "current_strategy=$current_strategy"
echo "policy=primary_objective_stability"
echo "target=reliable_monthly_baseline_income_diversified"
echo "rule=reliability_only_if_blocking_funding"
echo "rule=product_only_if_funding_idle"
echo "rule=outreach_prioritize_grant_partners_institutional_donors"
echo "rule=prefer_recurring_low_maintenance_income"
echo "rule=avoid_single_source_dependency"
echo "question: highest probability funding move this week?"
