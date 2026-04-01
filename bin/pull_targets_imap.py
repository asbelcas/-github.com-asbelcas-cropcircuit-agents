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
import socket
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from email_guard import build_thread_key, is_priority_contact, notify_ha_block, record_email_event


ROOT = Path("/home/asbelcas/cropcircuit")
OUT_FILE = ROOT / "runtime" / "morning_targets.json"
INGEST_LOG = ROOT / "logs" / "targets_ingest.log"
PRIORITY_ALERT_LOG = ROOT / "runtime" / "priority_alerts.log"
OFFLINE_MODE_JSON = ROOT / "runtime" / "offline_mode.json"

GMAIL_USER = os.environ.get("IMAP_USER", "asbelcas@gmail.com")
IMAP_HOST = os.environ.get("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))

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


def resolve_host_ipv4(host: str) -> list[str]:
    """Resolve host A records with system DNS fallback to local DoH helper script."""
    ips = []
    try:
        records = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
        ips.extend([item[4][0] for item in records if item and item[4]])
    except Exception:
        pass
    if ips:
        return list(dict.fromkeys(ips))

    # Fallback to DoH helper over HTTPS when resolver is flaky in automation runtime.
    helper = ROOT / "bin" / "doh_resolve.py"
    try:
        out = subprocess.check_output(
            ["python3", str(helper), host],
            text=True,
            timeout=12,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        out = ""
    return [out] if out else []


def imap_connect(host: str, port: int):
    """Connect IMAP using normal hostname path, then fallback to IP+SNI stream."""
    try:
        return imaplib.IMAP4_SSL(host, port)
    except Exception:
        ips = resolve_host_ipv4(host)
        if not ips:
            raise
        ip = ips[0]

        # Build an IMAPS tunnel to resolved IP with cert verification + SNI for host.
        cmd = f"openssl s_client -quiet -connect {ip}:{port} -servername {host} 2>/dev/null"
        return imaplib.IMAP4_stream(cmd)


def _msg_dt_utc(msg: email.message.Message) -> datetime:
    raw = msg.get("Date", "")
    try:
        dt = email.utils.parsedate_to_datetime(raw)
    except Exception:
        dt = None
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def imap_fetch_latest(app_password: str) -> tuple[str, str, str, dict]:
    """Fetch latest matching email via IMAP. Returns (uid, subject, body, message_meta)."""
    conn = imap_connect(IMAP_HOST, IMAP_PORT)
    conn.login(GMAIL_USER, app_password)
    conn.select("INBOX", readonly=True)

    # Search for recent emails with target-related subjects
    since_date = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
    search_criteria = f'(SINCE "{since_date}" OR SUBJECT "CropCircuit" SUBJECT "targets" SUBJECT "morning" SUBJECT "grant")'

    # Try multiple search patterns
    uid = ""
    subject = ""
    body = ""
    msg_meta = {}
    for criteria in [
        f'(SINCE "{since_date}" SUBJECT "CropCircuit")',
        f'(SINCE "{since_date}" SUBJECT "targets")',
        f'(SINCE "{since_date}" SUBJECT "morning")',
        f'(SINCE "{since_date}" SUBJECT "grant")',
        f'(SINCE "{since_date}" FROM "calhouncd@gmail.com")',
        f'(SINCE "{since_date}" FROM "calhouncd")',
        f'(SINCE "{since_date}" SUBJECT "Calhoun Conservation District")',
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
            from_addr = email.utils.parseaddr(str(msg.get("From", "")))[1].lower()
            refs = str(msg.get("References", "")).strip() or str(msg.get("Message-ID", "")).strip()
            msg_meta = {
                "from_addr": from_addr,
                "thread_refs": refs,
                "message_id": str(msg.get("Message-ID", "")).strip(),
                "date_utc": _msg_dt_utc(msg).isoformat(),
            }
            if body.strip():
                break
        except Exception:
            continue

    conn.logout()

    if not body:
        raise RuntimeError("no_matching_messages")

    return uid, subject, body, msg_meta


def main() -> int:
    ap = argparse.ArgumentParser(description="Pull morning targets from Gmail via IMAP")
    ap.add_argument("--dry-run", action="store_true", help="Use defaults, no IMAP")
    args = ap.parse_args()

    app_password = os.environ.get("GMAIL_APP_PASSWORD", "")
    offline_mode = OFFLINE_MODE_JSON.exists() and '"active": true' in OFFLINE_MODE_JSON.read_text(encoding="utf-8", errors="ignore").lower()

    if args.dry_run:
        uid = "dry-run"
        subject = "dry-run"
        body = (
            "monthly_stability_usd: 3000\n"
            "grant_goal_usd: 50000\n"
            "requested_amount_usd: 25000\n"
        )
    else:
        try:
            preflight_raw = subprocess.check_output(
                ["python3", str(ROOT / "bin" / "preflight_imap.py")],
                text=True,
                timeout=45,
            ).strip()
            preflight_detail = json.loads(preflight_raw.splitlines()[-1]) if preflight_raw else {}
            ok_preflight = bool(preflight_detail.get("ok"))
        except subprocess.CalledProcessError as exc:
            text = (exc.output or "").strip()
            try:
                preflight_detail = json.loads(text.splitlines()[-1]) if text else {}
            except Exception:
                preflight_detail = {"ok": False, "error": f"preflight_process_error: {text[:160]}"}
            ok_preflight = False
        except Exception as exc:
            preflight_detail = {"ok": False, "error": f"preflight_exception: {str(exc)[:160]}"}
            ok_preflight = False

        if offline_mode and not ok_preflight:
            print(json.dumps({"ok": False, "error": "offline_mode_imap_blocked", "preflight": preflight_detail}))
            return 2
        if not ok_preflight:
            print(json.dumps({"ok": False, "error": "preflight_imap_failed", "preflight": preflight_detail}))
            return 2
        if not app_password:
            print(json.dumps({"ok": False, "error": "GMAIL_APP_PASSWORD not set"}))
            return 1
        try:
            uid, subject, body, msg_meta = imap_fetch_latest(app_password)
        except RuntimeError as e:
            # No matching messages — use defaults
            uid = "no-match"
            subject = str(e)
            body = ""
            msg_meta = {}
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

    # Guard integration: record inbound_seen event for reply-aware send gate.
    if not args.dry_run and uid != "no-match":
        from_addr = str(msg_meta.get("from_addr", "")).strip().lower()
        refs = str(msg_meta.get("thread_refs", "")).strip()
        thread_key = build_thread_key(subject, from_addr, refs)
        ts = str(msg_meta.get("date_utc") or now_utc_iso())
        record_email_event(
            "inbound_seen",
            thread_key,
            ts,
            {
                "source": "pull_targets_imap",
                "uid": uid,
                "from_addr": from_addr,
                "subject": subject,
                "message_id": str(msg_meta.get("message_id", "")),
            },
        )
        priority_hit = is_priority_contact(from_addr) or ("calhouncd" in from_addr.lower()) or ("calhoun conservation district" in subject.lower())
        if priority_hit:
            alert_line = f"{now_utc_iso()} PRIORITY_REPLY from={from_addr} subject={subject[:180]}"
            PRIORITY_ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
            with PRIORITY_ALERT_LOG.open("a", encoding="utf-8") as fh:
                fh.write(alert_line + "\n")
            notify_ha_block(
                "Priority Reply Alert",
                f"Priority thread replied: {from_addr} | {subject}",
            )

    print(json.dumps({"ok": True, "source": "imap", "uid": uid, "targets": targets, "stored": str(OUT_FILE)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
