#!/usr/bin/env python3
"""Task helpers for ops_watchdog.sh."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path("/home/asbelcas/cropcircuit")
RUNTIME = ROOT / "runtime"
LOGS = ROOT / "logs"

STATUS_ROLLUP = LOGS / "status_rollup.log"
OPS_ERRORS = LOGS / "ops_errors.log"
WATCHDOG_LOG = LOGS / "ops_watchdog.log"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log_status(line: str) -> None:
    STATUS_ROLLUP.parent.mkdir(parents=True, exist_ok=True)
    STATUS_ROLLUP.open("a", encoding="utf-8").write(f"{now_iso()} {line}\n")


def log_watchdog(line: str) -> None:
    WATCHDOG_LOG.parent.mkdir(parents=True, exist_ok=True)
    WATCHDOG_LOG.open("a", encoding="utf-8").write(f"{now_iso()} {line}\n")


def log_error(line: str) -> None:
    OPS_ERRORS.parent.mkdir(parents=True, exist_ok=True)
    OPS_ERRORS.open("a", encoding="utf-8").write(f"{now_iso()} {line}\n")


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        os.environ.setdefault(k.strip().removeprefix("export ").strip(), v.strip().strip('"').strip("'"))


def check_ha() -> tuple[bool, str]:
    load_env(ROOT / ".env.grant")
    base = os.environ.get("HA_URL", "http://localhost:8123").rstrip("/")
    token = os.environ.get("HA_TOKEN", "").strip()
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(f"{base}/api/config", headers=headers, timeout=6)
        if r.status_code in (401, 403):
            return False, f"auth_error:{r.status_code}"
        if r.ok:
            return True, "ok"
        return False, f"http_{r.status_code}"
    except Exception as e:  # noqa: BLE001
        return False, f"unreachable:{type(e).__name__}"


def check_browser() -> tuple[bool, str]:
    try:
        r = requests.get("http://127.0.0.1:9222/json/version", timeout=4)
        if r.ok:
            return True, "cdp_ok"
        return False, f"cdp_http_{r.status_code}"
    except Exception as e:  # noqa: BLE001
        return False, f"cdp_down:{type(e).__name__}"


def self_check() -> int:
    du = shutil.disk_usage(ROOT)
    free_gb = du.free / (1024 ** 3)
    disk_ok = free_gb > 1.0
    repo_ok = (ROOT / ".git").exists()

    ha_ok, ha_msg = check_ha()
    browser_ok, browser_msg = check_browser()

    key_jobs = {
        "daily_ops_latest": max((RUNTIME.glob("daily_ops_*.md")), default=None),
        "email_triage_status": RUNTIME / "email_triage_status.json",
        "marketplace_liaison_status": RUNTIME / "ai_liaison.marketplace_status.json",
        "mdard_map": RUNTIME / "mdard_contact_map.csv",
    }
    job_stats = {}
    for k, p in key_jobs.items():
        if p and Path(p).exists():
            ts = datetime.fromtimestamp(Path(p).stat().st_mtime, tz=timezone.utc).isoformat()
            job_stats[k] = ts
        else:
            job_stats[k] = "missing"

    if not ha_ok:
        fallback = RUNTIME / "email_reply_queue.md"
        fallback.parent.mkdir(parents=True, exist_ok=True)
        fallback.open("a", encoding="utf-8").write(
            f"\n## HA Unreachable Fallback {now_iso()}\n- Next manual action: send queued drafts when HA auth/connectivity is restored.\n"
        )
        log_watchdog("ha_unreachable_fallback_queue_enabled")

    if not browser_ok:
        manual = RUNTIME / "manual_x_actions.md"
        targets = []
        ops = RUNTIME / "top50_ops_sheet.csv"
        if ops.exists():
            try:
                import csv

                with open(ops, "r", encoding="utf-8", newline="") as fh:
                    for row in csv.DictReader(fh):
                        acct = (row.get("account_handle") or "").strip()
                        if not acct:
                            continue
                        if acct.startswith("RESOLVE::"):
                            q = acct.replace("RESOLVE::", "").strip()
                        else:
                            q = f"@{acct}"
                        targets.append(q)
                        if len(targets) >= 20:
                            break
            except Exception:
                targets = []
        if not targets:
            targets = [
                "Michigan conservation district",
                "MSU Extension Calhoun",
                "USDA NRCS Michigan",
                "MDARD",
                "Michigan Farm Bureau",
            ]
        manual.write_text(
            "\n".join(
                [
                    "# Manual X Actions (Browser/CDP Fallback)",
                    "",
                    "Rules: no mass bursts, execute in waves from launch playbook, stop on rate-limit.",
                    "",
                    "1. Execute Wave A first (credibility anchors), max 5 follows per 30 minutes.",
                    "2. Then Wave B (partnership), max 10 follows per hour.",
                    "3. Then Wave C (amplification), max 10 follows per hour.",
                    "",
                    "Target queries (top 20):",
                    *[f"- {t}" for t in targets],
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    payload = {
        "disk_ok": disk_ok,
        "free_gb": round(free_gb, 2),
        "repo_ok": repo_ok,
        "ha_ok": ha_ok,
        "ha_status": ha_msg,
        "browser_ok": browser_ok,
        "browser_status": browser_msg,
        "key_jobs": job_stats,
    }
    log_status(f"self_check {json.dumps(payload, separators=(',', ':'))}")
    return 0


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    try:
        cp = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=600)
        out = (cp.stdout or "").strip()
        err = (cp.stderr or "").strip()
        msg = out if out else err
        return cp.returncode, msg[:600]
    except Exception as e:  # noqa: BLE001
        return 1, f"{type(e).__name__}:{e}"


def hourly_deep_check() -> int:
    tasks = [
        ("morning_engine", ["python3", "bin/morning_engine.py"]),
        ("mdard_pipeline", ["python3", "bin/mdard_outreach_pipeline.py"]),
        ("email_triage", ["python3", "bin/ha_email_triage.py"]),
        ("marketplace_liaison", ["python3", "bin/ha_marketplace_liaison.py"]),
    ]
    results = []
    for name, cmd in tasks:
        rc, msg = run_cmd(cmd)
        if rc != 0:
            log_error(f"deep_check_task_failed task={name} rc={rc} msg={msg}")
        results.append({"task": name, "rc": rc, "msg": msg})
    log_status(f"hourly_deep_check {json.dumps(results, separators=(',', ':'))}")
    return 0


def casey_briefing() -> int:
    ts = datetime.now(timezone.utc)
    stamp = ts.strftime("%Y-%m-%d_%H%M")
    out = RUNTIME / f"casey_briefing_{stamp}.md"

    contact_map_rows = 0
    cm = RUNTIME / "mdard_contact_map.csv"
    if cm.exists():
        contact_map_rows = max(0, len(cm.read_text(encoding="utf-8").splitlines()) - 1)

    prospects_rows = 0
    pp = RUNTIME / "partner_prospects_social.csv"
    if pp.exists():
        prospects_rows = max(0, len(pp.read_text(encoding="utf-8").splitlines()) - 1)

    email_actions = 0
    ea = RUNTIME / "email_actions.csv"
    if ea.exists():
        email_actions = max(0, len(ea.read_text(encoding="utf-8").splitlines()) - 1)
    marketplace_actions = 0
    ma = RUNTIME / "marketplace_email_actions.csv"
    if ma.exists():
        marketplace_actions = max(0, len(ma.read_text(encoding="utf-8").splitlines()) - 1)

    body = "\n".join(
        [
            f"# Casey Briefing {stamp} UTC",
            "",
            f"- MDARD/MNARD contact map rows: {contact_map_rows}",
            f"- Partner prospects rows: {prospects_rows}",
            f"- Email triage actions logged: {email_actions}",
            f"- Marketplace liaison actions logged: {marketplace_actions}",
            "- Mode: no X API credits; browser/manual queue strategy active",
            "- Next: execute top50 wave actions by timing window",
            "",
        ]
    )
    out.write_text(body, encoding="utf-8")

    # Try HA persistent notification.
    load_env(ROOT / ".env.grant")
    ha_url = os.environ.get("HA_URL", "http://localhost:8123").rstrip("/")
    ha_token = os.environ.get("HA_TOKEN", "").strip()
    if ha_token:
        try:
            requests.post(
                f"{ha_url}/api/services/persistent_notification/create",
                headers={"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"},
                json={"title": "CropCircuit Casey Briefing", "message": body[:3000]},
                timeout=8,
            )
        except Exception:
            pass

    log_status(f"casey_briefing file={out}")
    return 0


def main() -> int:
    import sys

    if len(sys.argv) < 2:
        print("usage: watchdog_tasks.py <self_check|hourly_deep_check|casey_briefing>")
        return 2
    cmd = sys.argv[1]
    if cmd == "self_check":
        return self_check()
    if cmd == "hourly_deep_check":
        return hourly_deep_check()
    if cmd == "casey_briefing":
        return casey_briefing()
    print(f"unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
