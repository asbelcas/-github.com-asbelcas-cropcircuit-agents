#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "logs" / "runs.jsonl"

if not RUNS.exists():
    print("stable")
    sys.exit(0)

fails = 0

for line in RUNS.read_text().splitlines():
    l = line.lower()
    if "fail" in l:
        fails += 1

if fails >= 3:
    print("failure_likely")
else:
    print("stable")
