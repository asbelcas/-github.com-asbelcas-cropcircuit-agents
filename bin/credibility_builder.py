#!/usr/bin/env python3
"""Helper for selecting daily credibility actions from ops rows."""

from __future__ import annotations

from typing import Any


def build_daily_credibility_pack(ops_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return one credibility target, one authority action, one partnership touchpoint."""
    credibility_rows = [r for r in ops_rows if (r.get("role") or "").strip() == "credibility"]
    partner_rows = [r for r in ops_rows if (r.get("role") or "").strip() == "partner"]

    credibility_target = credibility_rows[0] if credibility_rows else (ops_rows[0] if ops_rows else None)
    partner_target = partner_rows[0] if partner_rows else (ops_rows[1] if len(ops_rows) > 1 else credibility_target)

    authority_signal_action = (
        "Engage one credibility anchor with a concise implementation-focused reply "
        "that references measurable on-farm outcomes."
    )

    return {
        "credibility_target": credibility_target,
        "authority_signal_action": authority_signal_action,
        "partnership_touchpoint": partner_target,
    }

