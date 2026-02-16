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
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
PENDING_FILE = ROOT / "runtime" / "donor_leads_pending.json"
LEADS_CSV = ROOT / "runtime" / "donor_leads.csv"
HANDLER_LOG = ROOT / "logs" / "donor_intake.log"

GMAIL_USER = "asbelcas@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

CSV_FIELDS = [
    "timestamp_utc", "name", "email", "phone", "interest",
    "amount_range", "message", "status", "welcome_sent",
    "followup_1_date", "followup_2_date", "followup_3_date",
]

WELCOME_SUBJECT = "Thank you for supporting CropCircuit Farm!"
WELCOME_BODY = """Hi {name},

Thank you so much for your interest in supporting CropCircuit Farm and regenerative agriculture in Michigan!

We're building a healthier food system on 18 acres in Augusta, MI — focusing on soil health, biodiversity, and community resilience. Your support helps us:

- Implement cover cropping and no-till practices
- Monitor soil health with real-time sensors
- Share what we learn with fellow farmers in our network
- Apply for grants that multiply the impact of every dollar

We'll follow up soon with more details about how you can get involved.

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


def send_welcome_email(to_email: str, name: str, password: str) -> bool:
    body = WELCOME_BODY.format(name=name or "Friend")
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = f"Casey Armstrong <{GMAIL_USER}>"
    msg["To"] = to_email
    msg["Subject"] = WELCOME_SUBJECT

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_USER, password)
            server.sendmail(GMAIL_USER, [to_email], msg.as_string())
        return True
    except Exception as e:
        log_line(f"welcome_email_failed to={to_email} error={str(e)[:100]}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Process donor intake leads")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    log_line(f"donor_intake start dry_run={args.dry_run}")

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
        log_line(f"donor_lead_logged name={name} email={email_addr} interest={lead.get('interest','')}")

        if not args.dry_run and password:
            sent = send_welcome_email(email_addr, name, password)
            if sent:
                log_line(f"welcome_email_sent to={email_addr}")
        else:
            log_line(f"welcome_email_skipped to={email_addr} dry_run={args.dry_run}")

        processed += 1

    # Clear pending file
    PENDING_FILE.unlink(missing_ok=True)

    result = {"ok": True, "processed": processed}
    log_line(f"donor_intake complete processed={processed}")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
