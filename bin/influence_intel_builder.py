#!/usr/bin/env python3
"""Build influence rankings, warm-entry strategy, and launch protocol (no API)."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"

TARGETS_FILE = RUNTIME / "follow_targets_agriculture.json"
PROSPECTS_FILE = RUNTIME / "partner_prospects_social.csv"
FOLLOW_QUEUE_FILE = RUNTIME / "x_follow_queue.jsonl"

INFLUENCE_FILE = RUNTIME / "influence_rankings_agriculture.json"
CALENDAR_FILE = RUNTIME / "momentum_calendar_14d.md"
LAUNCH_PROTOCOL_FILE = RUNTIME / "launch_protocol_rate_reset.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def load_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []


def load_follow_queue(path: Path) -> list[dict]:
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


def infer_org_type(row: dict) -> str:
    segment = (row.get("segment") or "").lower()
    org = (row.get("org_name") or "").lower()
    tags = [str(t).lower() for t in (row.get("tags") or [])]

    if segment == "usda" or "usda" in org:
        return "USDA"
    if segment == "extension" or "extension" in org or "msu extension" in org:
        return "extension"
    if "farm" in org or "ranch" in org or "livestock" in org:
        return "farm"
    if segment in {"michigan_org", "commodity", "grant_partner", "michigan_agency", "conservation"}:
        if "county_cd" in tags or "conservation district" in org:
            return "nonprofit"
        return "nonprofit"
    return "nonprofit"


def michigan_proximity_score(row: dict) -> float:
    region = (row.get("region") or "").lower()
    org = (row.get("org_name") or "").lower()
    score = 1.0 if region == "michigan" else 0.35
    local_signals = [
        "calhoun",
        "battle creek",
        "barry",
        "kalamazoo",
        "jackson",
        "lansing",
        "marshall",
        "van buren",
    ]
    if any(sig in org for sig in local_signals):
        score += 0.2
    return min(1.0, score)


def follower_estimate(org_type: str, row: dict) -> int:
    region = (row.get("region") or "").lower()
    segment = (row.get("segment") or "").lower()
    org = (row.get("org_name") or "").lower()

    if org_type == "USDA":
        return 450_000 if region == "national" else 45_000
    if org_type == "extension":
        return 70_000 if "msu extension" in org else 22_000
    if segment == "michigan_agency":
        return 90_000
    if segment == "commodity":
        return 12_000
    if "conservation district" in org:
        return 6_500
    if org_type == "farm":
        return 4_000
    return 15_000


def partnership_likelihood(row: dict, org_type: str) -> int:
    score = 40
    seg = (row.get("segment") or "").lower()
    org = (row.get("org_name") or "").lower()
    priority = int(row.get("priority") or 2)
    proximity = michigan_proximity_score(row)

    if org_type == "extension":
        score += 35
    if seg in {"conservation", "grant_partner", "michigan_org"}:
        score += 25
    if seg == "michigan_agency":
        score += 15
    if "district" in org:
        score += 10
    if "service center" in org:
        score += 8
    if priority == 1:
        score += 8
    score += int(proximity * 10)
    return max(1, min(100, score))


def grant_relevance(row: dict, org_type: str) -> int:
    seg = (row.get("segment") or "").lower()
    org = (row.get("org_name") or "").lower()
    score = 35
    if seg in {"grant_partner", "conservation", "extension", "michigan_agency", "usda"}:
        score += 35
    if "conservation" in org or "service center" in org or "extension" in org:
        score += 20
    if org_type == "farm":
        score += 10
    return max(1, min(100, score))


def scale_followers(followers: int) -> int:
    return max(1, min(100, int((followers / 500_000) * 100)))


def classify_roles(item: dict) -> list[str]:
    roles = []
    followers = item["follower_estimate"]
    partnership = item["partnership_likelihood"]
    grant = item["grant_relevance"]
    org_type = item["org_type"]

    if partnership >= 75 and grant >= 70:
        roles.append("partnership_target")
    if followers >= 50_000 or item["authority_score"] >= 80:
        roles.append("amplification_target")
    if org_type in {"USDA", "extension"} or item["authority_score"] >= 85:
        roles.append("credibility_anchor")
    if not roles:
        roles.append("partnership_target")
    return roles


def primary_role(roles: list[str]) -> str:
    order = ["credibility_anchor", "amplification_target", "partnership_target"]
    for role in order:
        if role in roles:
            return role
    return "partnership_target"


def suggest_warm_entry(item: dict) -> dict:
    followers = item["follower_estimate"]
    partnership = item["partnership_likelihood"]
    org_type = item["org_type"]
    mode = item["target_mode"]
    org = item["org_name"]

    if mode == "search_resolve":
        first = "Resolve handle via search query, then follow in same execution wave."
    else:
        first = "Follow immediately when reset opens."

    if followers >= 100_000:
        channel = "reply_then_follow"
        timing = "Reply to latest relevant post within 2 hours of follow; DM only after one interaction."
    elif partnership >= 80:
        channel = "follow_then_dm"
        timing = "Follow at reset, send concise DM within 6-12 hours."
    else:
        channel = "follow_then_reply"
        timing = "Follow at reset, then public reply within 12-24 hours."

    if org_type == "USDA":
        angle = "Align CropCircuit updates to USDA producer resources and conservation implementation outcomes."
    elif org_type == "extension":
        angle = "Offer a practical Michigan field-status snapshot and request guidance/resource alignment."
    elif "conservation" in org.lower():
        angle = "Propose district-aligned conservation practice tracking and joint producer-facing updates."
    elif org_type == "farm":
        angle = "Peer-to-peer exchange on sheep/small-farm systems and regenerative operations."
    else:
        angle = "Position as a transparent implementation partner with measurable grant-linked outcomes."

    return {
        "suggested_first_interaction": first,
        "interaction_channel": channel,
        "timing_guidance": timing,
        "collaboration_angle": angle,
    }


def build_momentum_calendar(reset_at: datetime) -> str:
    lines = []
    lines.append("# Momentum Calendar (First 14 Days After Rate Reset)")
    lines.append("")
    lines.append(f"- Reset anchor (UTC): {reset_at.strftime('%Y-%m-%d %H:%M:%SZ')}")
    lines.append("- Execution mode: no API dependency required for planning artifacts")
    lines.append("")
    for day in range(1, 15):
        d = reset_at + timedelta(days=day)
        ds = d.strftime("%Y-%m-%d")
        if day == 1:
            follow = "Wave 1 follows (ranks 1-30), resolve+follow high-value search targets"
            outreach = "Start outreach to top 10 partnership targets within 6-24h"
            posts = "Deploy 2 credibility drafts (mission + conservation)"
        elif day == 2:
            follow = "Wave 1 completion + retries"
            outreach = "DM/reply top 10 amplification and credibility targets"
            posts = "Deploy 2 drafts (Michigan farming + regenerative operations)"
        elif day == 3:
            follow = "Wave 2 begins (ranks 31-55)"
            outreach = "Partner intros to county districts + MSU extension contacts"
            posts = "Deploy 2 drafts (conservation + sheep systems)"
        elif day == 4:
            follow = "Wave 2 continues (ranks 56-80)"
            outreach = "Grant collaboration pitch to high-likelihood nonprofits"
            posts = "Deploy 2 drafts (mission + partnership framing)"
        elif day in {5, 6, 7}:
            follow = "Wave 3 follows (ranks 81-120)"
            outreach = "Second-touch outreach for non-responders from top 25"
            posts = "Deploy 1-2 drafts/day, prioritize credibility themes"
        elif day in {8, 9, 10}:
            follow = "Wave 3 completion (ranks 121-177) + unresolved handle cleanup"
            outreach = "Expand to commodity and farm-peer targets"
            posts = "Deploy 1-2 drafts/day, mix Michigan farming + sheep/small-farm"
        elif day in {11, 12}:
            follow = "Stabilization and selective backfill follows"
            outreach = "Partnership conversion asks for warm contacts"
            posts = "Deploy 1 credibility + 1 collaboration-focused draft/day"
        else:
            follow = "Maintenance follows for any newly resolved high-value accounts"
            outreach = "Third-touch where engagement exists, otherwise park"
            posts = "Deploy best-performing remaining drafts by theme balance"
        lines.append(f"## Day {day} — {ds}")
        lines.append(f"- Follow Wave: {follow}")
        lines.append(f"- Outreach Wave: {outreach}")
        lines.append(f"- Post Sequencing: {posts}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_launch_protocol(reset_at: datetime) -> str:
    return "\n".join(
        [
            "# Launch Protocol — Rate Reset Activation",
            "",
            f"- Reset trigger (UTC): {reset_at.strftime('%Y-%m-%d %H:%M:%SZ')}",
            "- Constraints: no API usage required for planning outputs; no posting executed by this script",
            "",
            "## T+0 to T+1h",
            "- Execute follow queue Wave 1 by rank (1-30).",
            "- Resolve search_resolve targets first, then follow resolved handles.",
            "- Prioritize rows tagged high_value and credibility_anchor.",
            "",
            "## T+1h to T+6h",
            "- Trigger first credibility content batch from prepared drafts.",
            "- Start warm-entry interactions for top 10 partnership targets.",
            "- Log outcomes: followed, resolved, engaged, pending.",
            "",
            "## T+6h to T+24h",
            "- Launch outreach wave to top 25 targets (DM/reply based on strategy map).",
            "- Send partner intro script to extension/conservation targets.",
            "- Send grant collaboration pitch to high-likelihood nonprofit/grant partners.",
            "",
            "## T+24h+",
            "- Execute Wave 2 follows and second-touch outreach.",
            "- Continue scheduled post sequencing from 14-day calendar.",
            "- Re-rank weekly using observed engagement and partnership responses.",
            "",
        ]
    )


def main() -> int:
    run_ts = now_iso()
    data = load_json(TARGETS_FILE, {})
    targets = data.get("targets", []) if isinstance(data, dict) else []
    prospects = load_csv_rows(PROSPECTS_FILE)
    queue = load_follow_queue(FOLLOW_QUEUE_FILE)

    if not isinstance(targets, list):
        targets = []

    prospect_idx = {str(r.get("org_name") or "").strip().lower(): r for r in prospects}

    enriched = []
    for row in targets:
        org_name = str(row.get("org_name") or "").strip()
        org_key = org_name.lower()
        org_type = infer_org_type(row)
        proximity = michigan_proximity_score(row)
        followers = follower_estimate(org_type, row)
        partner = partnership_likelihood(row, org_type)
        grant = grant_relevance(row, org_type)
        authority = int(round((scale_followers(followers) * 0.7) + ((100 if row.get("high_value") else 40) * 0.3)))
        influence = int(
            round(
                (authority * 0.30)
                + (int(proximity * 100) * 0.20)
                + (partner * 0.20)
                + (grant * 0.20)
                + (int(row.get("relevance_score") or 0) * 0.10)
            )
        )
        item = {
            "org_name": org_name,
            "handle": row.get("handle") or "",
            "target_mode": row.get("target_mode") or "search_resolve",
            "lookup_query": row.get("lookup_query") or "",
            "segment": row.get("segment") or "",
            "region": row.get("region") or "",
            "priority": int(row.get("priority") or 2),
            "high_value": bool(row.get("high_value")),
            "org_type": org_type,
            "michigan_proximity": round(proximity, 2),
            "follower_estimate": followers,
            "follower_estimate_band": (
                "very_large"
                if followers >= 150_000
                else "large"
                if followers >= 50_000
                else "medium"
                if followers >= 15_000
                else "small"
            ),
            "partnership_likelihood": partner,
            "grant_relevance": grant,
            "authority_score": authority,
            "influence_score": influence,
            "source_org": row.get("source_org") or "",
            "source_url": row.get("source_url") or "",
            "tags": row.get("tags") or [],
            "prospect_row_present": org_key in prospect_idx,
        }
        item["roles"] = classify_roles(item)
        item["primary_role"] = primary_role(item["roles"])
        item["warm_entry"] = suggest_warm_entry(item)
        enriched.append(item)

    enriched.sort(
        key=lambda x: (
            -int(x["influence_score"]),
            -int(x["partnership_likelihood"]),
            -int(x["grant_relevance"]),
            x["org_name"].lower(),
        )
    )

    top50 = enriched[:50]

    # Parse next reset anchor from queue if present.
    reset_at = datetime.now(timezone.utc) + timedelta(days=1)
    if queue:
        raw = str(queue[0].get("execute_after") or "").strip()
        if raw.endswith("Z"):
            raw = raw.replace("Z", "+00:00")
        try:
            reset_at = datetime.fromisoformat(raw)
            if reset_at.tzinfo is None:
                reset_at = reset_at.replace(tzinfo=timezone.utc)
        except Exception:
            pass

    ranking_payload = {
        "generated_at": run_ts,
        "objective": "influence_intelligence_target_dominance",
        "input_counts": {
            "targets": len(targets),
            "prospects": len(prospects),
            "follow_queue": len(queue),
        },
        "model_weights": {
            "authority_score": 0.30,
            "michigan_proximity": 0.20,
            "partnership_likelihood": 0.20,
            "grant_relevance": 0.20,
            "existing_relevance_score": 0.10,
        },
        "top_50_summary": {
            "count": len(top50),
            "partnership_targets": sum(1 for r in top50 if "partnership_target" in r["roles"]),
            "amplification_targets": sum(1 for r in top50 if "amplification_target" in r["roles"]),
            "credibility_anchors": sum(1 for r in top50 if "credibility_anchor" in r["roles"]),
        },
        "top_50_priority_accounts": top50,
        "full_rankings": enriched,
    }
    INFLUENCE_FILE.write_text(json.dumps(ranking_payload, indent=2), encoding="utf-8")

    CALENDAR_FILE.write_text(build_momentum_calendar(reset_at), encoding="utf-8")
    LAUNCH_PROTOCOL_FILE.write_text(build_launch_protocol(reset_at), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "influence_rankings": str(INFLUENCE_FILE),
                "momentum_calendar": str(CALENDAR_FILE),
                "launch_protocol": str(LAUNCH_PROTOCOL_FILE),
                "counts": {
                    "ranked_accounts": len(enriched),
                    "top50": len(top50),
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
