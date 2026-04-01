#!/usr/bin/env python3
"""Generate social launch assets and queue payloads for launch_1."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
PROOF = ROOT / "runtime" / "proof_ledger.json"
PROGRESS = ROOT / "runtime" / "milestone_progress.json"
PUBLIC_URL_FILE = ROOT / "runtime" / "donor_public_url.txt"
ASSETS_OUT = ROOT / "runtime" / "social_assets_launch_1.json"
QUEUE_OUT = ROOT / "runtime" / "social_launch_queue.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def main() -> int:
    proof = load_json(PROOF, {})
    summary = proof.get("summary", {}) if isinstance(proof, dict) else {}
    donors = int(summary.get("donors_count", 0) or 0)
    funds = float(summary.get("funds_total", 0) or 0)
    last_action = str(summary.get("last_funded_action", "seed funding in motion"))

    progress = load_json(PROGRESS, {})
    next_gap = float(progress.get("next_gap", 0) or 0)
    next_target = str(progress.get("next_target", "next milestone"))

    public_url = "https://found-tunes-complications-nirvana.trycloudflare.com"
    if PUBLIC_URL_FILE.exists():
        txt = PUBLIC_URL_FILE.read_text(encoding="utf-8").strip()
        if txt:
            public_url = txt
    donor_link = f"{public_url}/go?src=launch_1"
    landing_link = f"{public_url}/?src=launch_1"

    twitter_thread = [
        "Watch a regenerative farm get built in real time.",
        f"{donors} people are already building this farm. ${funds:,.0f} committed. Last action funded: {last_action}.",
        "Michigan anchor: this is a working farm model designed to restore soil, grow real food, and be replicated.",
        "Milestone ladder: $500 soil testing -> $1,200 fencing -> $2,500 irrigation prep -> $5,000 livestock infrastructure.",
        f"Current gap: ${next_gap:,.0f} to {next_target}.",
        f"Watch proof: {landing_link} | Donate: {donor_link}",
    ]

    linkedin_post = (
        "Watch a regenerative farm get built in real time.\n\n"
        f"We already have {donors} supporters and ${funds:,.0f} committed. "
        f"Last action funded: {last_action}.\n\n"
        "This Michigan build focuses on regenerative methods, transparent execution, and a replicable model.\n\n"
        "Milestones:\n"
        "- $500 soil testing\n"
        "- $1,200 fencing\n"
        "- $2,500 irrigation prep\n"
        "- $5,000 livestock infrastructure\n\n"
        f"Current gap: ${next_gap:,.0f} to {next_target}.\n\n"
        f"Proof + progress: {landing_link}\n"
        f"Direct donor link: {donor_link}\n"
    )

    short_form_video_script = (
        "Hook: Watch a regenerative farm get built in real time.\n"
        f"Scene 1: {donors} people are already building this farm. ${funds:,.0f} committed.\n"
        f"Scene 2: Last action funded: {last_action}. Michigan-based, soil-first, real infrastructure.\n"
        "Scene 3: Milestones on screen: $500 soil testing, $1,200 fencing, $2,500 irrigation prep, $5,000 livestock infrastructure.\n"
        f"CTA: Follow progress at {landing_link} and contribute at {donor_link}."
    )

    email_forward_script = (
        "Subject: Watch a regenerative farm get built in real time\n\n"
        "Forward this to one person who cares about food-system resilience.\n\n"
        f"{donors} people are already building this farm and ${funds:,.0f} is committed.\n"
        f"Last action funded: {last_action}.\n\n"
        "Michigan build milestones:\n"
        "- $500 soil testing\n"
        "- $1,200 fencing\n"
        "- $2,500 irrigation prep\n"
        "- $5,000 livestock infrastructure\n\n"
        f"Watch proof: {landing_link}\n"
        f"Direct donor link: {donor_link}\n"
    )

    moment_clip = (
        "This is happening right now. "
        "People are funding soil restoration in Michigan. "
        "You can watch every step."
    )

    payload = {
        "generated_at": now_iso(),
        "tag": "launch_1",
        "links": {"landing": landing_link, "donor": donor_link},
        "metrics_snapshot": {
            "donors": donors,
            "funds": round(funds, 2),
            "last_action_funded": last_action,
            "next_gap": round(next_gap, 2),
            "next_target": next_target,
        },
        "assets": {
            "twitter_thread": twitter_thread,
            "linkedin_post": linkedin_post,
            "short_form_video_script": short_form_video_script,
            "email_forward_script": email_forward_script,
            "moment_clip_15_20s": moment_clip,
        },
    }
    ASSETS_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    queue = load_json(QUEUE_OUT, {"tag": "launch_1", "items": []})
    if not isinstance(queue, dict):
        queue = {"tag": "launch_1", "items": []}
    items = queue.get("items", [])
    if not isinstance(items, list):
        items = []
    items.append(
        {
            "tag": "launch_1",
            "created_at": now_iso(),
            "status": "ready",
            "asset_file": str(ASSETS_OUT),
            "channels": ["twitter", "linkedin", "short_video", "email_forward"],
        }
    )
    queue["tag"] = "launch_1"
    queue["items"] = items[-200:]
    QUEUE_OUT.write_text(json.dumps(queue, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "asset_file": str(ASSETS_OUT), "queue_file": str(QUEUE_OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
