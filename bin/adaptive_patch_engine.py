#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
from pathlib import Path

ALLOWED_TYPES = {"config", "retry_logic", "observability", "performance", "funding"}


def now_ts() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "consecutive_degrade": 0,
        "auto_patch_enabled": True,
        "last_change": {},
        "patch_fail_counts": {},
        "disabled_patches": [],
    }


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def parse_review(text: str) -> dict:
    pattern = re.compile(
        r"IMPROVEMENT:\s*\n(?P<improvement>.+?)\n\nPATCH_TYPE:\s*\n(?P<ptype>config|retry_logic|observability|performance|funding)\s*\n\nRISK:\s*\n(?P<risk>low|medium|high)\s*$",
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(text.strip())
    if not m:
        return {
            "ok": False,
            "improvement": "Invalid reviewer format",
            "ptype": "observability",
            "risk": "high",
        }
    return {
        "ok": True,
        "improvement": m.group("improvement").strip().replace("\n", " "),
        "ptype": m.group("ptype").strip().lower(),
        "risk": m.group("risk").strip().lower(),
    }


def update_env_var(env_path: Path, key: str, value: str) -> None:
    lines = env_path.read_text(encoding="utf-8").splitlines()
    target = f'export {key}="{value}"'
    replaced = False
    out = []
    for ln in lines:
        if re.match(rf"^\s*export\s+{re.escape(key)}=", ln):
            out.append(target)
            replaced = True
        else:
            out.append(ln)
    if not replaced:
        out.append(target)
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def get_env_value(env_path: Path, key: str, default: str) -> str:
    txt = env_path.read_text(encoding="utf-8")
    m = re.search(rf"^\s*export\s+{re.escape(key)}=\"?(.*?)\"?\s*$", txt, re.MULTILINE)
    return m.group(1) if m else default


def apply_low_patch(root: Path, ptype: str, improvement: str, state: dict) -> dict:
    env_path = root / ".env.grant"
    outreach_path = root / "outreach_log.csv"
    backups_dir = root / "patches" / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    ts = dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")

    if ptype in {"config", "retry_logic"}:
        backup = backups_dir / f"env_{ts}.bak"
        shutil.copy2(env_path, backup)
        current = int(get_env_value(env_path, "HA_RETRY_MAX", "4") or "4")
        newv = min(current + 1, 6)
        update_env_var(env_path, "HA_RETRY_MAX", str(newv))
        summary = f"HA_RETRY_MAX {current}->{newv}"
        target = str(env_path)
    elif ptype == "observability":
        backup = backups_dir / f"env_{ts}.bak"
        shutil.copy2(env_path, backup)
        current = int(get_env_value(env_path, "HA_POLL_ATTEMPTS", "3") or "3")
        newv = min(current + 1, 5)
        update_env_var(env_path, "HA_POLL_ATTEMPTS", str(newv))
        summary = f"HA_POLL_ATTEMPTS {current}->{newv}"
        target = str(env_path)
    elif ptype == "performance":
        backup = backups_dir / f"env_{ts}.bak"
        shutil.copy2(env_path, backup)
        current = int(get_env_value(env_path, "CLAUDE_REVIEW_TIMEOUT_SECONDS", "45") or "45")
        newv = max(20, min(current - 5, 45))
        update_env_var(env_path, "CLAUDE_REVIEW_TIMEOUT_SECONDS", str(newv))
        summary = f"CLAUDE_REVIEW_TIMEOUT_SECONDS {current}->{newv}"
        target = str(env_path)
    else:  # funding
        backup = backups_dir / f"outreach_{ts}.bak"
        shutil.copy2(outreach_path, backup)
        rows = []
        updated = False
        with outreach_path.open(newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            fn = r.fieldnames or []
            for row in r:
                if not updated and (row.get("Status", "").strip().upper() == "PENDING"):
                    for col in ("Follow_Up_1_Date", "Follow_Up_2_Date"):
                        v = (row.get(col, "") or "").strip()
                        if v:
                            try:
                                d = dt.datetime.strptime(v, "%Y-%m-%d").date()
                                d2 = d - dt.timedelta(days=1)
                                row[col] = d2.isoformat()
                            except Exception:
                                pass
                    notes = (row.get("Notes", "") or "").strip()
                    row["Notes"] = (notes + " | adaptive: followups accelerated").strip(" |")
                    updated = True
                rows.append(row)
        with outreach_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fn)
            w.writeheader()
            w.writerows(rows)
        summary = "Accelerated follow-up dates for first PENDING outreach row"
        target = str(outreach_path)

    state["last_change"] = {
        "timestamp": now_ts(),
        "improvement": improvement,
        "patch_type": ptype,
        "risk": "low",
        "action": "auto_patch_applied",
        "target": target,
        "backup": str(backup),
        "summary": summary,
    }
    return state["last_change"]


def stage_medium(root: Path, review: dict) -> dict:
    pending = root / "patches" / "pending"
    pending.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    f = pending / f"{ts}_{review['ptype']}.md"
    f.write_text(
        "\n".join(
            [
                "# Pending Adaptive Patch",
                f"- timestamp: {now_ts()}",
                f"- improvement: {review['improvement']}",
                f"- patch_type: {review['ptype']}",
                "- risk: medium",
                "- action: staged",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {"path": str(f)}


def cmd_apply(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    review_txt = Path(args.review_file).read_text(encoding="utf-8")
    review = parse_review(review_txt)

    state_path = root / "logs" / "adaptive_state.json"
    last_path = root / "logs" / "adaptive_last.json"
    state = load_state(state_path)
    state.setdefault("patch_fail_counts", {})
    state.setdefault("disabled_patches", [])

    auto_mode = get_env_value(root / ".env.grant", "AUTO_PATCH_MODE", "on").lower() != "off"
    state["auto_patch_enabled"] = auto_mode and state.get("auto_patch_enabled", True)
    patch_key = f"{review['ptype']}|{review['improvement'].strip().lower()}"

    out = {
        "action": "log_only",
        "risk": review["risk"],
        "improvement": review["improvement"],
        "patch_type": review["ptype"],
        "auto_patch_enabled": state["auto_patch_enabled"],
        "note": "",
    }

    if not review["ok"]:
        out["risk"] = "high"
        out["action"] = "log_only"
        out["note"] = "invalid reviewer format"
    elif review["risk"] == "low":
        if patch_key in set(state.get("disabled_patches", [])):
            out["action"] = "log_only"
            out["note"] = "patch_disabled_permanently"
        elif state["auto_patch_enabled"]:
            ch = apply_low_patch(root, review["ptype"], review["improvement"], state)
            state.setdefault("last_change", {})["patch_key"] = patch_key
            out["action"] = "auto_patch_applied"
            out["note"] = ch["summary"]
        else:
            out["action"] = "log_only"
            out["note"] = "auto_patch_mode_disabled"
    elif review["risk"] == "medium":
        st = stage_medium(root, review)
        out["action"] = "staged"
        out["note"] = st["path"]
        state["last_change"] = {
            "timestamp": now_ts(),
            "improvement": review["improvement"],
            "patch_type": review["ptype"],
            "patch_key": patch_key,
            "risk": "medium",
            "action": "staged",
            "target": st["path"],
            "backup": "",
            "summary": "staged pending patch",
        }
    else:
        out["action"] = "log_only"
        out["note"] = "high risk"
        state["last_change"] = {
            "timestamp": now_ts(),
            "improvement": review["improvement"],
            "patch_type": review["ptype"],
            "patch_key": patch_key,
            "risk": "high",
            "action": "log_only",
            "target": "",
            "backup": "",
            "summary": "high risk not applied",
        }

    last = {
        "timestamp": now_ts(),
        "improvement": review["improvement"],
        "patch_key": patch_key,
        "risk": review["risk"],
        "action": out["action"],
        "outcome_delta": "pending",
    }
    last_path.parent.mkdir(parents=True, exist_ok=True)
    last_path.write_text(json.dumps(last, indent=2), encoding="utf-8")

    save_state(state_path, state)

    for k, v in out.items():
        print(f"{k}={v}")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    state_path = root / "logs" / "adaptive_state.json"
    last_path = root / "logs" / "adaptive_last.json"
    env_path = root / ".env.grant"

    state = load_state(state_path)
    state.setdefault("patch_fail_counts", {})
    state.setdefault("disabled_patches", [])

    degrade = False
    reasons = []
    if args.after_failures > args.before_failures:
        degrade = True
        reasons.append("failures_increased")
    if args.before_latency > 0 and args.after_latency > (args.before_latency * 1.30):
        degrade = True
        reasons.append("latency_increased")
    if args.ha_before == "ok" and args.ha_after != "ok":
        degrade = True
        reasons.append("ha_health_dropped")

    if degrade:
        state["consecutive_degrade"] = int(state.get("consecutive_degrade", 0)) + 1
    else:
        state["consecutive_degrade"] = 0

    patch_disabled_now = False
    lc = state.get("last_change", {})
    last_patch_key = (
        lc.get("patch_key")
        or f"{lc.get('patch_type', '')}|{str(lc.get('improvement', '')).strip().lower()}"
    ).strip("|")
    if last_patch_key:
        counts = state.get("patch_fail_counts", {})
        if degrade:
            counts[last_patch_key] = int(counts.get(last_patch_key, 0)) + 1
            if counts[last_patch_key] >= 3:
                disabled = set(state.get("disabled_patches", []))
                if last_patch_key not in disabled:
                    disabled.add(last_patch_key)
                    state["disabled_patches"] = sorted(disabled)
                    patch_disabled_now = True
        else:
            counts[last_patch_key] = 0
        state["patch_fail_counts"] = counts

    reverted = False
    if state["consecutive_degrade"] >= 3:
        state["auto_patch_enabled"] = False
        update_env_var(env_path, "AUTO_PATCH_MODE", "off")
        lc = state.get("last_change", {})
        backup = lc.get("backup")
        target = lc.get("target")
        if backup and target and Path(backup).exists() and Path(target).exists():
            shutil.copy2(backup, target)
            reverted = True

    save_state(state_path, state)

    last = {}
    if last_path.exists():
        try:
            last = json.loads(last_path.read_text(encoding="utf-8"))
        except Exception:
            last = {}
    delta = f"failures:{args.before_failures}->{args.after_failures};latency:{args.before_latency:.2f}->{args.after_latency:.2f};ha:{args.ha_before}->{args.ha_after}"
    if degrade:
        delta += ";degrade=yes(" + ",".join(reasons) + ")"
    else:
        delta += ";degrade=no"
    if reverted:
        delta += ";reverted_last_change=yes"
    if patch_disabled_now:
        delta += ";patch_disabled_permanently=yes"
    last["outcome_delta"] = delta
    last["timestamp"] = now_ts()
    last_path.write_text(json.dumps(last, indent=2), encoding="utf-8")

    print(f"degrade={'1' if degrade else '0'}")
    print(f"consecutive_degrade={state['consecutive_degrade']}")
    print(f"auto_patch_enabled={'1' if state.get('auto_patch_enabled', True) else '0'}")
    print(f"reverted={'1' if reverted else '0'}")
    print(f"patch_disabled_now={'1' if patch_disabled_now else '0'}")
    print(f"delta={delta}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("apply")
    a.add_argument("--root", required=True)
    a.add_argument("--review-file", required=True)

    e = sub.add_parser("evaluate")
    e.add_argument("--root", required=True)
    e.add_argument("--before-failures", type=int, required=True)
    e.add_argument("--after-failures", type=int, required=True)
    e.add_argument("--before-latency", type=float, required=True)
    e.add_argument("--after-latency", type=float, required=True)
    e.add_argument("--ha-before", required=True)
    e.add_argument("--ha-after", required=True)

    args = ap.parse_args()
    if args.cmd == "apply":
        return cmd_apply(args)
    return cmd_evaluate(args)


if __name__ == "__main__":
    raise SystemExit(main())
