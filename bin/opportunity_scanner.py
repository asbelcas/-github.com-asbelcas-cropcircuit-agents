#!/usr/bin/env python3
"""Scan Gmail inbox for grant/loan/funding opportunities via IMAP.

Extracts links, deadlines, and amounts from matching emails.
Writes discovered opportunities to runtime/opportunity_queue.json.

Usage:
    python3 bin/opportunity_scanner.py              # live IMAP scan
    python3 bin/opportunity_scanner.py --dry-run    # skip IMAP, use test data
"""
from __future__ import annotations

import argparse
import email
import email.utils
import hashlib
import imaplib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
QUEUE_FILE = ROOT / "runtime" / "opportunity_queue.json"
SCAN_LOG = ROOT / "logs" / "opportunity_scan.log"

GMAIL_USER = "asbelcas@gmail.com"
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

# Keywords that signal a funding opportunity
KEYWORDS = [
    "grant", "loan", "funding", "microloan", "application",
    "conservation", "agriculture", "USDA", "NRCS", "EQIP", "CSP",
    "REAP", "VAPG", "FSA", "MDARD", "regenerative", "deadline",
    "submit", "apply", "RFP", "RFA", "solicitation", "SARE",
]

# URL extraction regex
URL_RE = re.compile(r'https?://[^\s<>"\')\]]+', re.IGNORECASE)

# Dollar amount extraction
AMOUNT_RE = re.compile(r'\$[\d,]+(?:\.\d{2})?|\b\d{1,3}(?:,\d{3})+\b(?:\s*(?:USD|dollars?))?', re.IGNORECASE)

# Date extraction (common formats)
DATE_RE = re.compile(
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
    r'\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4}',
    re.IGNORECASE
)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log_line(msg: str) -> None:
    SCAN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SCAN_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} {msg}\n")


def load_queue() -> dict:
    if not QUEUE_FILE.exists():
        return {"opportunities": []}
    try:
        data = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "opportunities" not in data:
            return {"opportunities": []}
        return data
    except Exception:
        return {"opportunities": []}


def save_queue(queue: dict) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    queue["updated_at"] = now_utc_iso()
    counts = {"total": 0, "NEW": 0, "REVIEWED": 0, "QUEUED": 0, "SUBMITTED": 0, "REJECTED": 0}
    for opp in queue.get("opportunities", []):
        counts["total"] += 1
        s = opp.get("status", "NEW")
        if s in counts:
            counts[s] += 1
    queue["stats"] = counts
    tmp = QUEUE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(queue, indent=2), encoding="utf-8")
    tmp.replace(QUEUE_FILE)


def make_id(source_email: str, subject: str) -> str:
    h = hashlib.md5(f"{source_email}:{subject}".encode()).hexdigest()[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"opp_{ts}_{h}"


def classify_type(subject: str, body: str) -> str:
    text = (subject + " " + body).lower()
    if any(w in text for w in ["loan", "microloan", "lending", "credit"]):
        return "LOAN"
    if any(w in text for w in ["donat", "giving", "sponsor", "contribute"]):
        return "DONATION"
    return "GRANT"


def extract_body(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body += payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode("utf-8", errors="replace")
    return body


def has_keywords(subject: str, body: str) -> list[str]:
    text = (subject + " " + body).lower()
    found = [kw for kw in KEYWORDS if kw.lower() in text]
    return found


def extract_amounts(text: str) -> list[str]:
    return AMOUNT_RE.findall(text)[:5]


def extract_dates(text: str) -> list[str]:
    return DATE_RE.findall(text)[:5]


def extract_links(text: str) -> list[str]:
    urls = URL_RE.findall(text)
    # Filter out common non-opportunity URLs
    skip = ["unsubscribe", "mailto:", "google.com/maps", "facebook.com", "twitter.com",
            "instagram.com", "youtube.com", "linkedin.com/company"]
    filtered = []
    for u in urls:
        if not any(s in u.lower() for s in skip):
            filtered.append(u)
    return filtered[:10]


def scan_imap(password: str, days_back: int = 7, max_results: int = 50) -> list[dict]:
    """Scan Gmail IMAP for funding opportunity emails."""
    opportunities = []

    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    conn.login(GMAIL_USER, password)
    conn.select("INBOX", readonly=True)

    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")

    # Search for emails with funding-related terms
    search_terms = ["grant", "funding", "loan", "USDA", "NRCS", "conservation", "agriculture"]
    all_uids = set()
    for term in search_terms:
        try:
            _typ, data = conn.search(None, f'(SINCE {since_date} SUBJECT "{term}")')
            if data and data[0]:
                all_uids.update(data[0].split())
        except Exception:
            pass
        try:
            _typ, data = conn.search(None, f'(SINCE {since_date} BODY "{term}")')
            if data and data[0]:
                all_uids.update(data[0].split())
        except Exception:
            pass

    log_line(f"imap_search found {len(all_uids)} candidate emails")

    for uid in sorted(all_uids, reverse=True)[:max_results]:
        try:
            _typ, msg_data = conn.fetch(uid, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            subject = str(email.header.decode_header(msg["Subject"])[0][0] or "")
            if isinstance(subject, bytes):
                subject = subject.decode("utf-8", errors="replace")
            from_addr = email.utils.parseaddr(msg.get("From", ""))[1]
            date_str = msg.get("Date", "")

            body = extract_body(msg)
            kws = has_keywords(subject, body)

            if len(kws) < 2:
                continue

            links = extract_links(body)
            amounts = extract_amounts(subject + " " + body)
            dates = extract_dates(subject + " " + body)

            # Parse first amount as USD
            amount_usd = None
            if amounts:
                cleaned = amounts[0].replace("$", "").replace(",", "").split(".")[0].strip()
                try:
                    amount_usd = int(cleaned) if cleaned.isdigit() else None
                except Exception:
                    pass

            opp = {
                "id": make_id(from_addr, subject),
                "type": classify_type(subject, body),
                "source_type": "EMAIL",
                "source_email": from_addr,
                "subject": subject[:200],
                "detected_at": now_utc_iso(),
                "deadline": dates[0] if dates else None,
                "amount_usd": amount_usd,
                "links": links,
                "keywords": kws,
                "snippet": body[:300].replace("\n", " ").strip(),
                "status": "NEW",
                "program_id": None,
                "notes": "",
            }
            opportunities.append(opp)
            log_line(f"opportunity_found id={opp['id']} type={opp['type']} from={from_addr} subject={subject[:60]}")

        except Exception as e:
            log_line(f"imap_parse_error uid={uid} error={str(e)[:80]}")

    conn.logout()
    return opportunities


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan Gmail for funding opportunities")
    parser.add_argument("--dry-run", action="store_true", help="Skip IMAP, use test data")
    parser.add_argument("--days", type=int, default=7, help="Days back to scan (default: 7)")
    args = parser.parse_args()

    log_line(f"opportunity_scan start dry_run={args.dry_run} days={args.days}")

    queue = load_queue()
    existing_ids = {o["id"] for o in queue["opportunities"]}

    if args.dry_run:
        new_opps = [{
            "id": make_id("test@example.com", "Test Grant Opportunity"),
            "type": "GRANT",
            "source_type": "EMAIL",
            "source_email": "test@example.com",
            "subject": "Test Grant Opportunity",
            "detected_at": now_utc_iso(),
            "deadline": None,
            "amount_usd": 10000,
            "links": [],
            "keywords": ["grant", "agriculture"],
            "snippet": "This is a dry-run test opportunity.",
            "status": "NEW",
            "program_id": None,
            "notes": "dry-run test",
        }]
    else:
        password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
        if not password:
            log_line("opportunity_scan error=GMAIL_APP_PASSWORD not set")
            print(json.dumps({"ok": False, "error": "GMAIL_APP_PASSWORD not set"}))
            return 1

        new_opps = scan_imap(password, days_back=args.days)

    # Deduplicate against existing queue
    added = 0
    for opp in new_opps:
        if opp["id"] not in existing_ids:
            queue["opportunities"].append(opp)
            existing_ids.add(opp["id"])
            added += 1

    save_queue(queue)

    result = {
        "ok": True,
        "source": "imap" if not args.dry_run else "dry_run",
        "scanned": len(new_opps),
        "added": added,
        "total_queue": len(queue["opportunities"]),
        "stored": str(QUEUE_FILE),
    }
    log_line(f"opportunity_scan complete scanned={len(new_opps)} added={added} total={len(queue['opportunities'])}")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
