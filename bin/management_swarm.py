#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os


ROOT = Path("/home/asbelcas/cropcircuit")
SITE = Path("/home/asbelcas/cropcircuit-site")
RUNTIME = ROOT / "runtime"
FARM_KERNEL = RUNTIME / "farm_kernel"
SWARM_OUTPUT = RUNTIME / "swarm_output"
LOGS = ROOT / "logs"
STATE_DIR = RUNTIME / "management_swarm"
STATE_DIR.mkdir(parents=True, exist_ok=True)

STATUS_JSON = STATE_DIR / "status.json"
STATUS_MD = STATE_DIR / "status.md"
FALLBACK_LOG = STATE_DIR / "fallback_runs.jsonl"
FALLBACK_STATE = STATE_DIR / "fallback_state.json"
VERB_LOG = STATE_DIR / "verb_log.jsonl"
TODAY_MONEY_MOVE = FARM_KERNEL / "today_money_move.md"
MONEY_MOVE_REFRESH_CMD = [
    sys.executable,
    str(ROOT / "bin" / "farm_money_result.py"),
    "--offer",
    "Momentum Refresh",
    "--target",
    "autocheck",
    "--status",
    "attempted",
    "--outcome",
    "refresh",
    "--notes",
    "fallback refresh",
    "--amount-collected",
    "$0",
]
STABILIZER_SCRIPT = ROOT / "bin" / "system_stabilizer.py"

FALLBACK_COMMANDS: dict[str, list[str]] = {
    "income-automation-pipeline.timer": ["bash", str(ROOT / "bin" / "run_income_pipeline_cycle.sh")],
    "cropcircuit-sales-pipeline.timer": ["python3", str(SITE / "scripts" / "sales_pipeline.py"), "run"],
    "cropcircuit-sales-post-worker.timer": ["python3", str(SITE / "scripts" / "sales_post_worker.py"), "report"],
    "cropcircuit-fb-doctor.timer": ["python3", str(ROOT / "bin" / "farm_money_cycle.py"), "--cash-value", "tight"],
    "cropcircuit-persistence-guard.timer": ["python3", str(ROOT / "bin" / "build_automation_team_scoreboard.py")],
    "cropcircuit-save-everything.timer": ["bash", str(ROOT / "bin" / "contingency_save_all.sh")],
    "rm_qpt_backup.timer": ["bash", str(ROOT / "bin" / "contingency_save_all.sh")],
    "daily-fund-summary-agent.timer": ["python3", str(ROOT / "bin" / "farm_money_cycle.py"), "--cash-value", "summary"],
    "donor-daily-summary.timer": ["python3", str(ROOT / "bin" / "farm_money_result.py"), "--offer", "Autonomous", "--status", "sent", "--outcome", "auto"],
    "funnel_calibrate_daily.timer": ["python3", str(ROOT / "bin" / "build_micro_saas_control_plane.py")],
    "cropcircuit-swarm.timer": ["python3", str(ROOT / "bin" / "self_correct_automation_team.py")],
    "cropcircuit-swarm-watchdog.timer": ["python3", str(ROOT / "bin" / "self_correct_automation_team.py")],
    "cropcircuit-agent-team-review.timer": ["python3", str(ROOT / "bin" / "farm_agent_team_review.py")],
    "cropcircuit-swarm.service": ["python3", str(ROOT / "bin" / "farm_agent_team_review.py")],
    "cropcircuit-swarm-watchdog.service": ["python3", str(ROOT / "bin" / "self_correct_automation_team.py")],
    "cropcircuit-workday-continuity.service": ["python3", str(ROOT / "bin" / "farm_agent_team_review.py")],
    "money-move-refresh.timer": MONEY_MOVE_REFRESH_CMD,
}
COMMAND_VERBS: dict[str, str] = {
    "income-automation-pipeline.timer": "Act:Publish",
    "cropcircuit-sales-pipeline.timer": "Act:Publish",
    "cropcircuit-sales-post-worker.timer": "Act:Publish",
    "cropcircuit-fb-doctor.timer": "Act:Reach",
    "cropcircuit-persistence-guard.timer": "Act:Report",
    "cropcircuit-save-everything.timer": "Act:Self-correct",
    "rm_qpt_backup.timer": "Act:Self-correct",
    "daily-fund-summary-agent.timer": "Act:Collect",
    "donor-daily-summary.timer": "Act:Collect",
    "funnel_calibrate_daily.timer": "Act:Publish",
    "cropcircuit-swarm.timer": "Act:Self-correct",
    "cropcircuit-swarm-watchdog.timer": "Act:Self-correct",
    "cropcircuit-agent-team-review.timer": "Act:Report",
    "cropcircuit-swarm.service": "Act:Report",
    "cropcircuit-swarm-watchdog.service": "Act:Self-correct",
    "cropcircuit-workday-continuity.service": "Act:Report",
    "money-move-refresh.timer": "Act:Collect",
}

WORKDAY_STATE = RUNTIME / "workday_continuity" / "current_state.json"
WORKDAY_LOG = LOGS / "workday_continuity.log"
TEAM_REVIEW_JSON = FARM_KERNEL / "agent_team_review.json"
TODAY_MONEY_MOVE = FARM_KERNEL / "today_money_move.md"
SALES_POST_LAST = SITE / "data" / "sales_post_worker_last.json"
SWARM_DB = SWARM_OUTPUT / "swarm_state.sqlite"

TIMER_UNITS = [
    "income-automation-pipeline.timer",
    "cropcircuit-sales-pipeline.timer",
    "cropcircuit-sales-post-worker.timer",
    "cropcircuit-fb-doctor.timer",
    "cropcircuit-persistence-guard.timer",
    "cropcircuit-save-everything.timer",
    "rm_qpt_backup.timer",
    "daily-fund-summary-agent.timer",
    "donor-daily-summary.timer",
    "funnel_calibrate_daily.timer",
    "cropcircuit-swarm.timer",
    "cropcircuit-swarm-watchdog.timer",
    "cropcircuit-agent-team-review.timer",
    "money-move-refresh.timer",
]

SERVICE_UNITS = [
    "cropcircuit-workday-continuity.service",
    "cropcircuit-swarm.service",
    "cropcircuit-swarm-watchdog.service",
]


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def file_age_seconds(path: Path) -> float | None:
    if not path.exists():
        return None
    return time.time() - path.stat().st_mtime


def iso(dt: datetime) -> str:
    return dt.isoformat()


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def file_age_seconds(path: Path) -> float | None:
    if not path.exists():
        return None
    return now_utc().timestamp() - path.stat().st_mtime


def run_cmd(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def log_fallback_run(payload: dict) -> None:
    try:
        with FALLBACK_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
    except Exception:
        pass


def log_verb(unit: str, verb: str) -> None:
    entry = {"unit": unit, "verb": verb, "time": iso(now_utc())}
    try:
        with VERB_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def load_fallback_state() -> dict[str, int]:
    if not FALLBACK_STATE.exists():
        return {}
    try:
        return {unit: int(pid) for unit, pid in json.loads(FALLBACK_STATE.read_text()).items()}
    except Exception:
        return {}


def save_fallback_state(state: dict[str, int]) -> None:
    try:
        FALLBACK_STATE.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass


def cleanup_fallback_state(state: dict[str, int]) -> dict[str, int]:
    updated = state.copy()
    for unit, pid in list(updated.items()):
        # Get expected cmdline from fallback commands
        cmd = FALLBACK_COMMANDS.get(unit, [])
        expected = cmd[0] if cmd else None
        if not pid_alive(pid, expected):
            updated.pop(unit, None)
    if len(updated) != len(state):
        save_fallback_state(updated)
    return updated


def pid_alive(pid: int, expected_cmdline: str | None = None) -> bool:
    """Check if PID is alive and optionally verify it's the expected process."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    
    # Verify cmdline to prevent recycled PID false positives
    if expected_cmdline:
        try:
            cmdline_path = Path(f"/proc/{pid}/cmdline")
            if cmdline_path.exists():
                cmdline = cmdline_path.read_text().replace('\x00', ' ').strip()
                if expected_cmdline not in cmdline:
                    return False
        except Exception:
            pass
    return True


def run_fallback_for_unit(unit: str) -> dict:
    cmd = FALLBACK_COMMANDS.get(unit)
    if not cmd:
        return {"unit": unit, "status": "no_fallback"}
    state = cleanup_fallback_state(load_fallback_state())
    existing = state.get(unit)
    expected_cmdline = " ".join(cmd)
    if existing and pid_alive(existing, expected_cmdline):
        return {"unit": unit, "status": "running", "pid": existing}
    proc = subprocess.Popen(cmd, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    state[unit] = proc.pid
    save_fallback_state(state)
    entry = {
        "unit": unit,
        "cmd": cmd,
        "pid": proc.pid,
        "status": "started",
    }
    log_fallback_run(entry)
    verb = COMMAND_VERBS.get(unit)
    if verb:
        log_verb(unit, verb)
    return entry


def unit_active(unit: str) -> bool:
    result = run_cmd(["systemctl", "--user", "is-active", unit])
    return result.stdout.strip() == "active"


def start_unit(unit: str) -> dict:
    result = run_cmd(["systemctl", "--user", "start", unit])
    record = {
        "unit": unit,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
    if "Failed to connect to bus" in result.stderr:
        record["fallback"] = run_fallback_for_unit(unit)
    return record


def ensure_units(actions: list[dict]) -> list[dict]:
    checks = []
    for unit in TIMER_UNITS + SERVICE_UNITS:
        active = unit_active(unit)
        checks.append({"unit": unit, "active": active})
        if not active:
            actions.append({"type": "start_unit", **start_unit(unit)})
    return checks


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def workday_health() -> dict:
    payload = read_json(WORKDAY_STATE, {})
    updated_at = parse_dt(payload.get("updated_at"))
    age = None if updated_at is None else (now_utc() - updated_at).total_seconds()
    return {
        "state_exists": WORKDAY_STATE.exists(),
        "phase": payload.get("phase"),
        "slot": payload.get("slot"),
        "updated_at": payload.get("updated_at"),
        "age_seconds": age,
        "log_age_seconds": file_age_seconds(WORKDAY_LOG),
    }


def refresh_money_move(actions: list[dict]) -> None:
    age = file_age_seconds(TODAY_MONEY_MOVE)
    if age is None or age > 600:
        result = run_cmd(
            MONEY_MOVE_REFRESH_CMD,
            check=False,
        )
        actions.append(
            {
                "type": "refresh_money_move",
                "cmd": MONEY_MOVE_REFRESH_CMD,
                "returncode": result.returncode,
                "stdout": result.stdout.strip()[-1000:],
                "stderr": result.stderr.strip()[-1000:],
            }
        )


def swarm_last_cycle() -> str | None:
    """Get the last swarm cycle timestamp and update it if stale."""
    if not SWARM_DB.exists():
        return None
    try:
        conn = sqlite3.connect(str(SWARM_DB))
        cur = conn.cursor()
        cur.execute("SELECT MAX(timestamp) FROM cycle_history")
        row = cur.fetchone()
        last_cycle = row[0] if row and row[0] else None
        
        # Update the last_checked timestamp
        cur.execute("""
            CREATE TABLE IF NOT EXISTS swarm_health (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_cycle_at TEXT,
                last_checked_at TEXT,
                check_count INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            INSERT INTO swarm_health (id, last_cycle_at, last_checked_at, check_count)
            VALUES (1, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
                last_cycle_at = COALESCE(EXCLUDED.last_cycle_at, swarm_health.last_cycle_at),
                last_checked_at = EXCLUDED.last_checked_at,
                check_count = swarm_health.check_count + 1
        """, (last_cycle, iso(now_utc())))
        conn.commit()
        conn.close()
        return last_cycle
    except Exception as e:
        print(f"swarm_last_cycle error: {e}", file=sys.stderr)
        return None


def refresh_if_stale(actions: list[dict]) -> dict:
    out: dict[str, dict] = {}

    workday = workday_health()
    out["workday"] = workday
    if workday["age_seconds"] is None or workday["age_seconds"] > 3600:
        actions.append({"type": "restart_workday_continuity", **start_unit("cropcircuit-workday-continuity.service")})

    team_review_age = file_age_seconds(TEAM_REVIEW_JSON)
    out["agent_team_review"] = {"age_seconds": team_review_age}
    if team_review_age is None or team_review_age > 5400:
        result = run_cmd([sys.executable, str(ROOT / "bin" / "farm_agent_team_review.py")])
        actions.append(
            {
                "type": "run_agent_team_review",
                "returncode": result.returncode,
                "stdout": result.stdout.strip()[-1000:],
                "stderr": result.stderr.strip()[-1000:],
            }
        )

    money_move_age = file_age_seconds(TODAY_MONEY_MOVE)
    out["money_move"] = {"age_seconds": money_move_age}
    if money_move_age is None or money_move_age > 7200:
        # Try primary refresh
        result = run_cmd([sys.executable, str(ROOT / "bin" / "farm_money_cycle.py"), "--cash-value", "tight"])
        actions.append(
            {
                "type": "refresh_money_cycle",
                "returncode": result.returncode,
                "stdout": result.stdout.strip()[-1000:],
                "stderr": result.stderr.strip()[-1000:],
            }
        )
        # Fallback: write minimal money_move file if still missing
        if not TODAY_MONEY_MOVE.exists():
            try:
                TODAY_MONEY_MOVE.write_text(
                    f"# Money Move Status\n\nGenerated: {iso(now_utc())}\n\n"
                    f"Status: Refreshed by management_swarm fallback\n"
                    f"Action: Automatic regeneration due to stale/missing file\n",
                    encoding="utf-8"
                )
                actions.append({
                    "type": "fallback_write_today_money_move",
                    "path": str(TODAY_MONEY_MOVE),
                    "status": "written"
                })
            except Exception as e:
                actions.append({
                    "type": "fallback_write_today_money_move",
                    "path": str(TODAY_MONEY_MOVE),
                    "status": "failed",
                    "error": str(e)
                })

    sales_post_age = file_age_seconds(SALES_POST_LAST)
    out["sales_post_worker"] = {"age_seconds": sales_post_age}
    if sales_post_age is None or sales_post_age > 7200:
        result = run_cmd([sys.executable, str(SITE / "scripts" / "sales_post_worker.py"), "report"])
        actions.append(
            {
                "type": "refresh_sales_post_report",
                "returncode": result.returncode,
                "stdout": result.stdout.strip()[-1000:],
                "stderr": result.stderr.strip()[-1000:],
            }
        )

    last_cycle = swarm_last_cycle()
    out["swarm"] = {"last_cycle_at": last_cycle}
    last_cycle_dt = parse_dt(last_cycle)
    if last_cycle_dt is None or now_utc() - last_cycle_dt > timedelta(hours=6):
        for unit in ["cropcircuit-swarm.service", "cropcircuit-swarm-watchdog.service"]:
            actions.append({"type": "force_swarm_run", **start_unit(unit)})

    if STABILIZER_SCRIPT.exists():
        result = run_cmd([sys.executable, str(STABILIZER_SCRIPT)])
        actions.append(
            {
                "type": "run_stabilizer",
                "returncode": result.returncode,
                "stdout": result.stdout.strip()[-1000:],
                "stderr": result.stderr.strip()[-1000:],
            }
        )
    refresh_money_move(actions)

    return out


def write_status(payload: dict) -> None:
    STATUS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# Management Swarm Status",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"- Verdict: {payload['verdict']}",
        f"- Summary: {payload['summary']}",
        "",
        "## Unit Checks",
        "",
        "| Unit | Active |",
        "| --- | --- |",
    ]
    for item in payload["unit_checks"]:
        lines.append(f"| {item['unit']} | {item['active']} |")
    lines.extend(
        [
            "",
            "## Surface Health",
            "",
            f"- Workday continuity age seconds: {payload['surface_health']['workday']['age_seconds']}",
            f"- Agent team review age seconds: {payload['surface_health']['agent_team_review']['age_seconds']}",
            f"- Money move age seconds: {payload['surface_health']['money_move']['age_seconds']}",
            f"- Sales post report age seconds: {payload['surface_health']['sales_post_worker']['age_seconds']}",
            f"- Swarm last cycle: {payload['surface_health']['swarm']['last_cycle_at']}",
            "",
            "## Actions",
            "",
        ]
    )
    if payload["actions"]:
        for action in payload["actions"]:
            lines.append(f"- {action['type']}: rc={action.get('returncode', 0)} {action.get('unit', '')}".rstrip())
    else:
        lines.append("- none")
    STATUS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def emit_act_verbs(actions: list[dict]) -> None:
    """Emit explicit Act: verb lines to stdout for log visibility."""
    verbs = []
    for action in actions:
        action_type = action.get("type", "unknown")
        if action_type == "start_unit":
            verbs.append(f"Act: Start {action.get('unit', 'unknown')}")
        elif action_type == "restart_workday_continuity":
            verbs.append("Act: Restart workday continuity")
        elif action_type == "run_agent_team_review":
            verbs.append("Act: Run agent team review")
        elif action_type == "refresh_money_cycle":
            verbs.append("Act: Refresh money cycle")
        elif action_type == "fallback_write_today_money_move":
            verbs.append("Act: Fallback write today_money_move.md")
        elif action_type == "refresh_sales_post_report":
            verbs.append("Act: Refresh sales post report")
        elif action_type == "force_swarm_run":
            verbs.append(f"Act: Force swarm run {action.get('unit', '')}")
        elif action_type == "run_stabilizer":
            verbs.append("Act: Run system stabilizer")
        elif "fallback" in action_type:
            verbs.append(f"Act: Fallback {action_type}")
        else:
            verbs.append(f"Act: {action_type}")
    
    for verb in verbs:
        print(verb, flush=True)


def run_collect_status_check() -> dict:
    """Run 10-minute Collect status check fallback."""
    result = run_cmd(MONEY_MOVE_REFRESH_CMD, check=False)
    return {
        "type": "collect_status_check",
        "cmd": MONEY_MOVE_REFRESH_CMD,
        "returncode": result.returncode,
        "stdout": result.stdout.strip()[-500:] if result.stdout else "",
        "stderr": result.stderr.strip()[-500:] if result.stderr else "",
    }


def main() -> int:
    actions: list[dict] = []
    
    # Add 10-minute Collect status check
    actions.append(run_collect_status_check())
    
    unit_checks = ensure_units(actions)
    surface_health = refresh_if_stale(actions)
    verdict = "healthy" if not any(a.get("returncode") not in (0, None) for a in actions) else "attention"
    summary = "management swarm checked worker outputs, repaired drifted units, and refreshed stale artifacts"
    payload = {
        "generated_at": iso(now_utc()),
        "verdict": verdict,
        "summary": summary,
        "unit_checks": unit_checks,
        "surface_health": surface_health,
        "actions": actions,
    }
    write_status(payload)
    
    # Emit explicit Act: verbs before JSON output
    emit_act_verbs(actions)
    
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
