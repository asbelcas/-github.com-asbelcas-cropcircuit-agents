#!/usr/bin/env python3
"""Build top-50 operator execution sheet and 48h playbook (prepare-only)."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"

INFLUENCE_FILE = RUNTIME / "influence_rankings_agriculture.json"
FOLLOW_QUEUE_FILE = RUNTIME / "x_follow_queue.jsonl"
OPS_SHEET_FILE = RUNTIME / "top50_ops_sheet.csv"
PLAYBOOK_FILE = RUNTIME / "launch_playbook_48h.md"


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def load_queue(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def parse_reset_time(queue: list[dict]) -> datetime:
    if not queue:
        return datetime.now(timezone.utc) + timedelta(days=1)
    raw = str(queue[0].get("execute_after") or "")
    if raw.endswith("Z"):
        raw = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc) + timedelta(days=1)


def map_role(primary_role: str) -> str:
    if primary_role == "credibility_anchor":
        return "credibility"
    if primary_role == "amplification_target":
        return "amplification"
    return "partner"


def wave_for_role(role: str) -> str:
    if role == "credibility":
        return "Wave A"
    if role == "partner":
        return "Wave B"
    return "Wave C"


def interaction_type(item: dict) -> str:
    channel = ((item.get("warm_entry") or {}).get("interaction_channel") or "").strip()
    if channel == "follow_then_dm":
        return "DM"
    if channel == "follow_then_reply":
        return "reply"
    if channel == "reply_then_follow":
        return "reply"
    return "follow"


def script_refs(role: str, interaction: str) -> tuple[str, str]:
    dm_ref = "runtime/outreach_scripts_social.md#expansion-pack-twitter-dm-variants"
    reply_ref = "runtime/outreach_scripts_social.md#partner-intro-script"
    if role == "credibility":
        dm_ref = "runtime/outreach_scripts_social.md#twitter-dm-variants-usda-local-office"
        reply_ref = "runtime/outreach_scripts_social.md#partner-intro-script"
    elif role == "partner":
        dm_ref = "runtime/outreach_scripts_social.md#twitter-dm-variants-conservation-district"
        reply_ref = "runtime/outreach_scripts_social.md#grant-collaboration-pitch"
    elif role == "amplification":
        dm_ref = "runtime/outreach_scripts_social.md#twitter-dm-variants-commodity-group"
        reply_ref = "runtime/outreach_scripts_social.md#email-templates"

    if interaction == "reply":
        dm_ref = "n/a"
    if interaction == "DM":
        reply_ref = "optional_after_first_response"
    return dm_ref, reply_ref


def day_actions(role: str, item: dict) -> tuple[str, str]:
    org = item.get("org_name") or "target"
    warm = item.get("warm_entry") or {}
    first = warm.get("suggested_first_interaction") or "Follow"
    angle = warm.get("collaboration_angle") or "Introduce CropCircuit scope"

    if role == "credibility":
        d1 = f"Resolve/follow {org}; engage with one relevant post using credibility framing."
        d2 = "Send concise DM introducing CropCircuit implementation proof; request resource alignment."
    elif role == "partner":
        d1 = f"{first} Then send partnership-oriented intro citing local Michigan outcomes."
        d2 = f"Follow-up with grant collaboration angle: {angle}"
    else:
        d1 = f"Resolve/follow {org}; leave one high-signal reply aligned to their audience."
        d2 = "Send optional DM requesting cross-audience alignment or content signal boost."
    return d1, d2


def write_ops_sheet(top50: list[dict], reset_at: datetime) -> list[dict]:
    prelim = []
    for item in top50:
        roles = item.get("roles") or []
        if "credibility_anchor" in roles:
            role = "credibility"
        elif "amplification_target" in roles:
            role = "amplification"
        else:
            role = "partner"
        prelim.append((item, role))

    # Ensure Wave C has coverage even when amplification flags overlap Wave A.
    if not any(role == "amplification" for _, role in prelim):
        candidates = sorted(
            [(i, itm) for i, (itm, role) in enumerate(prelim) if role == "partner"],
            key=lambda x: (
                -int(x[1].get("follower_estimate") or 0),
                -int(x[1].get("influence_score") or 0),
            ),
        )
        for idx, _itm in candidates[:8]:
            prelim[idx] = (prelim[idx][0], "amplification")

    rows = []
    for item, role in prelim:
        wave = wave_for_role(role)
        interaction = interaction_type(item)
        dm_ref, reply_ref = script_refs(role, interaction)
        d1, d2 = day_actions(role, item)
        timing = (
            "T+0h to T+6h"
            if wave == "Wave A"
            else "T+6h to T+24h"
            if wave == "Wave B"
            else "T+24h to T+48h"
        )
        handle = item.get("handle") or ""
        if not handle:
            handle = f"RESOLVE::{item.get('lookup_query') or item.get('org_name') or ''}"
        rows.append(
            {
                "account_handle": handle,
                "role": role,
                "day_1_action": d1,
                "day_2_action": d2,
                "first_interaction_type": interaction,
                "dm_script_reference": dm_ref,
                "reply_script_reference": reply_ref,
                "follow_timing": timing,
                "priority_score": int(item.get("influence_score") or 0),
                "_wave": wave,
            }
        )

    # Enforce wave grouping order: A -> B -> C, then score desc.
    wave_order = {"Wave A": 0, "Wave B": 1, "Wave C": 2}
    rows.sort(key=lambda r: (wave_order.get(r["_wave"], 9), -int(r["priority_score"]), r["account_handle"].lower()))

    cols = [
        "account_handle",
        "role",
        "day_1_action",
        "day_2_action",
        "first_interaction_type",
        "dm_script_reference",
        "reply_script_reference",
        "follow_timing",
        "priority_score",
    ]
    OPS_SHEET_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OPS_SHEET_FILE, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in cols})
    return rows


def write_playbook(rows: list[dict], reset_at: datetime) -> None:
    wave_a = [r for r in rows if r["_wave"] == "Wave A"]
    wave_b = [r for r in rows if r["_wave"] == "Wave B"]
    wave_c = [r for r in rows if r["_wave"] == "Wave C"]

    def sample_handles(items: list[dict], n: int = 8) -> str:
        vals = [x["account_handle"] for x in items[:n]]
        return ", ".join(vals) if vals else "none"

    lines = [
        "# Launch Playbook — First 48 Hours",
        "",
        f"- Reset anchor (UTC): {reset_at.strftime('%Y-%m-%d %H:%M:%SZ')}",
        "- Constraints: prepare-only artifact, no posting/API actions executed here",
        "",
        "## Wave Grouping",
        f"- Wave A (credibility anchors): {len(wave_a)} accounts",
        f"- Wave B (partnership targets): {len(wave_b)} accounts",
        f"- Wave C (amplification nodes): {len(wave_c)} accounts",
        "",
        "## Operator Instructions",
        "### Manual operator tasks",
        "- Validate profile identity for all `RESOLVE::` rows before follow/action.",
        "- Execute scripted replies/DMs in the order shown in `runtime/top50_ops_sheet.csv`.",
        "- Record outcomes (followed, replied, DM sent, responded) in your run log.",
        "",
        "### Agent tasks",
        "- Pull rows from `runtime/top50_ops_sheet.csv` in order and enforce wave timing windows.",
        "- Resolve handles for `RESOLVE::` entries and mark resolved handle for next pass.",
        "- Trigger action recommendations exactly as listed for Day 1 and Day 2.",
        "",
        "### Timing Relative To Reset",
        "- T+0h to T+6h: Execute Wave A only.",
        "- T+6h to T+24h: Execute Wave B and second pass on Wave A.",
        "- T+24h to T+48h: Execute Wave C and unresolved carry-over items.",
        "",
        "## First 48 Hours Sequencing",
        "### 0-6 Hours",
        "- Follow/resolve top credibility anchors.",
        "- Start first interactions for top 10 Wave A rows.",
        f"- Sample queue: {sample_handles(wave_a)}",
        "",
        "### 6-24 Hours",
        "- Execute partnership outreach rows and send intro/grant collaboration angle.",
        "- Start Day 2 actions for completed Wave A rows.",
        f"- Sample queue: {sample_handles(wave_b)}",
        "",
        "### 24-48 Hours",
        "- Execute amplification node actions and content-signal replies.",
        "- Complete Day 2 actions for Wave B rows and retry unresolved entries.",
        f"- Sample queue: {sample_handles(wave_c)}",
        "",
        "## No-Think Launch Checklist",
        "1. Open `runtime/top50_ops_sheet.csv` and process top-to-bottom.",
        "2. Respect wave windows by `follow_timing` column.",
        "3. Use script references in each row; do not improvise until row actions complete.",
        "4. Carry unresolved `RESOLVE::` rows to the next window.",
    ]
    PLAYBOOK_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    influence = load_json(INFLUENCE_FILE, {})
    top50 = influence.get("top_50_priority_accounts", []) if isinstance(influence, dict) else []
    queue = load_queue(FOLLOW_QUEUE_FILE)
    reset_at = parse_reset_time(queue)

    if not isinstance(top50, list):
        top50 = []
    top50 = top50[:50]

    rows = write_ops_sheet(top50, reset_at)
    write_playbook(rows, reset_at)

    print(
        json.dumps(
            {
                "ok": True,
                "ops_sheet": str(OPS_SHEET_FILE),
                "playbook_48h": str(PLAYBOOK_FILE),
                "counts": {
                    "top50_rows": len(rows),
                    "wave_a": len([r for r in rows if r["_wave"] == "Wave A"]),
                    "wave_b": len([r for r in rows if r["_wave"] == "Wave B"]),
                    "wave_c": len([r for r in rows if r["_wave"] == "Wave C"]),
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
