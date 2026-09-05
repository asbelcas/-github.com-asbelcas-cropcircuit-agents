#!/usr/bin/env python3
"""FLORAL CIPHER v2 certificate linter — verify production state files.

Checks every protected file whose path is EXPLICITLY configured in the manager
config (never implicit defaults). Exit 0 = all attested (Cert), exit 1 = any
violation (Claim-style or unattested writes detected).

Usage:
  python3 bin/cert_lint.py            # lint using the production config
  OPERATIONS_MANAGER_CONFIG=... python3 bin/cert_lint.py   # alt config

Run after manager cycles, before deploys, and from monitoring when the
tripwire or cert_attestation audit entries show ok=false.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cert_guard

CONFIG_PATH = Path(os.environ.get(
    "OPERATIONS_MANAGER_CONFIG",
    "/home/asbelcas/cropcircuit/pilot_audit/manager/config.json",
))


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    results = cert_guard.lint_config(config)
    if not results:
        print("cert_lint: no explicitly configured protected files — nothing to lint")
        return 0
    dirty = False
    for kind, violations in sorted(results.items()):
        path = config.get(cert_guard.PROTECTED[kind]["path_config_key"])
        if violations:
            dirty = True
            print(f"FAIL {kind} ({path}):")
            for v in violations:
                print(f"  - {v}")
        else:
            print(f"OK   {kind} ({path}): Cert attested")
    return 1 if dirty else 0


if __name__ == "__main__":
    sys.exit(main())
