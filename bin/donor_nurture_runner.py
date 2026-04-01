#!/usr/bin/env python3
"""Process queued donor nurture follow-up emails."""

from __future__ import annotations

import argparse
import json
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from email.mime.text import MIMEText
from pathlib import Path

from email_guard import build_thread_key, human_loop_active, notify_ha_block, record_email_event, should_send
from preflight_imap import run_preflight


ROOT = Path("/home/asbelcas/cropcircuit")
QUEUE_FILE = ROOT / "runtime" / "donor_nurture_queue.jsonl"
LOG_FILE = ROOT / "logs" / "donor_nurture.log"
CONVERSION_LOG = ROOT / "logs" / "donor_conversion.log"
OUTBOX_DIR = ROOT / "runtime" / "outbox_emails"
GMAIL_USER = "asbelcas@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
DONATION_LINK = os.environ.get("DONATION_LINK", os.environ.get("PAYPAL_DONATION_URL", "https://www.paypal.com/donate"))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().replace(microsecond=0).isoformat()


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{now_iso()} {msg}\n")


def conversion_log(event: str, email: str = "", stage: str = "", note: str = "") -> None:
    CONVERSION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CONVERSION_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{now_iso()} event={event} email={email[:120]} stage={stage[:40]} note={note[:120]}\n")


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def compose(stage: str, name: str, lead_type: str) -> tuple[str, str]:
    first = name or "there"
    if stage == "nurture_day2":
        subject = "Day 2: watch this farm being built"
        body = (
            f"Hi {first},\n\n"
            "Watch this being built in real time:\n"
            "- Intake and follow-up are running continuously\n"
            "- New donor support is feeding real Michigan farm and grant execution\n"
            "- We are documenting outcomes so this model can be replicated\n\n"
            "If you want to push the next build milestone forward:\n"
            f"{DONATION_LINK}\n\n"
            "With gratitude,\nCasey\n"
        )
    elif stage == "nurture_day5":
        subject = "Day 5: watch this become physical"
        body = (
            f"Hi {first},\n\n"
            "This farm is being built now, not someday.\n"
            "Can you take one concrete next step this week?\n"
            f"- Donate directly (Seed/Soil/Infrastructure/Founding): {DONATION_LINK}\n"
            "- Forward this to one person who cares about regenerative agriculture in Michigan\n"
            "- Reply if you'd like to partner on grants or customer pathways\n\n"
            "Your support at this stage has outsized impact.\n\n"
            "Appreciate you,\nCasey\n"
        )
    else:
        subject = "Crop Circuit follow-up"
        body = f"Hi {first},\n\nThanks again for supporting Crop Circuit.\n\n- Casey\n"
    return subject, body


def send_email(to_addr: str, subject: str, body: str, password: str) -> bool:
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = f"Casey Armstrong <{GMAIL_USER}>"
    msg["To"] = to_addr
    msg["Subject"] = subject
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_USER, password)
            server.sendmail(GMAIL_USER, [to_addr], msg.as_string())
        return True
    except Exception as exc:  # noqa: BLE001
        log(f"send_failed to={to_addr} error={str(exc)[:120]}")
        return False


def save_draft_eml(to_addr: str, subject: str, body: str, reason: str) -> Path:
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe = f"nurture_{to_addr.replace('@', '_at_').replace('.', '_')}_{ts}.eml"
    path = OUTBOX_DIR / safe
    msg = EmailMessage()
    msg["From"] = f"Casey Armstrong <{GMAIL_USER}>"
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["X-Guard-Reason"] = reason
    msg.set_content(body)
    path.write_text(msg.as_string(), encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="Run donor nurture queue")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true", help="Required for live send; default mode is draft-only")
    args = ap.parse_args()
    effective_dry_run = args.dry_run or (not args.execute)
    if not args.execute and not args.dry_run:
        log("draft_only_mode active; use --execute for live sends")

    if not QUEUE_FILE.exists():
        log("nurture_queue missing")
        print(json.dumps({"ok": True, "processed": 0, "sent": 0}))
        return 0

    lines = QUEUE_FILE.read_text(encoding="utf-8").splitlines()
    rows = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue

    pwd = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    processed = 0
    sent = 0
    now = now_utc()
    for rec in rows:
        if rec.get("status") != "pending":
            continue
        due = rec.get("due_utc", "")
        if not due:
            continue
        try:
            due_dt = parse_iso(due)
        except Exception:
            continue
        if due_dt > now:
            continue

        email = str(rec.get("email", "")).strip()
        if not email:
            rec["status"] = "invalid"
            processed += 1
            continue
        subject, body = compose(str(rec.get("stage", "")), str(rec.get("name", "")), str(rec.get("lead_type", "")))
        thread_key = build_thread_key(subject, email)
        rec["attempts"] = int(rec.get("attempts", 0)) + 1
        processed += 1
        if effective_dry_run:
            record_email_event("draft_created", thread_key, now_iso(), {"source": "donor_nurture_runner", "mode": "dry_run"})
            rec["status"] = "sent_dry_run"
            rec["sent_utc"] = now_iso()
            sent += 1
            log(f"sent_dry_run to={email} stage={rec.get('stage','')}")
            conversion_log("nurture_sent_dry_run", email=email, stage=str(rec.get("stage", "")))
            continue

        if human_loop_active():
            reason = "BLOCK: human_loop_requires_safe_autosend_tag"
            draft_path = save_draft_eml(email, subject, body, reason)
            record_email_event(
                "block",
                thread_key,
                now_iso(),
                {"source": "donor_nurture_runner", "mode": "human_loop_block", "reason": reason, "draft_path": str(draft_path)},
            )
            notify_ha_block(
                "Human Loop Blocked Send",
                f"source=donor_nurture_runner to={email} stage={rec.get('stage','')} reason={reason}",
            )
            rec["status"] = "blocked_human_loop"
            rec["guard_reason"] = reason
            log(f"blocked_human_loop to={email} stage={rec.get('stage','')} reason={reason} draft={draft_path}")
            conversion_log("nurture_blocked", email=email, stage=str(rec.get("stage", "")), note=reason)
            continue

        preflight_ok, preflight_detail = run_preflight(verbose=False, retries=3)
        if not preflight_ok:
            reason = f"BLOCK: preflight_imap_failed ({preflight_detail.get('error','unknown')})"
            record_email_event(
                "block",
                thread_key,
                now_iso(),
                {
                    "source": "donor_nurture_runner",
                    "mode": "preflight_block",
                    "reason": reason,
                    "preflight": preflight_detail,
                },
            )
            notify_ha_block(
                "Email Preflight Blocked Send",
                f"source=donor_nurture_runner to={email} stage={rec.get('stage','')} reason={reason}",
            )
            rec["status"] = "blocked_preflight"
            rec["guard_reason"] = reason
            log(f"blocked_preflight to={email} stage={rec.get('stage','')} reason={reason}")
            conversion_log("nurture_blocked", email=email, stage=str(rec.get("stage", "")), note=reason)
            continue

        allow, reason = should_send(thread_key, now_iso(), cooldown_minutes=180)
        if not allow:
            draft_path = save_draft_eml(email, subject, body, reason)
            record_email_event("draft_created", thread_key, now_iso(), {"source": "donor_nurture_runner", "mode": "guard_block", "reason": reason, "draft_path": str(draft_path)})
            notify_ha_block(
                "Email Guard Blocked Send",
                f"source=donor_nurture_runner to={email} stage={rec.get('stage','')} reason={reason}",
            )
            rec["status"] = "blocked_guard"
            rec["guard_reason"] = reason
            log(f"blocked_guard to={email} stage={rec.get('stage','')} reason={reason} draft={draft_path}")
            conversion_log("nurture_blocked", email=email, stage=str(rec.get("stage", "")), note=reason)
            continue

        if not pwd:
            rec["status"] = "blocked_no_password"
            log(f"blocked_no_password to={email} stage={rec.get('stage','')}")
            conversion_log("nurture_blocked", email=email, stage=str(rec.get("stage", "")), note="no_password")
            continue
        record_email_event("send_attempt", thread_key, now_iso(), {"source": "donor_nurture_runner", "stage": str(rec.get("stage", ""))})
        if send_email(email, subject, body, pwd):
            record_email_event("send_success", thread_key, now_iso(), {"source": "donor_nurture_runner", "stage": str(rec.get("stage", ""))})
            rec["status"] = "sent"
            rec["sent_utc"] = now_iso()
            sent += 1
            log(f"sent to={email} stage={rec.get('stage','')}")
            conversion_log("nurture_sent", email=email, stage=str(rec.get("stage", "")))
        else:
            rec["status"] = "failed"
            conversion_log("nurture_failed", email=email, stage=str(rec.get("stage", "")))

    out = "\n".join(json.dumps(r, ensure_ascii=True) for r in rows)
    QUEUE_FILE.write_text((out + "\n") if out else "", encoding="utf-8")
    result = {"ok": True, "processed": processed, "sent": sent}
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
