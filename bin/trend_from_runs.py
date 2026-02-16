#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "logs" / "runs.jsonl"

if not RUNS.exists():
    print("NO_DATA")
    sys.exit(0)

latencies = []
fail_signals = 0

with open(RUNS) as f:
    for line in f:
        try:
            j = json.loads(line)
        except:
            continue
        txt = (j.get("last_autopilot", "") + j.get("last_ha", "")).lower()
        if "fail" in txt:
            fail_signals += 1
        if "latency" in txt:
            try:
                lat = float(txt.split("latency=")[1].split()[0])
                latencies.append(lat)
            except:
                pass

trend = "stable"
if len(latencies) >= 5:
    if latencies[-1] > latencies[0] * 1.5:
        trend = "degrading"

if fail_signals >= 3:
    trend = "failure_likely"

print(trend)
