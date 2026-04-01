#!/usr/bin/env python3
"""Build MDARD/MNARD contact map, today queue, templates, and dedup prospects."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
RUNTIME = ROOT / "runtime"

PROSPECTS = RUNTIME / "partner_prospects_social.csv"
PARTNERS = ROOT / "partners_contacts.csv"
OUTREACH_LOG = ROOT / "outreach_log.csv"

CONTACT_MAP = RUNTIME / "mdard_contact_map.csv"
TODAY_QUEUE = RUNTIME / "today_queue.md"
TEMPLATES = RUNTIME / "outreach_email_templates.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def dedupe_partner_prospects() -> int:
    rows = read_csv(PROSPECTS)
    if not rows:
        return 0
    keyed = {}
    for r in rows:
        org = (r.get("org_name") or "").strip().lower()
        lookup = (r.get("lookup_query") or "").strip().lower()
        if not org:
            continue
        k = f"{org}|{lookup}"
        prev = keyed.get(k)
        if not prev:
            keyed[k] = r
            continue
        # Keep higher score row.
        prev_score = int(float(prev.get("prospect_score") or 0))
        new_score = int(float(r.get("prospect_score") or 0))
        if new_score > prev_score:
            keyed[k] = r
    deduped = list(keyed.values())
    headers = list(deduped[0].keys()) if deduped else list(rows[0].keys())
    write_csv(PROSPECTS, deduped, headers)
    return len(rows) - len(deduped)


def build_contact_map() -> int:
    rows = []
    seen = set()
    ts = now_iso()

    for r in read_csv(PARTNERS):
        org = (r.get("Org_Name") or "").strip()
        if not org:
            continue
        key = org.lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "org": org,
                "program": "MDARD/MNARD partner outreach",
                "contact_name": (r.get("Contact_Name") or "").strip(),
                "email": (r.get("Email") or "").strip(),
                "phone": (r.get("Phone") or "").strip(),
                "source_url": (r.get("Website") or "").strip(),
                "confidence": "medium",
                "notes": (r.get("Rationale") or "").strip(),
                "last_attempt_ts": "",
                "next_action": "send_intro_or_request_referral",
            }
        )

    for r in read_csv(OUTREACH_LOG):
        org = (r.get("Org_Name") or "").strip()
        if not org:
            continue
        key = org.lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "org": org,
                "program": "MDARD/MNARD partner outreach",
                "contact_name": (r.get("Contact_Name") or "").strip(),
                "email": (r.get("Email") or "").strip(),
                "phone": (r.get("Phone") or "").strip(),
                "source_url": "",
                "confidence": "medium",
                "notes": (r.get("Notes") or "").strip(),
                "last_attempt_ts": (r.get("First_Contact_Date") or "").strip(),
                "next_action": "followup_or_reroute",
            }
        )

    # Force include core MDARD/MNARD anchors if not present.
    anchors = [
        ("MDARD", "Michigan Department of Agriculture and Rural Development", "", "", "https://www.michigan.gov/mdard"),
        ("MDARD Grants", "MDARD grant coordination", "", "", "https://www.michigan.gov/mdardgrants"),
        ("MSU Extension Calhoun", "County extension", "", "269-781-0784", "https://canr.msu.edu/calhoun"),
        ("Calhoun Conservation District", "Conservation district", "", "269-781-4867", "https://www.calhouncd.org"),
        ("USDA NRCS Michigan", "Conservation assistance", "", "", "https://www.nrcs.usda.gov"),
    ]
    for org, notes, email, phone, src in anchors:
        key = org.lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "org": org,
                "program": "MDARD/MNARD partner outreach",
                "contact_name": "",
                "email": email,
                "phone": phone,
                "source_url": src,
                "confidence": "high",
                "notes": notes,
                "last_attempt_ts": ts,
                "next_action": "priority_outreach_today",
            }
        )

    rows = rows[:120]
    rows.sort(key=lambda r: r["org"].lower())
    write_csv(
        CONTACT_MAP,
        rows,
        [
            "org",
            "program",
            "contact_name",
            "email",
            "phone",
            "source_url",
            "confidence",
            "notes",
            "last_attempt_ts",
            "next_action",
        ],
    )
    return len(rows)


def build_templates() -> None:
    txt = "\n".join(
        [
            "# Outreach Email Templates (MDARD/MNARD Today)",
            "",
            "## Partner intro / collaboration",
            "Subject: Michigan regenerative agriculture collaboration (CropCircuit)",
            "",
            "Hi [Name],",
            "I run CropCircuit in Battle Creek and we are coordinating a Michigan regenerative agriculture execution plan tied to grant and partner outcomes.",
            "I’m reaching out to explore a practical collaboration point with [Org] this month.",
            "Would you be open to a brief 15-minute call this week to identify next steps?",
            "",
            "Best,",
            "Casey",
            "CropCircuit",
            "https://cropcircuit.com",
            "",
            "## Grant partner / letter of support request",
            "Subject: Quick letter of support request (CropCircuit / Michigan regenerative ag)",
            "",
            "Hi [Name],",
            "We’re moving a Michigan regenerative ag project forward and would value a short letter of support from [Org].",
            "A 3-5 sentence letter confirming alignment and potential collaboration would materially strengthen this outreach cycle.",
            "If useful, I can send draft language to minimize your time.",
            "",
            "Thank you,",
            "Casey",
            "CropCircuit",
            "https://cropcircuit.com",
            "",
        ]
    )
    TEMPLATES.write_text(txt, encoding="utf-8")


def build_today_queue() -> None:
    txt = "\n".join(
        [
            "# Today Queue (No API Required)",
            "",
            "1. Identify 5 MDARD/MNARD relevant programs/units from `runtime/mdard_contact_map.csv`.",
            "2. Identify 10 priority partner orgs (conservation districts, commodity groups, extension).",
            "3. Draft 10 short outreach emails using `runtime/outreach_email_templates.md`.",
            "4. Send 5 emails if safe channel available; otherwise queue 5 drafts in `runtime/email_reply_queue.md`.",
            "5. Log outcomes in `runtime/partner_prospects_social.csv` and `runtime/mdard_contact_map.csv`.",
            "6. Triage reply routing updates (retired/wrong-contact -> ask for best current contact).",
            "7. Add 10 new partner prospects with lookup queries for next wave.",
            "8. Check HA connectivity and notify Casey if in draft-only mode.",
            "9. Refresh `runtime/top50_ops_sheet.csv` progress markers (manual run-state notes).",
            "10. Generate Casey briefing and persist to runtime with timestamp.",
            "",
            "References:",
            "- `runtime/outreach_email_templates.md`",
            "- `runtime/launch_playbook_48h.md`",
            "- `runtime/top50_ops_sheet.csv`",
        ]
    )
    TODAY_QUEUE.write_text(txt + "\n", encoding="utf-8")


def main() -> int:
    removed = dedupe_partner_prospects()
    rows = build_contact_map()
    build_templates()
    build_today_queue()
    print(
        json.dumps(
            {
                "ok": True,
                "mdard_contact_map_rows": rows,
                "dedup_removed": removed,
                "contact_map": str(CONTACT_MAP),
                "today_queue": str(TODAY_QUEUE),
                "templates": str(TEMPLATES),
            }
        )
    )
    return 0


if __name__ == "__main__":
    import json

    raise SystemExit(main())
