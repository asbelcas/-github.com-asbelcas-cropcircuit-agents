#!/usr/bin/env python3
"""Send a controlled live wave from marketplace draft queue entries."""

from __future__ import annotations

import argparse
import csv
import email
from email import policy
from pathlib import Path

from send_grant_email import send_custom_email

ROOT = Path("/home/asbelcas/cropcircuit")
RUNTIME = ROOT / "runtime"
REPLY_QUEUE = RUNTIME / "marketplace_email_reply_queue.md"
EMAIL_ACTIONS = RUNTIME / "marketplace_email_actions.csv"


def parse_queue_entries() -> list[dict[str, str]]:
    if not REPLY_QUEUE.exists():
        return []
    out: list[dict[str, str]] = []
    for line in REPLY_QUEUE.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s.startswith("- TO: "):
            continue
        parts = [p.strip() for p in s[2:].split("|")]
        row = {}
        for p in parts:
            if ":" not in p:
                continue
            k, v = p.split(":", 1)
            row[k.strip().lower()] = v.strip()
        if {"to", "subject", "class", "draft"} <= set(row):
            out.append(row)
    return out


def sent_keys() -> set[str]:
    if not EMAIL_ACTIONS.exists():
        return set()
    keys = set()
    with open(EMAIL_ACTIONS, "r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if (r.get("status") or "").strip().lower() != "sent":
                continue
            k = f"{(r.get('to') or '').strip().lower()}|{(r.get('subject') or '').strip().lower()}"
            keys.add(k)
    return keys


def read_draft_body(path: Path) -> str:
    msg = email.message_from_string(path.read_text(encoding="utf-8", errors="ignore"), policy=policy.default)
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_content().strip()
    payload = msg.get_content()
    return payload.strip() if isinstance(payload, str) else ""


def append_actions(rows: list[dict[str, str]]) -> None:
    exists = EMAIL_ACTIONS.exists()
    with open(EMAIL_ACTIONS, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["timestamp", "to", "subject", "classification", "status", "notes"],
        )
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=3)
    args = ap.parse_args()
    max_count = max(1, min(20, args.count))

    queue = parse_queue_entries()
    sent = sent_keys()

    selected = []
    for q in reversed(queue):  # newest first
        to_addr = q["to"].lower()
        subject = q["subject"].lower()
        key = f"{to_addr}|{subject}"
        if key in sent:
            continue
        if to_addr.endswith("@cropcircuit.org"):  # skip synthetic internal pipeline addresses
            continue
        selected.append(q)
        if len(selected) >= max_count:
            break

    actions = []
    ok = 0
    failed = 0
    for q in selected:
        to_addr = q["to"]
        subject = q["subject"]
        cls = q["class"]
        draft_path = Path(q["draft"])
        if not draft_path.exists():
            failed += 1
            actions.append(
                {
                    "timestamp": "",
                    "to": to_addr,
                    "subject": subject,
                    "classification": cls,
                    "status": "send_failed",
                    "notes": f"draft_missing path={draft_path}",
                }
            )
            continue
        body = read_draft_body(draft_path)
        tag = f"SAFE_AUTOSEND_WAVE|marketplace:{to_addr}"
        sent_ok = bool(send_custom_email(to_addr, subject, body, tag=tag, dry_run=False))
        if sent_ok:
            ok += 1
            actions.append(
                {
                    "timestamp": "",
                    "to": to_addr,
                    "subject": subject,
                    "classification": cls,
                    "status": "sent",
                    "notes": "ha_triggered_send_wave",
                }
            )
        else:
            failed += 1
            actions.append(
                {
                    "timestamp": "",
                    "to": to_addr,
                    "subject": subject,
                    "classification": cls,
                    "status": "send_failed",
                    "notes": "ha_triggered_send_wave",
                }
            )

    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for a in actions:
        a["timestamp"] = ts
    if actions:
        append_actions(actions)

    print(
        {
            "selected": len(selected),
            "sent": ok,
            "failed": failed,
            "count_requested": max_count,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
