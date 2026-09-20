#!/usr/bin/env python3
"""Deterministic pre-send pacing gate for CropCircuit external messages.

Reads one JSON object from stdin and emits one JSON decision.
This is an advisory control: it cannot prove tone, truth, or relationship fit.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

LOW_VALUE_FOLLOWUP = (
    "just checking in",
    "just following up",
    "checking back",
    "circling back",
    "bumping this",
    "wanted to bump",
    "one more thing",
)

PRESSURE_PHRASES = (
    "asap",
    "immediately",
    "urgent",
    "need this today",
    "time sensitive",
)

DEFAULT_SAME_DAY_HOLD_HOURS = 12.0
LONG_MESSAGE_WORDS = 350
VERY_LONG_MESSAGE_WORDS = 650
MAX_QUESTIONS_BEFORE_REVIEW = 3


def _bool(data: dict[str, Any], key: str, default: bool = False) -> bool:
    value = data.get(key, default)
    return bool(value)


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    message = str(data.get("message") or "").strip()
    purpose = str(data.get("purpose") or "").strip()
    attention_reason = str(data.get("attention_reason") or "").strip()
    context_read = _bool(data, "context_read")
    urgent = _bool(data, "urgent")
    responding_to_inbound = _bool(data, "responding_to_inbound")
    material_update = _bool(data, "material_update")
    consequential_correction = _bool(data, "consequential_correction")

    hours_since = data.get("hours_since_last_outbound")
    recipient_reply_hours = data.get("recipient_average_reply_hours")
    next_step_count = int(data.get("next_step_count", 1) or 0)

    hard_holds: list[str] = []
    reviews: list[str] = []
    notes: list[str] = []

    if not message:
        hard_holds.append("Message body is empty.")

    # PACE metadata gates.
    if not purpose:
        hard_holds.append("PACE/Purpose is missing.")
    if not attention_reason and not responding_to_inbound:
        hard_holds.append("PACE/Attention reason is missing.")
    if not context_read:
        hard_holds.append("PACE/Context not confirmed as read.")
    if next_step_count > 1:
        reviews.append(
            f"PACE/Ease: {next_step_count} next steps are requested; prefer one primary action."
        )

    words = re.findall(r"\b\w+[’'-]?\w*\b|\b\w+\b", message)
    word_count = len(words)
    question_count = message.count("?")
    lower = message.lower()

    if word_count > VERY_LONG_MESSAGE_WORDS:
        hard_holds.append(
            f"Message is {word_count} words; compress before sending unless the format requires detail."
        )
    elif word_count > LONG_MESSAGE_WORDS:
        reviews.append(
            f"Message is {word_count} words; check whether the recipient needs this much detail."
        )

    if question_count > MAX_QUESTIONS_BEFORE_REVIEW:
        reviews.append(
            f"Message contains {question_count} question marks; batch/prioritize the asks."
        )

    low_value_hit = next((p for p in LOW_VALUE_FOLLOWUP if p in lower), None)
    if low_value_hit and not material_update and not responding_to_inbound:
        hard_holds.append(
            f'Low-value follow-up phrase detected ("{low_value_hit}") without a material update.'
        )

    pressure_hit = next((p for p in PRESSURE_PHRASES if p in lower), None)
    if pressure_hit and not urgent:
        reviews.append(
            f'Pressure phrase detected ("{pressure_hit}") but urgent=false.'
        )

    # Human-pacing gate. Material corrections, inbound replies, and true urgency may
    # bypass the timing hold, but not the cognitive-load checks above.
    timing_exception = urgent or responding_to_inbound or material_update or consequential_correction

    if hours_since is not None:
        try:
            hours_since_f = float(hours_since)
            if hours_since_f < 0:
                reviews.append("hours_since_last_outbound is negative; verify event timestamps.")
            elif hours_since_f < DEFAULT_SAME_DAY_HOLD_HOURS and not timing_exception:
                hard_holds.append(
                    f"Only {hours_since_f:g}h since the last outbound message; default to batching/waiting."
                )
        except (TypeError, ValueError):
            reviews.append("hours_since_last_outbound is not numeric.")

    if recipient_reply_hours is not None and hours_since is not None and not timing_exception:
        try:
            reply_f = float(recipient_reply_hours)
            gap_f = float(hours_since)
            # Do not impose a faster rhythm than half the recipient's observed cadence,
            # capped at a one-day waiting signal.
            min_gap = min(24.0, max(4.0, reply_f / 2.0))
            if gap_f < min_gap:
                hard_holds.append(
                    f"Recipient's observed cadence suggests waiting about {min_gap:g}h before another nonurgent outbound."
                )
        except (TypeError, ValueError):
            pass

    if urgent:
        notes.append("Urgency may justify faster timing; keep asks narrow and factual.")
    if responding_to_inbound:
        notes.append("Inbound reply: timing restraint is relaxed, but recipient-load checks still apply.")
    if material_update:
        notes.append("Material update: timing restraint is relaxed because new information changes the situation.")
    if consequential_correction:
        notes.append("Consequential correction: prompt follow-up may be appropriate.")

    # Deduplicate reasons while preserving order.
    hard_holds = list(dict.fromkeys(hard_holds))
    reviews = list(dict.fromkeys(reviews))

    if hard_holds:
        decision = "HOLD"
    elif reviews:
        decision = "REVIEW"
    else:
        decision = "PASS"

    return {
        "decision": decision,
        "word_count": word_count,
        "question_count": question_count,
        "hard_holds": hard_holds,
        "reviews": reviews,
        "notes": notes,
        "principle": "AI speed must never become human pressure.",
    }


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception as exc:
        json.dump({"decision": "HOLD", "error": f"Invalid JSON input: {exc}"}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2

    if not isinstance(data, dict):
        json.dump({"decision": "HOLD", "error": "Input must be a JSON object."}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2

    result = evaluate(data)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if result["decision"] != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
