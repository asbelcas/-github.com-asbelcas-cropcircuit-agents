#!/usr/bin/env python3
"""Home Assistant relay for NON-MDARD grant submission actions.

Purpose:
- Push immediate submission tasks to Home Assistant for programs marked ready.
- Works for the current FSA microloan and future non-MDARD programs.
- Logs each dispatch attempt for audit/proof.

Notes:
- This does not bypass portal auth/captcha; it creates real-time actionable tasks.
- Use with HA automations or mobile app notifications for human click-through.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
STATUS_MD = ROOT / "grants" / "global_submission_status.md"
LOG_FILE = ROOT / "logs" / "grant_submission_events.jsonl"
STATE_FILE = ROOT / "logs" / "grant_submission_dispatch_state.json"
PROOF_LOG = ROOT / "grants" / "submission_proof_log_non_mdard.csv"


PROGRAM_LINKS: Dict[str, str] = {
    "USDA FSA Operating Microloan": "https://www.fsa.usda.gov/programs-and-services/farm-loan-programs/farm-operating-loans",
    "USDA NRCS EQIP (Michigan)": "https://www.nrcs.usda.gov/programs-initiatives/eqip-environmental-quality-incentives/michigan/environmental-quality-incentives-program-in-michigan",
    "USDA NRCS CSP (Michigan)": "https://www.nrcs.usda.gov/programs-initiatives/csp-conservation-stewardship-program/michigan/conservation-stewardship-program-in-michigan",
    "USDA FSA Direct Operating Loan": "https://www.fsa.usda.gov/programs-and-services/farm-loan-programs/farm-operating-loans",
    "USDA FSA Farm Ownership Loan": "https://www.fsa.usda.gov/resources/farm-loan-programs/farm-ownership-loans",
    "USDA FSA Beginning Farmer Down Payment FO Loan": "https://www.fsa.usda.gov/resources/farm-loan-programs/farm-ownership-loans",
    "USDA FSA FSFL": "https://www.fsa.usda.gov/programs/price-support/facility-loans",
    "USDA REAP": "https://www.rd.usda.gov/programs-services/energy-programs/rural-energy-america-program-renewable-energy-systems-energy-efficiency-improvement-guaranteed-loans",
    "USDA VAPG": "https://www.rd.usda.gov/programs-services/business-programs/value-added-producer-grants",
    "NCR-SARE Farmer Rancher Grant": "https://northcentral.sare.org/grants/apply-for-a-grant/farmer-rancher-grant/",
}

PROGRAM_PACKETS: Dict[str, str] = {
    "USDA FSA Operating Microloan": "grants/submissions/USDA_FSA_Operating_Microloan_packet.md",
    "USDA NRCS EQIP (Michigan)": "grants/submissions/USDA_NRCS_EQIP_MI_packet.md",
    "USDA NRCS CSP (Michigan)": "grants/submissions/USDA_NRCS_CSP_MI_packet.md",
    "USDA FSA Direct Operating Loan": "grants/submissions/USDA_FSA_Direct_Operating_Loan_packet.md",
    "USDA FSA Farm Ownership Loan": "grants/submissions/USDA_FSA_Farm_Ownership_Loan_packet.md",
    "USDA FSA Beginning Farmer Down Payment FO Loan": "grants/submissions/USDA_FSA_Beginning_Farmer_Down_Payment_packet.md",
    "USDA FSA FSFL": "grants/submissions/USDA_FSA_FSFL_packet.md",
    "USDA REAP": "grants/submissions/USDA_REAP_packet.md",
    "USDA VAPG": "grants/submissions/USDA_VAPG_packet.md",
    "NCR-SARE Farmer Rancher Grant": "grants/submissions/NCR_SARE_Farmer_Rancher_packet.md",
}


@dataclass
class ProgramRow:
    program: str
    stage: str
    next_step: str
    expected_window: str

    @property
    def actionable_now(self) -> bool:
        s = self.stage.upper()
        return (
            "IMMEDIATE SUBMISSION QUEUE" in s
            or "FILE NOW" in s
            or "READY TO SUBMIT" in s
            or "READY TO FILE" in s
        )


def parse_status_table(path: Path) -> List[ProgramRow]:
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: List[ProgramRow] = []
    for ln in lines:
        if not ln.startswith("|") or ln.startswith("|---"):
            continue
        parts = [p.strip() for p in ln.strip().strip("|").split("|")]
        if len(parts) < 7:
            continue
        if parts[0].lower() == "program":
            continue
        rows.append(
            ProgramRow(
                program=parts[0],
                stage=parts[3],
                next_step=parts[5],
                expected_window=parts[6],
            )
        )
    return rows


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_state() -> Dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: Dict[str, str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def append_event_log(payload: Dict[str, str]) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def ensure_proof_log() -> None:
    if PROOF_LOG.exists():
        return
    PROOF_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROOF_LOG.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "program", "status", "confirmation #", "screenshot path", "next followup date"])


def dispatch_to_ha(row: ProgramRow, dry_run: bool = False) -> Dict[str, str]:
    packet_rel = PROGRAM_PACKETS.get(row.program, "")
    packet_abs = str((ROOT / packet_rel).resolve()) if packet_rel else "<missing>"
    link = PROGRAM_LINKS.get(row.program, "<missing>")

    if dry_run:
        return {
            "status": "dry_run",
            "program": row.program,
            "submission_link": link,
            "packet_path": packet_abs,
        }

    try:
        cmd = [str(ROOT / "bin" / "ha_dispatch_grant.sh"), "--program", row.program]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            return {"status": "sent", "program": row.program, "detail": proc.stdout.strip()}
        return {"status": "blocked", "program": row.program, "reason": proc.stderr.strip() or proc.stdout.strip()}
    except Exception as exc:
        return {"status": "blocked", "program": row.program, "reason": str(exc)}


def run_once(program_filter: str | None, include_non_actionable: bool, dry_run: bool, force: bool) -> int:
    ensure_proof_log()
    rows = parse_status_table(STATUS_MD)
    state = load_state()
    sent = 0

    for row in rows:
        if program_filter and row.program != program_filter:
            continue
        if not include_non_actionable and not row.actionable_now:
            continue

        stage_key = f"{row.program}::{row.stage}"
        if not force and state.get(row.program) == stage_key:
            continue

        result = dispatch_to_ha(row, dry_run=dry_run)
        append_event_log(
            {
                "timestamp_utc": now_iso(),
                "program": row.program,
                "stage": row.stage,
                "actionable_now": row.actionable_now,
                "result": result,
            }
        )

        if result.get("status") in {"sent", "dry_run"}:
            state[row.program] = stage_key
            sent += 1

    save_state(state)
    return sent


def main() -> int:
    p = argparse.ArgumentParser(description="Real-time HA relay for non-MDARD grant submissions")
    p.add_argument("--program", help="Exact program name to dispatch (e.g., USDA FSA Operating Microloan)")
    p.add_argument("--include-non-actionable", action="store_true", help="Also dispatch queued/future programs")
    p.add_argument("--dry-run", action="store_true", help="Do not call HA; print/record simulated dispatch")
    p.add_argument("--force", action="store_true", help="Dispatch even if same program+stage was already sent")
    p.add_argument("--watch", action="store_true", help="Poll status file and dispatch new/changed entries continuously")
    p.add_argument("--interval", type=int, default=30, help="Watch poll interval seconds (default: 30)")
    args = p.parse_args()

    if args.watch:
        last_mtime = None
        while True:
            try:
                mtime = STATUS_MD.stat().st_mtime
                if last_mtime is None or mtime != last_mtime:
                    count = run_once(args.program, args.include_non_actionable, args.dry_run, args.force)
                    print(f"[{now_iso()}] dispatched={count}")
                    last_mtime = mtime
            except FileNotFoundError:
                print(f"[{now_iso()}] missing status file: {STATUS_MD}")
            time.sleep(max(5, args.interval))
    else:
        count = run_once(args.program, args.include_non_actionable, args.dry_run, args.force)
        print(f"dispatched={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
