#!/usr/bin/env python3
"""Control helpers for ai_liaison.email and ai_liaison.marketplace."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/asbelcas/cropcircuit")
RUNTIME = ROOT / "runtime"
WWW = Path("/opt/homeassistant/config/www")
LOG = ROOT / "logs" / "ai_liaison.control.log"

CHANNELS = {
    "marketplace": {
        "source": RUNTIME / "ai_liaison.marketplace_status.json",
        "alias": RUNTIME / "ai_liaison.marketplace_status.json",
        "www": WWW / "ai_liaison.marketplace_status.json",
        "default_state": "idle",
    },
    "email": {
        "source": RUNTIME / "email_triage_status.json",
        "alias": RUNTIME / "ai_liaison.email_status.json",
        "www": WWW / "ai_liaison.email_status.json",
        "default_state": "idle",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(default)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except PermissionError:
        log(f"permission_denied path={path}")


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.open("a", encoding="utf-8").write(f"{now_iso()} {msg}\n")


def evaluate_risk(text: str) -> tuple[bool, float]:
    t = (text or "").lower()
    price_change = any(k in t for k in ["price change", "change price", "price", "discount", "raise", "lower", "increase", "decrease", "counteroffer"])
    contract = any(k in t for k in ["contract", "agreement", "terms", "signature", "sign", "binding", "legal"])
    timeline = any(k in t for k in ["deadline", "timeline", "by tomorrow", "by today", "asap", "commit", "guarantee", "deliver by", "eta"])
    emotional_or_ambiguous = any(k in t for k in ["upset", "angry", "frustrated", "confused", "not sure", "maybe", "possibly", "??", "!?"])

    risk_flag = price_change or contract or timeline or emotional_or_ambiguous
    hits = sum([price_change, contract, timeline, emotional_or_ambiguous])
    if risk_flag:
        confidence = max(0.35, 0.75 - (0.1 * max(0, hits - 1)))
    else:
        confidence = 0.92
    return risk_flag, round(confidence, 2)


def normalize(channel: str, raw: dict) -> dict:
    default_state = CHANNELS[channel]["default_state"]
    def pick(key: str, fallback):
        val = raw.get(key)
        return fallback if val is None else val

    queue_count = raw.get("queue_count")
    if not isinstance(queue_count, int):
        drafted = raw.get("drafted_count", 0)
        queue_count = int(drafted) if isinstance(drafted, int) else 0

    risk_text = " ".join(
        [
            str(pick("last_subject", "")),
            str(pick("summary", pick("mode", ""))),
            str(pick("suggested_reply", pick("draft_body", ""))),
            str(pick("draft_subject", "")),
            str(pick("draft_body", "")),
        ]
    )
    inferred_risk, inferred_confidence = evaluate_risk(risk_text)

    payload = {
        "state": pick("state", default_state),
        "last_from": pick("last_from", ""),
        "last_subject": pick("last_subject", ""),
        "summary": pick("summary", pick("mode", "")),
        "suggested_reply": pick("suggested_reply", pick("draft_body", "")),
        "draft_to": pick("draft_to", ""),
        "draft_subject": pick("draft_subject", ""),
        "draft_body": pick("draft_body", ""),
        "queue_count": queue_count,
        "last_updated": pick("last_updated", pick("updated_at", now_iso())),
        "risk_flag": pick("risk_flag", inferred_risk),
        "confidence": pick("confidence", inferred_confidence),
        "source_status": {k: v for k, v in raw.items() if k != "source_status"},
    }
    return payload


def sync_channel(channel: str) -> None:
    cfg = CHANNELS[channel]
    src = read_json(cfg["source"], {})
    alias = read_json(cfg["alias"], {})
    merged = {k: v for k, v in dict(src).items() if k != "source_status"}
    merged.update(
        {
            "state": alias.get("state", merged.get("state")),
            "last_from": alias.get("last_from", merged.get("last_from", "")),
            "last_subject": alias.get("last_subject", merged.get("last_subject", "")),
            "summary": alias.get("summary", merged.get("summary", "")),
            "suggested_reply": alias.get("suggested_reply", merged.get("suggested_reply", "")),
            "draft_to": alias.get("draft_to", merged.get("draft_to", "")),
            "draft_subject": alias.get("draft_subject", merged.get("draft_subject", "")),
            "draft_body": alias.get("draft_body", merged.get("draft_body", "")),
            "risk_flag": alias.get("risk_flag", merged.get("risk_flag")),
            "confidence": alias.get("confidence", merged.get("confidence")),
            "queue_count": alias.get("queue_count", merged.get("queue_count", merged.get("drafted_count", 0))),
            "last_updated": now_iso(),
        }
    )
    normalized = normalize(channel, merged)
    write_json(cfg["alias"], normalized)
    write_json(cfg["www"], normalized)


def set_state(channel: str, state: str, decrement: bool) -> None:
    cfg = CHANNELS[channel]
    payload = read_json(cfg["alias"], normalize(channel, {}))
    q = int(payload.get("queue_count", 0) or 0)
    if decrement and q > 0:
        q -= 1
    payload["state"] = state
    payload["queue_count"] = q
    payload["draft_to"] = ""
    payload["draft_subject"] = ""
    payload["draft_body"] = ""
    payload["suggested_reply"] = ""
    payload["risk_flag"] = False
    payload["confidence"] = 0.95
    payload["last_updated"] = now_iso()
    write_json(cfg["alias"], payload)
    write_json(cfg["www"], payload)
    log(f"{channel}_state={state} queue_count={q}")


def inject_fake(
    channel: str,
    from_addr: str,
    subject: str,
    summary: str,
    to_addr: str,
    draft_subject: str,
    draft_body: str,
) -> None:
    cfg = CHANNELS[channel]
    payload = read_json(cfg["alias"], normalize(channel, {}))
    payload.update(
        {
            "state": "pending_approval",
            "last_from": from_addr,
            "last_subject": subject,
            "summary": summary,
            "suggested_reply": draft_body,
            "draft_to": to_addr,
            "draft_subject": draft_subject,
            "draft_body": draft_body,
            "queue_count": max(1, int(payload.get("queue_count", 0) or 0)),
            "last_updated": now_iso(),
        }
    )
    risk_flag, confidence = evaluate_risk(" ".join([subject, summary, draft_subject, draft_body]))
    payload["risk_flag"] = risk_flag
    payload["confidence"] = confidence
    write_json(cfg["alias"], payload)
    write_json(cfg["www"], payload)
    log(f"{channel}_fake_injected to={to_addr} subject={draft_subject}")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sync = sub.add_parser("sync")
    p_sync.add_argument("--channel", choices=["email", "marketplace", "all"], default="all")

    p_approve = sub.add_parser("approve")
    p_approve.add_argument("--channel", choices=["email", "marketplace"], required=True)

    p_skip = sub.add_parser("skip")
    p_skip.add_argument("--channel", choices=["email", "marketplace"], required=True)

    p_fake = sub.add_parser("inject-fake")
    p_fake.add_argument("--channel", choices=["email", "marketplace"], required=True)
    p_fake.add_argument("--from-addr", required=True)
    p_fake.add_argument("--subject", required=True)
    p_fake.add_argument("--summary", required=True)
    p_fake.add_argument("--to-addr", required=True)
    p_fake.add_argument("--draft-subject", required=True)
    p_fake.add_argument("--draft-body", required=True)

    args = parser.parse_args()

    if args.cmd == "sync":
        channels = ["email", "marketplace"] if args.channel == "all" else [args.channel]
        for ch in channels:
            sync_channel(ch)
        print(json.dumps({"ok": True, "cmd": "sync", "channels": channels}))
        return 0

    if args.cmd == "approve":
        set_state(args.channel, "sent", decrement=True)
        print(json.dumps({"ok": True, "cmd": "approve", "channel": args.channel}))
        return 0

    if args.cmd == "skip":
        set_state(args.channel, "skipped", decrement=True)
        print(json.dumps({"ok": True, "cmd": "skip", "channel": args.channel}))
        return 0

    if args.cmd == "inject-fake":
        inject_fake(
            channel=args.channel,
            from_addr=args.from_addr,
            subject=args.subject,
            summary=args.summary,
            to_addr=args.to_addr,
            draft_subject=args.draft_subject,
            draft_body=args.draft_body,
        )
        print(json.dumps({"ok": True, "cmd": "inject-fake", "channel": args.channel}))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
