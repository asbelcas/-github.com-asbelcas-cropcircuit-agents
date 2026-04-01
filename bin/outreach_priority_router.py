#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('/home/asbelcas/cropcircuit')
RUNTIME = ROOT / 'runtime'
IN_CANDIDATES = [
    RUNTIME / 'mdard_contact_map.json',
    RUNTIME / 'partner_targets.json',
    RUNTIME / 'high_priority_queue.json',
]
OUT_QUEUE = RUNTIME / 'outreach_priority_queue.json'

TIER1_EMAILS = {
    'calhouncd@gmail.com',
}
TIER1_NAMES = {
    'bret green',
    'lizzie erwin',
    'michigan usda rd business program specialist',
    'kellogg foundation program officer',
    'calhoun county conservation district',
}


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for p in IN_CANDIDATES:
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        if isinstance(data, list):
            rows.extend([x for x in data if isinstance(x, dict)])
        elif isinstance(data, dict):
            for key in ('contacts', 'partners', 'targets', 'items'):
                if isinstance(data.get(key), list):
                    rows.extend([x for x in data[key] if isinstance(x, dict)])
    return rows


def tier_for(row: dict) -> tuple[int, str]:
    email = str(row.get('email') or row.get('to') or '').strip().lower()
    name = str(row.get('name') or row.get('contact_name') or row.get('org') or '').strip().lower()
    if email in TIER1_EMAILS or any(k in name for k in TIER1_NAMES):
        return 1, 'network_node'
    segment = str(row.get('segment') or row.get('tier') or '').lower()
    if any(k in segment for k in ('farmer', 'restaurant', 'market', 'supporting')):
        return 2, 'supporting_relationship'
    return 3, 'volume_outreach'


def main() -> None:
    rows = load_rows()
    queue = []
    for row in rows:
        tier, reason = tier_for(row)
        queue.append(
            {
                'name': row.get('name') or row.get('contact_name') or row.get('org_name') or row.get('org') or 'unknown',
                'email': row.get('email') or row.get('to') or '',
                'tier': tier,
                'tier_reason': reason,
                'human_review_required': tier == 1,
                'safe_autosend_allowed': False if tier == 1 else bool(row.get('SAFE_AUTOSEND', False)),
                'source': str(row.get('source') or 'merged_runtime_sources'),
            }
        )

    queue.sort(key=lambda x: (x['tier'], x['name']))
    payload = {
        'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'tier_order': ['TIER_1', 'TIER_2', 'TIER_3'],
        'count': len(queue),
        'queue': queue,
    }
    OUT_QUEUE.write_text(json.dumps(payload, indent=2))
    print(json.dumps({'ok': True, 'queue': str(OUT_QUEUE), 'count': len(queue)}))


if __name__ == '__main__':
    main()
