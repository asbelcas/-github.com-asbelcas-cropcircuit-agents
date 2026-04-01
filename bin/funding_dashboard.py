#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/asbelcas/cropcircuit')
RUNTIME = ROOT / 'runtime'
CLASSIFIED = RUNTIME / 'replies_classified.json'
FOLLOW = RUNTIME / 'followup_schedule.json'
CHAIN = RUNTIME / 'referral_chain.jsonl'
OUT = RUNTIME / 'funding_probability.json'


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    items = []
    if CLASSIFIED.exists():
        try:
            items = json.loads(CLASSIFIED.read_text(encoding='utf-8')).get('items', [])
        except Exception:
            items = []
    warm = sum(1 for x in items if x.get('bucket') == 'warm')
    grants = sum(1 for x in items if x.get('bucket') == 'funding_signal')
    threads = len({(x.get('from_addr') or '').lower() for x in items if isinstance(x, dict)})

    chain_count = 0
    if CHAIN.exists():
        try:
            chain_count = sum(1 for _ in CHAIN.open('r', encoding='utf-8'))
        except Exception:
            chain_count = 0

    follow_count = 0
    if FOLLOW.exists():
        try:
            follow_count = int(json.loads(FOLLOW.read_text(encoding='utf-8')).get('count', 0))
        except Exception:
            follow_count = 0

    score = min(100, int((warm * 15) + (grants * 20) + (threads * 2) + (chain_count * 5) - (follow_count // 3)))
    payload = {
        'timestamp': now_iso(),
        'warm_leads_count': warm,
        'active_threads': threads,
        'referral_chains': chain_count,
        'grants_detected': grants,
        'est_probability_score': max(0, score),
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'stored': str(OUT), 'score': payload['est_probability_score']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
