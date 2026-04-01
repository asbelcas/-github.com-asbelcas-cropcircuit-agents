#!/usr/bin/env python3
"""Offline operations cycle: email drafts, MDARD map, outreach targets, heartbeat."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
RUNTIME = ROOT / "runtime"

OUTBOX_DIR = RUNTIME / "outbox_emails"
EMAIL_LOG_FILE = RUNTIME / "email_log.json"
HEARTBEAT_FILE = RUNTIME / "ops_heartbeat.log"
STATE_FILE = RUNTIME / "offline_ops_state.json"

OPP_QUEUE = RUNTIME / "opportunity_queue.json"
OUTREACH_LOG = ROOT / "outreach_log.csv"
PARTNERS = ROOT / "partners_contacts.csv"
PROSPECTS = RUNTIME / "partner_prospects_social.csv"
INFLUENCE = RUNTIME / "influence_rankings_agriculture.json"
FOLLOW_TARGETS = RUNTIME / "follow_targets_agriculture.json"
MDARD_JSON = RUNTIME / "mdard_contact_map.json"
AG_TARGETS_JSON = RUNTIME / "ag_outreach_targets.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []


def sanitize_filename(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", s.strip().lower())
    return s[:80].strip("_") or "draft"


def email_log() -> dict:
    data = read_json(EMAIL_LOG_FILE, {"generated_at": now_iso(), "entries": []})
    if not isinstance(data, dict):
        data = {"generated_at": now_iso(), "entries": []}
    if not isinstance(data.get("entries"), list):
        data["entries"] = []
    return data


def draft_exists(log_entries: list[dict], to_addr: str, subject: str, cls: str) -> bool:
    k = f"{to_addr.lower()}|{subject.lower()}|{cls.lower()}"
    for e in log_entries:
        ek = f"{(e.get('to') or '').lower()}|{(e.get('subject') or '').lower()}|{(e.get('classification') or '').lower()}"
        if ek == k:
            return True
    return False


def write_outbox_draft(to_addr: str, subject: str, body: str) -> Path:
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    name = sanitize_filename(subject)
    h = hashlib.md5(f"{to_addr}|{subject}|{now_iso()}".encode()).hexdigest()[:8]
    p = OUTBOX_DIR / f"{now_stamp()}_{name}_{h}.txt"
    p.write_text(
        "\n".join(
            [
                f"TO: {to_addr}",
                f"SUBJECT: {subject}",
                "",
                body.strip(),
                "",
                "STATUS: queued_send_later",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return p


def build_retired_reply(name: str, topic: str) -> tuple[str, str]:
    subject = "Quick question on the right contact (CropCircuit / regenerative ag)"
    body = (
        f"Hi {name} — thank you for the quick note, and congratulations on retirement.\n"
        "We’re working on a Michigan regenerative agriculture project (CropCircuit) and a related grant / partner outreach effort.\n"
        f"Could you point me to the best current contact for {topic} (or the right inbox), or suggest who I should ask?\n"
        "If it’s easier, I can forward the original message to whoever you recommend.\n"
        "Thanks again,\n"
        "Casey\n"
        "CropCircuit\n"
        "https://cropcircuit.com\n"
    )
    return subject, body


def build_interest_reply(name: str) -> tuple[str, str]:
    return (
        "Great to connect — next step on CropCircuit partnership",
        (
            f"Hi {name},\n\n"
            "Thanks for your note and interest.\n"
            "CropCircuit is a Michigan regenerative agriculture project focused on measurable field execution and partner-aligned outcomes.\n"
            "Would you be open to a short 15-minute call next week to align on collaboration options?\n\n"
            "Best,\nCasey\nCropCircuit\nhttps://cropcircuit.com\n"
        ),
    )


def classify_message(subject: str, body: str) -> str:
    t = (subject + "\n" + body).lower()
    if any(x in t for x in ["retired", "wrong contact", "not correct point of contact", "not the right contact"]):
        return "retired_or_wrong_contact"
    if any(x in t for x in ["interested", "happy to", "yes", "let's connect", "available"]):
        return "interest_or_engagement"
    return "other"


def collect_inbound_candidates() -> list[dict]:
    cands = []
    oq = read_json(OPP_QUEUE, {})
    for o in (oq.get("opportunities", []) if isinstance(oq, dict) else []):
        subj = str(o.get("subject") or "")
        body = str(o.get("snippet") or "")
        if not subj and not body:
            continue
        cands.append(
            {
                "from_name": "there",
                "from_addr": str(o.get("source_email") or ""),
                "subject": subj,
                "body": body,
            }
        )
    # guaranteed known case fallback
    cands.extend(
        [
            {
                "from_name": "MSU Contact 1",
                "from_addr": "msue.calhoun@county.msu.edu",
                "subject": "RE: Following Up — MDARD Regenerative Grant Partnership",
                "body": "retired from MSU / not the correct point of contact",
            },
            {
                "from_name": "MSU Contact 2",
                "from_addr": "baasdean@msu.edu",
                "subject": "RE: MDARD partner outreach",
                "body": "not correct point of contact",
            },
        ]
    )
    return cands


def process_email_triage() -> dict:
    log = email_log()
    entries = log["entries"]
    now = datetime.now(timezone.utc)

    # periodic retry bookkeeping (send-later model, 30m cadence)
    for e in entries:
        if (e.get("status") or "").startswith("queued"):
            nxt = str(e.get("next_retry_at") or "")
            if not nxt:
                e["next_retry_at"] = (now + timedelta(minutes=30)).replace(microsecond=0).isoformat()
                e.setdefault("retry_count", 0)
                continue
            try:
                due = datetime.fromisoformat(nxt.replace("Z", "+00:00"))
                if due <= now:
                    e["retry_count"] = int(e.get("retry_count") or 0) + 1
                    e["status"] = "queued_retry_pending"
                    e["next_retry_at"] = (now + timedelta(minutes=30)).replace(microsecond=0).isoformat()
            except Exception:
                e["next_retry_at"] = (now + timedelta(minutes=30)).replace(microsecond=0).isoformat()

    drafted = 0
    queued = 0
    reviewed_no_action = 0
    for m in collect_inbound_candidates():
        to_addr = (m.get("from_addr") or "").strip().lower()
        if not to_addr or "@" not in to_addr:
            continue
        cls = classify_message(m.get("subject", ""), m.get("body", ""))
        base_subj = str(m.get("subject", "")).strip()
        if cls == "other":
            if not draft_exists(entries, to_addr, base_subj, "other"):
                entries.append(
                    {
                        "timestamp": now_iso(),
                        "to": to_addr,
                        "subject": base_subj,
                        "classification": "other",
                        "status": "reviewed_no_action",
                        "note": "retained_for_manual_review",
                    }
                )
                reviewed_no_action += 1
            continue
        if cls == "retired_or_wrong_contact":
            subject, body = build_retired_reply(m.get("from_name", "there"), "MDARD / MSU partner outreach")
        else:
            subject, body = build_interest_reply(m.get("from_name", "there"))
        if draft_exists(entries, to_addr, subject, cls):
            continue
        path = write_outbox_draft(to_addr, subject, body)
        entries.append(
            {
                "timestamp": now_iso(),
                "to": to_addr,
                "subject": subject,
                "classification": cls,
                "status": "queued_send_later",
                "outbox_path": str(path),
                "retry_after_minutes": 30,
                "next_retry_at": (now + timedelta(minutes=30)).replace(microsecond=0).isoformat(),
                "retry_count": 0,
            }
        )
        drafted += 1
        queued += 1
        if cls == "retired_or_wrong_contact" and drafted >= 2:
            # ensure mandatory two cases are handled quickly.
            continue
    log["generated_at"] = now_iso()
    log["entries"] = entries
    write_json(EMAIL_LOG_FILE, log)
    return {"drafted": drafted, "queued": queued, "reviewed_no_action": reviewed_no_action, "total_entries": len(entries)}


def build_mdard_contact_map() -> int:
    rows = []
    seen = set()

    def add(name: str, role: str, email: str, source: str, confidence: float):
        k = name.strip().lower()
        if not name or k in seen:
            return
        seen.add(k)
        rows.append(
            {
                "name": name,
                "role": role,
                "email": email,
                "confidence_score": round(confidence, 2),
                "source": source,
            }
        )

    for r in read_csv(PARTNERS):
        add(
            (r.get("Org_Name") or "").strip(),
            (r.get("Type") or "partner").strip(),
            (r.get("Email") or "").strip(),
            "partners_contacts.csv",
            0.75,
        )
    for r in read_csv(OUTREACH_LOG):
        add(
            (r.get("Org_Name") or "").strip(),
            (r.get("Type") or "outreach").strip(),
            (r.get("Email") or "").strip(),
            "outreach_log.csv",
            0.7,
        )
    for r in read_csv(PROSPECTS):
        add(
            (r.get("org_name") or "").strip(),
            (r.get("segment") or "prospect").strip(),
            "",
            "partner_prospects_social.csv",
            min(0.95, float(r.get("prospect_score") or 0) / 100 if str(r.get("prospect_score", "")).strip() else 0.65),
        )

    # fallback anchors
    add("MDARD", "agriculture grant coordinators", "", "fallback_anchor", 0.85)
    add("USDA MI Regional", "regional outreach", "", "fallback_anchor", 0.72)
    add("NRCS Michigan", "conservation funding officers", "", "fallback_anchor", 0.8)
    add("MSU Extension", "partnership outreach leads", "", "fallback_anchor", 0.8)

    rows.sort(key=lambda x: (-x["confidence_score"], x["name"].lower()))
    write_json(
        MDARD_JSON,
        {"generated_at": now_iso(), "count": len(rows), "contacts": rows[:300]},
    )
    return len(rows)


def build_ag_outreach_targets() -> int:
    rows = []
    seen = set()
    inf = read_json(INFLUENCE, {})
    for x in inf.get("full_rankings", []) if isinstance(inf, dict) else []:
        handle = (x.get("handle") or "").strip()
        if not handle:
            continue
        if handle.lower() in seen:
            continue
        seen.add(handle.lower())
        cat = x.get("segment") or x.get("org_type") or "agriculture"
        strategy = ((x.get("warm_entry") or {}).get("interaction_channel") or "follow_then_reply")
        rows.append(
            {
                "handle": handle,
                "category": cat,
                "influence_score": int(x.get("influence_score") or 0),
                "engagement_strategy": strategy,
            }
        )
    if not rows:
        ft = read_json(FOLLOW_TARGETS, {})
        for t in ft.get("targets", []) if isinstance(ft, dict) else []:
            h = (t.get("handle") or "").strip()
            if not h or h.lower() in seen:
                continue
            seen.add(h.lower())
            rows.append(
                {
                    "handle": h,
                    "category": t.get("segment", "agriculture"),
                    "influence_score": int(t.get("relevance_score") or 0),
                    "engagement_strategy": "follow_then_reply",
                }
            )
    rows.sort(key=lambda r: (-r["influence_score"], r["handle"].lower()))
    write_json(AG_TARGETS_JSON, {"generated_at": now_iso(), "count": len(rows), "targets": rows[:500]})
    return len(rows)


def heartbeat(progress: dict) -> None:
    state = read_json(STATE_FILE, {"last_progress": {}, "last_ts": ""})
    if not isinstance(state, dict):
        state = {"last_progress": {}, "last_ts": ""}
    last = state.get("last_progress", {}) if isinstance(state.get("last_progress"), dict) else {}

    stalled = []
    for key in ["email_entries", "mdard_contacts", "ag_targets"]:
        if int(progress.get(key, 0)) <= int(last.get(key, 0)):
            stalled.append(key)
    prompts = []
    if stalled:
        prompts = [
            "resume outreach operations",
            "generate next partner contact",
            "process inbox",
            "expand MDARD mapping",
        ]

    line = {
        "ts": now_iso(),
        "progress": progress,
        "stalled": stalled,
        "self_prompts": prompts,
    }
    HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_FILE.open("a", encoding="utf-8").write(json.dumps(line) + "\n")

    state["last_progress"] = progress
    state["last_ts"] = now_iso()
    write_json(STATE_FILE, state)


def main() -> int:
    email_stats = process_email_triage()
    mdard_count = build_mdard_contact_map()
    target_count = build_ag_outreach_targets()
    progress = {
        "email_entries": email_stats["total_entries"],
        "email_drafted_now": email_stats["drafted"],
        "mdard_contacts": mdard_count,
        "ag_targets": target_count,
    }
    heartbeat(progress)
    print(json.dumps({"ok": True, "progress": progress}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
