#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
OUT_FILE = ROOT / "runtime" / "morning_targets.json"
DEFAULT_PROGRAM = {
    "name": "USDA FSA Operating Microloan",
    "target_url": "https://public.govdelivery.com/accounts/USDAFARMERS/subscribers/qualify",
    "submit_selector": "input[type='submit']",
}


def ask_int(label: str, default: int) -> int:
    while True:
        raw = input(f"{label} [{default}]: ").strip()
        if not raw:
            return default
        try:
            return int(raw.replace(",", "").replace("$", ""))
        except Exception:
            print("Enter a valid integer.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-submit", action="store_true")
    args = ap.parse_args()

    monthly = ask_int("Monthly Stability USD", 3000)
    goal = ask_int("Grant Goal USD", 50000)
    requested = ask_int("Requested Amount USD", 25000)
    program_index = ask_int("Program choice index (0=USDA FSA Operating Microloan)", 0)

    programs = [DEFAULT_PROGRAM]
    if program_index != 0:
        print("Unsupported index currently; using default program 0.")
        program_index = 0

    payload = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "targets": {
            "monthly_stability_usd": monthly,
            "grant_goal_usd": goal,
            "requested_amount_usd": requested,
        },
        "programs": programs,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "stored": str(OUT_FILE), "targets": payload["targets"]}))

    if not args.no_submit:
        import subprocess
        rc = subprocess.run(["bash", str(ROOT / "bin" / "morning_apply_and_submit.sh")], check=False).returncode
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
