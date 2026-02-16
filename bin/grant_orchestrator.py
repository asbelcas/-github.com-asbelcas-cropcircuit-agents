#!/usr/bin/env python3
"""Autonomous grant outreach orchestrator.

What it does per run:
- Reads outreach_log.csv as the source of truth.
- Auto-sends due initial emails for rows that can be mapped to send_grant_email.py.
- Flags due follow-ups in the CSV and writes a follow-up queue file.
- Appends a run summary to automation_runs.csv.
- Emits a Home Assistant event (best effort) via bin/ha_event.

Usage:
    python3 bin/grant_orchestrator.py
    python3 bin/grant_orchestrator.py --date 2026-02-13
    python3 bin/grant_orchestrator.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
OUTREACH_LOG = ROOT_DIR / "outreach_log.csv"
FOLLOWUP_QUEUE = ROOT_DIR / "followup_queue.csv"
AUTOMATION_RUNS = ROOT_DIR / "automation_runs.csv"


try:
    import send_grant_email as mailer
except Exception as exc:  # pragma: no cover
    print(f"ERROR: unable to import send_grant_email.py: {exc}")
    sys.exit(1)


TERMINAL_STATUSES = {
    "REPLIED",
    "CALL_SCHEDULED",
    "DRAFT_SENT",
    "SIGNED",
    "DECLINED",
    "DONE",
}


@dataclass
class RunStats:
    run_date: str
    dry_run: bool
    initial_due: int = 0
    initial_sent: int = 0
    initial_failed: int = 0
    manual_required: int = 0
    followup_1_due: int = 0
    followup_2_due: int = 0
    followup_sent: int = 0
    followup_failed: int = 0


def parse_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return dt.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def normalize(value: str) -> str:
    return (value or "").strip()


def is_email_row(row: Dict[str, str]) -> bool:
    method = normalize(row.get("Method", "")).lower()
    email = normalize(row.get("Email", ""))
    return "email" in method and "@" in email


def build_email_index() -> Dict[str, str]:
    idx: Dict[str, str] = {}
    for eid, payload in mailer.EMAILS.items():
        to_addr = normalize(payload.get("to", "")).lower()
        if "@" in to_addr:
            idx[to_addr] = eid
    return idx


def compose_followup(row: Dict[str, str], stage: str, run_date: dt.date) -> Tuple[str, str]:
    org = normalize(row.get("Org_Name", "")) or "your team"
    contact = normalize(row.get("Contact_Name", ""))
    greeting = f"Hi {contact.split()[0]}," if contact else "Hello,"

    if stage == "FOLLOWUP_1":
        subject = f"Following Up — MDARD Regenerative Grant Partnership ({org})"
        body = f"""{greeting}

I wanted to follow up on my earlier message about partnering on the MDARD Regenerative Farmer Network Grant application due February 27, 2026.

{org} is a strong fit for this effort, and even a brief response would help me finalize roles and required documentation this week.

If helpful, I can send a one-page summary and draft language today. I can also jump on a quick 10-15 minute call at your convenience.

Thank you for your time."""
    else:
        subject = f"Time-Sensitive Follow-Up — MDARD Grant Deadline Feb 27 ({org})"
        body = f"""{greeting}

This is a time-sensitive follow-up regarding the MDARD Regenerative Farmer Network Grant (deadline: February 27, 2026).

I am finalizing partner confirmations now. If {org} is open to participating or providing support, a short confirmation reply today would allow me to include you in the final submission package.

If timing is not workable, a quick \"not this cycle\" response is also appreciated so I can finalize outreach routing.

Thank you again for considering this."""

    return subject, body


def update_notes(existing: str, suffix: str) -> str:
    existing = normalize(existing)
    if not existing:
        return suffix
    return f"{existing} | {suffix}"


def append_run_log(stats: RunStats) -> None:
    exists = AUTOMATION_RUNS.exists()
    with AUTOMATION_RUNS.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if not exists:
            writer.writerow(
                [
                    "timestamp_utc",
                    "run_date",
                    "dry_run",
                    "initial_due",
                    "initial_sent",
                    "initial_failed",
                    "manual_required",
                    "followup_1_due",
                    "followup_2_due",
                    "followup_sent",
                    "followup_failed",
                ]
            )
        writer.writerow(
            [
                dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                stats.run_date,
                str(stats.dry_run).lower(),
                stats.initial_due,
                stats.initial_sent,
                stats.initial_failed,
                stats.manual_required,
                stats.followup_1_due,
                stats.followup_2_due,
                stats.followup_sent,
                stats.followup_failed,
            ]
        )


def emit_ha_event(stats: RunStats) -> None:
    ha_event = SCRIPT_DIR / "ha_event"
    if not ha_event.exists():
        return
    if not os.environ.get("HA_URL") or not os.environ.get("HA_TOKEN"):
        return

    msg = (
        f"date={stats.run_date} dry_run={str(stats.dry_run).lower()} "
        f"sent={stats.initial_sent} failed={stats.initial_failed} manual={stats.manual_required} "
        f"f1_due={stats.followup_1_due} f2_due={stats.followup_2_due}"
    )
    try:
        subprocess.run(
            [str(ha_event), "grant_outreach_batch", msg],
            cwd=str(ROOT_DIR),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        # Event emission is best-effort and should not fail the run.
        pass


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run(run_date: dt.date, dry_run: bool) -> Tuple[RunStats, List[Dict[str, str]]]:
    if not OUTREACH_LOG.exists():
        raise FileNotFoundError(f"Missing required file: {OUTREACH_LOG}")

    with OUTREACH_LOG.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    stats = RunStats(run_date=run_date.isoformat(), dry_run=dry_run)
    email_idx = build_email_index()
    followup_rows: List[Dict[str, str]] = []

    for row in rows:
        status = normalize(row.get("Status", "")).upper() or "PENDING"
        first_contact = parse_date(row.get("First_Contact_Date", ""))
        f1 = parse_date(row.get("Follow_Up_1_Date", ""))
        f2 = parse_date(row.get("Follow_Up_2_Date", ""))

        if status in TERMINAL_STATUSES:
            continue

        # Initial outreach: due and mappable to SMTP automation.
        if status == "PENDING" and first_contact and first_contact <= run_date and is_email_row(row):
            stats.initial_due += 1
            to_email = normalize(row.get("Email", "")).lower()
            email_id = email_idx.get(to_email)

            if not email_id:
                stats.manual_required += 1
                row["Notes"] = update_notes(row.get("Notes", ""), f"{run_date}: no email template mapping")
            else:
                if dry_run:
                    ok = True
                    row["Notes"] = update_notes(row.get("Notes", ""), f"{run_date}: dry-run initial email send")
                else:
                    ok = mailer.send_email(email_id)
                    row["Notes"] = update_notes(
                        row.get("Notes", ""),
                        f"{run_date}: initial email send {'ok' if ok else 'failed'}",
                    )

                if ok:
                    stats.initial_sent += 1
                    row["Status"] = "SENT"
                else:
                    stats.initial_failed += 1
                    row["Status"] = "SEND_FAILED"

        # Follow-up automation and due detection.
        status = normalize(row.get("Status", status)).upper() or status
        if status in TERMINAL_STATUSES:
            continue

        sent_followup_this_run = False

        f1_due = f1 and f1 <= run_date and status in {"SENT", "FOLLOWUP_1_PENDING", "FOLLOWUP_1_DUE", "NO_RESPONSE"}
        if f1_due:
            stats.followup_1_due += 1
            if is_email_row(row):
                subject, body = compose_followup(row, "FOLLOWUP_1", run_date)
                if dry_run:
                    ok = True
                    row["Notes"] = update_notes(row.get("Notes", ""), f"{run_date}: dry-run followup_1 send")
                else:
                    ok = mailer.send_custom_email(normalize(row.get("Email", "")), subject, body, tag="followup_1")
                    row["Notes"] = update_notes(
                        row.get("Notes", ""),
                        f"{run_date}: followup_1 send {'ok' if ok else 'failed'}",
                    )
                if ok:
                    stats.followup_sent += 1
                    row["Status"] = "FOLLOWUP_1_SENT"
                    sent_followup_this_run = True
                else:
                    stats.followup_failed += 1
                    row["Status"] = "FOLLOWUP_1_DUE"
            else:
                row["Status"] = "FOLLOWUP_1_DUE"
                followup_rows.append(
                    {
                        "date": run_date.isoformat(),
                        "stage": "FOLLOWUP_1",
                        "org_name": normalize(row.get("Org_Name", "")),
                        "contact_name": normalize(row.get("Contact_Name", "")),
                        "email": normalize(row.get("Email", "")),
                        "phone": normalize(row.get("Phone", "")),
                        "method": normalize(row.get("Method", "")),
                        "notes": normalize(row.get("Notes", "")),
                    }
                )

        status = normalize(row.get("Status", status)).upper() or status
        f2_due = (
            not sent_followup_this_run
            and f2
            and f2 <= run_date
            and status in {"SENT", "FOLLOWUP_1_SENT", "FOLLOWUP_1_DUE", "FOLLOWUP_2_PENDING", "NO_RESPONSE"}
        )
        if f2_due:
            stats.followup_2_due += 1
            if is_email_row(row):
                subject, body = compose_followup(row, "FOLLOWUP_2", run_date)
                if dry_run:
                    ok = True
                    row["Notes"] = update_notes(row.get("Notes", ""), f"{run_date}: dry-run followup_2 send")
                else:
                    ok = mailer.send_custom_email(normalize(row.get("Email", "")), subject, body, tag="followup_2")
                    row["Notes"] = update_notes(
                        row.get("Notes", ""),
                        f"{run_date}: followup_2 send {'ok' if ok else 'failed'}",
                    )
                if ok:
                    stats.followup_sent += 1
                    row["Status"] = "FOLLOWUP_2_SENT"
                else:
                    stats.followup_failed += 1
                    row["Status"] = "FOLLOWUP_2_DUE"
            else:
                row["Status"] = "FOLLOWUP_2_DUE"
                followup_rows.append(
                    {
                        "date": run_date.isoformat(),
                        "stage": "FOLLOWUP_2",
                        "org_name": normalize(row.get("Org_Name", "")),
                        "contact_name": normalize(row.get("Contact_Name", "")),
                        "email": normalize(row.get("Email", "")),
                        "phone": normalize(row.get("Phone", "")),
                        "method": normalize(row.get("Method", "")),
                        "notes": normalize(row.get("Notes", "")),
                    }
                )

    write_csv(OUTREACH_LOG, rows, fieldnames)

    if followup_rows:
        fq_fields = ["date", "stage", "org_name", "contact_name", "email", "phone", "method", "notes"]
        mode = "a" if FOLLOWUP_QUEUE.exists() else "w"
        with FOLLOWUP_QUEUE.open(mode, newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fq_fields)
            if mode == "w":
                writer.writeheader()
            writer.writerows(followup_rows)

    append_run_log(stats)
    emit_ha_event(stats)
    return stats, followup_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Run grant outreach automation batch")
    parser.add_argument("--date", help="Run date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--dry-run", action="store_true", help="Do not send SMTP emails")
    args = parser.parse_args()

    run_date = parse_date(args.date) if args.date else dt.date.today()
    if not run_date:
        print("ERROR: invalid --date, expected YYYY-MM-DD")
        return 2

    try:
        stats, followups = run(run_date=run_date, dry_run=args.dry_run)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    print("Grant orchestration batch complete")
    print(f"  date:            {stats.run_date}")
    print(f"  dry_run:         {str(stats.dry_run).lower()}")
    print(f"  initial_due:     {stats.initial_due}")
    print(f"  initial_sent:    {stats.initial_sent}")
    print(f"  initial_failed:  {stats.initial_failed}")
    print(f"  manual_required: {stats.manual_required}")
    print(f"  followup_1_due:  {stats.followup_1_due}")
    print(f"  followup_2_due:  {stats.followup_2_due}")
    print(f"  followup_sent:   {stats.followup_sent}")
    print(f"  followup_failed: {stats.followup_failed}")
    if followups:
        print(f"  followup_queue:  {FOLLOWUP_QUEUE}")
    print(f"  run_log:         {AUTOMATION_RUNS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
