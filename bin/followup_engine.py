#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/asbelcas/cropcircuit')
RUNTIME = ROOT / 'runtime'
ACTIONS = RUNTIME / 'email_actions.csv'
CLASSIFIED = RUNTIME / 'replies_classified.json'
TEMPLATES = RUNTIME / 'followup_templates.md'
OUT = RUNTIME / 'followup_schedule.json'
FOCUS = RUNTIME / 'priority_partner_focus.json'

MARKETING_BLOCKLIST = [
    'rubylane.com',
    'join-eby.com',
    'naturallife.com',
    'thredup.com',
    'silpada.com',
    'marketing@',
    'newsletter@',
    'no-reply@',
    'noreply@',
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_ts(ts: str):
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except Exception:
        return None


def ensure_templates() -> None:
    if TEMPLATES.exists():
        return
    TEMPLATES.write_text(
        '# Followup Templates\n\n'
        '## 3-day\nGentle nudge\n\n'
        '## 7-day\nDifferent angle\n\n'
        '## 14-day\nClosing loop\n',
        encoding='utf-8',
    )


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return fallback


def normalize_elevate_patterns(values: list[str]) -> list[str]:
    patterns = []
    for v in values:
        s = str(v).strip().lower()
        if not s:
            continue
        patterns.append(s)
        if s == 'calhoun_conservation_district':
            patterns.extend(['calhouncd', 'calhoun conservation district'])
        if s == 'msu':
            patterns.extend(['msu', 'msu.edu', 'county.msu.edu'])
        if s == 'mdard':
            patterns.extend(['mdard', 'michigan.gov/mdard'])
    # dedupe preserve order
    out = []
    for p in patterns:
        if p not in out:
            out.append(p)
    return out


def is_marketing_email(addr: str) -> bool:
    a = addr.lower()
    return any(tok in a for tok in MARKETING_BLOCKLIST)


def match_high_priority(addr: str, elevated_patterns: list[str]) -> bool:
    a = addr.lower()
    return any(p in a for p in elevated_patterns)


def main() -> int:
    ap = argparse.ArgumentParser(description='Generate outreach followup schedule')
    ap.add_argument('--high-priority-only', action='store_true', help='Only schedule followups for elevated priority partners')
    args = ap.parse_args()

    ensure_templates()
    focus = read_json(FOCUS, {})
    elevate = normalize_elevate_patterns(focus.get('elevate', [])) if isinstance(focus, dict) else []
    deprioritize = [str(x).strip().lower() for x in (focus.get('deprioritize', []) if isinstance(focus, dict) else [])]
    deprioritize_marketing = 'marketing_emails' in deprioritize

    replies = []
    if CLASSIFIED.exists():
        try:
            replies = json.loads(CLASSIFIED.read_text(encoding='utf-8')).get('items', [])
        except Exception:
            replies = []
    replied = {(r.get('from_addr') or '').lower() for r in replies if isinstance(r, dict)}

    rows = []
    if ACTIONS.exists():
        with open(ACTIONS, 'r', encoding='utf-8', newline='') as fh:
            rows = list(csv.DictReader(fh))

    last_sent = {}
    for r in rows:
        to_addr = (r.get('to') or '').strip().lower()
        status = (r.get('status') or '').strip().lower()
        if not to_addr or status not in {'sent', 'queued', 'draft'}:
            continue
        ts = parse_ts((r.get('timestamp') or '').strip())
        if not ts:
            continue
        prev = last_sent.get(to_addr)
        if not prev or ts > prev:
            last_sent[to_addr] = ts

    now = datetime.now(timezone.utc)
    schedule = []
    for to_addr, ts in last_sent.items():
        if to_addr in replied:
            continue
        if deprioritize_marketing and is_marketing_email(to_addr):
            continue
        if args.high_priority_only and not match_high_priority(to_addr, elevate):
            continue
        days = (now - ts).days
        stage = ''
        if days >= 14:
            stage = '14_day_closing_loop'
        elif days >= 7:
            stage = '7_day_different_angle'
        elif days >= 3:
            stage = '3_day_gentle_nudge'
        if not stage:
            continue
        schedule.append({'to': to_addr, 'last_sent': ts.isoformat(), 'days_since': days, 'stage': stage, 'status': 'scheduled'})

    OUT.write_text(
        json.dumps(
            {
                'updated_at': now_iso(),
                'high_priority_only': args.high_priority_only,
                'count': len(schedule),
                'items': schedule,
            },
            indent=2,
        ),
        encoding='utf-8',
    )
    print(json.dumps({'ok': True, 'high_priority_only': args.high_priority_only, 'scheduled': len(schedule), 'stored': str(OUT)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
