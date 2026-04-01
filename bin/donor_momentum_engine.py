#!/usr/bin/env python3
"""Auto-update donor proof ledger, build feed, and social proof assets."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
CONVERSION_LOG = ROOT / "logs" / "donor_conversion.log"
PROOF_LEDGER = ROOT / "runtime" / "proof_ledger.json"
BUILD_FEED = ROOT / "runtime" / "build_feed.json"
SOCIAL_QUEUE = ROOT / "runtime" / "social_share_queue.jsonl"
MILESTONE_PROGRESS = ROOT / "runtime" / "milestone_progress.json"
MOMENTUM_STATE = ROOT / "runtime" / "momentum_state.json"
DAILY_SUMMARY = ROOT / "runtime" / "daily_fund_summary.md"

MILESTONES = [
    (500, "soil testing"),
    (1200, "fencing"),
    (2500, "irrigation prep"),
    (5000, "livestock infrastructure"),
]

KV_RE = re.compile(r"([a-zA-Z_]+)=([^ ]*)")
AMOUNT_RE = re.compile(r"[^0-9.]")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_line(line: str) -> dict:
    out: dict[str, str] = {}
    parts = line.strip().split(" ", 1)
    out["timestamp"] = parts[0] if parts else ""
    blob = parts[1] if len(parts) > 1 else ""
    for k, v in KV_RE.findall(blob):
        out[k] = v
    return out


def parse_amount(raw: str) -> float:
    cleaned = AMOUNT_RE.sub("", raw or "")
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except Exception:
        return 0.0


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def milestone_state(funds: float) -> tuple[str, float, float, str, float]:
    achieved_name = "none"
    achieved_target = 0.0
    next_name = MILESTONES[0][1]
    next_target = float(MILESTONES[0][0])
    for target, name in MILESTONES:
        if funds >= target:
            achieved_name = name
            achieved_target = float(target)
        else:
            next_name = name
            next_target = float(target)
            break
    if funds >= MILESTONES[-1][0]:
        next_name = "expand operations"
        next_target = float(MILESTONES[-1][0]) + 2500.0
    gap = max(0.0, next_target - funds)
    return achieved_name, achieved_target, gap, next_name, next_target


def main() -> int:
    state = load_json(MOMENTUM_STATE, {"processed_keys": []})
    processed_keys = set(state.get("processed_keys", []))
    build_payload = load_json(BUILD_FEED, {"entries": []})
    build_entries = build_payload.get("entries", [])
    if not isinstance(build_entries, list):
        build_entries = []

    accepted_events: list[dict] = []
    if CONVERSION_LOG.exists():
        for line in CONVERSION_LOG.read_text(encoding="utf-8").splitlines():
            rec = parse_line(line)
            if rec.get("event") == "lead_accepted":
                accepted_events.append(rec)

    donors_set: set[str] = set()
    funds = 0.0
    ledger_entries: list[dict] = []
    new_events = 0
    for rec in accepted_events:
        ts = rec.get("timestamp", "")
        email = rec.get("email", "")
        amount_raw = rec.get("amount", "")
        amount = parse_amount(amount_raw)
        if email:
            donors_set.add(email.lower())
        funds += amount
        key = f"{ts}|{email}|{amount_raw}"
        action = "farm build momentum"
        if amount >= 500:
            action = "founding-contributor infrastructure push"
        elif amount >= 100:
            action = "infrastructure readiness"
        elif amount >= 25:
            action = "soil and planning momentum"
        elif amount > 0:
            action = "seed-support continuity"
        ledger_entries.append(
            {
                "timestamp": ts,
                "funds_received": f"{amount:.0f}" if amount.is_integer() else f"{amount:.2f}",
                "build_action_funded": action,
                "status": "logged",
            }
        )
        if key in processed_keys:
            continue
        processed_keys.add(key)
        new_events += 1
        build_entries.insert(
            0,
            {
                "category": "infrastructure",
                "note": f"new donor committed ${amount:.0f} ({email})",
                "status": "updated",
                "timestamp": ts,
            },
        )
        SOCIAL_QUEUE.parent.mkdir(parents=True, exist_ok=True)
        with SOCIAL_QUEUE.open("a", encoding="utf-8") as qf:
            qf.write(
                json.dumps(
                    {
                        "timestamp": ts,
                        "type": "new_donor_social_proof",
                        "email": email,
                        "amount": amount,
                        "copy": f"${amount:.0f} just committed to building a regenerative farm in Michigan.",
                    },
                    ensure_ascii=True,
                )
                + "\n"
            )

    build_payload["entries"] = build_entries[:80]
    write_json(BUILD_FEED, build_payload)

    achieved_name, achieved_target, gap, next_name, next_target_amount = milestone_state(funds)
    proof_payload = {
        "summary": {
            "updated_at": now_iso(),
            "donors_count": len(donors_set),
            "funds_total": round(funds, 2),
            "last_funded_action": achieved_name if achieved_name != "none" else "seed funding in motion",
        },
        "entries": ledger_entries[-80:],
    }
    write_json(PROOF_LEDGER, proof_payload)

    progress = {
        "updated_at": now_iso(),
        "funds_total": round(funds, 2),
        "donors_count": len(donors_set),
        "milestones": [{"target": t, "action": a, "reached": funds >= t} for t, a in MILESTONES],
        "last_funded_action": achieved_name if achieved_name != "none" else "seed funding in motion",
        "next_target": next_name,
        "next_target_amount": next_target_amount,
        "next_gap": round(gap, 2),
        "achieved_target_amount": achieved_target,
    }
    write_json(MILESTONE_PROGRESS, progress)

    state["processed_keys"] = list(processed_keys)[-5000:]
    state["updated_at"] = now_iso()
    state["new_events_last_run"] = new_events
    write_json(MOMENTUM_STATE, state)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    donors_today = 0
    funds_today = 0.0
    for rec in accepted_events:
        if rec.get("timestamp", "").startswith(today):
            donors_today += 1
            funds_today += parse_amount(rec.get("amount", ""))
    summary = (
        f"# Daily Funding Summary ({today})\n\n"
        f"- donors today: {donors_today}\n"
        f"- funds today: ${funds_today:.2f}\n"
        f"- donors total: {len(donors_set)}\n"
        f"- funds total: ${funds:.2f}\n"
        f"- milestone progress: {achieved_name if achieved_name != 'none' else 'seed funding in motion'}\n"
        f"- next gap: ${gap:.2f} to {next_name}\n"
    )
    DAILY_SUMMARY.write_text(summary, encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "donors_total": len(donors_set),
                "funds_total": round(funds, 2),
                "new_events": new_events,
                "next_gap": round(gap, 2),
                "next_target": next_name,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
