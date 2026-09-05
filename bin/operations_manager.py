#!/usr/bin/env python3
"""
Crop Circuit Operations Manager
Local, bounded coordinator for the five-customer, $95 Small Farm Systems Audit pilot.

Design principles:
- Local Linux state remains authoritative.
- No cloud upload of credentials, customer data, or secrets.
- No autonomous public posts, messages, payments, or deliveries.
- Deterministic cheap checks run on schedule; Kimi/Codex invoked only for concrete tasks.
- Every action is logged; every external or customer-facing step requires approval.
"""

from __future__ import annotations

import csv
import email
import email.utils
import imaplib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

# FLORAL CIPHER v2 certificate guard (Claim[X] ≰ Cert[X]).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cert_guard

# Allow importing the existing agent bridge for Codex delegation
sys.path.insert(0, "/home/asbelcas/agent-bridge")

# Local imports only when enabled; bridge_runtime imports other bridge modules.
try:
    from bridge_runtime import start_codex_job, get_codex_job, refresh_codex_job, run_kimi
except Exception as _bridge_import_err:
    start_codex_job = None
    get_codex_job = None
    refresh_codex_job = None
    run_kimi = None


# ---------------------------------------------------------------------------
# Paths and configuration
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(os.environ.get("OPERATIONS_MANAGER_CONFIG", "/home/asbelcas/cropcircuit/pilot_audit/manager/config.json"))


def load_config() -> Dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def manager_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    root = Path(config["manager_dir"])
    return {
        "root": root,
        "state": root / "state.json",
        "audit_log": root / "audit.log",
        "tasks": root / "tasks.jsonl",
        "approvals": root / "approvals.jsonl",
        "diagnostic_approvals": root / "diagnostic_approvals.jsonl",
        "digest": root / "digest.md",
        "incoming": root / "incoming",
        "incoming_sales": root / "incoming_sales",
        "processed_sales": root / "processed_sales",
        "waitlisted_sales": root / "waitlisted_sales",
        "cases": root / "cases",
        "approvals_dir": root / "approvals",
    }


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------


def audit_log(paths: Dict[str, Path], action: str, details: Dict[str, Any]) -> None:
    record = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "details": details,
    }
    paths["audit_log"].parent.mkdir(parents=True, exist_ok=True)
    with paths["audit_log"].open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def load_state(paths: Dict[str, Path]) -> Dict[str, Any]:
    if paths["state"].exists():
        return json.loads(paths["state"].read_text(encoding="utf-8"))
    return {
        "active_cases": 0,
        "completed_cases": 0,
        "revenue_usd": 0.0,
        "slots_remaining": 5,
        "last_check_utc": None,
        "last_digest_utc": None,
        "changes_since_digest": False,
        "daily_cost_usd": 0.0,
        "daily_cost_reset_utc": datetime.utcnow().isoformat() + "Z",
        "monthly_cost_usd": 0.0,
        "monthly_cost_reset_utc": datetime.utcnow().isoformat() + "Z",
        "pending_codex_jobs": [],
        "capacity_pause_notified": False,
    }


def save_state(paths: Dict[str, Path], state: Dict[str, Any]) -> None:
    paths["state"].write_text(json.dumps(state, indent=2), encoding="utf-8")


def _load_env_file(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def notify_casey(config: Dict[str, Any], title: str, message: str, notification_id: str = "cropcircuit_ops") -> bool:
    """Send a Home Assistant persistent notification and Pixel 9 push if HA_TOKEN is configured.

    Checks the process environment first, then the configured env file.
    Falls back to localhost if the configured HA_URL does not resolve.
    The mobile_app push is best-effort; failure does not mark the overall notification failed.
    """
    ha_url = os.environ.get("HA_URL", "")
    ha_token = os.environ.get("HA_TOKEN", "")
    if not ha_url or not ha_token:
        ha_env_path = Path(config.get("ha_env_file", "/home/asbelcas/workforce/cropcircuit_email/.env"))
        env = _load_env_file(ha_env_path)
        ha_url = env.get("HA_URL", ha_url)
        ha_token = env.get("HA_TOKEN", ha_token)
    if not ha_url or not ha_token:
        return False

    # Normalize common local HA names to localhost when they fail to resolve.
    urls_to_try = [ha_url.rstrip("/")]
    if "homeassistant.local" in ha_url or "127.0.0.1" in ha_url:
        urls_to_try.append("http://localhost:8123")
    if "localhost" in ha_url:
        urls_to_try.insert(0, "http://localhost:8123")
    urls_to_try = list(dict.fromkeys(urls_to_try))

    try:
        import urllib.request
        import socket
        persistent_ok = False
        for url in urls_to_try:
            req = urllib.request.Request(
                f"{url}/api/services/persistent_notification/create",
                data=json.dumps({
                    "title": title,
                    "message": message,
                    "notification_id": notification_id,
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {ha_token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    persistent_ok = resp.status == 200
                    break
            except urllib.error.URLError as e:
                if isinstance(e.reason, socket.gaierror):
                    continue
                raise

        # Best-effort push to Casey's primary phone (Pixel 9). Non-fatal if it fails.
        if persistent_ok:
            for url in urls_to_try:
                try:
                    push_req = urllib.request.Request(
                        f"{url}/api/services/notify/mobile_app_pixel_9",
                        data=json.dumps({
                            "title": title,
                            "message": message,
                            "data": {"tag": notification_id},
                        }).encode("utf-8"),
                        headers={
                            "Authorization": f"Bearer {ha_token}",
                            "Content-Type": "application/json",
                        },
                        method="POST",
                    )
                    with urllib.request.urlopen(push_req, timeout=10):
                        pass
                    break
                except urllib.error.URLError as e:
                    if isinstance(e.reason, socket.gaierror):
                        continue
                    break

        return persistent_ok
    except Exception as e:
        # Notification failure is non-fatal; do not leak token.
        return False


# ---------------------------------------------------------------------------
# Pause / kill switch
# ---------------------------------------------------------------------------


def is_paused(config: Dict[str, Any], paths: Dict[str, Path]) -> bool:
    flag = Path(config["pause_flag"])
    if flag.exists():
        reason = flag.read_text(encoding="utf-8").strip() or "pause flag present"
        audit_log(paths, "manager_paused", {"reason": reason})
        return True
    return False


# ---------------------------------------------------------------------------
# Task queue
# ---------------------------------------------------------------------------


def add_task(
    paths: Dict[str, Path],
    task_type: str,
    input_data: Dict[str, Any],
    assignee: str = "manager",
    approval_required: bool = False,
) -> str:
    task_id = f"task_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:6]}"
    task = {
        "task_id": task_id,
        "type": task_type,
        "assignee": assignee,
        "status": "pending",
        "input": input_data,
        "output": None,
        "error": None,
        "retries": 0,
        "approval_required": approval_required,
        "created_at_utc": datetime.utcnow().isoformat() + "Z",
        "updated_at_utc": datetime.utcnow().isoformat() + "Z",
    }
    paths["tasks"].parent.mkdir(parents=True, exist_ok=True)
    with paths["tasks"].open("a", encoding="utf-8") as f:
        f.write(json.dumps(task) + "\n")
    audit_log(paths, "task_created", {"task_id": task_id, "type": task_type, "assignee": assignee})
    return task_id


def update_task(paths: Dict[str, Path], task_id: str, status: str, output: Any = None, error: str = None) -> None:
    if not paths["tasks"].exists():
        return
    lines = []
    updated = False
    with paths["tasks"].open("r", encoding="utf-8") as f:
        for line in f:
            task = json.loads(line)
            if task["task_id"] == task_id:
                task["status"] = status
                if output is not None:
                    task["output"] = output
                if error is not None:
                    task["error"] = error
                task["updated_at_utc"] = datetime.utcnow().isoformat() + "Z"
                updated = True
            lines.append(json.dumps(task))
    if updated:
        paths["tasks"].write_text("\n".join(lines) + "\n", encoding="utf-8")
        audit_log(paths, "task_updated", {"task_id": task_id, "status": status})


# ---------------------------------------------------------------------------
# Approval queue
# ---------------------------------------------------------------------------


def add_approval(
    paths: Dict[str, Path],
    approval_type: str,
    description: str,
    artifact_path: Optional[Path] = None,
    test_case: bool = False,
    dedupe_key: Optional[str] = None,
) -> str:
    queue_path = paths["diagnostic_approvals"] if test_case else paths["approvals"]
    if dedupe_key and queue_path.exists():
        for line in queue_path.read_text(encoding="utf-8").splitlines():
            try:
                existing = json.loads(line)
            except json.JSONDecodeError:
                continue
            if existing.get("dedupe_key") == dedupe_key and existing.get("status") == "pending":
                return existing["approval_id"]
    approval_id = f"appr_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:6]}"
    approval = {
        "approval_id": approval_id,
        "type": approval_type,
        "description": description,
        "status": "pending",
        "artifact_path": str(artifact_path) if artifact_path else None,
        "created_at_utc": datetime.utcnow().isoformat() + "Z",
        "test_case": test_case,
        "dedupe_key": dedupe_key,
    }
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(approval) + "\n")
    # Also write a human-readable approval file
    if artifact_path and not test_case:
        appr_file = paths["approvals_dir"] / f"{approval_id}.md"
        appr_file.parent.mkdir(parents=True, exist_ok=True)
        appr_file.write_text(
            f"# Approval Request: {approval_type}\n\n{description}\n\n"
            f"Artifact: {artifact_path}\n\n"
            f"Status: pending\n\n"
            f"To approve, update the approvals queue or tell the manager to proceed.\n",
            encoding="utf-8",
        )
    audit_log(paths, "approval_created", approval)
    return approval_id


# ---------------------------------------------------------------------------
# Codex / Kimi delegation
# ---------------------------------------------------------------------------


def check_budget(config: Dict[str, Any], state: Dict[str, Any], paths: Dict[str, Path]) -> bool:
    """Return True only if both daily and monthly model-cost ceilings allow spending."""
    now = datetime.utcnow().replace(tzinfo=__import__("datetime").timezone.utc)

    # Daily reset
    daily_reset = datetime.fromisoformat(state["daily_cost_reset_utc"].replace("Z", "+00:00"))
    if (now - daily_reset).total_seconds() >= 86400:
        state["daily_cost_usd"] = 0.0
        state["daily_cost_reset_utc"] = now.isoformat()
        save_state(paths, state)

    # Monthly reset (calendar month)
    monthly_reset = state.get("monthly_cost_reset_utc")
    if monthly_reset:
        monthly_reset = datetime.fromisoformat(monthly_reset.replace("Z", "+00:00"))
    if not monthly_reset or (now.year, now.month) != (monthly_reset.year, monthly_reset.month):
        state["monthly_cost_usd"] = 0.0
        state["monthly_cost_reset_utc"] = now.isoformat()
        save_state(paths, state)

    daily_budget = float(config.get("daily_budget_usd", 1.0))
    monthly_budget = float(config.get("monthly_budget_usd", 10.0))

    if state["daily_cost_usd"] >= daily_budget:
        audit_log(paths, "daily_budget_exceeded", {"spent": state["daily_cost_usd"], "limit": daily_budget})
        return False
    if state.get("monthly_cost_usd", 0.0) >= monthly_budget:
        audit_log(paths, "monthly_budget_exceeded", {"spent": state.get("monthly_cost_usd", 0.0), "limit": monthly_budget})
        return False
    return True


def delegate_codex(
    config: Dict[str, Any],
    paths: Dict[str, Path],
    state: Dict[str, Any],
    task_description: str,
    sandbox: str = "read-only",
) -> Optional[Dict[str, Any]]:
    if not config.get("enable_codex"):
        return None
    if not check_budget(config, state, paths):
        return {"ok": False, "error": "budget exceeded"}
    if start_codex_job is None:
        return {"ok": False, "error": "bridge_runtime import failed"}
    workspace = config.get("bridge_workspace", "/home/asbelcas/cropcircuit")
    try:
        result = start_codex_job(workspace, task_description, sandbox)
        cost = round(0.25, 2)
        state["daily_cost_usd"] = round(state["daily_cost_usd"] + cost, 2)
        state["monthly_cost_usd"] = round(state.get("monthly_cost_usd", 0.0) + cost, 2)
        save_state(paths, state)
        audit_log(paths, "codex_delegated", {"task": task_description[:120], "estimated_cost_usd": cost, "result": {"job_id": result.get("job_id"), "status": result.get("status")}})
        return result
    except Exception as e:
        audit_log(paths, "codex_delegation_failed", {"error": str(e)})
        return {"ok": False, "error": str(e)}


def refresh_pending_codex_jobs(
    config: Dict[str, Any],
    paths: Dict[str, Path],
    state: Dict[str, Any],
) -> None:
    """Check previously delegated Codex jobs and materialize completed drafts."""
    if refresh_codex_job is None:
        return
    pending = state.get("pending_codex_jobs", [])
    if not pending:
        return
    still_pending: List[Dict[str, Any]] = []
    for job_info in pending:
        job_id = job_info.get("job_id")
        customer_id = job_info.get("customer_id")
        run_dir = Path(job_info.get("run_dir", ""))
        if not job_id or not customer_id:
            continue
        try:
            job = refresh_codex_job(job_id)
        except Exception as e:
            audit_log(paths, "codex_job_refresh_failed", {"job_id": job_id, "error": str(e)})
            still_pending.append(job_info)
            continue
        status = job.get("status")
        if status == "completed":
            final_path = run_dir / "final_message.txt"
            draft_text = ""
            if final_path.exists():
                draft_text = final_path.read_text(encoding="utf-8", errors="replace")
            if not draft_text and job.get("final_message"):
                draft_text = job["final_message"]
            case_dir = paths["cases"] / customer_id
            case_dir.mkdir(parents=True, exist_ok=True)
            draft_path = case_dir / "audit_draft.md"
            if not draft_text:
                # Completed but empty: build fallback
                intake_text = ""
                for f in sorted(case_dir.glob("intake_*")):
                    intake_text += "\n\n" + f.read_text(encoding="utf-8", errors="replace")
                template = ""
                template_path = Path(config["audit_template"])
                if template_path.exists():
                    template = template_path.read_text(encoding="utf-8")
                draft_text = (
                    "# Preliminary Audit Draft\n\n"
                    "(Codex returned empty output; use template and intake below to complete manually.)\n\n"
                    + template
                    + "\n\n## Customer Intake\n\n"
                    + intake_text
                )
            draft_path.write_text(draft_text, encoding="utf-8")
            update_case_state(
                config,
                paths,
                customer_id,
                {"current_stage": "draft_ready", "draft_location": str(draft_path)},
            )
            add_approval(
                paths,
                "audit_review",
                f"Preliminary audit draft for {customer_id} is ready for Casey review.",
                artifact_path=draft_path,
            )
            audit_log(paths, "codex_job_completed", {"job_id": job_id, "customer_id": customer_id, "draft_path": str(draft_path)})
        elif status in {"failed", "canceled"}:
            audit_log(paths, "codex_job_failed_or_canceled", {"job_id": job_id, "customer_id": customer_id, "status": status})
            # Fallback draft will be created on next cycle by prepare_audit_draft if needed
            still_pending.append({**job_info, "failed": True})
        else:
            still_pending.append(job_info)
    state["pending_codex_jobs"] = still_pending
    save_state(paths, state)


def delegate_kimi(
    config: Dict[str, Any],
    paths: Dict[str, Path],
    state: Dict[str, Any],
    prompt: str,
    timeout_seconds: int = 120,
) -> Optional[Dict[str, Any]]:
    if not config.get("enable_kimi"):
        return None
    if not check_budget(config, state, paths):
        return {"ok": False, "error": "budget exceeded"}
    if run_kimi is None:
        return {"ok": False, "error": "bridge_runtime import failed"}
    try:
        result = run_kimi(prompt, timeout_seconds=timeout_seconds)
        cost = round(0.10, 2)
        state["daily_cost_usd"] = round(state["daily_cost_usd"] + cost, 2)
        state["monthly_cost_usd"] = round(state.get("monthly_cost_usd", 0.0) + cost, 2)
        save_state(paths, state)
        audit_log(paths, "kimi_delegated", {"prompt": prompt[:120], "estimated_cost_usd": cost, "ok": result.get("ok")})
        return result
    except Exception as e:
        audit_log(paths, "kimi_delegation_failed", {"error": str(e)})
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Case tracker helpers
# ---------------------------------------------------------------------------


def read_case_tracker(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_case_tracker(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    for row in rows[1:]:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def is_test_case(row: Dict[str, str]) -> bool:
    """Return True if the row is marked as a test/fictional case.

    Explicit test_case column is preferred; legacy markers are accepted for
    backward compatibility.
    """
    if row.get("test_case", "").strip().lower() in {"true", "yes", "1"}:
        return True
    if row.get("customer_name", "").strip().lower() == "test customer":
        return True
    cid = row.get("customer_id", "")
    if cid.startswith(("TEST-", "EXAMPLE-", "CODEX-")):
        return True
    notes = (row.get("notes", "") + " " + row.get("primary_goal", "")).lower()
    if "fictional" in notes or "test case" in notes:
        return True
    return False


def is_test_event(event: Dict[str, Any]) -> bool:
    """Return True if a Gumroad sale event is clearly fictional/test data."""
    sale_id = str(event.get("sale_id", ""))
    order_number = str(event.get("order_number", ""))
    email = (event.get("email", "") or "").lower()
    if sale_id.startswith("TEST-") or order_number.startswith("TEST-"):
        return True
    if "@example.com" in email or "@test.local" in email:
        return True
    return False


def separate_test_approvals(paths: Dict[str, Path], rows: List[Dict[str, str]]) -> int:
    """Move explicitly attributable test approvals out of the production queue."""
    if not paths["approvals"].exists():
        return 0
    markers = set()
    for row in rows:
        if not is_test_case(row):
            continue
        markers.update(v for v in (
            row.get("customer_id", ""), row.get("sale_id", ""), row.get("customer_email", "")
        ) if v)
    retained: List[str] = []
    diagnostic: List[Dict[str, Any]] = []
    for line in paths["approvals"].read_text(encoding="utf-8").splitlines():
        try:
            approval = json.loads(line)
        except json.JSONDecodeError:
            retained.append(line)
            continue
        description = approval.get("description", "")
        if approval.get("test_case") is True or any(marker in description for marker in markers):
            approval["test_case"] = True
            diagnostic.append(approval)
        else:
            retained.append(json.dumps(approval))
    if not diagnostic:
        return 0
    existing_ids = set()
    if paths["diagnostic_approvals"].exists():
        for line in paths["diagnostic_approvals"].read_text(encoding="utf-8").splitlines():
            try:
                existing_ids.add(json.loads(line).get("approval_id"))
            except json.JSONDecodeError:
                pass
    with paths["diagnostic_approvals"].open("a", encoding="utf-8") as f:
        for approval in diagnostic:
            if approval.get("approval_id") not in existing_ids:
                f.write(json.dumps(approval) + "\n")
    paths["approvals"].write_text("\n".join(retained) + ("\n" if retained else ""), encoding="utf-8")
    audit_log(paths, "test_approvals_separated", {"count": len(diagnostic)})
    return len(diagnostic)


def update_case_state(
    config: Dict[str, Any],
    paths: Dict[str, Path],
    customer_id: str,
    updates: Dict[str, str],
) -> bool:
    rows = read_case_tracker(Path(config["case_tracker"]))
    updated = False
    for row in rows:
        if row.get("customer_id") == customer_id:
            row.update(updates)
            updated = True
            break
    if updated:
        write_case_tracker(Path(config["case_tracker"]), rows)
        audit_log(paths, "case_tracker_updated", {"customer_id": customer_id, "updates": updates})
    return updated


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def assess_intake_text(text: str) -> str:
    """Conservatively classify intake without treating mere receipt as acceptance."""
    normalized = re.sub(r"\s+", " ", text or "").strip().lower()
    if len(normalized) < 40:
        return "incomplete"
    required_groups = (
        ("region", "location", "county", "state"),
        ("acre", "property size"),
        ("animal", "crop", "enterprise"),
        ("layout", "map", "sketch", "pasture", "garden"),
        ("facility", "equipment", "fencing", "shelter", "barn"),
        ("chore", "workflow", "labor"),
        ("bottleneck", "breakdown", "problem", "frustration"),
        ("safety", "welfare", "accessibility", "seasonal"),
        ("budget", "no-cost", "low-cost", "investment"),
        ("outcome", "goal", "decision"),
    )
    return "complete" if all(any(term in normalized for term in group) for group in required_groups) else "pending_review"


def intake_updates(text: str, observed_at: Optional[str] = None) -> Dict[str, str]:
    status = assess_intake_text(text)
    updates = {
        "intake_status": status,
        "current_stage": "intake_received" if status == "complete" else "intake_pending_review",
    }
    if status == "complete":
        updates["intake_accepted_at_utc"] = observed_at or utc_now_iso()
    return updates


# ---------------------------------------------------------------------------
# Monitoring
# ---------------------------------------------------------------------------


def current_public_url(config: Dict[str, Any]) -> str:
    file_path = Path(config["public_url_file"])
    if file_path.exists():
        return file_path.read_text(encoding="utf-8").strip()
    return "http://127.0.0.1:5000"


def curl_status(url: str) -> int:
    try:
        proc = subprocess.run(
            ["curl", "-s", "-L", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "15", "--max-redirs", "5", url],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return int(proc.stdout.strip() or "0")
    except Exception:
        return 0


def monitor_website(config: Dict[str, Any], paths: Dict[str, Path]) -> Dict[str, Any]:
    public_url = current_public_url(config)
    root_status = curl_status(public_url)
    offer_status = curl_status(public_url.rstrip("/") + config["offer_path"])
    gumroad_status = curl_status(config["gumroad_url"])
    result = {
        "public_url": public_url,
        "root_status": root_status,
        "offer_status": offer_status,
        "gumroad_status": gumroad_status,
    }
    failed = [k for k, v in result.items() if isinstance(v, int) and v != 200 and k != "public_url"]
    if failed:
        audit_log(paths, "monitor_alert", {"failed": failed, **result})
        add_task(paths, "website_check_failed", {"result": result}, assignee="manager")
    return result


def gumroad_remaining_capacity(config: Dict[str, Any]) -> Optional[int]:
    """Try to read remaining pilot capacity from the public Gumroad page."""
    try:
        proc = subprocess.run(
            ["curl", "-s", "-L", "--max-time", "15", "--max-redirs", "5", config["gumroad_url"]],
            capture_output=True,
            text=True,
            timeout=20,
        )
        html = proc.stdout
        # Look for quantity_remaining or max_purchase_count indicators
        m = re.search(r'"quantity_remaining":\s*(\d+)', html)
        if m:
            return int(m.group(1))
        m = re.search(r'"max_purchase_count":\s*(\d+)', html)
        if m:
            return int(m.group(1))
        # Fallback: if sales_limited but no number, return None and rely on case count
        if '"is_sales_limited":true' in html:
            return None
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Business-day deadline
# ---------------------------------------------------------------------------


def add_business_days(start_str: str, days: int) -> str:
    start = datetime.fromisoformat(start_str).date()
    added = 0
    current = start
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Mon-Fri
            added += 1
    return current.isoformat()


def add_business_day_deadline(start: datetime, days: int) -> datetime:
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


# ---------------------------------------------------------------------------
# Intake handling
# ---------------------------------------------------------------------------


def check_incoming(config: Dict[str, Any], paths: Dict[str, Path], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    incoming_dir = paths["incoming"]
    incoming_dir.mkdir(parents=True, exist_ok=True)
    events = []
    for item in sorted(incoming_dir.iterdir()):
        if not item.is_file():
            continue
        text = item.read_text(encoding="utf-8", errors="replace") if item.stat().st_size < 5_000_000 else ""
        # Try to find customer id in filename or contents.
        # Customer IDs generated by the manager are CUST-<safe_local>-<order_suffix>.
        customer_id = None
        cid_pattern = r'(TEST-\d+|EXAMPLE-\d+|CUST-[A-Za-z0-9_-]+|CODEX-\d+)'
        m = re.search(cid_pattern, item.name)
        if m:
            customer_id = m.group(1)
        else:
            m = re.search(cid_pattern, text)
            if m:
                customer_id = m.group(1)
        event = {
            "filename": item.name,
            "path": str(item),
            "customer_id": customer_id,
            "size": item.stat().st_size,
            "test_case": False,
        }
        events.append(event)
        if customer_id:
            case_dir = paths["cases"] / customer_id
            case_dir.mkdir(parents=True, exist_ok=True)
            dest = case_dir / f"intake_{item.name}"
            item.rename(dest)
            rows = read_case_tracker(Path(config["case_tracker"]))
            matched = next((r for r in rows if r.get("customer_id") == customer_id), {})
            test_case = is_test_case(matched)
            event["test_case"] = test_case
            update_case_state(config, paths, customer_id, intake_updates(text))
            if not test_case:
                add_task(paths, "intake_received", {"customer_id": customer_id, "file": str(dest)}, assignee="manager")
            # Manual payment-confirmation gate: never infer payment from the intake file.
            if matched.get("payment_status") != "paid":
                add_approval(
                    paths,
                    "payment_verification_required",
                    f"Intake received for {customer_id}, but payment_status is not 'paid' in the case tracker. "
                    "Please verify the Gumroad purchase in the Gumroad dashboard, then set payment_status to 'paid' "
                    "before any audit drafting begins.",
                    test_case=test_case,
                    dedupe_key=f"payment-verification:{customer_id}",
                )
        else:
            add_task(paths, "unmatched_intake", {"filename": item.name}, assignee="manager")
            add_approval(paths, "unmatched_intake", f"Intake file {item.name} could not be matched to a case.")
        audit_log(paths, "incoming_processed", event)
    return events


def check_incoming_sales(config: Dict[str, Any], paths: Dict[str, Path], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process unverified Gumroad sale events written by the webhook route.

    These events are treated as signals only. Payment is never auto-verified.
    A new case row is created with payment_status=unverified and an approval
    request is queued for Casey to confirm the sale in the Gumroad dashboard.
    """
    sales_dir = paths["incoming_sales"]
    sales_dir.mkdir(parents=True, exist_ok=True)
    events: List[Dict[str, Any]] = []
    rows = read_case_tracker(Path(config["case_tracker"]))
    paths["processed_sales"].mkdir(parents=True, exist_ok=True)

    for item in sorted(sales_dir.iterdir()):
        if not item.is_file() or not item.suffix == ".json":
            continue
        try:
            event = json.loads(item.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            audit_log(paths, "incoming_sale_parse_failed", {"filename": item.name})
            continue

        sale_id = event.get("sale_id")
        email = (event.get("email", "") or "").lower().strip()
        order_number = event.get("order_number")
        # Deduplicate by sale_id
        existing = next((r for r in rows if r.get("sale_id") == sale_id), None)
        if existing:
            audit_log(paths, "incoming_sale_duplicate", {"sale_id": sale_id})
            archived = paths["processed_sales"] / item.name
            if not archived.exists():
                item.rename(archived)
            continue
        events.append({
            "filename": item.name,
            "sale_id": sale_id,
            "email": email,
            "order_number": order_number,
            "test_case": is_test_event(event),
        })

        # Preserve every legitimate signal. A full pilot creates a reversible hold,
        # not an untracked sixth fulfillment case.
        recalculate_capacity(config, paths, state)
        capacity_hold = not is_test_event(event) and state["slots_remaining"] <= 0

        # Generate a customer_id from email or order number
        local_part = email.split("@")[0] if email and "@" in email else "customer"
        safe_local = re.sub(r"[^a-z0-9_-]+", "_", local_part).strip("_")[:30]
        customer_id = f"CUST-{safe_local}-{order_number or sale_id[-6:]}"

        # Ensure unique customer_id in tracker
        suffix = 1
        base_customer_id = customer_id
        while any(r.get("customer_id") == customer_id for r in rows):
            customer_id = f"{base_customer_id}-{suffix}"
            suffix += 1

        new_row = {
            "customer_id": customer_id,
            "received_date": datetime.utcnow().date().isoformat(),
            "due_date": "",
            "customer_name": event.get("full_name", ""),
            "farm_name": "",
            "region": event.get("country", ""),
            "primary_goal": "Small Farm Systems Audit purchase",
            "payment_status": "unverified",
            "intake_status": "incomplete",
            "current_stage": "capacity_hold" if capacity_hold else "new",
            "missing_info": "",
            "draft_location": "",
            "casey_approval_status": "",
            "delivery_status": "",
            "delivery_date": "",
            "followup_status": "",
            "notes": f"Gumroad sale signal. sale_id={sale_id}, email={email}. Verify in Gumroad dashboard before marking paid.",
            "test_case": "true" if is_test_event(event) else "false",
            "sale_id": sale_id,
            "order_number": order_number or "",
            "customer_email": email,
        }

        # Add columns that may not exist in older tracker files
        fieldnames = list(rows[0].keys()) if rows else list(new_row.keys())
        for key in new_row:
            if key not in fieldnames:
                fieldnames.append(key)
        for row in rows:
            for key in fieldnames:
                row.setdefault(key, "")
        for key in fieldnames:
            new_row.setdefault(key, "")

        rows.append(new_row)
        write_case_tracker(Path(config["case_tracker"]), rows)
        rows = read_case_tracker(Path(config["case_tracker"]))

        add_approval(
            paths,
            "payment_verification_required",
            f"Gumroad sale signal received for {customer_id} (sale_id={sale_id}, email={email}). "
            "Please verify this purchase in the Gumroad dashboard, then set payment_status to 'paid' "
            "in the case tracker.",
            test_case=is_test_event(event),
            dedupe_key=f"payment-verification:{sale_id}",
        )
        if capacity_hold:
            add_approval(
                paths,
                "capacity_hold",
                f"Pilot capacity is full. Signal {sale_id} is preserved on capacity hold and needs human resolution.",
                dedupe_key=f"capacity-hold:{sale_id}",
            )
            audit_log(paths, "incoming_sale_capacity_hold", {"customer_id": customer_id, "sale_id": sale_id})
        audit_log(paths, "incoming_sale_recorded", {"customer_id": customer_id, "sale_id": sale_id, "email": email})
        item.rename(paths["processed_sales"] / item.name)

    return events


# ---------------------------------------------------------------------------
# Gumroad API payment verification
# ---------------------------------------------------------------------------


def _gumroad_access_token(config: Dict[str, Any]) -> str:
    env = _load_env_file(Path(config.get("gumroad_env_file", "/home/asbelcas/workforce/.env")))
    return env.get("GUMROAD_ACCESS_TOKEN", "").strip()


def _gumroad_api_get(config: Dict[str, Any], endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Make an authenticated GET to the Gumroad API. Never logs the token."""
    token = _gumroad_access_token(config)
    if not token:
        raise RuntimeError("GUMROAD_ACCESS_TOKEN not configured")
    import urllib.request
    import urllib.parse

    base = "https://api.gumroad.com"
    url = base + endpoint
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "cropcircuit-local",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def verify_payment_via_gumroad_api(
    config: Dict[str, Any],
    email: str,
    sale_id: Optional[str] = None,
    order_number: Optional[str] = None,
    after_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """Return {'verified': bool, ...} after querying Gumroad's authenticated API.

    Agreement required: product, price, currency, sale/order identity, and that the
    sale is not refunded/chargebacked/cancelled.
    """
    product_id = config.get("gumroad_product_id")
    expected_price = int(config.get("gumroad_expected_price_cents", 9500))
    if not product_id or not email or "@" not in email:
        return {"verified": False, "reason": "missing product_id or email"}
    params: Dict[str, str] = {"product_id": product_id, "email": email.lower().strip()}
    if after_utc:
        params["after"] = after_utc
    try:
        data = _gumroad_api_get(config, "/v2/sales", params)
    except Exception as e:
        return {"verified": False, "reason": f"api_error: {type(e).__name__}"}

    sales = data.get("sales", []) or []
    for sale in sales:
        s_id = str(sale.get("sale_id", "") or "").strip()
        o_id = str(sale.get("order_number", "") or "").strip()
        price_raw = sale.get("price") or sale.get("price_cents") or 0
        try:
            price_cents = int(price_raw)
        except (ValueError, TypeError):
            price_cents = 0
        currency = (sale.get("currency", "") or "").lower()
        refunded = bool(sale.get("refunded")) or bool(sale.get("chargebacked")) or bool(sale.get("cancelled"))

        identity_match = False
        if sale_id and s_id == sale_id:
            identity_match = True
        if order_number and o_id == order_number:
            identity_match = True

        if identity_match:
            if price_cents != expected_price:
                return {"verified": False, "reason": f"price_mismatch: {price_cents}", "sale": sale}
            if currency != "usd":
                return {"verified": False, "reason": f"currency_mismatch: {currency}", "sale": sale}
            if refunded:
                return {"verified": False, "reason": "sale_refunded_or_chargebacked", "sale": sale}
            return {"verified": True, "sale": sale}
    return {"verified": False, "reason": "no_matching_sale", "matches_checked": len(sales)}


def check_gumroad_api_verification(config: Dict[str, Any], paths: Dict[str, Path], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Verify unverified cases against the Gumroad API and mark paid when confirmed."""
    if not config.get("enable_gumroad_api_verify"):
        return []

    rows = [r for r in read_case_tracker(Path(config["case_tracker"])) if not is_test_case(r)]
    results: List[Dict[str, Any]] = []
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    throttle_seconds = 300
    last_checks = state.setdefault("gumroad_verification_last_check", {})

    for row in rows:
        if row.get("payment_status") != "unverified":
            continue
        email = (row.get("customer_email", "") or "").lower().strip()
        sale_id = row.get("sale_id", "")
        order_number = row.get("order_number", "")
        customer_id = row.get("customer_id", "")
        if not email or not sale_id:
            continue

        last_check = last_checks.get(sale_id)
        if last_check:
            try:
                last_dt = datetime.fromisoformat(last_check.replace("Z", "+00:00"))
                if (now - last_dt).total_seconds() < throttle_seconds:
                    continue
            except Exception:
                pass

        result = verify_payment_via_gumroad_api(config, email, sale_id, order_number)
        last_checks[sale_id] = now.isoformat()
        results.append({"customer_id": customer_id, "sale_id": sale_id, "result": result})

        if result.get("verified"):
            # Re-check capacity before confirming payment; do not exceed pilot limit.
            recalculate_capacity(config, paths, state)
            if state["slots_remaining"] <= 0:
                update_case_state(config, paths, customer_id, {
                    "payment_status": "paid",
                    "payment_verified_at_utc": now.isoformat().replace("+00:00", "Z"),
                    "current_stage": "capacity_hold",
                    "due_date": "",
                    "fulfillment_deadline_at": "",
                })
                audit_log(
                    paths,
                    "payment_verification_capacity_full",
                    {"customer_id": customer_id, "sale_id": sale_id},
                )
                add_approval(
                    paths,
                    "capacity_full",
                    f"Payment verified via Gumroad API for {customer_id}, but pilot capacity is full. "
                    "Case is verified and held outside fulfillment. Review before releasing the slot.",
                    dedupe_key=f"capacity-hold:{sale_id}",
                )
                continue
            update_case_state(config, paths, customer_id, {
                "payment_status": "paid",
                "payment_verified_at_utc": now.isoformat().replace("+00:00", "Z"),
            })
            add_approval(
                paths,
                "payment_verified_via_api",
                f"Payment for {customer_id} verified via Gumroad API (sale_id={sale_id}, order_number={order_number}).",
            )
            audit_log(
                paths,
                "payment_verified_via_api",
                {"customer_id": customer_id, "sale_id": sale_id, "order_number": order_number},
            )
        else:
            audit_log(
                paths,
                "payment_verification_api_failed",
                {"customer_id": customer_id, "sale_id": sale_id, "reason": result.get("reason")},
            )

    save_state(paths, state)
    return results


# ---------------------------------------------------------------------------
# Bounded IMAP intake polling
# ---------------------------------------------------------------------------


def _imap_login(config: Dict[str, Any]) -> imaplib.IMAP4_SSL:
    env = _load_env_file(Path(config.get("imap_env_file", "/home/asbelcas/workforce/cropcircuit_email/.env")))
    password = env.get("GMAIL_APP_PASSWORD", "").strip()
    mailbox = config.get("imap_mailbox", "asbelcas@gmail.com")
    server = config.get("imap_server", "imap.gmail.com")
    if not password or not mailbox:
        raise RuntimeError("IMAP credentials not configured")
    mail = imaplib.IMAP4_SSL(server)
    resp, _ = mail.login(mailbox, password)
    if resp != "OK":
        raise RuntimeError("IMAP login failed")
    return mail


def _decode_mime_header(value: str) -> str:
    parts = decode_header(value)
    out = []
    for part, charset in parts:
        if isinstance(part, bytes):
            out.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            out.append(part)
    return " ".join(out)


def _allowed_attachment(ext: str) -> bool:
    return ext.lower().lstrip(".") in {"jpg", "jpeg", "png", "gif", "webp", "pdf"}


def _sanitize_attachment_filename(name: str) -> str:
    base = os.path.basename(name)
    name_no_ext, ext = os.path.splitext(base)
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", name_no_ext).strip("_")[:60]
    ext = re.sub(r"[^.a-zA-Z0-9]", "", ext).lower()
    if not _allowed_attachment(ext):
        ext = ".quarantine"
    return f"{safe_name or 'attachment'}{ext}"


def _extract_email_body(msg: email.message.Message) -> str:
    body_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition", "")).lower()
            if "attachment" in cdisp:
                continue
            if ctype == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body_text += payload.decode("utf-8", errors="replace")
            elif ctype == "text/html" and not body_text:
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode("utf-8", errors="replace")
                    body_text += re.sub(r"<[^>]+>", " ", html)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body_text = payload.decode("utf-8", errors="replace")
    return body_text.strip()


def _save_email_attachments(
    msg: email.message.Message,
    case_dir: Path,
    quarantine_dir: Path,
) -> Dict[str, List[str]]:
    saved: List[str] = []
    quarantined: List[str] = []
    if not msg.is_multipart():
        return {"saved": saved, "quarantined": quarantined}
    for part in msg.walk():
        cdisp = str(part.get("Content-Disposition", "")).lower()
        if "attachment" not in cdisp:
            continue
        filename = part.get_filename()
        if not filename:
            continue
        ext = os.path.splitext(filename)[1].lstrip(".").lower()
        payload = part.get_payload(decode=True) or b""
        if _allowed_attachment(ext):
            safe = _sanitize_attachment_filename(filename)
            att_dir = case_dir / "attachments"
            att_dir.mkdir(parents=True, exist_ok=True)
            att_path = att_dir / safe
            att_path.write_bytes(payload)
            saved.append(str(att_path))
        else:
            safe = _sanitize_attachment_filename(filename) + ".quarantine"
            quarantine_dir.mkdir(parents=True, exist_ok=True)
            q_path = quarantine_dir / safe
            q_path.write_bytes(payload)
            quarantined.append(str(q_path))
    return {"saved": saved, "quarantined": quarantined}


def check_email_intake(config: Dict[str, Any], paths: Dict[str, Path], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Poll Gmail for unread Small Farm Systems Audit intake replies.

    Does not delete, archive, label, forward, mark read, or reply to messages.
    Deduplicates by Message-ID so the same message is processed once.
    """
    if not config.get("enable_imap_intake"):
        return []

    # Back off after repeated IMAP auth failures so a dead credential cannot
    # hammer the provider (risking account lockout) every poll cycle.
    now = datetime.now(timezone.utc)
    pause_until = state.get("imap_failure_pause_until_utc")
    if pause_until:
        try:
            if datetime.fromisoformat(pause_until) > now:
                events = [{
                    "type": "intake_channel_failed",
                    "error": "paused",
                    "message": f"IMAP intake paused until {pause_until} after repeated auth failures",
                }]
                return events
        except (TypeError, ValueError):
            state.pop("imap_failure_pause_until_utc", None)

    processed = set(state.get("processed_email_message_ids", []))
    rows = read_case_tracker(Path(config["case_tracker"]))
    events: List[Dict[str, Any]] = []
    try:
        mail = _imap_login(config)
        state["imap_consecutive_auth_failures"] = 0
        mail.select("inbox")
        # Bounded query: unread messages whose subject contains the audit name.
        typ, data = mail.search(None, '(UNSEEN SUBJECT "Small Farm Systems Audit")')
        msg_ids = data[0].split()
        for msg_id in msg_ids:
            typ2, msg_data = mail.fetch(msg_id, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            msg_id_header = (msg.get("Message-ID", "") or "").strip()
            if msg_id_header and msg_id_header in processed:
                continue

            from_header = msg.get("From", "")
            from_email = email.utils.parseaddr(from_header)[1].lower().strip()
            subject_header = _decode_mime_header(msg.get("Subject", ""))

            matches = [r for r in rows if (r.get("customer_email", "") or "").lower().strip() == from_email]
            event: Dict[str, Any] = {
                "message_id": msg_id_header,
                "from": from_email,
                "subject": subject_header,
            }

            if len(matches) == 0:
                add_approval(
                    paths,
                    "intake_unmatched",
                    f"Intake email from {from_email} could not be matched to a case. Subject: {subject_header[:80]}",
                )
                audit_log(paths, "email_intake_unmatched", {"from": from_email, "subject": subject_header[:80]})
                events.append(event)
            elif len(matches) > 1:
                cids = [r["customer_id"] for r in matches]
                add_approval(
                    paths,
                    "ambiguous_match",
                    f"Intake email from {from_email} matches multiple cases ({cids}). Subject: {subject_header[:80]}",
                )
                audit_log(paths, "email_intake_ambiguous", {"from": from_email, "cases": cids})
                events.append(event)
            else:
                row = matches[0]
                cid = row["customer_id"]
                test_case = is_test_case(row)
                case_dir = paths["cases"] / cid
                case_dir.mkdir(parents=True, exist_ok=True)

                body_text = _extract_email_body(msg)
                att_result = _save_email_attachments(msg, case_dir, paths["root"] / "quarantine")

                safe_msg_id = re.sub(r"[^A-Za-z0-9_-]+", "_", msg_id_header or str(msg_id, "utf-8"))[:80]
                intake_path = case_dir / f"intake_email_{safe_msg_id}.md"
                intake_path.write_text(
                    f"# Intake email from {from_email}\n\n"
                    f"**Subject:** {subject_header}\n\n"
                    f"**Message-ID:** {msg_id_header}\n\n"
                    f"{body_text}",
                    encoding="utf-8",
                )
                update_case_state(config, paths, cid, intake_updates(body_text))
                if not test_case:
                    add_task(
                        paths,
                        "intake_received",
                        {"customer_id": cid, "source": "imap", "file": str(intake_path)},
                        assignee="manager",
                    )
                event["matched"] = cid
                event["test_case"] = test_case
                events.append(event)
                audit_log(
                    paths,
                    "email_intake_matched",
                    {
                        "customer_id": cid,
                        "from": from_email,
                        "subject": subject_header[:80],
                        "attachments_saved": len(att_result["saved"]),
                        "attachments_quarantined": len(att_result["quarantined"]),
                    },
                )

            if msg_id_header:
                processed.add(msg_id_header)
        mail.logout()
    except Exception as e:
        audit_log(paths, "email_intake_failed", {"error": type(e).__name__, "message": str(e)})
        if "AUTHENTICATIONFAILED" in str(e):
            failures = int(state.get("imap_consecutive_auth_failures", 0)) + 1
            state["imap_consecutive_auth_failures"] = failures
            if failures >= 10:
                paused_until = (now + timedelta(hours=24)).isoformat()
                state["imap_failure_pause_until_utc"] = paused_until
                audit_log(paths, "imap_auth_pause_engaged", {
                    "consecutive_failures": failures,
                    "paused_until_utc": paused_until,
                })
        # Surface channel failure to the digest (once per cycle) so a broken
        # intake path is not silently invisible in audit.log only.
        events.append({
            "type": "intake_channel_failed",
            "error": type(e).__name__,
            "message": str(e)[:200],
        })

    state["processed_email_message_ids"] = sorted(processed)
    save_state(paths, state)
    return events


# ---------------------------------------------------------------------------
# Draft preparation
# ---------------------------------------------------------------------------


def prepare_missing_intake_message(customer_id: str) -> str:
    return (
        f"Hi—thank you for purchasing the Small Farm Systems Audit. "
        f"Case {customer_id} is open, but I don’t yet have a complete intake. "
        f"Please reply with: property region/acreage, layout photo or sketch, "
        f"animals or crops, facilities and equipment, chore sequence, biggest bottleneck, "
        f"safety/welfare concerns, budget range, and desired outcome. "
        f"Delivery starts after both payment and a sufficiently complete intake are received."
    )


def prepare_acknowledgement(customer_id: str) -> str:
    return (
        f"Hi—your intake for case {customer_id} is received. "
        f"I’ll confirm scope within one business day, and the written audit will follow "
        f"within three business days after that confirmation."
    )


def prepare_audit_draft(
    config: Dict[str, Any],
    paths: Dict[str, Path],
    state: Dict[str, Any],
    customer_id: str,
) -> Optional[Path]:
    case_dir = paths["cases"] / customer_id
    intake_files = list(case_dir.glob("intake_*"))
    if not intake_files:
        return None
    intake_text = "\n\n".join(f.read_text(encoding="utf-8", errors="replace") for f in intake_files)
    template_path = Path(config["audit_template"])
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

    pending = state.get("pending_codex_jobs", [])
    existing = next((j for j in pending if j.get("customer_id") == customer_id), None)
    if existing and not existing.get("failed"):
        # Still waiting on a live Codex job; refresh_pending_codex_jobs will handle it.
        audit_log(paths, "audit_draft_deferred", {"customer_id": customer_id, "job_id": existing.get("job_id")})
        return None

    max_retries = int(config.get("max_retries", 2))
    if existing and existing.get("failed"):
        if existing.get("retries", 0) >= max_retries:
            audit_log(paths, "audit_draft_retry_exhausted", {"customer_id": customer_id, "job_id": existing.get("job_id")})
            # Remove exhausted job so we produce a fallback draft now
            pending = [j for j in pending if j.get("customer_id") != customer_id]
            state["pending_codex_jobs"] = pending
            save_state(paths, state)
            existing = None
        else:
            existing["retries"] = existing.get("retries", 0) + 1
            existing["failed"] = False
            # fall through to start a new job below

    # Prefer Codex to synthesize a draft from template + intake
    task = (
        "Using the following audit template and customer intake, produce a preliminary "
        "ten-section Small Farm Systems Audit. Do not invent credentials, testimonials, or results. "
        "Use only the information provided. Output plain markdown.\n\n"
        "=== AUDIT TEMPLATE ===\n" + template + "\n\n"
        "=== CUSTOMER INTAKE ===\n" + intake_text
    )
    result = delegate_codex(config, paths, state, task, sandbox="read-only")
    draft_text = ""
    if result and result.get("ok"):
        job_id = result.get("job_id")
        run_dir = Path(result.get("run_dir", ""))
        if job_id and run_dir:
            job_info = {
                "job_id": job_id,
                "customer_id": customer_id,
                "run_dir": str(run_dir),
                "retries": existing.get("retries", 0) if existing else 0,
                "failed": False,
            }
            pending = state.get("pending_codex_jobs", [])
            pending = [j for j in pending if j.get("customer_id") != customer_id]
            pending.append(job_info)
            state["pending_codex_jobs"] = pending
            save_state(paths, state)
        # Poll briefly for quick completion
        if job_id and get_codex_job is not None:
            for _ in range(6):
                time.sleep(5)
                if refresh_codex_job is not None:
                    try:
                        job = refresh_codex_job(job_id)
                    except Exception:
                        job = get_codex_job(job_id)
                else:
                    job = get_codex_job(job_id)
                if job.get("status") in {"completed", "failed", "canceled"}:
                    break
            final_path = run_dir / "final_message.txt"
            if final_path.exists():
                draft_text = final_path.read_text(encoding="utf-8", errors="replace")
    if not draft_text:
        # Codex not ready or not enabled: leave pending for refresh on next cycle
        if state.get("pending_codex_jobs") and any(j.get("customer_id") == customer_id for j in state["pending_codex_jobs"]):
            audit_log(paths, "audit_draft_pending", {"customer_id": customer_id})
            return None
        draft_text = (
            "# Preliminary Audit Draft\n\n"
            "(Codex did not return output; use template and intake below to complete manually.)\n\n"
            + template
            + "\n\n## Customer Intake\n\n"
            + intake_text
        )
    draft_path = case_dir / "audit_draft.md"
    draft_path.write_text(draft_text, encoding="utf-8")
    update_case_state(config, paths, customer_id, {"current_stage": "draft_ready", "draft_location": str(draft_path)})
    add_approval(
        paths,
        "audit_review",
        f"Preliminary audit draft for {customer_id} is ready for Casey review.",
        artifact_path=draft_path,
    )
    audit_log(paths, "audit_draft_prepared", {"customer_id": customer_id, "path": str(draft_path)})
    return draft_path


# ---------------------------------------------------------------------------
# Capacity and deadline checks
# ---------------------------------------------------------------------------


def recalculate_capacity(config: Dict[str, Any], paths: Dict[str, Path], state: Dict[str, Any]) -> None:
    rows = [r for r in read_case_tracker(Path(config["case_tracker"])) if not is_test_case(r)]
    active = [r for r in rows if r.get("payment_status") == "paid" and r.get("delivery_status") != "delivered" and r.get("current_stage") != "capacity_hold"]
    completed = [r for r in rows if r.get("delivery_status") == "delivered"]
    state["active_cases"] = len(active)
    state["completed_cases"] = len(completed)
    state["revenue_usd"] = (len(active) + len(completed)) * config["pilot_price_usd"]
    state["slots_remaining"] = max(0, config["pilot_capacity"] - state["active_cases"] - state["completed_cases"])

    # Cross-check Gumroad if possible
    remaining = gumroad_remaining_capacity(config)
    if remaining is not None and remaining != state["slots_remaining"]:
        audit_log(
            paths,
            "capacity_cross_check",
            {"case_tracker_remaining": state["slots_remaining"], "gumroad_remaining": remaining},
        )
        # Trust case tracker for local state, but flag mismatch
        if remaining == 0 and state["slots_remaining"] > 0:
            add_approval(
                paths,
                "capacity_mismatch",
                "Gumroad reports zero remaining slots but local tracker shows slots open.",
            )

    save_state(paths, state)
    publish_capacity_snapshot(config, paths, state)


def publish_capacity_snapshot(
    config: Dict[str, Any], paths: Dict[str, Path], state: Dict[str, Any]
) -> bool:
    """Atomically publish the capacity snapshot consumed by the website.

    The snapshot contains no customer details—only the validated active count.
    If the publisher or schema is invalid, the website's audit_capacity_status
    fails closed and checkout pauses.

    Never implicitly publish to the production path: only an explicitly
    configured capacity_snapshot_path is published where the website reads it.
    Without one, the snapshot goes to a scratch location under the manager
    dir, so tests and ad-hoc runs cannot overwrite the live state file.
    """
    configured = config.get("capacity_snapshot_path")
    if configured:
        snapshot_path = Path(configured)
    else:
        snapshot_path = Path(paths["root"]) / "state" / "audit_capacity_state.json"
    try:
        active = int(state.get("active_cases", 0))
        if active < 0:
            raise ValueError("active_cases must be non-negative")
        capacity = int(config.get("pilot_capacity", 5))
        if capacity != 5:
            raise ValueError("pilot_capacity must remain 5")
        payload = {
            "schema_version": 1,
            "source": "cropcircuit_operations_manager",
            "counting_rule": "paid_production_nonterminal_v1",
            "generated_at_utc": datetime.utcnow().isoformat() + "Z",
            "capacity": capacity,
            "active_paid_audits": active,
        }
        # FLORAL CIPHER v2: stamp Cert provenance before writing.
        payload = cert_guard.stamp(payload, "capacity_snapshot")
        # Validate before writing.
        json.dumps(payload)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = snapshot_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        # Restrict permissions before atomic promotion.
        os.chmod(temp_path, 0o600)
        temp_path.replace(snapshot_path)
        audit_log(paths, "capacity_snapshot_published", {
            "path": str(snapshot_path),
            "active_paid_audits": active,
            "capacity": capacity,
            "generated_at_utc": payload["generated_at_utc"],
        })
        # v2 self-attestation: verify our own publish against the audit witness.
        violations = cert_guard.verify(snapshot_path, paths["audit_log"], "capacity_snapshot")
        audit_log(paths, "cert_attestation", {
            "path": str(snapshot_path),
            "ok": not violations,
            "violations": violations[:3],
        })
        return True
    except Exception as e:
        audit_log(paths, "capacity_snapshot_failed", {"error": type(e).__name__, "message": str(e)})
        return False


def process_deadlines(config: Dict[str, Any], paths: Dict[str, Path], state: Dict[str, Any]) -> None:
    rows = [r for r in read_case_tracker(Path(config["case_tracker"])) if not is_test_case(r)]
    for row in rows:
        if row.get("payment_status") != "paid" or row.get("intake_status") != "complete":
            continue
        if row.get("delivery_status") == "delivered" or row.get("current_stage") == "capacity_hold":
            continue
        updates: Dict[str, str] = {}
        payment_at = row.get("payment_verified_at_utc")
        intake_at = row.get("intake_accepted_at_utc")
        observed_at = utc_now_iso()
        if not payment_at:
            payment_at = observed_at
            updates["payment_verified_at_utc"] = payment_at
        if not intake_at:
            intake_at = observed_at
            updates["intake_accepted_at_utc"] = intake_at
        ready_at = row.get("fulfillment_ready_at_utc")
        if not ready_at:
            payment_dt = datetime.fromisoformat(payment_at.replace("Z", "+00:00"))
            intake_dt = datetime.fromisoformat(intake_at.replace("Z", "+00:00"))
            ready_at = max(payment_dt, intake_dt).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            updates["fulfillment_ready_at_utc"] = ready_at
        if not row.get("due_date"):
            ready_dt = datetime.fromisoformat(ready_at.replace("Z", "+00:00"))
            local_ready = ready_dt.astimezone(ZoneInfo("America/Detroit"))
            deadline = add_business_day_deadline(local_ready, config["delivery_business_days"])
            due = deadline.date().isoformat()
            updates["due_date"] = due
            updates["fulfillment_deadline_at"] = deadline.isoformat()
            audit_log(paths, "delivery_clock_started", {"customer_id": row["customer_id"], "due_date": due, "clock_start": ready_at})
        if updates:
            update_case_state(config, paths, row["customer_id"], updates)


def _privacy_safe_notification_text(digest_lines: List[str]) -> str:
    """Return a Home Assistant-safe summary without customer emails, names, or property details."""
    safe: List[str] = []
    for line in digest_lines:
        if not line.startswith("- "):
            continue
        core = line[2:].strip()
        if core.startswith("Sale signal received"):
            safe.append("Sale signal received for Small Farm Systems Audit")
        elif core.startswith("Payment verified via Gumroad API"):
            safe.append("Payment verified via Gumroad API")
        elif core.startswith("Payment verification failed"):
            safe.append("Payment verification failed")
        elif core.startswith("Payment verification required"):
            safe.append("Payment verification required")
        elif core.startswith("Intake channel failure"):
            safe.append("Email intake channel failure; customer replies may be missed")
        elif core.startswith("Intake email received"):
            safe.append("Intake email received")
        elif core.startswith("Intake file received"):
            safe.append("Intake file received")
        elif core.startswith("Audit draft ready"):
            safe.append("Audit draft ready for review")
        elif core.startswith("Deadline approaching"):
            safe.append("Deadline approaching")
        elif core.startswith("Monitor alert"):
            safe.append("Website or checkout monitor alert")
        elif core.startswith("Daily model budget stopped") or core.startswith("Monthly model budget stopped"):
            safe.append(core)
        elif core.startswith("Pilot capacity is full"):
            safe.append(core)
        else:
            safe.append("New action item in manager digest")
    text = "\n".join(safe)
    # Redact any stray email address that slips through.
    text = re.sub(r"[^\s@]+@[^\s@]+\.[^\s@]+", "[email redacted]", text)
    return text[:500]


# ---------------------------------------------------------------------------
# Main cycle
# ---------------------------------------------------------------------------


def run_cycle() -> Dict[str, Any]:
    config = load_config()
    paths = manager_paths(config)

    if is_paused(config, paths):
        return {"status": "paused"}

    state = load_state(paths)
    state["last_check_utc"] = datetime.utcnow().isoformat() + "Z"
    save_state(paths, state)

    # First, materialize any async Codex work already in flight
    refresh_pending_codex_jobs(config, paths, state)

    # Deterministic cheap checks
    web_result = monitor_website(config, paths)
    incoming_events = check_incoming(config, paths, state)
    sale_events = check_incoming_sales(config, paths, state)
    api_verifications = check_gumroad_api_verification(config, paths, state)
    email_intake_events = check_email_intake(config, paths, state)
    recalculate_capacity(config, paths, state)
    process_deadlines(config, paths, state)

    # Decide concrete tasks (production cases only)
    state = load_state(paths)
    rows = [r for r in read_case_tracker(Path(config["case_tracker"])) if not is_test_case(r)]
    for row in rows:
        cid = row["customer_id"]
        if row.get("payment_status") == "paid" and row.get("intake_status") != "complete":
            msg = prepare_missing_intake_message(cid)
            add_task(paths, "draft_customer_message", {"customer_id": cid, "message": msg, "reason": "missing_intake"}, assignee="manager")
        if row.get("payment_status") == "paid" and row.get("intake_status") == "complete" and row.get("current_stage") == "intake_received":
            ack = prepare_acknowledgement(cid)
            add_task(paths, "draft_customer_message", {"customer_id": cid, "message": ack, "reason": "acknowledgement"}, assignee="manager")
            # Move stage so we don't re-draft
            update_case_state(config, paths, cid, {"current_stage": "drafting_audit"})
            row["current_stage"] = "drafting_audit"
        if row.get("current_stage") == "drafting_audit":
            draft_path = prepare_audit_draft(config, paths, state, cid)
            if draft_path:
                update_case_state(config, paths, cid, {"current_stage": "awaiting_casey_review"})

    # Build targeted digest only for actionable events
    digest_lines = []
    if sale_events:
        for ev in sale_events:
            if ev.get("test_case"):
                continue
            digest_lines.append(f"- Sale signal received: {ev.get('sale_id')} ({ev.get('email')}) — verify in Gumroad dashboard")
    if api_verifications:
        for v in api_verifications:
            if v["result"].get("verified"):
                digest_lines.append(f"- Payment verified via Gumroad API: {v['customer_id']}")
            else:
                digest_lines.append(f"- Payment verification failed for {v['customer_id']}: {v['result'].get('reason')}")
    intake_channel_failures = [ev for ev in email_intake_events if ev.get("type") == "intake_channel_failed"]
    if intake_channel_failures:
        failure = intake_channel_failures[-1]
        digest_lines.append(f"- Intake channel failure: email intake unreachable ({failure.get('error', 'error')}); customer replies may be missed")
    if email_intake_events:
        for ev in email_intake_events:
            if ev.get("type") == "intake_channel_failed":
                continue
            if ev.get("test_case"):
                continue
            cid = ev.get("matched")
            digest_lines.append(f"- Intake email received: {ev.get('from')}" + (f" matched to {cid}" if cid else " (unmatched)"))
    if incoming_events:
        for ev in incoming_events:
            if ev.get("test_case"):
                continue
            cid = ev.get("customer_id")
            digest_lines.append(f"- Intake file received: {ev['filename']}" + (f" matched to {cid}" if cid else " (unmatched)"))
    if web_result.get("failed"):
        digest_lines.append(f"- Monitor alert: {web_result['failed']}")

    state = load_state(paths)
    separate_test_approvals(paths, read_case_tracker(Path(config["case_tracker"])))

    # Budget stop notifications
    daily_budget = float(config.get("daily_budget_usd", 1.0))
    monthly_budget = float(config.get("monthly_budget_usd", 10.0))
    if state["daily_cost_usd"] >= daily_budget:
        digest_lines.append(f"- Daily model budget stopped further calls (${state['daily_cost_usd']:.2f} / ${daily_budget:.2f}).")
    if state.get("monthly_cost_usd", 0.0) >= monthly_budget:
        digest_lines.append(f"- Monthly model budget stopped further calls (${state['monthly_cost_usd']:.2f} / ${monthly_budget:.2f}).")

    # Capacity full
    if state["slots_remaining"] == 0 and not state.get("capacity_pause_notified"):
        digest_lines.append("- Pilot capacity is full. Pause further sales.")
        state["capacity_pause_notified"] = True
        save_state(paths, state)

    # Pending actionable approvals
    approval_alerts = {
        "payment_verification_required": "Payment verification required",
        "payment_verified_via_api": "Payment verified via Gumroad API",
        "audit_review": "Audit draft ready for Casey review",
        "capacity_mismatch": "Capacity mismatch detected",
        "capacity_hold": "Verified signal on capacity hold",
        "unmatched_intake": "Unmatched intake file",
        "intake_unmatched": "Unmatched intake email",
        "ambiguous_match": "Ambiguous intake match",
    }
    if paths["approvals"].exists():
        for line in paths["approvals"].read_text(encoding="utf-8").strip().splitlines():
            try:
                appr = json.loads(line)
            except json.JSONDecodeError:
                continue
            if appr.get("status") == "pending" and appr.get("type") in approval_alerts:
                if appr.get("test_case") is True:
                    continue
                digest_lines.append(f"- {approval_alerts[appr['type']]}: {appr.get('description', '')[:120]}")

    # Deadline approaching (within 24 hours)
    rows = [r for r in read_case_tracker(Path(config["case_tracker"])) if not is_test_case(r)]
    now = datetime.utcnow().date()
    for row in rows:
        if row.get("delivery_status") == "delivered":
            continue
        due = row.get("due_date")
        if not due:
            continue
        try:
            due_date = datetime.strptime(due, "%Y-%m-%d").date()
        except ValueError:
            continue
        days_until = (due_date - now).days
        if 0 <= days_until <= 1:
            digest_lines.append(f"- Deadline approaching ({days_until} business day(s)): {row.get('customer_id', '')}")

    if digest_lines:
        state["changes_since_digest"] = True
        save_state(paths, state)
        digest_path = paths["digest"]
        digest_lines.append(f"\nDaily cost: ${state['daily_cost_usd']:.2f} / ${daily_budget:.2f}")
        digest_lines.append(f"Monthly cost: ${state.get('monthly_cost_usd', 0.0):.2f} / ${monthly_budget:.2f}")
        digest_body = "# Operations Manager Digest\n\n" + "\n".join(digest_lines) + "\n\n" + f"_Generated at {datetime.utcnow().isoformat()}Z_\n"
        digest_path.write_text(digest_body, encoding="utf-8")
        audit_log(paths, "digest_written", {"lines": len(digest_lines)})
        # Best-effort Home Assistant notification. Privacy-safe summary only.
        notified = notify_casey(
            config,
            "Crop Circuit Ops Manager Alert",
            _privacy_safe_notification_text(digest_lines),
            notification_id=f"cropcircuit_ops_{datetime.utcnow().strftime('%Y%m%d')}",
        )
        audit_log(paths, "notification_sent" if notified else "notification_failed", {"channel": "home_assistant", "title": "Crop Circuit Ops Manager Alert"})

    audit_log(paths, "cycle_completed", {"web": web_result, "incoming": len(incoming_events), "sales": len(sale_events), "api_verifications": len(api_verifications), "email_intake": len(email_intake_events)})
    return {"status": "ok", "web": web_result, "incoming": len(incoming_events), "sales": len(sale_events), "api_verifications": len(api_verifications), "email_intake": len(email_intake_events)}


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("--run", "run"):
        result = run_cycle()
        print(json.dumps(result, indent=2))
        return 0
    print("Usage: operations_manager.py --run")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
