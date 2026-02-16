#!/usr/bin/env python3
"""Apply morning monetary targets into non-MDARD packet markdown files."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
TARGETS_JSON = ROOT / "runtime" / "morning_targets.json"
STATUS_MD = ROOT / "grants" / "global_submission_status.md"
LOG_FILE = ROOT / "logs" / "targets_apply.log"

PROGRAM_TO_PACKET = {
    "USDA FSA Operating Microloan": ROOT / "grants/submissions/USDA_FSA_Operating_Microloan_packet.md",
    "USDA FSA Direct Operating Loan": ROOT / "grants/submissions/USDA_FSA_Direct_Operating_Loan_packet.md",
    "USDA FSA Farm Ownership Loan": ROOT / "grants/submissions/USDA_FSA_Farm_Ownership_Loan_packet.md",
    "USDA FSA Beginning Farmer Down Payment FO Loan": ROOT / "grants/submissions/USDA_FSA_Beginning_Farmer_Down_Payment_packet.md",
    "USDA FSA FSFL": ROOT / "grants/submissions/USDA_FSA_FSFL_packet.md",
}

BEGIN = "<!-- MORNING_TARGETS_BEGIN -->"
END = "<!-- MORNING_TARGETS_END -->"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_immediate_programs(md_text: str) -> list[str]:
    out = []
    for ln in md_text.splitlines():
        if not ln.startswith("|") or ln.startswith("|---"):
            continue
        parts = [p.strip() for p in ln.strip().strip("|").split("|")]
        if len(parts) < 7:
            continue
        if parts[0].lower() == "program":
            continue
        stage = parts[3].upper()
        if "IMMEDIATE SUBMISSION QUEUE" in stage:
            out.append(parts[0])
    return out


def replace_amount_lines(text: str, amount_usd: int) -> str:
    patterns = [
        r"^- Amount requested.*$",
        r"^- Amount target.*$",
        r"^- Requested microloan amount.*$",
    ]
    for pat in patterns:
        text = re.sub(pat, f"- Amount requested: ${amount_usd:,}", text, flags=re.MULTILINE)
    return text


def upsert_targets_block(text: str, monthly: int, grant_goal: int, req: int) -> str:
    block = (
        f"{BEGIN}\n"
        f"- Requested amount target (USD): ${req:,}\n"
        f"- Monthly stability target (USD): ${monthly:,}\n"
        f"- Grant goal target (USD): ${grant_goal:,}\n"
        f"{END}"
    )
    if BEGIN in text and END in text:
        return re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), block, text, flags=re.DOTALL)
    return text.rstrip() + "\n\n## Morning Monetary Targets\n\n" + block + "\n"


def append_log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main() -> int:
    if not TARGETS_JSON.exists():
        raise SystemExit(f"missing targets file: {TARGETS_JSON}")
    targets = json.loads(TARGETS_JSON.read_text(encoding="utf-8"))
    t = targets.get("targets", {}) if isinstance(targets, dict) else {}
    monthly = int(t.get("monthly_stability_usd", 3000))
    grant_goal = int(t.get("grant_goal_usd", 50000))
    req = int(t.get("requested_amount_usd", 25000))

    immediate = parse_immediate_programs(STATUS_MD.read_text(encoding="utf-8"))
    files_updated = []
    # Always include microloan minimum.
    programs = list(dict.fromkeys(["USDA FSA Operating Microloan"] + immediate))
    for program in programs:
        path = PROGRAM_TO_PACKET.get(program)
        if not path or not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        updated = replace_amount_lines(original, req)
        updated = upsert_targets_block(updated, monthly, grant_goal, req)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            files_updated.append(str(path))

    append_log(
        json.dumps(
            {
                "timestamp_utc": now_iso(),
                "event": "targets_applied",
                "requested_amount_usd": req,
                "monthly_stability_usd": monthly,
                "grant_goal_usd": grant_goal,
                "programs_considered": programs,
                "files_updated": files_updated,
            },
            ensure_ascii=True,
        )
    )
    print(json.dumps({"updated_files": files_updated, "requested_amount_usd": req}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
