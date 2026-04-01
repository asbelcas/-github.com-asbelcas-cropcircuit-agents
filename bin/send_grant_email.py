#!/usr/bin/env python3
"""Send grant outreach emails via Gmail SMTP.

Usage:
    python3 send_grant_email.py --list
    python3 send_grant_email.py <email_id>
    python3 send_grant_email.py 1          # Send to Calhoun Conservation District
    python3 send_grant_email.py 1 --dry-run  # Build RFC822 only, do not send
    python3 send_grant_email.py 2          # Send to MSU Extension
    python3 send_grant_email.py all_today  # Send all emails marked for today
    python3 send_grant_email.py all_tomorrow  # Send all emails marked for tomorrow

Requires GMAIL_APP_PASSWORD environment variable.
"""

import argparse
import email
import email.utils
import http.client
import imaplib
import json
import socket
import ssl
import smtplib
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

SENDER_EMAIL = "asbelcas@gmail.com"
SENDER_NAME = "Casey Armstrong"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from ha_config import get_website_url as _get_url
    _WEBSITE = _get_url()
except Exception:
    _WEBSITE = "https://cropcircuit.com"
try:
    from email_guard import (
        build_thread_key,
        human_loop_active,
        is_priority_contact,
        notify_ha_block,
        record_email_event,
        should_send,
    )
except Exception:
    build_thread_key = None
    human_loop_active = None
    is_priority_contact = None
    notify_ha_block = None
    record_email_event = None
    should_send = None
try:
    from preflight_imap import run_preflight
except Exception:
    run_preflight = None

SIGNATURE = f"""
Best regards,

Casey Armstrong
CropCircuit Farm
5828 N 38th St, Augusta, MI 49012
asbelcas@gmail.com
269-986-8595
{_WEBSITE}"""

EMAILS = {
    "1": {
        "to": "calhouncd@gmail.com",
        "subject": "Partnership Opportunity — MDARD Regenerative Farmer Network Grant in Calhoun County",
        "send_day": "today",
        "body": """Hi there,

My name is Casey Armstrong, and I operate CropCircuit Farm, an 18-acre farm in Calhoun County. I'm reaching out because I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000) with a deadline of February 27, and the Calhoun Conservation District is the partner I'd most like to work with on this.

The grant funds a county-level network of farmers adopting regenerative practices — cover cropping, reduced tillage, soil health monitoring — with structured peer learning and technical support. Given your 80 years of conservation leadership in Calhoun County and your partnership with USDA-NRCS at the Marshall office, your soil health expertise would be invaluable to this network.

What I'm asking for is a Memorandum of Understanding to serve as the lead conservation partner. The MOU is straightforward — it outlines your advisory role and willingness to provide technical guidance to participating farmers.

Could we schedule a 15-minute call this week to walk through the details? I'm available any day and happy to work around your schedule. My cell is 269-986-8595.

Thank you for considering this. I believe this grant could make a real difference for soil health across our county."""
    },
    "2": {
        "to": "baasdean@msu.edu",
        "subject": "MDARD Regenerative Farmer Network Grant — Seeking MSU Extension Support in Calhoun County",
        "send_day": "today",
        "body": """Hi Dean,

My name is Casey Armstrong, and I farm 18 acres in Calhoun County under CropCircuit Farm. I'm writing because I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000, due February 27), and I'd love to explore how MSU Extension could be involved.

The grant supports building a county-level network of farmers practicing regenerative agriculture — cover crops, soil health monitoring, reduced tillage — with peer learning sessions and technical mentorship. MSU Extension's sustainable agriculture expertise and soil health research would be a tremendous asset to the farmers in this network.

I'm flexible on the form of support. That could mean serving as an advisory partner, co-facilitating workshops, providing a letter of support, or even a formal MOU partnership if that's appropriate.

Would you have time for a brief call this week to discuss what role might be the best fit? I'm happy to share the full grant details. You can reach me anytime at 269-986-8595.

Thank you for your time, and I look forward to connecting."""
    },
    "3": {
        "to": "calhouncfb@gmail.com",
        "subject": "Help Connecting Calhoun County Farmers with a New MDARD Regenerative Ag Grant",
        "send_day": "tomorrow",
        "body": """Hello,

My name is Casey Armstrong. I operate CropCircuit Farm in Calhoun County and I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000), which funds a peer-learning network for farmers adopting regenerative practices like cover cropping, soil health monitoring, and reduced tillage.

I need to recruit at least 5 farmers in Calhoun County who are interested in joining or already doing conservation-minded work. With your connection to 898 farms across the county, the Farm Bureau is uniquely positioned to help spread the word.

I have two asks. First, would you be willing to share this opportunity with your members through your newsletter, email list, or social channels? Second, can you point me toward any specific farmers you know who are already doing regenerative or conservation work and might be interested?

I'm happy to provide a short write-up you can share. Feel free to call or email me anytime.

Thank you for supporting Calhoun County agriculture."""
    },
    "4": {
        "to": "MANUAL",
        "subject": "Invitation to Join MDARD-Funded Regenerative Farmer Network in Calhoun County Area",
        "send_day": "tomorrow",
        "note": "Submit via drumhillerfarms.com contact form",
        "body": """Hi there,

My name is Casey Armstrong, and I run CropCircuit Farm, an 18-acre operation in Calhoun County. I'm reaching out because Drumhiller Farms is exactly the kind of operation I'd love to have in a new regenerative farmer network I'm building.

I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000), which funds a structured peer-learning network for farmers practicing regenerative agriculture. You're already doing this work — grass-fed livestock, pastured poultry, soil-first management — and you hosted MDARD's regenerative ag workshop, which tells me you're invested in this movement. Since you serve the Calhoun County area, it's a natural fit.

What I'm asking is simple: would you be willing to join the network as a farmer member and sign a brief commitment letter saying you'll participate in peer learning sessions and share your experience? No cost to you — the grant covers everything.

I'd love to talk. You can reach me at 269-986-8595 or asbelcas@gmail.com."""
    },
    "5": {
        "to": "MANUAL",
        "subject": "Community Partnership — MDARD Regenerative Farmer Network Grant in Battle Creek",
        "send_day": "tomorrow",
        "note": "Submit via sprouturbanfarms.org/contact-us AND call 269-962-3003",
        "body": """Hello,

My name is Casey Armstrong, and I operate CropCircuit Farm, an 18-acre farm in Calhoun County. I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000, deadline February 27), and I'd love for Sprout Urban Farms to be part of it.

The grant builds a county-level network of farmers adopting regenerative practices — cover cropping, soil health improvement, reduced tillage — with peer learning and community outreach. Your food access work in Battle Creek and your community education programs align directly with the grant's goals of connecting regenerative farming to the broader community.

Given Sprout's 501(c)(3) status and deep roots in Battle Creek, I'd welcome your involvement as a community partner. That could be as straightforward as providing a letter of support describing how a regenerative farmer network would benefit the communities you serve.

Could we connect briefly this week? I'm at 269-986-8595 or asbelcas@gmail.com anytime.

Thank you for all the work you do for Battle Creek."""
    },
    "6": {
        "to": "Perez@bcunlimited.org",
        "subject": "Letter of Support Request — MDARD Regenerative Farmer Network Grant",
        "send_day": "tomorrow",
        "body": """Dear Gabriela,

My name is Casey Armstrong, and I operate CropCircuit Farm, an 18-acre farm here in Calhoun County. I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000, deadline February 27) and would be grateful for a letter of support from Battle Creek Food Reimagined.

The grant funds a peer-learning network for Calhoun County farmers adopting regenerative practices — cover cropping, soil health monitoring, reduced tillage — with the goal of strengthening our local food system from the ground up. BCFR's food innovation work, your partnership with MEDC, and your direct support of local food producers make you an ideal voice to speak to why this matters.

A brief letter connecting regenerative farming practices to local food entrepreneurship and food system resilience would carry real weight with the reviewers.

Would you be open to providing that support? I'm happy to share grant details or draft language to make it easy. You can reach me at 269-986-8595 or asbelcas@gmail.com.

Thank you for your leadership in Battle Creek's food economy."""
    },
    "7": {
        "to": "info@kbs.msu.edu",
        "subject": "Letter of Support Request — MDARD Regenerative Farmer Network Grant (Calhoun Network)",
        "send_day": "tomorrow",
        "body": """Hello KBS Team,

My name is Casey Armstrong, and I run CropCircuit Farm in Calhoun County. I am applying for the MDARD Regenerative Farmer Network Grant ($50,000, deadline February 27) and would be grateful for a brief letter of support from W.K. Kellogg Biological Station.

The project builds a farmer-led regenerative network focused on measurable soil health outcomes, peer learning, and practical on-farm implementation. KBS's long-term agroecology and soil systems research makes your perspective uniquely valuable to this effort.

A short letter confirming support for this type of county-level regenerative network and data-informed soil stewardship would strengthen the application significantly.

If useful, I can share draft language and project details immediately. I am reachable at 269-986-8595 or asbelcas@gmail.com.

Thank you for your consideration."""
    },
    "8": {
        "to": "msue.calhoun@county.msu.edu",
        "subject": "Partnership Request — MDARD Regenerative Farmer Network Grant (Calhoun County)",
        "send_day": "tomorrow",
        "body": """Hello MSU Extension Calhoun Team,

My name is Casey Armstrong, and I operate CropCircuit Farm in Calhoun County. I am applying for the MDARD Regenerative Farmer Network Grant ($50,000, deadline February 27) and am seeking an Extension partner for advisory support and outreach.

The proposed network supports local farmers adopting regenerative practices, including soil health monitoring, cover cropping, and peer learning events. MSU Extension is an ideal fit given your local presence and technical leadership.

Would your office be open to a brief call this week to discuss a support role or letter of support? I can send a concise summary and draft language to make review easy.

I can be reached at 269-986-8595 or asbelcas@gmail.com. Thank you for your time."""
    }
}

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = SCRIPT_DIR.parent


def _load_list_file(filename):
    """Load a set of lowercased email addresses from a text file (one per line, # comments ok)."""
    p = REPO_ROOT / "runtime" / filename
    try:
        return {
            line.strip().lower()
            for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
    except FileNotFoundError:
        return set()


def load_denylist():
    return _load_list_file("email_denylist.txt")


def load_holdlist():
    return _load_list_file("email_holdlist.txt")


DOH_IP = "1.1.1.1"
DOH_SNI = "cloudflare-dns.com"
IMAP_USER = os.environ.get("IMAP_USER", "asbelcas@gmail.com")
IMAP_HOST = os.environ.get("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))


class SMTPSSLByIP(smtplib.SMTP_SSL):
    """SMTP over SSL that connects to an explicit IP but verifies cert via logical host."""

    def __init__(self, connect_ip, logical_host, port, timeout, context):
        self._connect_ip = connect_ip
        super().__init__(host=logical_host, port=port, timeout=timeout, context=context)

    def _get_socket(self, host, port, timeout):
        if timeout is not None and not timeout:
            raise ValueError("Non-blocking socket (timeout=0) is not supported")
        new_socket = socket.create_connection((self._connect_ip, port), timeout, self.source_address)
        return self.context.wrap_socket(new_socket, server_hostname=host)


def _unique_preserve(values):
    out = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


def doh_resolve_a(name, timeout=8):
    """Resolve A records via Cloudflare DoH over direct IP connection (no local DNS needed)."""
    query_path = f"/dns-query?name={quote_plus(name)}&type=A"
    ctx = ssl.create_default_context()
    ips = []

    try:
        raw_sock = socket.create_connection((DOH_IP, 443), timeout=timeout)
        try:
            tls_sock = ctx.wrap_socket(raw_sock, server_hostname=DOH_SNI)
            request = (
                f"GET {query_path} HTTP/1.1\r\n"
                f"Host: {DOH_SNI}\r\n"
                "Accept: application/dns-json\r\n"
                "Connection: close\r\n"
                "User-Agent: cropcircuit-mailer/1.0\r\n"
                "\r\n"
            ).encode("ascii")
            tls_sock.sendall(request)

            response = http.client.HTTPResponse(tls_sock)
            response.begin()
            if response.status != 200:
                return []

            payload = response.read()
            data = json.loads(payload.decode("utf-8", errors="replace"))
            for answer in data.get("Answer", []):
                if answer.get("type") == 1 and isinstance(answer.get("data"), str):
                    ips.append(answer["data"])
            return _unique_preserve(ips)
        finally:
            raw_sock.close()
    except Exception:
        return []


def system_resolve_a(host, port):
    try:
        records = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    ips = [item[4][0] for item in records if item and item[4]]
    return _unique_preserve(ips)


def resolve_smtp_host(host, port):
    system_ips = system_resolve_a(host, port)
    if system_ips:
        return system_ips, "system"
    doh_ips = doh_resolve_a(host)
    if doh_ips:
        return doh_ips, "doh"
    return [], "none"


def run_dns_check():
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    system_ips = system_resolve_a(host, port)
    doh_ips = doh_resolve_a(host)
    chosen_ips, source = resolve_smtp_host(host, port)
    chosen_ip = chosen_ips[0] if chosen_ips else "(none)"
    print(f"DNS CHECK host={host} port={port}")
    print(f"system_dns={system_ips if system_ips else '(none)'}")
    print(f"doh_dns={doh_ips if doh_ips else '(none)'}")
    print(f"chosen_source={source}")
    print(f"chosen_ip={chosen_ip}")


def normalize_subject_root(subject: str) -> str:
    s = (subject or "").strip()
    while True:
        lowered = s.lower()
        if lowered.startswith("re:"):
            s = s[3:].strip()
        elif lowered.startswith("fwd:"):
            s = s[4:].strip()
        else:
            break
    return " ".join(s.split())


def imap_connect(host: str, port: int):
    """Connect IMAP with DNS fallback to DoH-resolved IP + SNI stream."""
    try:
        return imaplib.IMAP4_SSL(host, port)
    except Exception:
        ips, _source = resolve_smtp_host(host, port)
        if not ips:
            raise
        ip = ips[0]
        cmd = f"openssl s_client -quiet -connect {ip}:{port} -servername {host} 2>/dev/null"
        return imaplib.IMAP4_stream(cmd)


def _parse_email_datetime(value: str):
    if not value:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(value)
    except Exception:
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def imap_last_inbound_after(to_email: str, subject_root: str, after_dt_utc) -> datetime | None:
    """
    Returns datetime of last inbound email from recipient AFTER after_dt_utc,
    or None if no newer inbound exists.

    Uses IMAP because OAuth Gmail API isn't configured.
    """
    if not GMAIL_APP_PASSWORD:
        return None

    if after_dt_utc.tzinfo is None:
        after_dt_utc = after_dt_utc.replace(tzinfo=timezone.utc)
    else:
        after_dt_utc = after_dt_utc.astimezone(timezone.utc)

    to_email_l = (to_email or "").strip().lower()
    if not to_email_l or "@" not in to_email_l:
        return None
    domain = to_email_l.split("@", 1)[1]

    subject_norm = normalize_subject_root(subject_root)
    subject_token = " ".join(subject_norm.split()[:6])[:60]
    since_date = after_dt_utc.strftime("%d-%b-%Y")

    conn = imap_connect(IMAP_HOST, IMAP_PORT)
    try:
        conn.login(IMAP_USER, GMAIL_APP_PASSWORD)
        conn.select("INBOX", readonly=True)

        query_candidates = [
            f'(SINCE "{since_date}" FROM "{to_email_l}")',
            f'(SINCE "{since_date}" FROM "{domain}")',
        ]
        if subject_token:
            query_candidates.extend([
                f'(SINCE "{since_date}" FROM "{to_email_l}" SUBJECT "{subject_token}")',
                f'(SINCE "{since_date}" FROM "{domain}" SUBJECT "{subject_token}")',
            ])

        msg_ids = []
        for query in query_candidates:
            try:
                status, data = conn.search(None, query)
            except Exception:
                continue
            if status != "OK" or not data or not data[0]:
                continue
            msg_ids.extend(data[0].split())

        if not msg_ids:
            return None

        seen = set()
        ordered_ids = []
        for mid in msg_ids:
            if mid in seen:
                continue
            seen.add(mid)
            ordered_ids.append(mid)

        last_inbound = None
        for mid in ordered_ids:
            try:
                status, data = conn.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            except Exception:
                continue
            if status != "OK" or not data or not data[0]:
                continue
            header_bytes = data[0][1] if isinstance(data[0], tuple) and len(data[0]) > 1 else b""
            if not header_bytes:
                continue

            try:
                msg = email.message_from_bytes(header_bytes)
            except Exception:
                continue

            from_hdr = (msg.get("From") or "").lower()
            subj_hdr = normalize_subject_root(msg.get("Subject", ""))
            date_hdr = msg.get("Date", "")
            dt = _parse_email_datetime(date_hdr)
            if not dt or dt <= after_dt_utc:
                continue

            if to_email_l not in from_hdr and domain not in from_hdr:
                continue
            if subject_norm and subject_norm.lower() not in subj_hdr.lower():
                continue

            if last_inbound is None or dt > last_inbound:
                last_inbound = dt

        return last_inbound
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def send_email(email_id):
    """Send a single email by ID."""
    email_data = EMAILS.get(email_id)
    if not email_data:
        print(f"ERROR: Email ID '{email_id}' not found. Valid IDs: {list(EMAILS.keys())}")
        return False

    if email_data["to"] == "MANUAL":
        print(f"SKIP: Email {email_id} requires manual submission.")
        if "note" in email_data:
            print(f"  -> {email_data['note']}")
        print(f"  Subject: {email_data['subject']}")
        print(f"  Body saved — copy from ready_to_send_emails.md")
        return True

    return send_custom_email(email_data["to"], email_data["subject"], email_data["body"], tag=f"id={email_id}")


def build_message(to_addr, subject, body):
    """Build MIME message payload."""
    msg = MIMEMultipart()
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to_addr
    msg["Subject"] = subject

    full_body = body + SIGNATURE
    msg.attach(MIMEText(full_body, "plain"))
    return msg


def save_dry_run_message(email_id, msg, *, reason="dry_run"):
    out_dir = Path("/home/asbelcas/cropcircuit/runtime/outbox_emails")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"dry_run_{email_id}_{ts}.eml"
    out_path.write_text(msg.as_string(), encoding="utf-8")
    print(f'DRAFT: to {msg["To"]} subject "{msg["Subject"]}" reason={reason}')
    print(f"Saved: {out_path}")
    return True


def send_custom_email(to_addr, subject, body, tag="custom", dry_run=False):
    """Send an arbitrary email payload via configured Gmail SMTP."""
    msg = build_message(to_addr, subject, body)

    thread_key = build_thread_key(subject, to_addr) if build_thread_key else f"{subject.lower()}|{to_addr.lower()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    if dry_run:
        if record_email_event:
            record_email_event("draft_created", thread_key, now_iso, {"tag": tag, "mode": "dry_run"})
        return save_dry_run_message(tag.replace("id=", ""), msg, reason="dry_run")

    if human_loop_active and human_loop_active() and "SAFE_AUTOSEND" not in (tag or "").upper():
        reason = "BLOCK: human_loop_requires_safe_autosend_tag"
        if record_email_event:
            record_email_event(
                "block",
                thread_key,
                now_iso,
                {"source": "send_grant_email", "tag": tag, "reason": reason},
            )
        if notify_ha_block:
            notify_ha_block(
                "Human Loop Blocked Send",
                f"source=send_grant_email to={to_addr} tag={tag} reason={reason}",
            )
        print(f"BLOCKED by human loop mode: {reason} thread={thread_key}")
        return save_dry_run_message(tag.replace("id=", ""), msg, reason=reason)

    if run_preflight:
        ok, detail = run_preflight(verbose=False, retries=3)
        if not ok:
            reason = f"BLOCK: preflight_imap_failed ({detail.get('error','unknown')})"
            if record_email_event:
                record_email_event(
                    "block",
                    thread_key,
                    now_iso,
                    {
                        "source": "send_grant_email",
                        "tag": tag,
                        "mode": "preflight_block",
                        "reason": reason,
                        "preflight": detail,
                    },
                )
            if notify_ha_block:
                notify_ha_block(
                    "Email Preflight Blocked Send",
                    f"source=send_grant_email tag={tag} to={to_addr} reason={reason}",
                )
            print(f"BLOCKED by IMAP preflight: {reason} thread={thread_key}")
            return False

    if should_send:
        allow, reason = should_send(thread_key, now_iso, cooldown_minutes=180)
        if not allow:
            if record_email_event:
                record_email_event("draft_created", thread_key, now_iso, {"tag": tag, "mode": "guard_block", "reason": reason})
            if notify_ha_block:
                notify_ha_block(
                    "Email Guard Blocked Send",
                    f"tag={tag} to={to_addr} reason={reason} thread={thread_key}",
                )
            print(f"BLOCKED by email guard: {reason} thread={thread_key}")
            return save_dry_run_message(tag.replace("id=", ""), msg, reason=reason)

    if not GMAIL_APP_PASSWORD:
        print("ERROR: GMAIL_APP_PASSWORD not set. Run: export GMAIL_APP_PASSWORD='your-app-password'")
        return False

    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_ips, resolve_source = resolve_smtp_host(smtp_host, smtp_port)
    if not smtp_ips:
        print(f"ERROR sending email {tag}: unable to resolve SMTP host {smtp_host} via system DNS and DoH fallback")
        return False
    smtp_ip = smtp_ips[0]
    tls_ctx = ssl.create_default_context()

    try:
        if record_email_event:
            record_email_event("send_attempt", thread_key, now_iso, {"tag": tag, "to": to_addr, "subject": subject})
        if smtp_port == 465:
            with SMTPSSLByIP(
                connect_ip=smtp_ip,
                logical_host=smtp_host,
                port=smtp_port,
                timeout=20,
                context=tls_ctx,
            ) as server:
                server.ehlo(smtp_host)
                server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
                server.send_message(msg)
        elif smtp_port == 587:
            with smtplib.SMTP(timeout=20) as server:
                server.connect(smtp_ip, smtp_port)
                # Force SNI/cert hostname during STARTTLS while TCP goes to resolved IP.
                server._host = smtp_host
                server.ehlo(smtp_host)
                server.starttls(context=tls_ctx)
                server.ehlo(smtp_host)
                server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
                server.send_message(msg)
        else:
            print(f"ERROR sending email {tag}: unsupported SMTP_PORT={smtp_port} (use 465 or 587)")
            return False
        if record_email_event:
            record_email_event("send_success", thread_key, datetime.now(timezone.utc).isoformat(), {"tag": tag, "to": to_addr, "subject": subject})
        print(f"SENT: Email {tag} to {to_addr} — {subject} (smtp_ip={smtp_ip} source={resolve_source})")
        return True
    except smtplib.SMTPAuthenticationError:
        print("ERROR: Gmail authentication failed. Check your App Password.")
        print("  Generate one at: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"ERROR sending email {tag}: {e}")
        return False


def list_emails():
    denylist = load_denylist()
    holdlist = load_holdlist()
    print("Available email IDs:")
    for eid in sorted(EMAILS, key=lambda x: int(x)):
        data = EMAILS[eid]
        to_addr = data.get("to", "")
        subj = data.get("subject", "")
        day = data.get("send_day", "")
        flags = ""
        if to_addr.lower() in denylist:
            flags = " [BLOCKED-denylist]"
        elif to_addr.lower() in holdlist:
            flags = " [ON HOLD]"
        elif to_addr == "MANUAL":
            flags = " [MANUAL]"
        if is_priority_contact and is_priority_contact(to_addr):
            flags += " [PRIORITY]"
        print(f"{eid}: to={to_addr} day={day}{flags} subject={subj}")


def main():
    parser = argparse.ArgumentParser(description="Send grant outreach emails")
    parser.add_argument("email_id", nargs="?", help="Email ID (1..8), all, all_today, all_tomorrow")
    parser.add_argument("--dry-run", action="store_true", help="Build message(s) and save .eml without sending")
    parser.add_argument("--execute", action="store_true", help="Explicitly execute send (required for live send; default is draft-only)")
    parser.add_argument("--list", action="store_true", help="List available email IDs")
    parser.add_argument("--tag", default="", help="Optional send tag; include SAFE_AUTOSEND to permit live send in human-loop mode")
    parser.add_argument("--dns-check", action="store_true", help="Show system DNS, DoH fallback, and chosen SMTP IP")
    args = parser.parse_args()

    if args.dns_check:
        run_dns_check()
        return

    if args.list or not args.email_id:
        list_emails()
        return

    effective_dry_run = args.dry_run or (not args.execute)
    if not args.execute and not args.dry_run:
        print("INFO: draft-only mode active (use --execute for live send).")

    target = args.email_id
    denylist = load_denylist()
    holdlist = load_holdlist()

    def run_target(eid):
        email_data = EMAILS.get(eid)
        if not email_data:
            print(f"ERROR: Email ID '{eid}' not found. Valid IDs: {list(EMAILS.keys())}")
            return
        to_addr = email_data["to"]
        to_lower = to_addr.lower()

        # Denylist: block all modes (send and dry-run build the .eml but never send)
        if to_lower in denylist:
            print(f"BLOCKED: {to_addr} is in denylist (runtime/email_denylist.txt)")
            if effective_dry_run:
                msg = build_message(to_addr, email_data["subject"], email_data["body"])
                save_dry_run_message(eid, msg)
            return

        # Holdlist: dry-run allowed, live send blocked
        if to_lower in holdlist and not effective_dry_run:
            print(f"ON HOLD: {to_addr} is paused (runtime/email_holdlist.txt) — use --dry-run to preview")
            return

        if to_addr == "MANUAL":
            print(f"SKIP: Email {eid} requires manual submission.")
            if "note" in email_data:
                print(f"  -> {email_data['note']}")
            print(f"  Subject: {email_data['subject']}")
            print("  Body saved — copy from ready_to_send_emails.md")
            if effective_dry_run:
                msg = build_message(to_addr, email_data["subject"], email_data["body"])
                save_dry_run_message(eid, msg)
            return
        send_custom_email(
            to_addr,
            email_data["subject"],
            email_data["body"],
            tag=(f"{args.tag}|id={eid}" if args.tag else f"id={eid}"),
            dry_run=effective_dry_run,
        )

    if target == "all_today":
        for eid, data in EMAILS.items():
            if data["send_day"] == "today":
                run_target(eid)
    elif target == "all_tomorrow":
        for eid, data in EMAILS.items():
            if data["send_day"] == "tomorrow":
                run_target(eid)
    elif target == "all":
        for eid in EMAILS:
            run_target(eid)
    else:
        run_target(target)


if __name__ == "__main__":
    main()
