#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path('/home/asbelcas/cropcircuit')
RUNTIME = ROOT / 'runtime'
CLASSIFIED = RUNTIME / 'replies_classified.json'
FOLLOWUPS = RUNTIME / 'followup_schedule.json'
REFERRAL_CHAIN = RUNTIME / 'referral_chain.jsonl'

LIVE_OPPS = RUNTIME / 'live_opportunities.json'
APP_TASKS = RUNTIME / 'application_tasks.md'
PRIORITY_PARTNERS = RUNTIME / 'priority_partners.json'
OPERATOR_ACTION = RUNTIME / 'operator_action_required.md'
DAILY_BRIEF = RUNTIME / 'daily_funding_brief.md'

KEYWORDS_HUMAN = ['call', 'meeting', 'proposal', 'application']


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def parse_deadline(text: str) -> str:
    t = text.strip()
    patterns = [
        r'(\b\w+\s+\d{1,2},\s+\d{4}\b)',
        r'(\b\d{1,2}/\d{1,2}/\d{2,4}\b)',
        r'(\b\d{4}-\d{2}-\d{2}\b)',
    ]
    for p in patterns:
        m = re.search(p, t, re.I)
        if m:
            return m.group(1)
    if 'deadline' in t.lower() or 'due' in t.lower():
        return 'mentioned_no_exact_date'
    return ''


def infer_funding_type(text: str) -> str:
    s = text.lower()
    if 'rfp' in s:
        return 'RFP'
    if 'grant' in s:
        return 'grant'
    if 'application' in s:
        return 'application'
    if 'funding cycle' in s:
        return 'funding_cycle'
    return 'unspecified'


def extract_contact_name(item: dict) -> str:
    name = str(item.get('from_name', '')).strip()
    if name:
        return name
    addr = str(item.get('from_addr', '')).strip()
    if '@' in addr:
        return addr.split('@')[0].replace('.', ' ').title()
    return ''


def detect_live_opportunities(items: list[dict]) -> list[dict]:
    out = []
    for it in items:
        body = str(it.get('body', ''))
        subject = str(it.get('subject', ''))
        bucket = str(it.get('bucket', ''))
        text = f'{subject}\n{body}'

        is_warm_funding = bucket == 'warm' and any(k in text.lower() for k in ['grant', 'deadline', 'rfp', 'application', 'funding cycle'])
        if bucket != 'funding_signal' and not is_warm_funding:
            continue

        contact = extract_contact_name(it)
        from_addr = str(it.get('from_addr', '')).strip().lower()
        org = from_addr.split('@')[-1] if '@' in from_addr else 'unknown'
        org = org.replace('county.msu.edu', 'MSU Extension').replace('gmail.com', 'Gmail Contact')
        deadline = parse_deadline(text)
        funding_type = infer_funding_type(text)

        confidence = 85 if bucket == 'funding_signal' else 72
        if deadline:
            confidence += 8
        if 'application' in text.lower():
            confidence += 4
        confidence = max(1, min(100, confidence))

        if deadline and deadline != 'mentioned_no_exact_date':
            action_required = f'Prepare submission package before {deadline}'
        elif deadline == 'mentioned_no_exact_date':
            action_required = 'Reply requesting exact deadline and submission requirements'
        else:
            action_required = 'Request timeline, eligibility, and submission portal details'

        out.append(
            {
                'org': org,
                'contact': contact,
                'funding_type': funding_type,
                'deadline': deadline,
                'action_required': action_required,
                'confidence_score': confidence,
                'source_subject': subject,
                'source_email': from_addr,
                'detected_at': now_iso(),
            }
        )

    # dedupe by org+email+subject
    uniq = {}
    for x in out:
        k = f"{x['org']}|{x['source_email']}|{x['source_subject']}"
        uniq[k] = x
    return list(uniq.values())


def build_application_tasks(opps: list[dict]) -> str:
    lines = ['# Application Tasks', '', f'Generated: {now_iso()}', '']
    if not opps:
        lines.extend(['No live funding opportunities detected in this cycle.', ''])
        return '\n'.join(lines)

    for i, opp in enumerate(sorted(opps, key=lambda x: x['confidence_score'], reverse=True), start=1):
        lines.extend(
            [
                f'## Opportunity {i}: {opp["org"]} ({opp["funding_type"]})',
                f'- Contact: {opp["contact"]} <{opp["source_email"]}>',
                f'- Deadline: {opp["deadline"] or "not specified"}',
                f'- Action required: {opp["action_required"]}',
                '- Materials needed: project narrative, budget, timeline, impact metrics, org profile',
                '- Partners required: conservation district / extension / implementation partner as applicable',
                '- Forms: eligibility form, narrative form, budget worksheet, attestation',
                '- Submission path: ask contact for exact portal; confirm account + file format limits',
                '- Contact followup plan: day 0 acknowledge, day 1 requirements confirmation, day 2 draft package review',
                '',
            ]
        )
    return '\n'.join(lines)


def build_priority_partners() -> list[dict]:
    counts_org = Counter()
    counts_email = Counter()
    latest_by_email = {}

    if REFERRAL_CHAIN.exists():
        for line in REFERRAL_CHAIN.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            org = str(row.get('org', '')).strip()
            email_addr = str(row.get('email', '')).strip().lower()
            if org:
                counts_org[org] += 1
            if email_addr:
                counts_email[email_addr] += 1
                latest_by_email[email_addr] = row

    partners = []
    for email_addr, n in counts_email.items():
        row = latest_by_email.get(email_addr, {})
        org = str(row.get('org', '')).strip() or 'unknown'
        contact = str(row.get('contact_name', '')).strip() or email_addr.split('@')[0].title()
        score = min(100, 60 + (n * 15) + (counts_org.get(org, 0) * 5))
        partners.append(
            {
                'org': org,
                'contact': contact,
                'email': email_addr,
                'role': str(row.get('role', '')).strip(),
                'referrals_count': n,
                'org_chain_count': counts_org.get(org, 0),
                'priority_score': score,
                'routing': ['faster_replies', 'personalized_followups', 'call_scheduling_prompt'],
                'updated_at': now_iso(),
            }
        )

    partners.sort(key=lambda x: x['priority_score'], reverse=True)
    return partners


def build_operator_actions(items: list[dict]) -> list[dict]:
    acts = []
    for it in items:
        subject = str(it.get('subject', ''))
        body = str(it.get('body', ''))
        text = f'{subject}\n{body}'.lower()
        if not any(k in text for k in KEYWORDS_HUMAN):
            continue
        acts.append(
            {
                'from': str(it.get('from_addr', '')),
                'contact': extract_contact_name(it),
                'subject': subject,
                'trigger_terms': [k for k in KEYWORDS_HUMAN if k in text],
                'recommended_action': 'Human follow-up within 24h: propose two call windows + clarify next deliverable',
            }
        )
    return acts


def format_operator_actions(actions: list[dict]) -> str:
    lines = ['# Operator Action Required', '', f'Generated: {now_iso()}', '']
    if not actions:
        lines.extend(['No operator escalation terms detected this cycle.', ''])
        return '\n'.join(lines)
    for i, a in enumerate(actions, start=1):
        lines.extend(
            [
                f'## {i}. {a["contact"]} <{a["from"]}>',
                f'- Subject: {a["subject"]}',
                f'- Trigger terms: {", ".join(a["trigger_terms"])}',
                f'- Action: {a["recommended_action"]}',
                '',
            ]
        )
    return '\n'.join(lines)


def parse_deadline_days(opps: list[dict]) -> list[dict]:
    soon = []
    for o in opps:
        d = str(o.get('deadline', '')).strip()
        if not d or d == 'mentioned_no_exact_date':
            continue
        parsed = None
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%B %d, %Y', '%b %d, %Y']:
            try:
                parsed = datetime.strptime(d, fmt).replace(tzinfo=timezone.utc)
                break
            except Exception:
                continue
        if not parsed:
            continue
        days = (parsed - datetime.now(timezone.utc)).days
        if days <= 7:
            soon.append({'org': o.get('org', ''), 'deadline': d, 'days_left': days})
    return soon


def build_daily_brief(opps: list[dict], warm_count: int, followup_count: int, operator_actions: list[dict]) -> str:
    deadlines = parse_deadline_days(opps)
    lines = [
        '# Daily Funding Brief',
        '',
        f'Generated: {now_iso()}',
        '',
        f'- New opportunities detected: {len(opps)}',
        f'- Warm leads status: {warm_count} warm threads',
        f'- Followups scheduled: {followup_count}',
        f'- Operator actions needed: {len(operator_actions)}',
        '',
        '## Deadlines Approaching',
    ]
    if deadlines:
        for d in deadlines:
            lines.append(f"- {d['org']}: {d['deadline']} ({d['days_left']} days)")
    else:
        lines.append('- No hard deadlines parsed within 7 days.')
    lines.append('')
    lines.append('## Top Opportunity Actions')
    for o in sorted(opps, key=lambda x: x['confidence_score'], reverse=True)[:5]:
        lines.append(f"- {o['org']} ({o['funding_type']}): {o['action_required']}")
    if not opps:
        lines.append('- No opportunities detected this cycle.')
    lines.append('')
    return '\n'.join(lines)


def main() -> int:
    classified = read_json(CLASSIFIED, {'items': [], 'counts': {}})
    items = classified.get('items', []) if isinstance(classified, dict) else []
    counts = classified.get('counts', {}) if isinstance(classified, dict) else {}

    opps = detect_live_opportunities(items)
    write_json(LIVE_OPPS, {'updated_at': now_iso(), 'count': len(opps), 'items': opps})

    APP_TASKS.write_text(build_application_tasks(opps), encoding='utf-8')

    partners = build_priority_partners()
    write_json(PRIORITY_PARTNERS, {'updated_at': now_iso(), 'count': len(partners), 'items': partners})

    operator_actions = build_operator_actions(items)
    OPERATOR_ACTION.write_text(format_operator_actions(operator_actions), encoding='utf-8')

    follow = read_json(FOLLOWUPS, {'count': 0})
    follow_count = int(follow.get('count', 0)) if isinstance(follow, dict) else 0
    warm_count = int(counts.get('warm', 0)) if isinstance(counts, dict) else 0
    DAILY_BRIEF.write_text(build_daily_brief(opps, warm_count, follow_count, operator_actions), encoding='utf-8')

    print(
        json.dumps(
            {
                'ok': True,
                'live_opportunities': str(LIVE_OPPS),
                'application_tasks': str(APP_TASKS),
                'priority_partners': str(PRIORITY_PARTNERS),
                'operator_action_required': str(OPERATOR_ACTION),
                'daily_funding_brief': str(DAILY_BRIEF),
                'opportunities_count': len(opps),
                'operator_actions_count': len(operator_actions),
            }
        )
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
