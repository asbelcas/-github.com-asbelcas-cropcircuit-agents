#!/usr/bin/env python3
"""Build offline draft assets for partner outreach and MDARD packet prep."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/asbelcas/cropcircuit")
RUNTIME = ROOT / "runtime"
DRAFTS = RUNTIME / "drafts"

MAP_CSV = RUNTIME / "mdard_contact_map.csv"
PARTNER_TARGETS_JSON = RUNTIME / "partner_targets.json"

FOCUS_COUNTIES = {"calhoun", "kalamazoo", "barry", "branch", "st joseph", "st. joseph", "van buren", "battle creek"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_mdard_rows() -> list[dict[str, str]]:
    if not MAP_CSV.exists():
        return []
    with MAP_CSV.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _county_hit(text: str) -> bool:
    t = (text or "").lower()
    return any(c in t for c in FOCUS_COUNTIES)


def _looks_decision_maker(contact_name: str, notes: str) -> bool:
    t = f"{contact_name} {notes}".lower()
    keys = [
        "director",
        "manager",
        "coordinator",
        "educator",
        "lead",
        "office",
        "conservation district",
        "farm bureau",
        "extension",
    ]
    return any(k in t for k in keys)


def build_partner_list() -> list[dict[str, str]]:
    rows = _load_mdard_rows()
    out = []
    for r in rows:
        org = (r.get("org") or "").strip()
        email = (r.get("email") or "").strip()
        phone = (r.get("phone") or "").strip()
        notes = (r.get("notes") or "").strip()
        next_action = (r.get("next_action") or "").strip()
        if not org:
            continue
        if not (email or phone):
            continue
        if not _county_hit(f"{org} {notes}"):
            continue
        if not _looks_decision_maker(org, notes):
            continue
        out.append(
            {
                "org": org,
                "email": email,
                "phone": phone,
                "notes": notes[:240],
                "next_action": next_action or "priority_outreach_today",
            }
        )
    # stable dedupe by org+email+phone
    seen = set()
    uniq = []
    for row in out:
        key = f"{row['org'].lower()}|{row['email'].lower()}|{row['phone']}"
        if key in seen:
            continue
        seen.add(key)
        uniq.append(row)
    return uniq


def build_outreach_tiers(partners: list[dict[str, str]]) -> dict:
    tier_1, tier_2, tier_3 = [], [], []
    for p in partners:
        text = f"{p['org']} {p['notes']}".lower()
        if any(k in text for k in ["conservation district", "msu extension", "farm bureau"]):
            tier_1.append(p)
        elif any(k in text for k in ["food", "nonprofit", "station", "kellogg"]):
            tier_2.append(p)
        else:
            tier_3.append(p)
    return {
        "updated_at": now_iso(),
        "tier_1_call_first": tier_1[:12],
        "tier_2_email_first": tier_2[:20],
        "tier_3_network_expansion": tier_3[:30],
    }


def build_email_drafts(tiers: dict) -> dict:
    drafts = []
    for item in tiers.get("tier_1_call_first", [])[:10]:
        org = item["org"]
        to = item["email"] or "PHONE_FIRST"
        subj = f"Quick local coordination: MDARD regenerative network ({org})"
        body = (
            f"Hi {org} team,\n\n"
            "I run CropCircuit Farm in Augusta and I am preparing a practical MDARD regenerative network packet.\n"
            "I am looking for a local implementation partner for Calhoun/Kalamazoo area execution.\n"
            "Can we do a 15-minute call this week to confirm fit and next step?\n\n"
            "Thanks,\nCasey\n"
            "269-986-8595\n"
        )
        drafts.append({"to": to, "subject": subj, "body": body, "mode": "draft_only"})
    return {"updated_at": now_iso(), "drafts": drafts}


def build_mdard_packet(partners: list[dict[str, str]]) -> str:
    lines = [
        "# MDARD Packet Draft (Offline Mode)",
        "",
        f"Updated: {now_iso()}",
        "",
        "## Core Narrative",
        "- CropCircuit builds practical funding + outreach systems for farms and ag organizations.",
        "- Focus geography: Calhoun, Kalamazoo, Barry, Branch, St. Joseph, Van Buren, Battle Creek radius.",
        "- Delivery model: intake -> partner map -> submission workflow -> follow-up loop.",
        "",
        "## Attachments Checklist",
        "- Program summary (1 page)",
        "- Budget and timeline",
        "- Partner map and contact roster",
        "- Letters of support draft set",
        "- Implementation milestones (90 days)",
        "",
        "## Priority Partner Calls (Offline Queue)",
    ]
    for p in partners[:12]:
        lines.append(f"- {p['org']} | {p['email'] or 'no-email'} | {p['phone'] or 'no-phone'}")
    lines.extend(
        [
            "",
            "## Risk Controls",
            "- No IMAP/send execution until preflight returns ok:true.",
            "- Draft-only queue maintained under runtime/drafts.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_followup_templates() -> str:
    return (
        "# Follow-up Templates (Offline Queue)\n\n"
        "## Day 2 Check-in\n"
        "Subject: Quick follow-up on MDARD coordination\n"
        "Body: Hi {name}, checking whether your team is the right fit for this local partner role. If not, who should I coordinate with?\n\n"
        "## Day 5 Action Ask\n"
        "Subject: Hold 15 minutes this week?\n"
        "Body: Hi {name}, can we lock a short call this week to confirm fit, scope, and who signs off on collaboration?\n\n"
        "## Day 10 Close Loop\n"
        "Subject: Closing loop for now\n"
        "Body: Hi {name}, I will close this loop for now and re-open once the next packet milestone is ready.\n"
    )


def main() -> int:
    DRAFTS.mkdir(parents=True, exist_ok=True)
    (RUNTIME / "offline_mode.json").write_text(
        json.dumps(
            {
                "active": True,
                "updated_at": now_iso(),
                "rule": "No IMAP/send actions until preflight_imap ok:true",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    partners = build_partner_list()
    tiers = build_outreach_tiers(partners)
    drafts = build_email_drafts(tiers)
    mdard_packet = build_mdard_packet(partners)
    templates = build_followup_templates()

    (DRAFTS / "partner_list_offline.json").write_text(json.dumps({"updated_at": now_iso(), "partners": partners}, indent=2) + "\n", encoding="utf-8")
    (DRAFTS / "outreach_tiers.json").write_text(json.dumps(tiers, indent=2) + "\n", encoding="utf-8")
    (DRAFTS / "outreach_email_drafts.json").write_text(json.dumps(drafts, indent=2) + "\n", encoding="utf-8")
    (DRAFTS / "mdard_packet_draft.md").write_text(mdard_packet, encoding="utf-8")
    (DRAFTS / "followup_templates_offline.md").write_text(templates, encoding="utf-8")

    manifest = {
        "updated_at": now_iso(),
        "mode": "offline",
        "generated_files": [
            "runtime/drafts/partner_list_offline.json",
            "runtime/drafts/outreach_tiers.json",
            "runtime/drafts/outreach_email_drafts.json",
            "runtime/drafts/mdard_packet_draft.md",
            "runtime/drafts/followup_templates_offline.md",
            "runtime/offline_mode.json",
        ],
    }
    (DRAFTS / "_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "mode": "offline", "partners": len(partners), "drafts": len(drafts["drafts"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
