#!/usr/bin/env python3
"""Normalize donor lead payloads and enqueue for donor_intake_handler.

Primary output:
  /home/asbelcas/cropcircuit/runtime/donor_leads_pending.json

Optional side effect:
  /opt/homeassistant/config/grant_triggers/trigger_donor.json
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
PENDING_FILE = ROOT / "runtime" / "donor_leads_pending.json"
DONOR_LOG = ROOT / "logs" / "donor_intake.log"
TRIGGER_DIR = Path("/opt/homeassistant/config/grant_triggers")
TRIGGER_FILE = TRIGGER_DIR / "trigger_donor.json"

FIELD_NAMES = ("name", "email", "phone", "interest", "amount_range", "message")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log_line(msg: str) -> None:
    DONOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DONOR_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} {msg}\n")


def parse_json_value(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    try:
        val = json.loads(raw)
        return "" if val is None else str(val).strip()
    except Exception:
        return raw.strip()


def load_payload(args: argparse.Namespace) -> dict:
    if args.input_file:
        try:
            p = Path(args.input_file)
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}

    if args.stdin_json:
        try:
            return json.loads(os.sys.stdin.read() or "{}")
        except Exception:
            return {}

    if args.from_env_json:
        out = {}
        for field in FIELD_NAMES:
            env_key = f"DONOR_{field.upper()}_JSON"
            out[field] = parse_json_value(os.environ.get(env_key, ""))
        out["source"] = parse_json_value(os.environ.get("DONOR_SOURCE_JSON", ""))
        return out

    # plain env fallback
    out = {}
    for field in FIELD_NAMES:
        env_key = f"DONOR_{field.upper()}"
        out[field] = (os.environ.get(env_key, "") or "").strip()
    out["source"] = (os.environ.get("DONOR_SOURCE", "") or "").strip()
    return out


def normalize(payload: dict) -> dict:
    payload = payload if isinstance(payload, dict) else {}
    lead = {k: str(payload.get(k, "") or "").strip() for k in FIELD_NAMES}
    lead["timestamp_utc"] = now_utc()
    lead["source"] = str(payload.get("source", "ha_webhook") or "ha_webhook")
    return lead


def read_pending() -> list[dict]:
    if not PENDING_FILE.exists():
        return []
    try:
        data = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def write_pending(rows: list[dict]) -> None:
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    PENDING_FILE.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def write_trigger() -> bool:
    try:
        TRIGGER_DIR.mkdir(parents=True, exist_ok=True)
        TRIGGER_FILE.write_text(json.dumps({"action": "donor_intake"}), encoding="utf-8")
        return True
    except Exception as e:
        log_line(f"donor_bridge trigger_write_failed error={str(e)[:120]}")
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Bridge donor payload into pending lead queue")
    ap.add_argument("--input-file", default="", help="Read payload JSON from file path")
    ap.add_argument("--stdin-json", action="store_true", help="Read payload JSON from stdin")
    ap.add_argument("--from-env-json", action="store_true", help="Read DONOR_*_JSON env vars")
    ap.add_argument("--trigger-donor-intake", action="store_true", help="Write trigger_donor.json")
    args = ap.parse_args()

    payload = load_payload(args)
    lead = normalize(payload)
    if not lead.get("email"):
        result = {"ok": False, "status": "invalid", "reason": "missing_email"}
        log_line("donor_bridge invalid missing_email")
        print(json.dumps(result))
        return 1

    pending = read_pending()
    pending.append(lead)
    write_pending(pending)
    log_line(f"donor_bridge queued email={lead.get('email','')} pending_count={len(pending)}")

    triggered = False
    if args.trigger_donor_intake:
        triggered = write_trigger()
        log_line(f"donor_bridge trigger_donor_intake={triggered}")

    print(json.dumps({"ok": True, "queued": 1, "pending_count": len(pending), "triggered": triggered}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
