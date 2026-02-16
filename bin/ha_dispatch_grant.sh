#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SESSION_FILE="$ROOT_DIR/runtime/grant_intake_session.json"
PROGRAM_OVERRIDE=""
MARK_SUBMITTED=0
CONFIRMATION=""
SCREENSHOT=""
NEXT_FOLLOWUP=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session)
      SESSION_FILE="$2"
      shift 2
      ;;
    --program)
      PROGRAM_OVERRIDE="$2"
      shift 2
      ;;
    --mark-submitted)
      MARK_SUBMITTED=1
      shift
      ;;
    --confirmation)
      CONFIRMATION="$2"
      shift 2
      ;;
    --screenshot)
      SCREENSHOT="$2"
      shift 2
      ;;
    --next-followup)
      NEXT_FOLLOWUP="$2"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.grant"
fi

export ROOT_DIR SESSION_FILE PROGRAM_OVERRIDE MARK_SUBMITTED CONFIRMATION SCREENSHOT NEXT_FOLLOWUP
python3 - <<'PY'
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

root = Path(os.environ["ROOT_DIR"])
session_file = Path(os.environ["SESSION_FILE"])
program_override = os.environ.get("PROGRAM_OVERRIDE", "").strip()
mark_submitted = os.environ.get("MARK_SUBMITTED", "0") == "1"
confirmation = os.environ.get("CONFIRMATION", "").strip()
screenshot = os.environ.get("SCREENSHOT", "").strip()
next_followup = os.environ.get("NEXT_FOLLOWUP", "").strip()

proof_log = root / "grants" / "submission_proof_log_non_mdard.csv"
event_log = root / "logs" / "grant_submission_events.jsonl"
event_log.parent.mkdir(parents=True, exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def ensure_proof():
    if proof_log.exists():
        return
    proof_log.parent.mkdir(parents=True, exist_ok=True)
    with proof_log.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["date", "program", "status", "confirmation #", "screenshot path", "next followup date"])

def append_proof(program: str, status: str, conf: str, shot: str, followup: str):
    ensure_proof()
    with proof_log.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([now_iso(), program, status, conf, shot, followup])

def append_event(payload: dict):
    with event_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")

program_links = {
    "USDA FSA Operating Microloan": "https://www.fsa.usda.gov/programs-and-services/farm-loan-programs/farm-operating-loans",
    "USDA NRCS EQIP (Michigan)": "https://www.nrcs.usda.gov/programs-initiatives/eqip-environmental-quality-incentives/michigan/environmental-quality-incentives-program-in-michigan",
    "USDA NRCS CSP (Michigan)": "https://www.nrcs.usda.gov/programs-initiatives/csp-conservation-stewardship-program/michigan/conservation-stewardship-program-in-michigan",
    "USDA FSA Direct Operating Loan": "https://www.fsa.usda.gov/programs-and-services/farm-loan-programs/farm-operating-loans",
    "USDA FSA Farm Ownership Loan": "https://www.fsa.usda.gov/resources/farm-loan-programs/farm-ownership-loans",
    "USDA FSA Beginning Farmer Down Payment FO Loan": "https://www.fsa.usda.gov/resources/farm-loan-programs/farm-ownership-loans",
    "USDA FSA FSFL": "https://www.fsa.usda.gov/programs/price-support/facility-loans",
}
program_packets = {
    "USDA FSA Operating Microloan": str(root / "grants/submissions/USDA_FSA_Operating_Microloan_packet.md"),
    "USDA NRCS EQIP (Michigan)": str(root / "grants/submissions/USDA_NRCS_EQIP_MI_packet.md"),
    "USDA NRCS CSP (Michigan)": str(root / "grants/submissions/USDA_NRCS_CSP_MI_packet.md"),
    "USDA FSA Direct Operating Loan": str(root / "grants/submissions/USDA_FSA_Direct_Operating_Loan_packet.md"),
    "USDA FSA Farm Ownership Loan": str(root / "grants/submissions/USDA_FSA_Farm_Ownership_Loan_packet.md"),
    "USDA FSA Beginning Farmer Down Payment FO Loan": str(root / "grants/submissions/USDA_FSA_Beginning_Farmer_Down_Payment_packet.md"),
    "USDA FSA FSFL": str(root / "grants/submissions/USDA_FSA_FSFL_packet.md"),
}
docs = [
    "Borrower identification and filing proof",
    "Revenue/financial records",
    "Acreage/production summary",
    "Livestock summary",
    "Prior federal funding disclosure statement",
]

if mark_submitted:
    program = program_override or "UNKNOWN"
    append_proof(program, "submitted", confirmation, screenshot, next_followup)
    append_event({
        "timestamp_utc": now_iso(),
        "event": "grant_mark_submitted",
        "program": program,
        "confirmation": confirmation,
        "screenshot": screenshot,
        "next_followup": next_followup,
    })
    print(f"logged_submission={program}")
    raise SystemExit(0)

session = {}
if session_file.exists():
    try:
        session = json.loads(session_file.read_text(encoding="utf-8"))
    except Exception:
        session = {}

program = program_override or session.get("program") or "USDA FSA Operating Microloan"
portal = session.get("submission_url") or program_links.get(program, "")
packet = session.get("packet_path") or program_packets.get(program, "")
answers = session.get("answers", {})

ha_url = os.environ.get("HA_URL", "").strip()
ha_token = os.environ.get("HA_TOKEN", "").strip()
if not ha_url.startswith("http"):
    ha_url = f"http://{ha_url}" if ha_url else ha_url
ha_url = ha_url.rstrip("/")

message = (
    f"Grant ready for submission\n\n"
    f"Program: {program}\n"
    f"Portal: {portal}\n"
    f"Packet: {packet}\n"
    f"Docs: {', '.join(docs)}\n"
    f"Open portal and submit now.\n"
    f"Then log with: {root}/bin/ha_dispatch_grant.sh --mark-submitted --program \"{program}\" --confirmation \"<id>\" --screenshot \"<path>\" --next-followup \"<YYYY-MM-DD>\""
)

event_payload = {
    "event": "grant_submission_ready",
    "timestamp_utc": now_iso(),
    "program": program,
    "portal_url": portal,
    "packet_path": packet,
    "docs_checklist": docs,
    "answers": answers,
    "actions": [
        {"id": "OPEN_PORTAL", "label": "OPEN PORTAL", "url": portal},
        {"id": "OPEN_PACKET", "label": "OPEN PACKET", "path": packet},
        {"id": "MARK_SUBMITTED", "label": "MARK SUBMITTED"},
        {"id": "NEED_INFO", "label": "NEED INFO"},
    ],
}

result = {"status": "blocked", "reason": "HA_URL/HA_TOKEN missing"}
if ha_url and ha_token:
    try:
        r1 = requests.post(
            f"{ha_url}/api/services/persistent_notification/create",
            headers={"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"},
            json={
                "title": f"Grant ready for submission: {program}",
                "message": message,
                "notification_id": f"grant_ready_{program.lower().replace(' ', '_').replace('(', '').replace(')', '')}",
            },
            timeout=10,
        )
        r1.raise_for_status()
        r2 = requests.post(
            f"{ha_url}/api/events/grant_submission_ready",
            headers={"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"},
            json=event_payload,
            timeout=10,
        )
        r2.raise_for_status()
        result = {"status": "sent", "ha_url": ha_url, "program": program}
    except Exception as exc:
        result = {"status": "blocked", "reason": str(exc), "ha_url": ha_url, "program": program}

append_event({"timestamp_utc": now_iso(), "program": program, "result": result, "payload": event_payload})
print(json.dumps(result))
PY
