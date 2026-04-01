#!/usr/bin/env python3
"""Reply-aware outbound email guard state and policy."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

ROOT = Path("/home/asbelcas/cropcircuit")
DEFAULT_STATE_PATH = ROOT / "runtime" / "email_state.json"
HUMAN_MODE_PATH = ROOT / "runtime" / "human_loop_mode.json"
CALL_MODE_PATH = ROOT / "runtime" / "call_support_mode.json"

VALID_KINDS = {"draft_created", "send_attempt", "send_success", "inbound_seen", "block"}


def _parse_ts(ts: str | datetime) -> datetime:
    if isinstance(ts, datetime):
        dt = ts
    else:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_subject_root(subject: str) -> str:
    s = (subject or "").strip()
    while True:
        lowered = s.lower()
        if lowered.startswith("re:"):
            s = s[3:].strip()
        elif lowered.startswith("fwd:"):
            s = s[4:].strip()
        else:
            break
    return " ".join(s.split()).lower()


def build_thread_key(subject: str, recipient: str = "", message_refs: str = "") -> str:
    refs = (message_refs or "").strip().lower()
    if refs:
        return refs
    return f"{normalize_subject_root(subject)}|{(recipient or '').strip().lower()}"


def load_email_state(path: str = "runtime/email_state.json") -> dict[str, Any]:
    p = ROOT / path if not path.startswith("/") else Path(path)
    if not p.exists():
        return {"events": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"events": []}
    if not isinstance(data, dict):
        return {"events": []}
    events = data.get("events")
    if not isinstance(events, list):
        data["events"] = []
    return data


def _write_email_state(state: dict[str, Any], path: Path = DEFAULT_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(path)


def record_email_event(kind: str, thread_key: str, ts_utc, meta: dict[str, Any] | None):
    if kind not in VALID_KINDS:
        raise ValueError(f"invalid kind: {kind}")

    dt = _parse_ts(ts_utc)
    event = {
        "kind": kind,
        "thread_key": (thread_key or "").strip().lower(),
        "ts_utc": _to_iso_z(dt),
        "meta": meta or {},
    }

    state = load_email_state(str(DEFAULT_STATE_PATH))
    state.setdefault("events", []).append(event)
    _write_email_state(state, DEFAULT_STATE_PATH)
    return event


def _latest(events: list[dict[str, Any]], kind: str) -> datetime | None:
    candidates = []
    for e in events:
        if e.get("kind") != kind:
            continue
        try:
            candidates.append(_parse_ts(e.get("ts_utc")))
        except Exception:
            continue
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]


def should_send(thread_key: str, now_utc, cooldown_minutes: int = 180) -> tuple[bool, str]:
    now_dt = _parse_ts(now_utc)
    key = (thread_key or "").strip().lower()

    state = load_email_state(str(DEFAULT_STATE_PATH))
    events = [e for e in state.get("events", []) if (e.get("thread_key") or "").lower() == key]

    last_draft = _latest(events, "draft_created")
    last_attempt = _latest(events, "send_attempt")
    last_success = _latest(events, "send_success")
    last_inbound = _latest(events, "inbound_seen")

    if call_support_blocked_thread(key):
        return False, "BLOCK: call_support_mode_active_for_calhoun_conservation_district"

    latest_outbound = None
    outbound_points = [dt for dt in [last_draft, last_success] if dt is not None]
    if outbound_points:
        outbound_points.sort(reverse=True)
        latest_outbound = outbound_points[0]

    if last_inbound and latest_outbound and last_inbound > latest_outbound:
        return False, "BLOCK: inbound_seen_after_latest_outbound"

    if last_inbound and last_attempt and last_inbound > last_attempt:
        return False, "BLOCK: inbound_seen_after_send_attempt"

    if last_success and (now_dt - last_success) < timedelta(minutes=cooldown_minutes):
        return False, "BLOCK: within_cooldown"

    return True, "ALLOW: normal"


def notify_ha_block(title: str, message: str) -> bool:
    """Send persistent notification to HA when configured."""
    base = (
        os.environ.get("HA_BASE_URL", "").strip()
        or os.environ.get("HA_URL", "").strip()
        or "http://localhost:8123"
    ).rstrip("/")
    token = os.environ.get("HA_TOKEN", "").strip()
    if not token:
        return False
    payload = json.dumps({"title": title, "message": message}).encode("utf-8")
    req = request.Request(
        f"{base}/api/services/persistent_notification/create",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=8) as resp:
            return 200 <= int(getattr(resp, "status", 0)) < 300
    except (error.URLError, TimeoutError, ValueError):
        return False


def load_human_loop_mode() -> dict[str, Any]:
    if not HUMAN_MODE_PATH.exists():
        return {"active": False, "priority_contacts": []}
    try:
        payload = json.loads(HUMAN_MODE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"active": False, "priority_contacts": []}
    if not isinstance(payload, dict):
        return {"active": False, "priority_contacts": []}
    payload.setdefault("active", False)
    payload.setdefault("priority_contacts", [])
    return payload


def human_loop_active() -> bool:
    return bool(load_human_loop_mode().get("active"))


def is_priority_contact(addr: str) -> bool:
    target = (addr or "").strip().lower()
    if not target:
        return False
    mode = load_human_loop_mode()
    listed = {str(x).strip().lower() for x in mode.get("priority_contacts", []) if str(x).strip()}
    return target in listed


def load_call_support_mode() -> dict[str, Any]:
    if not CALL_MODE_PATH.exists():
        return {"active": False, "paused_contacts": [], "paused_keywords": []}
    try:
        payload = json.loads(CALL_MODE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"active": False, "paused_contacts": [], "paused_keywords": []}
    if not isinstance(payload, dict):
        return {"active": False, "paused_contacts": [], "paused_keywords": []}
    payload.setdefault("active", False)
    payload.setdefault("paused_contacts", [])
    payload.setdefault("paused_keywords", [])
    return payload


def call_support_active() -> bool:
    return bool(load_call_support_mode().get("active"))


def call_support_blocked_thread(thread_key: str) -> bool:
    if not call_support_active():
        return False
    key = (thread_key or "").lower()
    mode = load_call_support_mode()
    paused_contacts = {str(x).strip().lower() for x in mode.get("paused_contacts", []) if str(x).strip()}
    paused_keywords = [str(x).strip().lower() for x in mode.get("paused_keywords", []) if str(x).strip()]
    if any(c in key for c in paused_contacts):
        return True
    if any(k in key for k in paused_keywords):
        return True
    # default safety for CCD aliases
    return ("calhouncd" in key) or ("calhoun conservation district" in key)
