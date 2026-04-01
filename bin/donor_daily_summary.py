#!/usr/bin/env python3
"""Generate daily donor/pipeline summary metrics."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
DONOR_WEB_JSONL = ROOT / "logs" / "donor_web.log.jsonl"
WATCHER_LOG = ROOT / "logs" / "pipeline_watcher.log"
OUT_LOG = ROOT / "logs" / "donor_daily_summary.log"


def today_prefix() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def count_donor_metrics(prefix: str) -> tuple[int, int, int]:
    leads_received = 0
    duplicates_blocked = 0
    failures = 0
    if not DONOR_WEB_JSONL.exists():
        return leads_received, duplicates_blocked, failures
    with DONOR_WEB_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            ts = str(rec.get("timestamp_utc", ""))
            if not ts.startswith(prefix):
                continue
            accepted = bool(rec.get("accepted", False))
            reason = str(rec.get("reason", ""))
            if accepted:
                leads_received += 1
            elif reason == "duplicate_24h":
                duplicates_blocked += 1
            else:
                failures += 1
    return leads_received, duplicates_blocked, failures


def count_pipeline_metrics(prefix: str) -> tuple[int, int]:
    runs = 0
    failures = 0
    if not WATCHER_LOG.exists():
        return runs, failures
    with WATCHER_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            if prefix not in line:
                continue
            if "Running pipeline" in line:
                runs += 1
            if "Pipeline completed with exit code" in line and "exit code 0" not in line:
                failures += 1
    return runs, failures


def main() -> int:
    prefix = today_prefix()
    leads_received, duplicates_blocked, donor_failures = count_donor_metrics(prefix)
    pipeline_runs, pipeline_failures = count_pipeline_metrics(prefix)
    total_failures = donor_failures + pipeline_failures
    out = {
        "date_utc": prefix,
        "leads_received": leads_received,
        "duplicates_blocked": duplicates_blocked,
        "pipeline_runs": pipeline_runs,
        "failures": total_failures,
        "pipeline_failures": pipeline_failures,
        "donor_failures": donor_failures,
    }
    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with OUT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=True) + "\n")
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
