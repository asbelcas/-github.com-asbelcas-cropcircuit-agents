#!/usr/bin/env python3
"""Tripwire: detect and identify writers of the live capacity snapshot.

Polls /home/asbelcas/cropcircuit-site/data/audit_capacity_state.json every
2s. When active_paid_audits changes, records the event and an immediate
snapshot of recently-started python/docker processes (etimes < 300s) plus
the full process list, so an unknown writer can be identified.

Exit codes: never exits on its own; kill via TERM.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TARGET = Path("/home/asbelcas/cropcircuit-site/data/audit_capacity_state.json")
LOG = Path("/home/asbelcas/cropcircuit/runtime/capacity_tripwire.log")


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def ps_snapshot() -> str:
    try:
        out = subprocess.run(
            ["ps", "-eo", "pid,etimes,args", "--sort=-etimes"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except Exception as e:
        return f"ps failed: {e}"
    lines = out.splitlines()
    header, rows = lines[0], lines[1:]
    young = [r for r in rows if r.split(None, 2)[1].isdigit() and int(r.split(None, 2)[1]) < 300]
    docker = subprocess.run(["docker", "ps", "--format", "{{.Names}} {{.Image}} {{.Status}}"],
                            capture_output=True, text=True).stdout
    return header + "\n" + "\n".join(young) + "\n--- docker ---\n" + docker


def read_state():
    try:
        return json.loads(TARGET.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    prev = read_state()
    prev_sig = None if prev is None else (prev.get("active_paid_audits"), prev.get("generated_at_utc"))
    log(f"tripwire armed; initial={prev_sig}")
    while True:
        time.sleep(2)
        cur = read_state()
        if cur is None:
            continue
        sig = (cur.get("active_paid_audits"), cur.get("generated_at_utc"))
        if sig == prev_sig:
            continue
        prev_sig = sig
        log(f"CHANGE detected: active_paid_audits={cur.get('active_paid_audits')} "
            f"generated_at_utc={cur.get('generated_at_utc')}")
        log("--- ps snapshot (processes < 300s old) ---\n" + ps_snapshot())


if __name__ == "__main__":
    sys.exit(main())
