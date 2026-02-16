#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
CFG_DIR = Path.home() / ".config" / "cropcircuit"
CREDS_FILE = CFG_DIR / "gmail_credentials.json"
TOKEN_FILE = CFG_DIR / "gmail_token.json"
OUT_FILE = ROOT / "runtime" / "morning_targets.json"
INGEST_LOG = ROOT / "logs" / "targets_ingest.log"

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
    monthly = parse_money(
        body,
        [
            re.compile(r"monthly[_\s-]*stability[_\s-]*usd\D*([\d,]+)", re.I),
            re.compile(r"monthly\D*\$?([\d,]+)", re.I),
        ],
        DEFAULTS["monthly_stability_usd"],
    )
    goal = parse_money(
        body,
        [
            re.compile(r"grant[_\s-]*goal[_\s-]*usd\D*([\d,]+)", re.I),
            re.compile(r"grant\s*goal\D*\$?([\d,]+)", re.I),
        ],
        DEFAULTS["grant_goal_usd"],
    )
    req = parse_money(
        body,
        [
            re.compile(r"requested[_\s-]*amount[_\s-]*usd\D*([\d,]+)", re.I),
            re.compile(r"requested\s*amount\D*\$?([\d,]+)", re.I),
        ],
        DEFAULTS["requested_amount_usd"],
    )
    return {
        "monthly_stability_usd": monthly,
        "grant_goal_usd": goal,
        "requested_amount_usd": req,
    }


def extract_body(payload: dict) -> str:
    parts = []

    def walk(part):
        if not isinstance(part, dict):
            return
        body = part.get("body", {})
        data = body.get("data")
        if data:
            try:
                decoded = base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
                parts.append(decoded)
            except Exception:
                pass
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(payload)
    return "\n".join(parts)


def gmail_fetch_latest() -> tuple[str, str, str]:
    # Returns (message_id, subject, body_text)
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    CFG_DIR.mkdir(parents=True, exist_ok=True)

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                raise RuntimeError(f"missing credentials file: {CREDS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
    after_epoch = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp())
    query = "newer_than:1d (from:homeassistant OR subject:\"CropCircuit Morning Targets\" OR label:CropCircuit)"
    resp = svc.users().messages().list(userId="me", q=query, maxResults=5).execute()
    msgs = resp.get("messages", []) or []
    if not msgs:
        raise RuntimeError("no_matching_messages")

    msg_id = msgs[0]["id"]
    msg = svc.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = msg.get("payload", {}).get("headers", []) or []
    subject = ""
    for h in headers:
        if str(h.get("name", "")).lower() == "subject":
            subject = str(h.get("value", ""))
            break
    body = extract_body(msg.get("payload", {}))
    return msg_id, subject, body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    msg_id = "dry-run"
    subject = "dry-run"
    body = (
        "monthly_stability_usd: 3000\n"
        "grant_goal_usd: 50000\n"
        "requested_amount_usd: 25000\n"
    )

    if not args.dry_run:
        msg_id, subject, body = gmail_fetch_latest()

    targets = parse_targets(body)
    payload = {
        "timestamp": now_local_iso(),
        "targets": targets,
        "programs": [PROGRAM_DEFAULT],
    }
    atomic_write(OUT_FILE, payload)
    append_log(
        {
            "timestamp_utc": now_utc_iso(),
            "source": "gmail",
            "message_id": msg_id,
            "subject": subject,
            "parsed_targets": targets,
            "stored": str(OUT_FILE),
            "dry_run": args.dry_run,
        }
    )
    print(json.dumps({"ok": True, "source": "gmail", "message_id": msg_id, "targets": targets, "stored": str(OUT_FILE)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
