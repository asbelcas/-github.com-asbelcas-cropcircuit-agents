#!/usr/bin/env python3
"""Offline self-test for email guard behavior."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

import email_guard as guard


def _reset_state(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"events": []}, indent=2), encoding="utf-8")


def main() -> int:
    tmp_state = Path(tempfile.gettempdir()) / "email_state_selftest.json"
    guard.DEFAULT_STATE_PATH = tmp_state
    backup = tmp_state.read_text(encoding="utf-8") if tmp_state.exists() else None
    try:
        _reset_state(tmp_state)

        base = datetime(2026, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
        thread = "grant follow up|calhouncd@gmail.com"

        # 1) inbound after draft => BLOCK
        guard.record_email_event("draft_created", thread, base.isoformat(), {"case": 1})
        guard.record_email_event("inbound_seen", thread, (base + timedelta(minutes=10)).isoformat(), {"case": 1})
        allow1, reason1 = guard.should_send(thread, (base + timedelta(minutes=11)).isoformat(), cooldown_minutes=180)
        ok1 = (allow1 is False) and ("inbound_seen_after_latest_outbound" in reason1)
        print(f"1) inbound after draft => BLOCK: {'PASS' if ok1 else 'FAIL'}")

        # 2) inbound after send => BLOCK
        thread2 = "cooldown thread|ops@example.org"
        guard.record_email_event("send_success", thread2, base.isoformat(), {"case": 2})
        guard.record_email_event("inbound_seen", thread2, (base + timedelta(minutes=1)).isoformat(), {"case": 2})
        allow2, reason2 = guard.should_send(thread2, (base + timedelta(minutes=2)).isoformat(), cooldown_minutes=180)
        ok2 = (allow2 is False) and ("inbound_seen_after_latest_outbound" in reason2)
        print(f"2) inbound after send => BLOCK: {'PASS' if ok2 else 'FAIL'}")

        # 3) cooldown => BLOCK
        thread3 = "cooldown-only|ops@example.org"
        guard.record_email_event("send_success", thread3, base.isoformat(), {"case": 3})
        allow3, reason3 = guard.should_send(thread3, (base + timedelta(minutes=30)).isoformat(), cooldown_minutes=180)
        ok3 = (allow3 is False) and ("within_cooldown" in reason3)
        print(f"3) cooldown => BLOCK: {'PASS' if ok3 else 'FAIL'}")

        # 4) normal => ALLOW
        thread4 = "normal thread|person@example.org"
        guard.record_email_event("draft_created", thread4, (base - timedelta(hours=8)).isoformat(), {"case": 4})
        guard.record_email_event("send_success", thread4, (base - timedelta(hours=6)).isoformat(), {"case": 4})
        allow4, reason4 = guard.should_send(thread4, base.isoformat(), cooldown_minutes=180)
        ok4 = (allow4 is True) and ("ALLOW" in reason4)
        print(f"4) normal => ALLOW: {'PASS' if ok4 else 'FAIL'}")

        return 0 if (ok1 and ok2 and ok3 and ok4) else 1
    finally:
        if backup is None:
            try:
                tmp_state.unlink(missing_ok=True)
            except Exception:
                pass
        else:
            tmp_state.write_text(backup, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
