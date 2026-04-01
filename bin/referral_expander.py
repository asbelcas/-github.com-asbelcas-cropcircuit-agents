#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/asbelcas/cropcircuit')
RUNTIME = ROOT / 'runtime'
CLASSIFIED = RUNTIME / 'replies_classified.json'
MAP = RUNTIME / 'mdard_contact_map.csv'
CHAIN = RUNTIME / 'referral_chain.jsonl'
STATE = RUNTIME / 'referral_expander_state.json'

sys.path.insert(0, str(ROOT / 'bin'))
from send_grant_email import send_custom_email  # noqa: E402


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_referral(item: dict) -> dict | None:
    body = str(item.get('body', ''))
    source = str(item.get('from_addr', ''))
    m = re.search(r'([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})', body, re.I)
    if not m:
        return None
    email_addr = m.group(1).lower()
    name = ''
    nm = re.search(r'(?:contact|reach out to|try)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})', body, re.I)
    if nm:
        name = nm.group(1).strip()
    role = ''
    rm = re.search(r'(director|manager|coordinator|educator|specialist|agent|officer|lead)', body, re.I)
    if rm:
        role = rm.group(1).title()
    org = email_addr.split('@')[-1].split('.')[0].replace('-', ' ').title()
    return {'org': org, 'role': role, 'email': email_addr, 'contact_name': name, 'referred_by': source}


def upsert_map(refs: list[dict]) -> int:
    rows = []
    if MAP.exists():
        with open(MAP, 'r', encoding='utf-8', newline='') as fh:
            rows = list(csv.DictReader(fh))
    fields = list(rows[0].keys()) if rows else ['org','program','contact_name','email','phone','source_url','confidence','notes','last_attempt_ts','next_action']
    seen = {(r.get('email') or '').lower() for r in rows}
    added = 0
    for r in refs:
        if r['email'] in seen:
            continue
        rows.append({'org': r['org'], 'program': 'MDARD/MNARD partner outreach', 'contact_name': r['contact_name'], 'email': r['email'], 'phone': '', 'source_url': '', 'confidence': 'high', 'notes': f"Referral from {r['referred_by']} role={r['role'] or 'unknown'}", 'last_attempt_ts': '', 'next_action': 'priority_outreach_today'})
        seen.add(r['email'])
        added += 1
    if added:
        with open(MAP, 'w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    return added


def append_chain(refs: list[dict]) -> None:
    if not refs:
        return
    with CHAIN.open('a', encoding='utf-8') as fh:
        for r in refs:
            fh.write(json.dumps({'timestamp': now_iso(), **r}) + '\n')


def main() -> int:
    if not CLASSIFIED.exists():
        print(json.dumps({'ok': True, 'referrals': 0, 'added': 0, 'intro_sent': 0}))
        return 0
    data = json.loads(CLASSIFIED.read_text(encoding='utf-8'))
    items = data.get('items', [])
    refs = []
    for it in items:
        if it.get('bucket') != 'referral':
            continue
        r = parse_referral(it)
        if r:
            refs.append(r)

    uniq = {}
    for r in refs:
        uniq[r['email']] = r
    refs = list(uniq.values())

    added = upsert_map(refs)
    append_chain(refs)

    state = {'sent_intro': []}
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding='utf-8'))
        except Exception:
            state = {'sent_intro': []}
    sent_set = set(state.get('sent_intro', []))

    intro_sent = 0
    send_execute = os.environ.get('EXECUTE_SEND', '0').strip() == '1'
    if send_execute and os.environ.get('GMAIL_APP_PASSWORD', '').strip():
        for r in refs:
            if r['email'] in sent_set:
                continue
            subj = 'Intro — referred contact (CropCircuit)'
            body = (
                f"Hi {r.get('contact_name') or 'there'},\\n\\n"
                f"I was referred to you by {r.get('referred_by', 'a colleague')} for this outreach. "
                'I run CropCircuit and wanted to introduce myself for regenerative-ag collaboration.\\n\\nBest,\\nCasey'
            )
            ok = send_custom_email(r['email'], subj, body, tag=f"referral:{r['email']}")
            if ok:
                intro_sent += 1
                sent_set.add(r['email'])
    else:
        # Draft-only mode: no auto-send unless explicit execute flag.
        pass

    STATE.write_text(json.dumps({'sent_intro': sorted(sent_set), 'updated_at': now_iso()}, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'referrals': len(refs), 'added': added, 'intro_sent': intro_sent, 'draft_only': (not send_execute)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
