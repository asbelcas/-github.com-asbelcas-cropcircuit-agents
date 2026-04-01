#!/usr/bin/env python3
"""HA-first email triage loop with safe draft fallback."""

from __future__ import annotations

import csv
import email
import hashlib
import imaplib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import requests
from email_guard import build_thread_key, human_loop_active, notify_ha_block, record_email_event, should_send
from preflight_imap import run_preflight


ROOT = Path("/home/asbelcas/cropcircuit")
RUNTIME = ROOT / "runtime"
LOGS = ROOT / "logs"

EMAIL_ACTIONS = RUNTIME / "email_actions.csv"
EMAIL_DRAFTS_DIR = RUNTIME / "email_drafts"
EMAIL_REPLY_QUEUE = RUNTIME / "email_reply_queue.md"
TRIAGE_STATUS = RUNTIME / "email_triage_status.json"
HA_AUTH_FIX = RUNTIME / "NEEDS_HA_AUTH_FIX.md"
TRIAGE_LOG = LOGS / "email_triage.log"
CONTACT_MAP = RUNTIME / "mdard_contact_map.csv"
TODAY_QUEUE = RUNTIME / "today_queue.md"
HIGH_PRIORITY_QUEUE = RUNTIME / "high_priority_queue.json"
FOLLOWUP_TEMPLATES = RUNTIME / "followup_templates.md"
REFERRAL_CHAIN_LOG = RUNTIME / "referral_chain.jsonl"
FUNDING_PROBABILITY_JSON = RUNTIME / "funding_probability.json"
OFFLINE_MODE_JSON = RUNTIME / "offline_mode.json"

GMAIL_USER = "asbelcas@gmail.com"
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

KEYWORDS = ["grant", "farm", "mdard", "mnard", "conservation", "district", "msu", "nrcs", "usda", "partner"]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log(msg: str) -> None:
    TRIAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with TRIAGE_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{now_iso()} {msg}\n")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip().removeprefix("export ").strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def load_env() -> None:
    load_env_file(ROOT / ".env")
    load_env_file(ROOT / ".env.grant")
    load_env_file(ROOT / ".env.donor")
    load_env_file(ROOT / ".env.x")


def ha_base() -> str:
    return os.environ.get("HA_URL", "http://localhost:8123").rstrip("/")


def ha_token() -> str:
    return os.environ.get("HA_TOKEN", "").strip()


def ha_get(path: str, timeout: int = 8) -> requests.Response:
    headers = {}
    tok = ha_token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return requests.get(f"{ha_base()}{path}", headers=headers, timeout=timeout)


def ha_post(path: str, payload: dict[str, Any], timeout: int = 8) -> requests.Response:
    headers = {"Content-Type": "application/json"}
    tok = ha_token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return requests.post(f"{ha_base()}{path}", headers=headers, json=payload, timeout=timeout)


def notify_ha(title: str, message: str) -> bool:
    try:
        resp = ha_post(
            "/api/services/persistent_notification/create",
            {"title": title, "message": message},
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


def detect_ha_services() -> dict[str, Any]:
    out = {
        "reachable": False,
        "auth_error": False,
        "notify_services": [],
        "email_like_services": [],
        "script_services": [],
    }
    try:
        r = ha_get("/api/services")
        if r.status_code in (401, 403):
            out["auth_error"] = True
            return out
        if not r.ok:
            return out
        out["reachable"] = True
        services = r.json()
        for domain_block in services:
            domain = domain_block.get("domain", "")
            for svc in (domain_block.get("services", {}) or {}).keys():
                full = f"{domain}.{svc}"
                if domain == "notify":
                    out["notify_services"].append(full)
                if any(x in full for x in ["gmail", "google_mail", "imap", "smtp", "send_email", "mail"]):
                    out["email_like_services"].append(full)
                if domain == "script":
                    out["script_services"].append(full)
        return out
    except Exception as e:  # noqa: BLE001
        log(f"ha_service_detect_error={type(e).__name__}")
        return out


def extract_text(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body += payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode("utf-8", errors="replace")
    return body


def classify_email(subject: str, body: str) -> str:
    text = (subject + "\n" + body).lower()
    if any(x in text for x in ["retired", "wrong office", "no longer handling", "not the right person", "not the right contact", "wrong contact"]):
        return "dead_end"
    if any(x in text for x in ["contact x", "try ", "reach out to", "contact "]):
        return "referral"
    if any(x in text for x in ["happy to talk", "interested", "let's connect", "lets connect", "available", "call"]):
        return "warm_lead"
    if any(x in text for x in ["grant", "rfp", "application", "funding cycle", "deadline"]):
        return "funding_signal"
    if any(x in text for x in ["out of office", "automatic reply", "auto-reply", "vacation"]):
        return "bounce_or_ooo"
    return "needs_more_info"


def score_email(bucket: str, subject: str, body: str) -> int:
    score = 25
    if bucket == "warm_lead":
        score = 90
    elif bucket == "referral":
        score = 85
    elif bucket == "funding_signal":
        score = 95
    elif bucket == "dead_end":
        score = 40
    text = (subject + " " + body).lower()
    if "deadline" in text:
        score += 5
    return max(1, min(100, score))


def read_json(path: Path, fallback: Any):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def append_high_priority(items: list[dict[str, Any]]) -> int:
    if not items:
        return 0
    existing = read_json(HIGH_PRIORITY_QUEUE, [])
    if not isinstance(existing, list):
        existing = []
    seen = {
        f"{(x.get('from_addr') or '').lower()}|{(x.get('subject') or '').lower()}|{(x.get('bucket') or '').lower()}"
        for x in existing if isinstance(x, dict)
    }
    added = 0
    for item in items:
        key = f"{(item.get('from_addr') or '').lower()}|{(item.get('subject') or '').lower()}|{(item.get('bucket') or '').lower()}"
        if key in seen:
            continue
        existing.append(item)
        seen.add(key)
        added += 1
    write_json(HIGH_PRIORITY_QUEUE, existing)
    return added


def build_retired_reply(name: str, topic: str) -> tuple[str, str]:
    subj = "Quick question on the right contact (CropCircuit / regenerative ag)"
    body = (
        f"Hi {name} — thank you for the quick note, and congratulations on retirement.\n"
        "We’re working on a Michigan regenerative agriculture project (CropCircuit) and a related grant / partner outreach effort.\n"
        f"Could you point me to the best current contact for {topic} (or the right inbox), or suggest who I should ask?\n"
        "If it’s easier, I can forward the original message to whoever you recommend.\n"
        "Thanks again,\n"
        "Casey\n"
        "CropCircuit\n"
        "https://cropcircuit.com\n"
    )
    return subj, body


def build_reply(classification: str, sender_name: str, subject: str) -> tuple[str, str]:
    name = sender_name or "there"
    topic = "MDARD / MSU partner outreach"
    if "nrcs" in subject.lower():
        topic = "NRCS / conservation coordination"
    if "msu" in subject.lower():
        topic = "MSU Extension / regenerative agriculture coordination"

    if classification == "dead_end":
        return build_retired_reply(name, topic)
    if classification == "warm_lead":
        return (
            "Thanks for connecting — next step for CropCircuit collaboration",
            (
                f"Hi {name},\n\n"
                "Thanks for the quick response.\n"
                "Would you be open to a 15-minute call this week to align on Michigan regenerative ag partnership options?\n"
                "I can send a one-page summary before we speak.\n\n"
                "Best,\nCasey\nCropCircuit\nhttps://cropcircuit.com\n"
            ),
        )
    if classification == "referral":
        return (
            "Thanks — quick intro follow-up",
            (
                f"Hi {name},\n\n"
                "Thanks for the referral. I’ll follow up with that contact and keep this moving.\n\n"
                "Best,\nCasey\nCropCircuit\nhttps://cropcircuit.com\n"
            ),
        )
    if classification == "bounce_or_ooo":
        return (
            "Quick follow-up on regenerative ag contact routing",
            (
                f"Hi {name},\n\n"
                "Thanks for the update. When you’re back, could you point me to the best current contact for this request?\n\n"
                "Best,\nCasey\nCropCircuit\nhttps://cropcircuit.com\n"
            ),
        )
    return (
        "Quick follow-up on CropCircuit partnership outreach",
        (
            f"Hi {name},\n\n"
            "Thanks for the note. Happy to share a concise project summary and specific ask.\n"
            "Would email or a brief call be easier for next step?\n\n"
            "Best,\nCasey\nCropCircuit\nhttps://cropcircuit.com\n"
        ),
    )


def write_eml(to_addr: str, subject: str, body: str) -> Path:
    EMAIL_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    h = hashlib.md5(f"{to_addr}|{subject}|{now_iso()}".encode("utf-8")).hexdigest()[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = EMAIL_DRAFTS_DIR / f"{ts}_{h}.eml"
    msg = EmailMessage()
    msg["From"] = GMAIL_USER
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    path.write_text(msg.as_string(), encoding="utf-8")
    return path


def append_reply_queue(entries: list[dict[str, str]]) -> None:
    EMAIL_REPLY_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if EMAIL_REPLY_QUEUE.exists():
        lines.append(EMAIL_REPLY_QUEUE.read_text(encoding="utf-8").rstrip())
    lines.append(f"## Queue Update {now_iso()}")
    for e in entries:
        lines.append(f"- TO: {e['to']} | SUBJECT: {e['subject']} | CLASS: {e['classification']} | DRAFT: {e['draft_path']}")
    EMAIL_REPLY_QUEUE.write_text("\n".join([x for x in lines if x]) + "\n", encoding="utf-8")


def append_email_actions(rows: list[dict[str, str]]) -> None:
    EMAIL_ACTIONS.parent.mkdir(parents=True, exist_ok=True)
    exists = EMAIL_ACTIONS.exists()
    with open(EMAIL_ACTIONS, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["timestamp", "to", "subject", "classification", "status", "notes"],
        )
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def parse_referral_contact(subject: str, body: str, from_addr: str) -> dict[str, str] | None:
    text = f"{subject}\n{body}"
    lower = text.lower()
    trigger_phrases = ["retired", "not the right person", "not the right contact", "wrong contact", "contact"]
    if not any(p in lower for p in trigger_phrases):
        return None

    email_match = re.search(r"([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})", text, re.I)
    if not email_match:
        return None
    new_email = email_match.group(1).strip().lower()

    # Common patterns: "Contact Jane Doe at jane@org.com", "Jane Doe (Role) jane@org.com"
    name = ""
    role = ""
    m1 = re.search(r"(?:contact|reach out to|speak with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})", text, re.I)
    if m1:
        name = m1.group(1).strip()
    m2 = re.search(rf"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{0,3}})\s*(?:,|\(|-)\s*([^,\n\)]+)\s*{re.escape(new_email)}", text)
    if m2:
        if not name:
            name = m2.group(1).strip()
        role = m2.group(2).strip()

    if not role:
        m_role = re.search(r"(director|manager|coordinator|educator|specialist|agent|officer|lead)", text, re.I)
        if m_role:
            role = m_role.group(1).title()

    org = ""
    m_org = re.search(r"\b(MSU Extension|MDARD|USDA NRCS|Calhoun Conservation District|Farm Bureau|Kellogg Biological Station)\b", text, re.I)
    if m_org:
        org = m_org.group(1).strip()
    if not org:
        domain = new_email.split("@")[-1]
        org = domain.split(".")[0].replace("-", " ").title()

    return {
        "contact_name": name,
        "org": org,
        "email": new_email,
        "role": role,
        "source_from": from_addr,
        "referred_by": from_addr,
    }


def upsert_contact_map(referrals: list[dict[str, str]]) -> int:
    if not referrals:
        return 0
    rows = []
    if CONTACT_MAP.exists():
        with open(CONTACT_MAP, "r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = [
            "org", "program", "contact_name", "email", "phone", "source_url", "confidence", "notes", "last_attempt_ts", "next_action"
        ]

    existing_emails = {(r.get("email") or "").strip().lower() for r in rows}
    added = 0
    for ref in referrals:
        if ref["email"] in existing_emails:
            continue
        rows.append(
            {
                "org": ref["org"],
                "program": "MDARD/MNARD partner outreach",
                "contact_name": ref["contact_name"],
                "email": ref["email"],
                "phone": "",
                "source_url": "",
                "confidence": "high",
                "notes": f"Auto-extracted referral from reply by {ref['source_from']}. role={ref['role'] or 'unknown'}",
                "last_attempt_ts": "",
                "next_action": "priority_outreach_today",
            }
        )
        existing_emails.add(ref["email"])
        added += 1

    if added:
        with open(CONTACT_MAP, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return added


def append_today_queue(referrals: list[dict[str, str]]) -> None:
    if not referrals:
        return
    lines = []
    if TODAY_QUEUE.exists():
        lines.append(TODAY_QUEUE.read_text(encoding="utf-8").rstrip())
    lines.append("")
    lines.append(f"## Auto-Referral Priority {now_iso()}")
    for ref in referrals:
        role = f" ({ref['role']})" if ref.get("role") else ""
        lines.append(f"- HIGH: Contact {ref.get('contact_name') or '(name missing)'}{role} at {ref['org']} <{ref['email']}>")
    TODAY_QUEUE.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def send_intro_for_referral(ref: dict[str, str]) -> bool:
    if os.environ.get("EXECUTE_SEND", "0").strip() != "1":
        return False
    subject = "Intro — CropCircuit regenerative ag collaboration"
    greeting = ref.get("contact_name") or "there"
    body = (
        f"Hi {greeting},\n\n"
        f"I was referred to you by {ref.get('referred_by', 'a colleague')} as the best contact for this Michigan regenerative agriculture partnership outreach.\n"
        "I run CropCircuit in Battle Creek and we are coordinating a practical grant + partner execution plan with MDARD/MNARD alignment.\n"
        "Would you be open to a brief 15-minute call this week to identify the best collaboration path?\n\n"
        "Best,\n"
        "Casey\n"
        "CropCircuit\n"
        "https://cropcircuit.com\n"
    )
    try:
        to_addr = ref["email"]
        thread_key = build_thread_key(subject, to_addr)
        if human_loop_active():
            reason = "BLOCK: human_loop_requires_safe_autosend_tag"
            draft_path = write_eml(to_addr, subject, body)
            record_email_event(
                "block",
                thread_key,
                now_iso(),
                {
                    "source": "ha_email_triage",
                    "mode": "human_loop_block",
                    "reason": reason,
                    "draft_path": str(draft_path),
                },
            )
            notify_ha_block(
                "Human Loop Blocked Send",
                f"source=ha_email_triage to={to_addr} reason={reason}",
            )
            log(f"referral_human_loop_block email={to_addr} reason={reason} draft={draft_path}")
            return False
        preflight_ok, preflight_detail = run_preflight(verbose=False, retries=3)
        if not preflight_ok:
            reason = f"BLOCK: preflight_imap_failed ({preflight_detail.get('error','unknown')})"
            record_email_event(
                "block",
                thread_key,
                now_iso(),
                {
                    "source": "ha_email_triage",
                    "mode": "preflight_block",
                    "reason": reason,
                    "preflight": preflight_detail,
                },
            )
            notify_ha_block(
                "Email Preflight Blocked Send",
                f"source=ha_email_triage to={to_addr} reason={reason}",
            )
            log(f"referral_preflight_block email={to_addr} reason={reason}")
            return False
        allow, reason = should_send(thread_key, now_iso(), cooldown_minutes=180)
        if not allow:
            draft_path = write_eml(to_addr, subject, body)
            record_email_event(
                "draft_created",
                thread_key,
                now_iso(),
                {
                    "source": "ha_email_triage",
                    "mode": "guard_block",
                    "reason": reason,
                    "draft_path": str(draft_path),
                },
            )
            notify_ha_block(
                "Email Guard Blocked Send",
                f"source=ha_email_triage to={to_addr} reason={reason}",
            )
            log(f"referral_guard_block email={to_addr} reason={reason} draft={draft_path}")
            return False
        from send_grant_email import send_custom_email  # local import after env loaded
        return bool(send_custom_email(to_addr, subject, body, tag=f"referral:{to_addr}"))
    except Exception as e:  # noqa: BLE001
        log(f"referral_send_error email={ref.get('email','')} err={type(e).__name__}")
        return False


def existing_action_keys() -> set[str]:
    if not EMAIL_ACTIONS.exists():
        return set()
    out = set()
    try:
        with open(EMAIL_ACTIONS, "r", encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                key = f"{(r.get('to') or '').strip().lower()}|{(r.get('subject') or '').strip().lower()}|{(r.get('classification') or '').strip().lower()}"
                out.add(key)
    except Exception:
        return out
    return out


def ensure_followup_templates() -> None:
    if FOLLOWUP_TEMPLATES.exists():
        return
    FOLLOWUP_TEMPLATES.write_text(
        "\n".join(
            [
                "# Followup Templates",
                "",
                "## day_3_gentle_nudge",
                "Subject: Quick nudge — should we connect this week?",
                "Body: Hi {name}, quick nudge on my prior note. If useful, I can send a concise one-page summary before a 15-minute call.",
                "",
                "## day_7_different_angle",
                "Subject: Alternate angle — measurable outcomes + local partners",
                "Body: Hi {name}, sharing a different angle: we are focused on measurable outcomes, local partner coordination, and practical implementation.",
                "",
                "## day_14_closing_loop",
                "Subject: Closing the loop for now",
                "Body: Hi {name}, closing the loop for now. If timing changes, I’m happy to reconnect and share the current execution snapshot.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def parse_ts(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def run_followup_engine(recent_emails: list[dict[str, str]]) -> list[dict[str, str]]:
    ensure_followup_templates()
    now = datetime.now(timezone.utc)
    replied_addrs = {(e.get("from_addr") or "").strip().lower() for e in recent_emails}
    actions_rows = []
    if EMAIL_ACTIONS.exists():
        with open(EMAIL_ACTIONS, "r", encoding="utf-8", newline="") as fh:
            actions_rows = list(csv.DictReader(fh))

    last_outreach: dict[str, tuple[datetime, str]] = {}
    for row in actions_rows:
        to_addr = (row.get("to") or "").strip().lower()
        status = (row.get("status") or "").strip().lower()
        if not to_addr or status not in {"sent", "queued", "draft"}:
            continue
        ts = parse_ts((row.get("timestamp") or "").strip())
        if not ts:
            continue
        prev = last_outreach.get(to_addr)
        if not prev or ts > prev[0]:
            last_outreach[to_addr] = (ts, row.get("classification", ""))

    followup_actions = []
    for to_addr, (last_ts, cls) in last_outreach.items():
        if to_addr in replied_addrs:
            continue
        days = (now - last_ts).days
        if days < 3:
            continue
        name_guess = to_addr.split("@")[0].split(".")[0].title()
        if days >= 14:
            subject = "Closing the loop for now"
            body = f"Hi {name_guess},\n\nClosing the loop for now on this thread. If timing changes, I can reconnect with an updated snapshot.\n\nBest,\nCasey\nCropCircuit"
            stage = "followup_14d"
        elif days >= 7:
            subject = "Alternate angle — measurable outcomes + local partners"
            body = f"Hi {name_guess},\n\nSharing a different angle: we are focused on measurable outcomes, local partner coordination, and practical implementation.\n\nBest,\nCasey\nCropCircuit"
            stage = "followup_7d"
        else:
            subject = "Quick nudge — should we connect this week?"
            body = f"Hi {name_guess},\n\nQuick nudge on my prior note. If useful, I can send a concise one-page summary before a 15-minute call.\n\nBest,\nCasey\nCropCircuit"
            stage = "followup_3d"

        dedupe_key = f"{to_addr}|{subject.lower()}|{stage}"
        if dedupe_key in existing_action_keys():
            continue
        draft = write_eml(to_addr, subject, body)
        followup_actions.append(
            {
                "timestamp": now_iso(),
                "to": to_addr,
                "subject": subject,
                "classification": stage,
                "status": "draft",
                "notes": f"auto_followup from={cls} age_days={days} draft={draft}",
            }
        )
    return followup_actions


def append_referral_chain(referrals: list[dict[str, str]]) -> None:
    if not referrals:
        return
    REFERRAL_CHAIN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with REFERRAL_CHAIN_LOG.open("a", encoding="utf-8") as fh:
        for ref in referrals:
            fh.write(
                json.dumps(
                    {
                        "timestamp": now_iso(),
                        "org": ref.get("org", ""),
                        "role": ref.get("role", ""),
                        "email": ref.get("email", ""),
                        "referred_by": ref.get("referred_by", ref.get("source_from", "")),
                    }
                )
                + "\n"
            )


def fetch_recent_emails(hours_back: int = 48, max_results: int = 80) -> list[dict[str, str]]:
    app_pwd = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not app_pwd:
        return []

    try:
        conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        conn.login(GMAIL_USER, app_pwd)
        conn.select("INBOX", readonly=True)
        since = (datetime.now() - timedelta(hours=hours_back)).strftime("%d-%b-%Y")
        typ, data = conn.search(None, f'(SINCE {since})')
        uids = data[0].split() if typ == "OK" and data and data[0] else []
        results = []
        for uid in uids[-max_results:]:
            try:
                typ, msg_data = conn.fetch(uid, "(RFC822)")
                if typ != "OK" or not msg_data or not msg_data[0]:
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                subject = msg.get("Subject", "")
                from_name, from_addr = email.utils.parseaddr(msg.get("From", ""))
                body = extract_text(msg)
                txt = (subject + " " + body).lower()
                if not any(k in txt for k in KEYWORDS):
                    continue
                results.append(
                    {
                        "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
                        "from_name": from_name or "there",
                        "from_addr": from_addr,
                        "subject": subject,
                        "body": body[:4000],
                    }
                )
            except Exception:
                continue
        conn.logout()
        return results
    except Exception as e:  # noqa: BLE001
        log(f"imap_unavailable fallback_reason={type(e).__name__}")
        return []


def ensure_auth_fix_file() -> None:
    HA_AUTH_FIX.write_text(
        "\n".join(
            [
                "# NEEDS_HA_AUTH_FIX",
                "",
                f"Generated: {now_iso()}",
                "Home Assistant returned 401/403 for API access.",
                "Email send/draft via HA is disabled until token/auth is fixed.",
                "System switched to draft-only mode.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def synthesize_known_retired_cases() -> list[dict[str, str]]:
    # Guarantee handling for known retired/wrong-contact MSU cases.
    return [
        {
            "from_name": "MSU Contact 1",
            "from_addr": "msue.calhoun@county.msu.edu",
            "subject": "RE: Following Up — MDARD Regenerative Grant Partnership",
            "body": "I am retired / not the correct point of contact.",
        },
        {
            "from_name": "MSU Contact 2",
            "from_addr": "baasdean@msu.edu",
            "subject": "RE: MDARD Partner Outreach",
            "body": "Not the right contact now.",
        },
    ]


def main() -> int:
    load_env()
    svcs = detect_ha_services()

    draft_only = True
    status_note = "fallback_draft_only"
    if svcs["auth_error"]:
        ensure_auth_fix_file()
    elif not svcs["reachable"]:
        status_note = "ha_unreachable_draft_only"
    elif svcs["email_like_services"]:
        status_note = "ha_email_services_detected_draft_preferred"
    else:
        status_note = "no_ha_email_service_draft_only"

    offline_mode = OFFLINE_MODE_JSON.exists() and '"active": true' in OFFLINE_MODE_JSON.read_text(encoding="utf-8", errors="ignore").lower()
    if offline_mode:
        preflight_ok, preflight_detail = run_preflight(verbose=False, retries=3)
        if not preflight_ok:
            log(f"offline_mode_imap_blocked reason={preflight_detail.get('error','unknown')}")
            emails = []
        else:
            emails = fetch_recent_emails(hours_back=48)
    else:
        emails = fetch_recent_emails(hours_back=48)
    if not emails:
        emails.extend(synthesize_known_retired_cases())

    drafted_entries: list[dict[str, str]] = []
    actions: list[dict[str, str]] = []
    existing_keys = existing_action_keys()
    high_priority_items: list[dict[str, Any]] = []
    referral_contacts: list[dict[str, str]] = []
    warm_leads_count = 0
    grants_detected = 0

    for e in emails:
        bucket = classify_email(e["subject"], e["body"])
        score = score_email(bucket, e["subject"], e["body"])
        if bucket == "warm_lead":
            warm_leads_count += 1
        if bucket == "funding_signal":
            grants_detected += 1

        high_priority_items.append(
            {
                "timestamp": now_iso(),
                "uid": e.get("uid", ""),
                "from_addr": e.get("from_addr", ""),
                "from_name": e.get("from_name", ""),
                "subject": e.get("subject", ""),
                "bucket": bucket,
                "priority_score": score,
            }
        )

        if bucket == "referral":
            referral = parse_referral_contact(e.get("subject", ""), e.get("body", ""), e.get("from_addr", ""))
            if referral:
                referral_contacts.append(referral)

        if bucket not in {"dead_end", "referral"}:
            continue
        subject, body = build_reply(bucket, e.get("from_name", "there"), e.get("subject", ""))
        to_addr = e.get("from_addr", "").strip()
        if not to_addr:
            continue
        dedupe_key = f"{to_addr.lower()}|{subject.strip().lower()}|{bucket}"
        if dedupe_key in existing_keys:
            continue
        draft_path = write_eml(to_addr, subject, body)
        existing_keys.add(dedupe_key)
        drafted_entries.append(
            {
                "to": to_addr,
                "subject": subject,
                "classification": bucket,
                "draft_path": str(draft_path),
            }
        )
        actions.append(
            {
                "timestamp": now_iso(),
                "to": to_addr,
                "subject": subject,
                "classification": bucket,
                "status": "draft" if draft_only else "queued",
                "notes": status_note,
            }
        )

    if drafted_entries:
        append_reply_queue(drafted_entries)

    unique_referrals: list[dict[str, str]] = []
    seen_ref = set()
    for ref in referral_contacts:
        em = (ref.get("email") or "").strip().lower()
        if not em or em in seen_ref:
            continue
        seen_ref.add(em)
        unique_referrals.append(ref)

    added_to_map = upsert_contact_map(unique_referrals)
    append_today_queue(unique_referrals)
    append_referral_chain(unique_referrals)

    referral_intro_sent = 0
    for ref in unique_referrals:
        intro_subject = "Intro — CropCircuit regenerative ag collaboration"
        intro_key = f"{ref['email'].lower()}|{intro_subject.lower()}|referral_intro"
        if intro_key in existing_keys:
            continue
        sent = send_intro_for_referral(ref)
        actions.append(
            {
                "timestamp": now_iso(),
                "to": ref["email"],
                "subject": intro_subject,
                "classification": "referral_intro",
                "status": "sent" if sent else "send_failed",
                "notes": f"referred_by={ref.get('referred_by', ref.get('source_from',''))} org={ref.get('org','')}",
            }
        )
        existing_keys.add(intro_key)
        if sent:
            referral_intro_sent += 1

    followup_actions = run_followup_engine(emails)
    if followup_actions:
        actions.extend(followup_actions)

    if actions:
        append_email_actions(actions)

    added_hp = append_high_priority(high_priority_items)
    active_threads = len({(x.get("from_addr") or "").lower() for x in high_priority_items})
    referral_chains = len(unique_referrals)
    est_probability_score = min(100, int((warm_leads_count * 12) + (grants_detected * 18) + (referral_chains * 10) + (active_threads * 2)))
    write_json(
        FUNDING_PROBABILITY_JSON,
        {
            "timestamp": now_iso(),
            "warm_leads_count": warm_leads_count,
            "active_threads": active_threads,
            "referral_chains": referral_chains,
            "grants_detected": grants_detected,
            "est_probability_score": est_probability_score,
        },
    )

    if svcs["reachable"]:
        notify_ha(
            "CropCircuit Email Triage",
            (
                f"Processed replies={len(high_priority_items)} drafted={len(drafted_entries)}. "
                f"Referrals added={added_to_map} intro_sent={referral_intro_sent}. "
                f"HighPriority+={added_hp}. Mode={status_note}."
            ),
        )

    TRIAGE_STATUS.write_text(
        json.dumps(
            {
                "updated_at": now_iso(),
                "ha": svcs,
                "mode": status_note,
                "drafted_count": len(drafted_entries),
                "high_priority_added": added_hp,
                "referrals_added_to_map": added_to_map,
                "referral_intro_sent": referral_intro_sent,
                "warm_leads_count": warm_leads_count,
                "grants_detected": grants_detected,
                "funding_probability_json": str(FUNDING_PROBABILITY_JSON),
                "email_actions_csv": str(EMAIL_ACTIONS),
                "high_priority_queue": str(HIGH_PRIORITY_QUEUE),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    log(
        "triage_done "
        f"mode={status_note} drafted={len(drafted_entries)} hp_added={added_hp} "
        f"warm={warm_leads_count} grants={grants_detected} referrals={referral_chains} "
        f"referral_intro_sent={referral_intro_sent} prob={est_probability_score}"
    )
    print(
        json.dumps(
            {
                "ok": True,
                "mode": status_note,
                "drafted": len(drafted_entries),
                "high_priority_added": added_hp,
                "warm_leads_count": warm_leads_count,
                "grants_detected": grants_detected,
                "referrals_added_to_map": added_to_map,
                "referral_intro_sent": referral_intro_sent,
                "funding_probability_score": est_probability_score,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
