#!/usr/bin/env python3
from __future__ import annotations

import email
import email.utils
import imaplib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path('/home/asbelcas/cropcircuit')
RUNTIME = ROOT / 'runtime'
OUT = RUNTIME / 'replies_classified.json'


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k, v = s.split('=', 1)
        k = k.strip().removeprefix('export ').strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def load_env() -> None:
    for f in ['.env', '.env.grant', '.env.donor', '.env.x']:
        load_env_file(ROOT / f)


def classify(subject: str, body: str) -> str:
    t = (subject + '\n' + body).lower()
    if any(k in t for k in ['retired', 'wrong office', 'no longer handling', 'not the right person', 'wrong contact']):
        return 'dead_end'
    if any(k in t for k in ['contact ', 'try ', 'reach out to']):
        return 'referral'
    if any(k in t for k in ['happy to talk', 'interested', "let's connect", 'lets connect', 'available', 'call']):
        return 'warm'
    if any(k in t for k in ['grant', 'rfp', 'application', 'funding cycle', 'deadline']):
        return 'funding_signal'
    return 'other'


def classify_incoming(subject: str, body: str, from_addr: str) -> str:
    t = (subject + '\\n' + body).lower()
    a = from_addr.lower()
    if any(k in a for k in ['mdard', 'nrcs', 'msu.edu', 'conservation', 'county.msu.edu']) or any(k in t for k in ['partner', 'conservation district', 'letter of support', 'collaboration']):
        return 'partner'
    if any(k in t for k in ['grant', 'rfp', 'application', 'deadline', 'funding cycle']):
        return 'grant'
    if any(k in t for k in ['outreach', 'follow up', 'follow-up', 'call', 'meeting']):
        return 'outreach'
    return 'irrelevant'


def extract_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        parts = []
        for p in msg.walk():
            if p.get_content_type() == 'text/plain':
                payload = p.get_payload(decode=True)
                if payload:
                    parts.append(payload.decode('utf-8', errors='replace'))
        return '\n'.join(parts)
    payload = msg.get_payload(decode=True)
    return payload.decode('utf-8', errors='replace') if payload else ''


def fetch_replies() -> list[dict]:
    user = os.environ.get('IMAP_USER', os.environ.get('GMAIL_USER', 'asbelcas@gmail.com'))
    pwd = os.environ.get('IMAP_APP_PASSWORD', os.environ.get('GMAIL_APP_PASSWORD', '')).strip()
    host = os.environ.get('IMAP_HOST', 'imap.gmail.com')
    port = int(os.environ.get('IMAP_PORT', '993'))
    if not pwd:
        return []

    out = []
    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(user, pwd)
    conn.select('INBOX', readonly=True)
    since = (datetime.now() - timedelta(days=5)).strftime('%d-%b-%Y')
    typ, data = conn.search(None, f'(SINCE {since})')
    ids = data[0].split() if typ == 'OK' and data and data[0] else []

    for uid in ids[-120:]:
        try:
            typ, msg_data = conn.fetch(uid, '(RFC822)')
            if typ != 'OK' or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subject = str(msg.get('Subject', ''))
            from_name, from_addr = email.utils.parseaddr(msg.get('From', ''))
            body = extract_text(msg)[:5000]
            bucket = classify(subject, body)
            if bucket == 'other':
                continue
            out.append(
                {
                    'timestamp': now_iso(),
                    'uid': uid.decode() if isinstance(uid, bytes) else str(uid),
                    'from_name': from_name,
                    'from_addr': from_addr,
                    'subject': subject,
                    'body': body,
                    'bucket': bucket,
                    'incoming_class': classify_incoming(subject, body, from_addr),
                }
            )
        except Exception:
            continue
    conn.logout()
    return out


def fallback_from_queue() -> list[dict]:
    hp = RUNTIME / 'high_priority_queue.json'
    if not hp.exists():
        return []
    try:
        rows = json.loads(hp.read_text(encoding='utf-8'))
    except Exception:
        return []
    out = []
    for r in rows[-50:]:
        if not isinstance(r, dict):
            continue
        b = r.get('bucket')
        if b not in {'warm', 'referral', 'dead_end', 'funding_signal'}:
            continue
        out.append(
            {
                'timestamp': now_iso(),
                'uid': str(r.get('uid', '')),
                'from_name': str(r.get('from_name', '')),
                'from_addr': str(r.get('from_addr', '')),
                'subject': str(r.get('subject', '')),
                'body': str(r.get('body', '')),
                'bucket': b,
            }
        )
    return out


def main() -> int:
    load_env()
    RUNTIME.mkdir(parents=True, exist_ok=True)
    try:
        rows = fetch_replies()
        source = 'imap'
    except Exception:
        rows = fallback_from_queue()
        source = 'fallback'

    payload = {
        'updated_at': now_iso(),
        'source': source,
        'counts': {
            'warm': sum(1 for r in rows if r['bucket'] == 'warm'),
            'referral': sum(1 for r in rows if r['bucket'] == 'referral'),
            'dead_end': sum(1 for r in rows if r['bucket'] == 'dead_end'),
            'funding_signal': sum(1 for r in rows if r['bucket'] == 'funding_signal'),
        },
        'incoming_counts': {
            'partner': sum(1 for r in rows if r.get('incoming_class') == 'partner'),
            'grant': sum(1 for r in rows if r.get('incoming_class') == 'grant'),
            'outreach': sum(1 for r in rows if r.get('incoming_class') == 'outreach'),
            'irrelevant': sum(1 for r in rows if r.get('incoming_class') == 'irrelevant'),
        },
        'items': rows,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'source': source, 'classified': len(rows), 'stored': str(OUT)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
