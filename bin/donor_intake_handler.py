#!/usr/bin/env python3
"""Process donor intake leads.

Reads new leads from runtime/donor_leads_pending.json (written by HA webhook),
logs to runtime/donor_leads.csv, sends welcome email, fires HA notification.

Usage:
    python3 bin/donor_intake_handler.py
    python3 bin/donor_intake_handler.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import smtplib
import re
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.mime.text import MIMEText
from pathlib import Path

from email_guard import build_thread_key, human_loop_active, notify_ha_block, record_email_event, should_send
from preflight_imap import run_preflight

ROOT = Path("/home/asbelcas/cropcircuit")
PENDING_FILE = ROOT / "runtime" / "donor_leads_pending.json"
LEADS_CSV = ROOT / "runtime" / "donor_leads.csv"
HANDLER_LOG = ROOT / "logs" / "donor_intake.log"
CONVERSION_LOG = ROOT / "logs" / "donor_conversion.log"
NURTURE_QUEUE = ROOT / "runtime" / "donor_nurture_queue.jsonl"
LEAD_TAGS = ROOT / "runtime" / "donor_lead_tags.jsonl"
OUTBOX_DIR = ROOT / "runtime" / "outbox_emails"

GMAIL_USER = "asbelcas@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
DONATION_LINK = os.environ.get("DONATION_LINK", os.environ.get("PAYPAL_DONATION_URL", "https://www.paypal.com/donate"))

CSV_FIELDS = [
    "timestamp_utc", "name", "email", "phone", "interest",
    "amount_range", "message", "status", "welcome_sent",
    "followup_1_date", "followup_2_date", "followup_3_date",
]

WELCOME_SUBJECT = "Help build the farm that feeds the future"
WELCOME_BODY = """Hi {name},

Thank you for stepping in to support Crop Circuit.

We are building a regenerative farm in Michigan designed to restore soil, grow real food, and create a model others can replicate.
Early supporters help fund infrastructure, land prep, animals, and systems.
Every contribution directly builds something physical.

Support tiers:
- $5 - Seed Supporter
- $25 - Soil Builder
- $100 - Infrastructure Backer
- $500 - Founding Contributor

If you want to contribute now, use this secure link:
{donation_link}

We'll send concise progress updates and direct asks over the next few days.

With gratitude,
Casey Armstrong
CropCircuit Farm
5828 N 38th St, Augusta, MI 49012
269-986-8595 | asbelcas@gmail.com
"""

SIGNATURE = """
--
Casey Armstrong
CropCircuit Farm
5828 N 38th St, Augusta, MI 49012
269-986-8595 | asbelcas@gmail.com
"""


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log_line(msg: str) -> None:
    HANDLER_LOG.parent.mkdir(parents=True, exist_ok=True)
    with HANDLER_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} {msg}\n")


def conversion_log(event: str, email: str = "", lead_type: str = "", amount: str = "", note: str = "") -> None:
    CONVERSION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CONVERSION_LOG.open("a", encoding="utf-8") as f:
        f.write(
            f"{now_utc()} event={event} email={email[:120]} lead_type={lead_type[:40]} "
            f"amount={amount[:32]} note={note[:120]}\n"
        )


def ensure_csv() -> None:
    LEADS_CSV.parent.mkdir(parents=True, exist_ok=True)
    if not LEADS_CSV.exists():
        with LEADS_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()


def append_lead(lead: dict) -> None:
    ensure_csv()
    now = datetime.now(timezone.utc)
    row = {
        "timestamp_utc": now_utc(),
        "name": lead.get("name", ""),
        "email": lead.get("email", ""),
        "phone": lead.get("phone", ""),
        "interest": lead.get("interest", ""),
        "amount_range": lead.get("amount_range", ""),
        "message": lead.get("message", ""),
        "status": "NEW",
        "welcome_sent": "",
        "followup_1_date": (now + timedelta(days=3)).strftime("%Y-%m-%d"),
        "followup_2_date": (now + timedelta(days=7)).strftime("%Y-%m-%d"),
        "followup_3_date": (now + timedelta(days=14)).strftime("%Y-%m-%d"),
    }
    with LEADS_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow(row)


def classify_lead_type(lead: dict) -> str:
    interest = str(lead.get("interest", "") or "").lower()
    message = str(lead.get("message", "") or "").lower()
    amount = str(lead.get("amount_range", "") or "").lower()

    if "partner" in interest or "partner" in message:
        return "grant_partner"
    if re.search(r"\bcustomer|buy|purchase|service|product\b", message):
        return "customer"
    if any(token in amount for token in ["250", "500", "1000", "250+", "500+", "1000+"]):
        return "donor_high_intent"
    return "donor"


def append_tag(lead: dict, lead_type: str) -> None:
    LEAD_TAGS.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "timestamp_utc": now_utc(),
        "email": str(lead.get("email", "") or "").strip(),
        "name": str(lead.get("name", "") or "").strip(),
        "interest": str(lead.get("interest", "") or "").strip(),
        "amount_range": str(lead.get("amount_range", "") or "").strip(),
        "lead_type": lead_type,
    }
    with LEAD_TAGS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=True) + "\n")


def append_nurture_sequence(lead: dict, lead_type: str) -> int:
    NURTURE_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    existing_keys: set[str] = set()
    if NURTURE_QUEUE.exists():
        with NURTURE_QUEUE.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    key = str(rec.get("task_key", "")).strip()
                    if key:
                        existing_keys.add(key)
                except Exception:
                    continue

    now = datetime.now(timezone.utc)
    email_addr = str(lead.get("email", "") or "").strip().lower()
    name = str(lead.get("name", "") or "").strip()
    stages = [
        ("nurture_day2", 2),
        ("nurture_day5", 5),
    ]
    queued = 0
    with NURTURE_QUEUE.open("a", encoding="utf-8") as f:
        for stage, days in stages:
            due = now + timedelta(days=days)
            task_key = f"{email_addr}|{stage}|{due.strftime('%Y-%m-%d')}"
            if task_key in existing_keys:
                continue
            rec = {
                "task_key": task_key,
                "created_utc": now_utc(),
                "due_utc": due.replace(microsecond=0).isoformat(),
                "email": email_addr,
                "name": name,
                "lead_type": lead_type,
                "stage": stage,
                "status": "pending",
                "attempts": 0,
            }
            f.write(json.dumps(rec, ensure_ascii=True) + "\n")
            queued += 1
    return queued


def send_welcome_email(to_email: str, name: str, password: str) -> bool:
    body = WELCOME_BODY.format(name=name or "Friend", donation_link=DONATION_LINK)
    thread_key = build_thread_key(WELCOME_SUBJECT, to_email)
    if human_loop_active():
        reason = "BLOCK: human_loop_requires_safe_autosend_tag"
        record_email_event(
            "block",
            thread_key,
            now_utc(),
            {"source": "donor_intake_handler", "mode": "human_loop_block", "reason": reason},
        )
        notify_ha_block(
            "Human Loop Blocked Send",
            f"source=donor_intake_handler to={to_email} reason={reason}",
        )
        log_line(f"welcome_human_loop_block to={to_email} reason={reason}")
        return False

    preflight_ok, preflight_detail = run_preflight(verbose=False, retries=3)
    if not preflight_ok:
        reason = f"BLOCK: preflight_imap_failed ({preflight_detail.get('error','unknown')})"
        record_email_event(
            "block",
            thread_key,
            now_utc(),
            {
                "source": "donor_intake_handler",
                "mode": "preflight_block",
                "reason": reason,
                "preflight": preflight_detail,
            },
        )
        notify_ha_block(
            "Email Preflight Blocked Send",
            f"source=donor_intake_handler to={to_email} reason={reason}",
        )
        log_line(f"welcome_preflight_block to={to_email} reason={reason}")
        return False

    allow, reason = should_send(thread_key, now_utc(), cooldown_minutes=180)
    if not allow:
        OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        draft_path = OUTBOX_DIR / f"donor_welcome_{to_email.replace('@', '_at_')}_{ts}.eml"
        draft_msg = EmailMessage()
        draft_msg["From"] = f"Casey Armstrong <{GMAIL_USER}>"
        draft_msg["To"] = to_email
        draft_msg["Subject"] = WELCOME_SUBJECT
        draft_msg["X-Guard-Reason"] = reason
        draft_msg.set_content(body)
        draft_path.write_text(draft_msg.as_string(), encoding="utf-8")
        record_email_event(
            "draft_created",
            thread_key,
            now_utc(),
            {
                "source": "donor_intake_handler",
                "mode": "guard_block",
                "reason": reason,
                "draft_path": str(draft_path),
            },
        )
        notify_ha_block(
            "Email Guard Blocked Send",
            f"source=donor_intake_handler to={to_email} reason={reason}",
        )
        log_line(f"welcome_guard_block to={to_email} reason={reason} draft={draft_path}")
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = f"Casey Armstrong <{GMAIL_USER}>"
    msg["To"] = to_email
    msg["Subject"] = WELCOME_SUBJECT

    try:
        record_email_event(
            "send_attempt",
            thread_key,
            now_utc(),
            {"source": "donor_intake_handler", "to": to_email, "subject": WELCOME_SUBJECT},
        )
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_USER, password)
            server.sendmail(GMAIL_USER, [to_email], msg.as_string())
        record_email_event(
            "send_success",
            thread_key,
            now_utc(),
            {"source": "donor_intake_handler", "to": to_email, "subject": WELCOME_SUBJECT},
        )
        return True
    except Exception as e:
        log_line(f"welcome_email_failed to={to_email} error={str(e)[:100]}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Process donor intake leads")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Required for live send; default mode is draft-only")
    args = parser.parse_args()
    effective_dry_run = args.dry_run or (not args.execute)

    log_line(f"donor_intake start dry_run={effective_dry_run}")

    # Read pending leads
    if not PENDING_FILE.exists():
        log_line("donor_intake no_pending_leads")
        print(json.dumps({"ok": True, "processed": 0}))
        return 0

    try:
        pending = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log_line(f"donor_intake read_error={str(e)[:80]}")
        print(json.dumps({"ok": False, "error": str(e)[:80]}))
        return 1

    leads = pending if isinstance(pending, list) else [pending]
    password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

    processed = 0
    for lead in leads:
        email_addr = lead.get("email", "").strip()
        name = lead.get("name", "").strip()
        if not email_addr:
            continue

        append_lead(lead)
        lead_type = classify_lead_type(lead)
        append_tag(lead, lead_type)
        queued = append_nurture_sequence(lead, lead_type)
        conversion_log(
            "lead_tagged",
            email=email_addr,
            lead_type=lead_type,
            amount=str(lead.get("amount_range", "") or ""),
            note=f"nurture_queued={queued}",
        )
        log_line(
            f"donor_lead_logged name={name} email={email_addr} interest={lead.get('interest','')} "
            f"lead_type={lead_type} nurture_queued={queued}"
        )

        if not effective_dry_run and password:
            sent = send_welcome_email(email_addr, name, password)
            if sent:
                log_line(f"welcome_email_sent to={email_addr}")
                conversion_log("welcome_sent", email=email_addr, lead_type=lead_type, amount=str(lead.get("amount_range", "") or ""))
            else:
                conversion_log("welcome_failed", email=email_addr, lead_type=lead_type, amount=str(lead.get("amount_range", "") or ""))
        else:
            log_line(f"welcome_email_skipped to={email_addr} dry_run={effective_dry_run}")
            conversion_log(
                "welcome_skipped",
                email=email_addr,
                lead_type=lead_type,
                amount=str(lead.get("amount_range", "") or ""),
                note=f"dry_run={effective_dry_run}",
            )

        processed += 1

    # Clear pending file
    PENDING_FILE.unlink(missing_ok=True)

    result = {"ok": True, "processed": processed}
    log_line(f"donor_intake complete processed={processed}")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
