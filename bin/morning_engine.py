#!/usr/bin/env python3
"""Daily momentum engine (no API, no posting)."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from credibility_builder import build_daily_credibility_pack


ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"

OPS_SHEET = RUNTIME / "top50_ops_sheet.csv"
CALENDAR = RUNTIME / "momentum_calendar_14d.md"
STATE_FILE = RUNTIME / "momentum_state.json"
FOLLOW_TARGETS_JSON = RUNTIME / "follow_targets_agriculture.json"
FOLLOW_TARGETS_CSV = RUNTIME / "follow_targets_agriculture.csv"
PARTNERS_CONTACTS = ROOT / "partners_contacts.csv"
OUTREACH_LOG = ROOT / "outreach_log.csv"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().replace(microsecond=0).isoformat()


def load_json(path: Path, fallback: Any):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []


def read_ops_sheet() -> list[dict[str, str]]:
    return load_csv(OPS_SHEET)


def extract_todays_calendar_block(calendar_text: str, today_ymd: str) -> str:
    marker = f"## Day "
    lines = calendar_text.splitlines()
    start_idx = -1
    end_idx = len(lines)
    for i, line in enumerate(lines):
        if line.startswith(marker) and line.rstrip().endswith(today_ymd):
            start_idx = i
            break
    if start_idx == -1:
        return ""
    for j in range(start_idx + 1, len(lines)):
        if lines[j].startswith(marker):
            end_idx = j
            break
    return "\n".join(lines[start_idx:end_idx]).strip()


def choose_today_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    # Keep execution short: cap to 12 actions/day.
    wave_a = [r for r in rows if (r.get("follow_timing") or "").strip() == "T+0h to T+6h"]
    wave_b = [r for r in rows if (r.get("follow_timing") or "").strip() == "T+6h to T+24h"]
    wave_c = [r for r in rows if (r.get("follow_timing") or "").strip() == "T+24h to T+48h"]
    selected = wave_a[:4] + wave_b[:6] + wave_c[:2]
    if not selected:
        selected = rows[:12]
    return selected[:12]


def infer_segment(org: str) -> str:
    o = org.lower()
    if "usda" in o:
        return "usda"
    if "extension" in o:
        return "extension"
    if "conservation district" in o:
        return "conservation"
    if "farm" in o or "ranch" in o:
        return "grant_partner"
    return "michigan_org"


def priority_for_segment(segment: str) -> int:
    if segment in {"usda", "extension", "conservation"}:
        return 1
    return 2


def relevance_for_segment(segment: str, priority: int) -> int:
    base = 100 - (priority * 10)
    bonus = {
        "usda": 8,
        "extension": 8,
        "conservation": 8,
        "grant_partner": 7,
        "michigan_org": 6,
    }.get(segment, 5)
    return max(1, min(100, base + bonus + 2))


def discover_passive_targets(existing_targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_org = {
        str(t.get("org_name") or "").strip().lower()
        for t in existing_targets
        if str(t.get("org_name") or "").strip()
    }
    candidates: list[dict[str, str]] = []

    for row in load_csv(PARTNERS_CONTACTS):
        org = (row.get("Org_Name") or "").strip()
        website = (row.get("Website") or "").strip()
        if not org:
            continue
        candidates.append({"org_name": org, "website": website, "source": "partners_contacts.csv"})

    for row in load_csv(OUTREACH_LOG):
        org = (row.get("Org_Name") or "").strip()
        if not org:
            continue
        candidates.append({"org_name": org, "website": "", "source": "outreach_log.csv"})

    new_rows: list[dict[str, Any]] = []
    for c in candidates:
        org_key = c["org_name"].lower()
        if org_key in seen_org:
            continue
        seen_org.add(org_key)
        segment = infer_segment(c["org_name"])
        priority = priority_for_segment(segment)
        relevance = relevance_for_segment(segment, priority)
        tags = ["passive_discovery", "search_resolve", "auto_scored"]
        if relevance >= 90:
            tags.append("high_value")
        new_rows.append(
            {
                "target_mode": "search_resolve",
                "handle": "",
                "org_name": c["org_name"],
                "profile_url": "",
                "lookup_query": f"\"{c['org_name']}\" x.com",
                "source_org": f"passive_growth:{c['source']}",
                "source_url": c["website"],
                "segment": segment,
                "region": "michigan",
                "priority": priority,
                "verified_source": False,
                "method": "passive_growth_local_compute",
                "notes": "Discovered from local partner/outreach records",
                "last_verified_at": now_iso(),
                "status": "candidate",
                "tags": tags,
                "relevance_score": relevance,
                "high_value": relevance >= 90,
            }
        )
        if len(new_rows) >= 20:
            break
    return new_rows


def write_follow_targets_csv(targets: list[dict[str, Any]]) -> None:
    headers = [
        "target_mode",
        "handle",
        "org_name",
        "profile_url",
        "lookup_query",
        "source_org",
        "source_url",
        "segment",
        "region",
        "priority",
        "relevance_score",
        "high_value",
        "verified_source",
        "status",
        "last_verified_at",
        "method",
        "tags",
        "notes",
    ]
    with open(FOLLOW_TARGETS_CSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for t in targets:
            writer.writerow(
                {
                    "target_mode": t.get("target_mode", ""),
                    "handle": t.get("handle", ""),
                    "org_name": t.get("org_name", ""),
                    "profile_url": t.get("profile_url", ""),
                    "lookup_query": t.get("lookup_query", ""),
                    "source_org": t.get("source_org", ""),
                    "source_url": t.get("source_url", ""),
                    "segment": t.get("segment", ""),
                    "region": t.get("region", ""),
                    "priority": t.get("priority", ""),
                    "relevance_score": t.get("relevance_score", ""),
                    "high_value": t.get("high_value", ""),
                    "verified_source": t.get("verified_source", ""),
                    "status": t.get("status", ""),
                    "last_verified_at": t.get("last_verified_at", ""),
                    "method": t.get("method", ""),
                    "tags": "|".join(t.get("tags", [])) if isinstance(t.get("tags"), list) else str(t.get("tags", "")),
                    "notes": t.get("notes", ""),
                }
            )


def update_momentum_state(today: str, today_rows: list[dict[str, str]], credibility_pack: dict[str, Any]) -> dict[str, Any]:
    state = load_json(STATE_FILE, {})
    if not isinstance(state, dict):
        state = {}

    tracking = state.get("tracking", {})
    if not isinstance(tracking, dict):
        tracking = {}
    for key in ["engaged", "followed", "replied", "escalate_to_dm"]:
        if not isinstance(tracking.get(key), list):
            tracking[key] = []

    day_key = today
    daily = state.get("daily", {})
    if not isinstance(daily, dict):
        daily = {}

    accounts = [r.get("account_handle", "") for r in today_rows if r.get("account_handle")]
    escalate = [r.get("account_handle", "") for r in today_rows if r.get("first_interaction_type") == "reply"][:3]

    daily[day_key] = {
        "assigned_accounts": accounts,
        "actions_count": len(today_rows),
        "credibility_target": (credibility_pack.get("credibility_target") or {}).get("account_handle")
        if isinstance(credibility_pack.get("credibility_target"), dict)
        else "",
        "authority_signal_action": credibility_pack.get("authority_signal_action", ""),
        "partnership_touchpoint": (credibility_pack.get("partnership_touchpoint") or {}).get("account_handle")
        if isinstance(credibility_pack.get("partnership_touchpoint"), dict)
        else "",
        "status": "planned",
    }

    tracking["escalate_to_dm"] = sorted(set(tracking["escalate_to_dm"] + [e for e in escalate if e]))

    state["tracking"] = tracking
    state["daily"] = daily
    state["updated_at"] = now_iso()
    state["last_run_date"] = today
    return state


def build_daily_ops_markdown(
    today: str,
    today_rows: list[dict[str, str]],
    calendar_block: str,
    credibility_pack: dict[str, Any],
    new_targets: list[dict[str, Any]],
) -> str:
    lines: list[str] = []
    lines.append(f"# Daily Ops {today}")
    lines.append("")
    lines.append("- Mode: no API, no posting, local compute + browser-read allowed")
    lines.append("- Goal: execute daily growth in <10 minutes")
    lines.append("")

    lines.append("## Today's Actions")
    if today_rows:
        for idx, row in enumerate(today_rows, start=1):
            lines.append(
                f"{idx}. `{row.get('account_handle','')}` | {row.get('role','')} | "
                f"Day 1: {row.get('day_1_action','')}"
            )
    else:
        lines.append("1. No actions found in ops sheet.")
    lines.append("")

    lines.append("## Follow Queue Prep")
    for row in today_rows[:8]:
        lines.append(f"- `{row.get('account_handle','')}` at `{row.get('follow_timing','')}`")
    if not today_rows:
        lines.append("- none")
    lines.append("")

    lines.append("## Outreach Reminders")
    for row in today_rows[:8]:
        lines.append(
            f"- `{row.get('account_handle','')}` -> `{row.get('first_interaction_type','')}` "
            f"(DM ref: `{row.get('dm_script_reference','')}`)"
        )
    if not today_rows:
        lines.append("- none")
    lines.append("")

    lines.append("## Credibility Builder")
    cred = credibility_pack.get("credibility_target") or {}
    partner = credibility_pack.get("partnership_touchpoint") or {}
    lines.append(f"- Daily interaction target: `{cred.get('account_handle','')}`")
    lines.append(f"- Authority signal action: {credibility_pack.get('authority_signal_action','')}")
    lines.append(f"- Partnership touchpoint: `{partner.get('account_handle','')}`")
    lines.append("")

    lines.append("## Passive Growth Tasks")
    lines.append(f"- New ag accounts discovered and appended today: `{len(new_targets)}`")
    for t in new_targets[:10]:
        lines.append(f"- `{t.get('org_name','')}` ({t.get('segment','')}, score={t.get('relevance_score','')})")
    if not new_targets:
        lines.append("- none")
    lines.append("")

    lines.append("## Calendar Context")
    if calendar_block:
        lines.append(calendar_block)
    else:
        lines.append("- No explicit day block in 14-day calendar for today; using ops-sheet priority order.")
    lines.append("")

    lines.append("## Completion Log")
    lines.append("- Mark followed/replied/engaged in `runtime/momentum_state.json` during execution.")
    lines.append("- Promote to DM escalation when reply gets a response.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    today_dt = now_utc()
    today = today_dt.strftime("%Y-%m-%d")
    ops_rows = read_ops_sheet()
    calendar_text = CALENDAR.read_text(encoding="utf-8") if CALENDAR.exists() else ""
    calendar_block = extract_todays_calendar_block(calendar_text, today)

    today_rows = choose_today_rows(ops_rows)
    credibility_pack = build_daily_credibility_pack(today_rows)

    targets_payload = load_json(FOLLOW_TARGETS_JSON, {})
    if not isinstance(targets_payload, dict):
        targets_payload = {}
    targets = targets_payload.get("targets", [])
    if not isinstance(targets, list):
        targets = []

    new_targets = discover_passive_targets(targets)
    if new_targets:
        targets.extend(new_targets)
        targets.sort(
            key=lambda t: (
                -int(t.get("relevance_score") or 0),
                int(t.get("priority") or 2),
                str(t.get("org_name") or "").lower(),
            )
        )
        targets_payload["targets"] = targets
        targets_payload["target_count"] = len(targets)
        targets_payload["generated_at"] = now_iso()
        save_json(FOLLOW_TARGETS_JSON, targets_payload)
        write_follow_targets_csv(targets)

    state = update_momentum_state(today, today_rows, credibility_pack)
    save_json(STATE_FILE, state)

    output = RUNTIME / f"daily_ops_{today}.md"
    output.write_text(
        build_daily_ops_markdown(today, today_rows, calendar_block, credibility_pack, new_targets),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "ok": True,
                "daily_ops_file": str(output),
                "momentum_state": str(STATE_FILE),
                "passive_targets_added": len(new_targets),
                "actions_today": len(today_rows),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
