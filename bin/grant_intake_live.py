#!/usr/bin/env python3
"""Live terminal intake for non-MDARD grant submissions."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "runtime"
SESSION_JSON = RUNTIME_DIR / "grant_intake_session.json"
PROOF_LOG = ROOT / "grants" / "submission_proof_log_non_mdard.csv"

DEFAULT_PROGRAM = "USDA FSA Operating Microloan"
PROGRAM_LINKS = {
    "USDA FSA Operating Microloan": "https://www.fsa.usda.gov/programs-and-services/farm-loan-programs/farm-operating-loans",
}
PROGRAM_PACKETS = {
    "USDA FSA Operating Microloan": ROOT / "grants" / "submissions" / "USDA_FSA_Operating_Microloan_packet.md",
}

DOCS_CHECKLIST = [
    "Borrower identification and filing proof",
    "Revenue/financial records",
    "Acreage/production summary",
    "Livestock summary",
    "Prior federal funding disclosure statement",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def prompt_confirm(label: str) -> str:
    while True:
        print(label)
        val = input("> ").strip()
        print(f"CAPTURED: {val}")
        yn = input("CONFIRM (Y/N)? ").strip().lower()
        if yn == "y":
            return val
        print("Re-entering same field.")


def ensure_proof_log() -> None:
    if PROOF_LOG.exists():
        return
    PROOF_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROOF_LOG.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "program", "status", "confirmation #", "screenshot path", "next followup date"])


def append_packet(session: dict) -> None:
    packet = Path(session["packet_path"])
    if not packet.exists():
        return
    lines = [
        "",
        f"## Live Intake Session ({session['timestamp_utc']})",
        "",
    ]
    for key, value in session["answers"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    packet.write_text(packet.read_text(encoding="utf-8") + "\n".join(lines), encoding="utf-8")


def maybe_open_browser(url: str) -> None:
    opener = None
    for cmd in ("xdg-open", "gio", "open"):
        if subprocess.run(["bash", "-lc", f"command -v {cmd} >/dev/null 2>&1"], check=False).returncode == 0:
            opener = cmd
            break
    if not opener:
        return
    if opener == "gio":
        subprocess.run(["gio", "open", url], check=False)
    else:
        subprocess.run([opener, url], check=False)


def main() -> int:
    p = argparse.ArgumentParser(description="Live grant intake CLI")
    p.add_argument("--program", default=DEFAULT_PROGRAM)
    p.add_argument("--open-browser", action="store_true")
    args = p.parse_args()

    program = args.program
    link = PROGRAM_LINKS.get(program, "https://www.fsa.usda.gov/programs-and-services/farm-loan-programs/farm-operating-loans")
    packet_path = PROGRAM_PACKETS.get(program, ROOT / "grants" / "submissions" / "USDA_FSA_Operating_Microloan_packet.md")

    print("FSA MICROLOAN — LIVE INTAKE STARTED")
    print("Type answer -> press ENTER -> next field loads.")

    fields = [
        "Name",
        "Entity",
        "EIN/SSN",
        "Address",
        "Phone",
        "Email",
        "Acreage",
        "Livestock",
        "Revenue",
        "Requested Amount",
        "Collateral",
        "Docs ready? (Y/N)",
    ]

    answers = {}
    total = len(fields)
    for i, f in enumerate(fields, 1):
        answers[f] = prompt_confirm(f"FIELD {i}/{total}: {f}")

    missing = prompt_confirm(f"FIELD {total+1}/{total+1}: Anything missing")

    session = {
        "timestamp_utc": now_iso(),
        "program": program,
        "submission_url": link,
        "packet_path": str(packet_path),
        "docs_checklist": DOCS_CHECKLIST,
        "answers": answers,
        "anything_missing": missing,
    }

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_JSON.write_text(json.dumps(session, indent=2), encoding="utf-8")
    append_packet(session)
    ensure_proof_log()

    dispatch = ROOT / "bin" / "ha_dispatch_grant.sh"
    subprocess.run([str(dispatch), "--session", str(SESSION_JSON)], check=False)

    if args.open_browser:
        maybe_open_browser(link)

    print("INTAKE CAPTURE COMPLETE — BUILDING SUBMISSION PROFILE")
    print(f"Session saved: {SESSION_JSON}")
    print(f"Packet updated: {packet_path}")
    print(f"Dispatch invoked: {dispatch}")
    print(f"NEXT STEP: Open {link}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
