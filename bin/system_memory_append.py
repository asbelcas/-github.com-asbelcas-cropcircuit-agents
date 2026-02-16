#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path

entry = {
    "ts": time.time(),
    "event": sys.stdin.read()
}

path = Path("logs/system_memory.json")
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")
