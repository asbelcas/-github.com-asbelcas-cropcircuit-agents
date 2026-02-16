#!/usr/bin/env python3
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
outreach = root / "outreach_log.csv"
capital_log = root / "logs" / "capital_events.log"
metrics_log = root / "logs" / "funding_metrics.jsonl"

partner_count = 0
if outreach.exists():
    with outreach.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = (row.get("Type") or "").upper()
            org = (row.get("Org_Name") or "").lower()
            if "PARTNER" in t or any(
                x in org for x in ["extension", "district", "university", "college", "foundation", "agency", "institute", "department"]
            ):
                partner_count += 1

capital_events = 0
channel_counts = {}
recurring_revenue_signals = 0
infrastructure_capital_events = 0
if capital_log.exists():
    for ln in capital_log.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            j = json.loads(ln)
        except Exception:
            continue
        if j.get("event") == "capital_move_selected":
            capital_events += 1
            ch = str(j.get("channel", "")).lower()
            if ch:
                channel_counts[ch] = channel_counts.get(ch, 0) + 1
            move_blob = f"{j.get('move','')} {j.get('next_step','')}".lower()
            if re.search(r"\b(recurring|subscription|retainer|monthly)\b", move_blob):
                recurring_revenue_signals += 1
            if re.search(r"\b(infrastructure|equipment|irrigation|storage|greenhouse|solar|water)\b", move_blob):
                infrastructure_capital_events += 1

channel_diversity = len(channel_counts)
single_source_dependency = 1 if (capital_events >= 3 and channel_diversity <= 1) else 0
funding_probability_score = min(
    100,
    30
    + partner_count * 4
    + capital_events * 5
    + recurring_revenue_signals * 6
    + min(channel_diversity, 4) * 4
    + infrastructure_capital_events * 3
    - (15 if single_source_dependency else 0),
)
row = {
    "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "funding_probability_score": funding_probability_score,
    "partner_count": partner_count,
    "capital_events": capital_events,
    "channel_diversity": channel_diversity,
    "recurring_revenue_signals": recurring_revenue_signals,
    "infrastructure_capital_events": infrastructure_capital_events,
    "single_source_dependency": single_source_dependency,
}

metrics_log.parent.mkdir(parents=True, exist_ok=True)
with metrics_log.open("a", encoding="utf-8") as f:
    f.write(json.dumps(row) + "\n")

print(json.dumps(row))
