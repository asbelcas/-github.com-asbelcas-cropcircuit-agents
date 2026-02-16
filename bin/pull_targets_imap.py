#!/usr/bin/env python3
"""Pull morning monetary targets from Gmail via IMAP.

Uses the GMAIL_APP_PASSWORD from .env.grant — no OAuth2 needed.
Searches recent emails for target patterns and writes to morning_targets.json.

Usage:
    python3 bin/pull_targets_imap.py              # live IMAP fetch
    python3 bin/pull_targets_imap.py --dry-run     # use defaults, no IMAP
"""
from __future__ import annotations

import argparse
import email
import email.utils
import imaplib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
OUT_FILE = ROOT / "runtime" / "morning_targets.json"
INGEST_LOG = ROOT / "logs" / "targets_ingest.log"

GMAIL_USER = "asbelcas@gmail.com"
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

DEFAULTS = {
    "monthly_stability_usd": 3000,
    "grant_goal_usd": 50000,
    "requested_amount_usd": 25000,
}

PROGRAM_DEFAULT = {
    "name": "USDA FSA Operating Microloan",
    "target_url": "https://public.govdelivery.com/accounts/USDAFARMERS/subscribers/qualify",
    "submit_selector": "input[type='submit']",
}


def now_local_iso() -> str:
    return datetime.now().astimezone().isoformat()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def append_log(payload: dict) -> None:
    INGEST_LOG.parent.mkdir(parents=True, exist_ok=True)
    with INGEST_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def parse_money(text: str, patterns: list[re.Pattern], default: int) -> int:
    for pat in patterns:
        m = pat.search(text)
        if not m:
            continue
        raw = m.group(1)
        try:
            return int(raw.replace(",", "").replace("$", "").strip())
        except Exception:
            continue
    return default


def parse_targets(body: str) -> dict:
    monthly = parse_money(body, [
        re.compile(r"monthly[_\s-]*stability[_\s-]*usd\D*([\d,]+)", re.I),
        re.compile(r"monthly\D*\$?([\d,]+)", re.I),
    ], DEFAULTS["monthly_stability_usd"])

    goal = parse_money(body, [
        re.compile(r"grant[_\s-]*goal[_\s-]*usd\D*([\d,]+)", re.I),
        re.compile(r"grant\s*goal\D*\$?([\d,]+)", re.I),
    ], DEFAULTS["grant_goal_usd"])

    req = parse_money(body, [
        re.compile(r"requested[_\s-]*amount[_\s-]*usd\D*([\d,]+)", re.I),
        re.compile(r"requested\s*amount\D*\$?([\d,]+)", re.I),
        re.compile(r"loan[_\s-]*amount\D*\$?([\d,]+)", re.I),
    ], DEFAULTS["requested_amount_usd"])

    return {
        "monthly_stability_usd": monthly,
        "grant_goal_usd": goal,
        "requested_amount_usd": req,
    }


def extract_text(msg: email.message.Message) -> str:
    parts = []
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    parts.append(payload.decode("utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            parts.append(payload.decode("utf-8", errors="replace"))
    return "\n".join(parts)


def imap_fetch_latest(app_password: str) -> tuple[str, str, str]:
    """Fetch latest matching email via IMAP. Returns (uid, subject, body)."""
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    conn.login(GMAIL_USER, app_password)
    conn.select("INBOX", readonly=True)

    # Search for recent emails with target-related subjects
    since_date = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
    search_criteria = f'(SINCE "{since_date}" OR SUBJECT "CropCircuit" SUBJECT "targets" SUBJECT "morning" SUBJECT "grant")'

    # Try multiple search patterns
    uid = ""
    subject = ""
    body = ""
    for criteria in [
        f'(SINCE "{since_date}" SUBJECT "CropCircuit")',
        f'(SINCE "{since_date}" SUBJECT "targets")',
        f'(SINCE "{since_date}" SUBJECT "morning")',
        f'(SINCE "{since_date}" SUBJECT "grant")',
        f'(SINCE "{since_date}" FROM "asbelcas")',
    ]:
        try:
            status, data = conn.search(None, criteria)
            if status != "OK" or not data[0]:
                continue
            msg_ids = data[0].split()
            if not msg_ids:
                continue
            latest_id = msg_ids[-1]  # most recent
            status, msg_data = conn.fetch(latest_id, "(RFC822)")
            if status != "OK":
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            uid = latest_id.decode() if isinstance(latest_id, bytes) else str(latest_id)
            subject = str(msg.get("Subject", ""))
            body = extract_text(msg)
            if body.strip():
                break
        except Exception:
            continue

    conn.logout()

    if not body:
        raise RuntimeError("no_matching_messages")

    return uid, subject, body


def main() -> int:
    ap = argparse.ArgumentParser(description="Pull morning targets from Gmail via IMAP")
    ap.add_argument("--dry-run", action="store_true", help="Use defaults, no IMAP")
    args = ap.parse_args()

    app_password = os.environ.get("GMAIL_APP_PASSWORD", "")

    if args.dry_run:
        uid = "dry-run"
        subject = "dry-run"
        body = (
            "monthly_stability_usd: 3000\n"
            "grant_goal_usd: 50000\n"
            "requested_amount_usd: 25000\n"
        )
    else:
        if not app_password:
            print(json.dumps({"ok": False, "error": "GMAIL_APP_PASSWORD not set"}))
            return 1
        try:
            uid, subject, body = imap_fetch_latest(app_password)
        except RuntimeError as e:
            # No matching messages — use defaults
            uid = "no-match"
            subject = str(e)
            body = ""
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e)[:200]}))
            return 1

    targets = parse_targets(body) if body else DEFAULTS.copy()
    payload = {
        "timestamp": now_local_iso(),
        "targets": targets,
        "programs": [PROGRAM_DEFAULT],
    }
    atomic_write(OUT_FILE, payload)
    append_log({
        "timestamp_utc": now_utc_iso(),
        "source": "imap" if not args.dry_run else "dry-run",
        "message_uid": uid,
        "subject": subject,
        "parsed_targets": targets,
        "stored": str(OUT_FILE),
        "dry_run": args.dry_run,
    })
    print(json.dumps({"ok": True, "source": "imap", "uid": uid, "targets": targets, "stored": str(OUT_FILE)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
