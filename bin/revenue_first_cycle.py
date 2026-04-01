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

OUT_REVENUE = RUNTIME / 'revenue_targets.json'
OUT_OFFERS = RUNTIME / 'revenue_outbound_offers.json'
OUT_MDARD = RUNTIME / 'mdard_execution_state.json'
OUT_CUSTOMERS = RUNTIME / 'paying_customer_prospects.json'


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


def classify_revenue(subject: str, body: str, from_addr: str) -> str:
    t = (subject + '\n' + body).lower()
    a = from_addr.lower()
    if any(k in t for k in ['consulting', 'advisor', 'help us set up', 'proposal']):
        return 'consulting_inquiry'
    if any(k in t for k in ['partnership', 'collaborate', 'sponsor', 'co-op']):
        return 'partnership_offer'
    if any(k in t for k in ['speaking', 'webinar', 'panel', 'present']):
        return 'speaking_request'
    if any(k in t for k in ['grant collaboration', 'letter of support', 'application support', 'rfp']):
        return 'grant_collaboration'
    if any(k in a for k in ['conservation', 'msu.edu', 'nrcs', 'farmbureau']) or any(k in t for k in ['district', 'extension', 'regenerative']):
        return 'local_ag_org_communication'
    return 'other'


def fetch_revenue_candidates() -> list[dict]:
    user = os.environ.get('IMAP_USER', 'asbelcas@gmail.com')
    pwd = os.environ.get('IMAP_APP_PASSWORD', os.environ.get('GMAIL_APP_PASSWORD', '')).strip()
    host = os.environ.get('IMAP_HOST', 'imap.gmail.com')
    port = int(os.environ.get('IMAP_PORT', '993'))
    if not pwd:
        return []

    out = []
    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(user, pwd)
    conn.select('INBOX', readonly=True)
    since = (datetime.now() - timedelta(days=10)).strftime('%d-%b-%Y')
    typ, data = conn.search(None, f'(SINCE {since})')
    ids = data[0].split() if typ == 'OK' and data and data[0] else []

    for uid in ids[-180:]:
        try:
            typ, msg_data = conn.fetch(uid, '(RFC822)')
            if typ != 'OK' or not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject = str(msg.get('Subject', ''))
            from_name, from_addr = email.utils.parseaddr(msg.get('From', ''))
            body = extract_text(msg)[:6000]
            cls = classify_revenue(subject, body, from_addr)
            if cls == 'other':
                continue
            out.append({
                'timestamp': now_iso(),
                'uid': uid.decode() if isinstance(uid, bytes) else str(uid),
                'from_name': from_name,
                'from_addr': from_addr,
                'subject': subject,
                'category': cls,
                'snippet': body[:500],
            })
        except Exception:
            continue
    conn.logout()
    return out


def build_outbound_offers() -> dict:
    offer_structure = {
        'services': [
            'Grant pipeline automation setup',
            'Outreach automation',
            'Partner discovery service',
        ],
        'message': (
            'We help Michigan ag and conservation organizations deploy practical funding operations: '
            'faster partner routing, cleaner outreach execution, and repeatable grant pipeline workflows.'
        ),
    }

    drafts = [
        {
            'segment': 'conservation_districts',
            'subject': 'Offer: practical grant pipeline support for district-aligned projects',
            'body': 'Hi [Name],\\n\\nI run CropCircuit in Michigan. I help teams stand up lightweight grant + outreach operations that reduce admin drag and improve partner follow-through.\\n\\nIf useful, I can share a district-friendly setup for grant pipeline automation, outreach automation, and partner discovery support.\\n\\nBest,\\nCasey',
        },
        {
            'segment': 'farm_coops',
            'subject': 'Offer: partner discovery + outreach automation for cooperative growth',
            'body': 'Hi [Name],\\n\\nI support Michigan ag teams with practical outreach automation and partner discovery so funding and collaboration opportunities move faster.\\n\\nIf you want, I can send a concise setup outline for co-op use.\\n\\nBest,\\nCasey',
        },
        {
            'segment': 'ag_nonprofits',
            'subject': 'Offer: grant workflow support for regenerative program delivery',
            'body': 'Hi [Name],\\n\\nI help regenerative agriculture organizations operationalize grant outreach and partner coordination without heavy tooling.\\n\\nHappy to share a 1-page implementation option if relevant.\\n\\nBest,\\nCasey',
        },
        {
            'segment': 'extension_offices',
            'subject': 'Offer: field-ready outreach + partner coordination support',
            'body': 'Hi [Name],\\n\\nI support Michigan ag initiatives with practical partner discovery and outreach systems that improve response quality and speed.\\n\\nIf helpful, I can share a draft workflow adapted for Extension collaboration contexts.\\n\\nBest,\\nCasey',
        },
    ]
    return {'updated_at': now_iso(), 'offer_structure': offer_structure, 'drafts': drafts}


def build_customer_prospects() -> dict:
    return {
        'updated_at': now_iso(),
        'focus': ['Michigan ag', 'conservation districts', 'regenerative organizations'],
        'prospects': [
            {'name': 'Calhoun Conservation District', 'segment': 'conservation_district', 'status': 'warm', 'revenue_fit': 'high'},
            {'name': 'MSU Extension contacts', 'segment': 'extension', 'status': 'active_thread', 'revenue_fit': 'medium'},
            {'name': 'Michigan Farm Bureau local units', 'segment': 'farm_coop_org', 'status': 'prospect', 'revenue_fit': 'medium'},
            {'name': 'Regional regenerative nonprofits', 'segment': 'ag_nonprofit', 'status': 'prospect', 'revenue_fit': 'high'},
        ],
    }


def main() -> int:
    load_env()
    RUNTIME.mkdir(parents=True, exist_ok=True)

    try:
        items = fetch_revenue_candidates()
        source = 'imap'
    except Exception:
        # fallback to existing classified queue if IMAP unavailable
        c = read_json(RUNTIME / 'replies_classified.json', {'items': []})
        items = []
        for it in c.get('items', []):
            cat = classify_revenue(str(it.get('subject','')), str(it.get('body','')), str(it.get('from_addr','')))
            if cat == 'other':
                continue
            items.append({
                'timestamp': now_iso(),
                'uid': str(it.get('uid','')),
                'from_name': str(it.get('from_name','')),
                'from_addr': str(it.get('from_addr','')),
                'subject': str(it.get('subject','')),
                'category': cat,
                'snippet': str(it.get('body',''))[:500],
            })
        source = 'fallback_classified'

    revenue = {
        'updated_at': now_iso(),
        'source': source,
        'counts': {
            'consulting_inquiry': sum(1 for x in items if x['category'] == 'consulting_inquiry'),
            'partnership_offer': sum(1 for x in items if x['category'] == 'partnership_offer'),
            'speaking_request': sum(1 for x in items if x['category'] == 'speaking_request'),
            'grant_collaboration': sum(1 for x in items if x['category'] == 'grant_collaboration'),
            'local_ag_org_communication': sum(1 for x in items if x['category'] == 'local_ag_org_communication'),
        },
        'items': items,
    }
    write_json(OUT_REVENUE, revenue)
    write_json(OUT_OFFERS, build_outbound_offers())
    write_json(OUT_CUSTOMERS, build_customer_prospects())

    mdard_state = {
        'updated_at': now_iso(),
        'mode': 'revenue_first_background_mdard',
        'paused': ['calhoun_conservation_district_until_callback'],
        'active': ['statewide_partner_discovery', 'nrcs_partner_mapping', 'bison_grazing_partner_expansion'],
    }
    write_json(OUT_MDARD, mdard_state)

    print(json.dumps({'ok': True, 'revenue_targets': str(OUT_REVENUE), 'outbound_offers': str(OUT_OFFERS), 'mdard_state': str(OUT_MDARD)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
