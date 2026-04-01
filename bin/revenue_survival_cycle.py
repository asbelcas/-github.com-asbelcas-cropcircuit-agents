#!/usr/bin/env python3
from __future__ import annotations

import csv
import email
import email.utils
import imaplib
import json
import os
import socket
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path('/home/asbelcas/cropcircuit')
RUNTIME = ROOT / 'runtime'
LOGS = ROOT / 'logs'

OUT_TARGETS = RUNTIME / 'high_probability_revenue_targets.json'
OUT_DRAFTS = RUNTIME / 'revenue_offer_drafts.json'
OUT_SOCIAL = RUNTIME / 'revenue_social_posts.json'
OUT_PACKAGES = RUNTIME / 'service_packages.json'
OUT_ESCALATION = RUNTIME / 'revenue_escalation_state.json'
OUT_MDARD = RUNTIME / 'mdard_execution_state.json'
HEARTBEAT = RUNTIME / 'ops_heartbeat.log'
DECISIONS = RUNTIME / 'decision_log.json'
SUPPRESS = RUNTIME / 'suppress_senders.txt'


def now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def now_iso() -> str:
    return now().isoformat()


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


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return fallback


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def read_suppress_list() -> set[str]:
    if not SUPPRESS.exists():
        return set()
    out = set()
    for line in SUPPRESS.read_text(encoding='utf-8').splitlines():
        s = line.strip().lower()
        if not s or s.startswith('#'):
            continue
        out.add(s)
    return out


def is_email_like(value: str) -> bool:
    v = (value or '').strip()
    return '@' in v and ' ' not in v and '.' in v.split('@')[-1]


def append_heartbeat(msg: str) -> None:
    HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    with HEARTBEAT.open('a', encoding='utf-8') as f:
        f.write(f"{now_iso()} mode=revenue_survival {msg}\n")


def append_decision(decision: str, details: str) -> None:
    entries = read_json(DECISIONS, [])
    if not isinstance(entries, list):
        entries = []
    entries.append({'timestamp': now_iso(), 'decision': decision, 'details': details})
    write_json(DECISIONS, entries[-1000:])


def extract_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        parts = []
        for p in msg.walk():
            if p.get_content_type() == 'text/plain':
                d = p.get_payload(decode=True)
                if d:
                    parts.append(d.decode('utf-8', errors='replace'))
        return '\n'.join(parts)
    d = msg.get_payload(decode=True)
    return d.decode('utf-8', errors='replace') if d else ''


def classify_revenue(subject: str, body: str, from_addr: str) -> tuple[str, int]:
    t = (subject + '\n' + body).lower()
    a = from_addr.lower()
    score = 25
    category = 'other'

    if any(k in t for k in ['consulting', 'advisor', 'contract', 'proposal request']):
        category, score = 'consulting', 92
    elif any(k in t for k in ['grant writing', 'help with grant', 'application help', 'rfp support']):
        category, score = 'grant_writing_for_others', 90
    elif any(k in t for k in ['automation', 'workflow', 'pipeline setup', 'crm', 'follow-up system']):
        category, score = 'outreach_automation_install', 88
    elif any(k in t for k in ['retainer', 'monthly support', 'ongoing support']) or any(k in a for k in ['conservation', 'district', 'extension', 'farmbureau']):
        category, score = 'ag_org_support_retainer', 84
    elif any(k in t for k in ['local business', 'small business', 'operations automation']):
        category, score = 'local_business_automation', 78

    if any(k in t for k in ['call', 'meeting', 'this week', 'urgent', 'deadline']):
        score += 6
    if any(k in t for k in ['not interested', 'unsubscribe', 'promotion', 'sale', 'shop now']):
        score -= 25
    score = max(1, min(100, score))
    return category, score


def fetch_imap_folder(conn, folder: str, days_back: int = 14, max_n: int = 200) -> list[dict]:
    out = []
    try:
        typ, _ = conn.select(folder, readonly=True)
        if typ != 'OK':
            return out
        since = (datetime.now() - timedelta(days=days_back)).strftime('%d-%b-%Y')
        typ, data = conn.search(None, f'(SINCE {since})')
        ids = data[0].split() if typ == 'OK' and data and data[0] else []
        for uid in ids[-max_n:]:
            try:
                typ, msg_data = conn.fetch(uid, '(RFC822)')
                if typ != 'OK' or not msg_data or not msg_data[0]:
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                subject = str(msg.get('Subject', ''))
                from_name, from_addr = email.utils.parseaddr(msg.get('From', ''))
                body = extract_text(msg)[:5000]
                out.append({
                    'mailbox': folder,
                    'uid': uid.decode() if isinstance(uid, bytes) else str(uid),
                    'from_name': from_name,
                    'from_addr': from_addr,
                    'subject': subject,
                    'body': body,
                })
            except Exception:
                continue
    except Exception:
        return out
    return out


def scan_mailboxes() -> list[dict]:
    socket.setdefaulttimeout(20)
    user = os.environ.get('IMAP_USER', os.environ.get('GMAIL_USER', 'asbelcas@gmail.com'))
    pwd = os.environ.get('IMAP_APP_PASSWORD', os.environ.get('GMAIL_APP_PASSWORD', '')).strip()
    host = os.environ.get('IMAP_HOST', 'imap.gmail.com')
    port = int(os.environ.get('IMAP_PORT', '993'))
    if not pwd:
        return []

    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(user, pwd)
    items = []
    items.extend(fetch_imap_folder(conn, 'INBOX', days_back=14, max_n=220))
    # Common Gmail sent folder names
    for sent_name in ['"[Gmail]/Sent Mail"', '[Gmail]/Sent Mail', 'Sent', 'Sent Mail']:
        sent_items = fetch_imap_folder(conn, sent_name, days_back=14, max_n=180)
        if sent_items:
            items.extend(sent_items)
            break
    conn.logout()
    return items


def scan_mailboxes_bounded(timeout_seconds: int = 45) -> tuple[list[dict], str]:
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(scan_mailboxes)
        try:
            return fut.result(timeout=timeout_seconds), 'imap_inbox_sent'
        except FuturesTimeout:
            return [], 'imap_timeout'
        except Exception:
            return [], 'imap_failed'


def local_contacts() -> list[dict]:
    rows = []
    for path in [ROOT / 'partners_contacts.csv', ROOT / 'outreach_log.csv']:
        if not path.exists():
            continue
        with path.open('r', encoding='utf-8', newline='') as fh:
            for r in csv.DictReader(fh):
                org = (r.get('Org_Name') or '').strip()
                email_addr = (r.get('Email') or '').strip()
                if not org and not email_addr:
                    continue
                rows.append({'org': org, 'email': email_addr, 'source': path.name})
    return rows


def build_targets(items: list[dict], contacts: list[dict]) -> dict:
    suppress = read_suppress_list()
    self_email = os.environ.get('IMAP_USER', os.environ.get('GMAIL_USER', 'asbelcas@gmail.com')).strip().lower()
    targets = []
    for it in items:
        from_addr = (it.get('from_addr','') or '').strip().lower()
        if not is_email_like(from_addr):
            continue
        if from_addr == self_email or from_addr in suppress:
            continue
        cat, score = classify_revenue(it.get('subject',''), it.get('body',''), it.get('from_addr',''))
        if cat == 'other':
            continue
        targets.append({
            'timestamp': now_iso(),
            'source_mailbox': it.get('mailbox',''),
            'contact_name': it.get('from_name',''),
            'contact_email': it.get('from_addr',''),
            'org_hint': (it.get('from_addr','').split('@')[-1] if '@' in it.get('from_addr','') else ''),
            'category': cat,
            'probability_score': score,
            'subject': it.get('subject',''),
            'action': 'draft_offer_reply' if score >= 75 else 'watch',
        })

    # Add local contacts as proactive targets
    for c in contacts:
        org = c.get('org','')
        email_addr = (c.get('email','') or '').strip()
        email_addr_l = email_addr.lower()
        if not org and not email_addr:
            continue
        if not is_email_like(email_addr):
            continue
        if email_addr_l == self_email or email_addr_l in suppress:
            continue
        targets.append({
            'timestamp': now_iso(),
            'source_mailbox': 'local_contacts',
            'contact_name': org,
            'contact_email': email_addr,
            'org_hint': org,
            'category': 'outreach_automation_install',
            'probability_score': 68,
            'subject': 'Proactive revenue outreach target',
            'action': 'draft_offer_outbound',
        })

    # dedupe top targets by email+category
    seen = {}
    for t in targets:
        key = f"{t.get('contact_email','')}|{t.get('category','')}"
        prev = seen.get(key)
        if not prev or t['probability_score'] > prev['probability_score']:
            seen[key] = t
    final = sorted(seen.values(), key=lambda x: x['probability_score'], reverse=True)[:120]

    return {
        'updated_at': now_iso(),
        'mode': 'revenue_survival',
        'counts': {
            'consulting': sum(1 for x in final if x['category'] == 'consulting'),
            'grant_writing_for_others': sum(1 for x in final if x['category'] == 'grant_writing_for_others'),
            'outreach_automation_install': sum(1 for x in final if x['category'] == 'outreach_automation_install'),
            'ag_org_support_retainer': sum(1 for x in final if x['category'] == 'ag_org_support_retainer'),
            'local_business_automation': sum(1 for x in final if x['category'] == 'local_business_automation'),
        },
        'items': final,
    }


def build_outreach_messages() -> dict:
    base_offer = 'We set up automated grant pipelines + outreach systems for farms/orgs.'
    drafts = [
        {
            'segment': 'conservation_district',
            'subject': 'Practical support: grant pipeline + outreach system setup',
            'message': f"Hi [Name],\\n\\n{base_offer} We can stand up a district-friendly workflow quickly with clear handoff and low staff burden.\\n\\nIf useful, I can share a one-page setup plan and fixed-scope options.\\n\\nBest,\\nCasey",
        },
        {
            'segment': 'farm_coop',
            'subject': 'Offer: outreach automation + partner routing for co-ops',
            'message': f"Hi [Name],\\n\\n{base_offer} Focus is practical outcomes: faster follow-up, cleaner lead handling, and partner discovery support.\\n\\nHappy to send fixed-price options.\\n\\nBest,\\nCasey",
        },
        {
            'segment': 'ag_nonprofit',
            'subject': 'Offer: grant + outreach operations support',
            'message': f"Hi [Name],\\n\\n{base_offer} We help nonprofits reduce admin load while improving response speed and pipeline visibility.\\n\\nIf relevant, I can send implementation details today.\\n\\nBest,\\nCasey",
        },
        {
            'segment': 'extension_office',
            'subject': 'Offer: partner discovery + outreach workflow setup',
            'message': f"Hi [Name],\\n\\n{base_offer} This is outcome-focused support for extension and partner engagement cycles.\\n\\nIf useful, I can share a quick-scope install approach.\\n\\nBest,\\nCasey",
        },
    ]
    return {'updated_at': now_iso(), 'base_offer': base_offer, 'drafts': drafts}


def build_social_posts() -> dict:
    return {
        'updated_at': now_iso(),
        'posts': [
            {
                'platform': 'facebook',
                'status': 'ready_to_post',
                'text': 'Michigan farms/orgs: we set up automated grant pipelines + outreach systems. Practical installs, fixed scope, faster follow-through. DM for options.',
            },
            {
                'platform': 'x',
                'status': 'ready_to_post',
                'text': 'We set up automated grant pipelines + outreach systems for farms/orgs in Michigan. Direct, practical, outcome-focused. DM for setup options.',
            },
            {
                'platform': 'linkedin',
                'status': 'ready_to_post_if_available',
                'text': 'Offering practical service packages for Michigan ag/conservation organizations: grant pipeline setup, outreach automation installs, and partner network build.',
            },
        ],
    }


def build_service_packages() -> dict:
    return {
        'updated_at': now_iso(),
        'packages': [
            {'name': 'Grant Pipeline Setup', 'price_range': '$500-$1500', 'includes': ['workflow setup', 'field mapping', 'status tracking', 'handoff docs']},
            {'name': 'Outreach Automation Install', 'price_range': '$300-$800', 'includes': ['draft queue', 'follow-up cadence', 'classification routing']},
            {'name': 'Partner Network Build', 'price': '$250 flat', 'includes': ['target list build', 'contact enrichment', 'prioritization tags']},
        ],
    }


def apply_escalation_if_needed(targets_payload: dict) -> dict:
    state = read_json(OUT_ESCALATION, {'last_response_at': now_iso(), 'volume_multiplier': 1})
    if not isinstance(state, dict):
        state = {'last_response_at': now_iso(), 'volume_multiplier': 1}

    # if no high-probability actionable targets (proxy for no response) for 2 hours, escalate x3
    last_response_ts = datetime.fromisoformat(str(state.get('last_response_at', now_iso())).replace('Z', '+00:00'))
    no_response_hours = (now() - last_response_ts).total_seconds() / 3600.0
    actionable = sum(1 for x in targets_payload.get('items', []) if x.get('probability_score', 0) >= 80)

    if actionable == 0 and no_response_hours >= 2:
        state['volume_multiplier'] = 3
        state['escalation_status'] = 'escalated_x3'
        state['escalated_at'] = now_iso()
    else:
        state['volume_multiplier'] = max(1, int(state.get('volume_multiplier', 1)))
        state['escalation_status'] = 'normal'

    state['updated_at'] = now_iso()
    write_json(OUT_ESCALATION, state)
    return state


def main() -> int:
    load_env()
    append_heartbeat('objective=revenue_survival_cycle start=1')

    mail_items, source = scan_mailboxes_bounded(timeout_seconds=45)

    contacts = local_contacts()
    targets_payload = build_targets(mail_items, contacts)
    targets_payload['source'] = source
    write_json(OUT_TARGETS, targets_payload)

    write_json(OUT_DRAFTS, build_outreach_messages())
    write_json(OUT_SOCIAL, build_social_posts())
    write_json(OUT_PACKAGES, build_service_packages())

    escalation = apply_escalation_if_needed(targets_payload)

    write_json(
        OUT_MDARD,
        {
            'updated_at': now_iso(),
            'mode': 'revenue_survival_background_mdard',
            'paused': ['calhoun_county_outreach_until_callback'],
            'active': ['statewide_regenerative_partner_discovery', 'conservation_district_expansion', 'bison_grazing_and_nrcs_partner_mapping'],
        },
    )

    append_decision('revenue_survival_cycle_completed', f"source={source} targets={len(targets_payload.get('items', []))} escalation={escalation.get('escalation_status')}")
    append_heartbeat('objective=revenue_survival_cycle complete=1')

    print(
        json.dumps(
            {
                'ok': True,
                'revenue_targets': str(OUT_TARGETS),
                'outreach_drafts': str(OUT_DRAFTS),
                'social_posts': str(OUT_SOCIAL),
                'service_packages': str(OUT_PACKAGES),
                'escalation_state': str(OUT_ESCALATION),
            }
        )
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
