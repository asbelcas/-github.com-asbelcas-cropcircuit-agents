#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


ROOT = Path("/home/asbelcas/cropcircuit")
FIELD_MAP_FILE = ROOT / "runtime" / "field_map.json"
STATUS_FILE = ROOT / "runtime" / "ha_grant_pipeline_status.json"
PROGRAMS_DIR = ROOT / "runtime" / "programs"
LOG_DIR = ROOT / "logs"
PIPELINE_LOG = LOG_DIR / "pipeline.log"

CDP_URL = "http://127.0.0.1:9222"
PROGRAM_NAME = "USDA FSA Operating Microloan"
TARGET_URL_SUBSTR = "public.govdelivery.com/accounts/USDAFARMERS/subscribers/qualify"
SUBMIT_SELECTOR = "input[name='commit']"

TEST_VALUES = {
    "name": "Crop Circuit Test",
    "email": "asbelcas@gmail.com",
    "phone": "2025550147",
    "subscription_type": "email",
    "country_code_display": "1 (US)",
    "password": "CropCircuit!234",
    "privacy_consent": "true",
}

CAPTCHA_TOKENS = ["mtcaptcha", "captcha", "recaptcha", "hcaptcha", "turnstile"]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def safe_url(obj) -> str:
    try:
        return obj.url or ""
    except Exception:
        return ""


def is_captcha_text(text: str) -> bool:
    low = (text or "").lower()
    return any(tok in low for tok in CAPTCHA_TOKENS)


def log_line(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with PIPELINE_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} {message}\n")


def write_status(
    status: str,
    screenshot: str,
    result_url: str,
    selected_page_url: str,
    selected_frame_url: str,
    failures: list[dict],
    program_state_file: Path | None = None,
) -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp_utc": now_utc(),
        "status": status,
        "last_screenshot_path": screenshot,
        "result_url": result_url,
        "selected_page_url": selected_page_url,
        "selected_frame_url": selected_frame_url,
        "failures": failures,
    }
    STATUS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if program_state_file is not None:
        program_state_file.parent.mkdir(parents=True, exist_ok=True)
        program_state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_field_map(program_id: str | None = None) -> dict:
    if program_id:
        p = PROGRAMS_DIR / program_id / "field_map.json"
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}
    if not FIELD_MAP_FILE.exists():
        return {}
    try:
        raw = json.loads(FIELD_MAP_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    prog = raw.get(PROGRAM_NAME, {})
    return prog if isinstance(prog, dict) else {}


def load_program_input_values(program_id: str | None = None) -> dict:
    if not program_id:
        return {}
    p = PROGRAMS_DIR / program_id / "input.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    vals = data.get("values", {})
    return vals if isinstance(vals, dict) else {}


def selector_candidates(field_key: str, selector: str) -> list[str]:
    """Return deterministic selector fallbacks for known govdelivery variants.

    Keeps legacy mapping compatible across:
    - /subscribers/qualify (email-only form)
    - /subscriber/qualify (account-style form with subscriber_* ids)
    """
    key = (field_key or "").lower()
    sel = (selector or "").strip()
    out: list[str] = []
    if sel:
        out.append(sel)

    # Id remaps between subscriber_* and shorter ids
    aliases = {
        "subscriber_email": ["#email", "input[name='email']"],
        "subscriber_email_confirm": ["#email", "input[name='email']"],
        "subscriber_phone": ["#phone", "input[name='phone']"],
        "subscriber_phone_confirm": ["#phone", "input[name='phone']"],
        "subscriber_country_code_display": ["#country_code_display", "select[name='country_code_display']"],
        "subscriber_country_code": ["#country_code", "input[name='country_code']"],
        "subscriber_privacy_consent": ["input[name*='privacy' i]", "input[type='checkbox'][name*='consent' i]"],
        "subscription_type": ["#subscription_type", "select[name='subscription_type']"],
        "name": ["#name", "input[name='name']"],
    }
    for cand in aliases.get(key, []):
        if cand not in out:
            out.append(cand)

    # Generic semantic fallbacks when key naming indicates a field class.
    if "email" in key:
        for cand in ("#email", "input[type='email']", "input[name*='email' i]"):
            if cand not in out:
                out.append(cand)
    if "phone" in key:
        for cand in ("#phone", "input[type='tel']", "input[name*='phone' i]"):
            if cand not in out:
                out.append(cand)
    if "country_code_display" in key:
        for cand in ("#country_code_display", "select[name*='country_code' i]"):
            if cand not in out:
                out.append(cand)
    if "password" in key:
        for cand in ("input[type='password']", "input[name*='password' i]"):
            if cand not in out:
                out.append(cand)

    return out


def resolve_selector(frame, field_key: str, selector: str):
    """Resolve first existing selector candidate; returns (selector, locator) or (None, None)."""
    for cand in selector_candidates(field_key, selector):
        try:
            loc = frame.locator(cand).first
            if loc.count() > 0:
                return cand, loc
        except Exception:
            continue
    return None, None


def attach_target_page(browser):
    page_urls = []
    for ctx in browser.contexts:
        for page in ctx.pages:
            if page.is_closed():
                continue
            u = safe_url(page)
            page_urls.append(u)
            if TARGET_URL_SUBSTR.lower() in u.lower():
                return page, page_urls

    # deterministic fallback when target tab is not already open
    ctx = browser.new_context()
    page = ctx.new_page()
    target_url = f"https://{TARGET_URL_SUBSTR}"
    page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1200)
    page_urls.append(safe_url(page))
    return page, page_urls


def choose_best_frame(page):
    target = TARGET_URL_SUBSTR.lower()
    frame_stats = []
    for idx, frame in enumerate(page.frames):
        u = safe_url(frame)
        count = 0
        try:
            count += frame.locator("input").count()
            count += frame.locator("select").count()
            count += frame.locator("textarea").count()
        except Exception:
            pass
        frame_stats.append({
            "index": idx,
            "url": u,
            "count": count,
            "captcha": is_captcha_text(u),
            "target_match": target in u.lower(),
        })

    preferred = [x for x in frame_stats if x["target_match"] and not x["captcha"]]
    eligible = [x for x in frame_stats if not x["captcha"]]
    pool = preferred if preferred else eligible
    if not pool:
        return page.main_frame, frame_stats
    best = max(pool, key=lambda x: x["count"])
    return page.frames[best["index"]], frame_stats


def infer_value(field_key: str, selector: str, tag: str, input_type: str):
    low = (field_key + " " + selector).lower()
    if "email" in low:
        return TEST_VALUES["email"]
    if "phone" in low or "tel" in low:
        return TEST_VALUES["phone"]
    if "name" in low:
        return TEST_VALUES["name"]
    if "subscription_type" in low:
        return TEST_VALUES["subscription_type"]
    if "country_code_display" in low:
        return TEST_VALUES["country_code_display"]
    if "password" in low:
        return TEST_VALUES["password"]
    if "consent" in low or "privacy" in low:
        return TEST_VALUES["privacy_consent"]
    if tag == "textarea":
        return "Crop Circuit test message"
    if input_type == "checkbox":
        return "true"
    return "test"


def set_value(frame, selector: str, value: str, tag: str, input_type: str) -> str:
    loc = frame.locator(selector).first
    try:
        frame.wait_for_selector(selector, state="visible", timeout=5000)
    except Exception:
        try:
            loc.scroll_into_view_if_needed(timeout=3000)
            frame.wait_for_selector(selector, state="visible", timeout=5000)
        except Exception:
            return "not_visible"

    try:
        if not loc.is_enabled():
            return "not_enabled"
    except Exception:
        return "not_enabled"

    try:
        if tag == "select":
            picked = loc.select_option(value=value, timeout=5000)
            if not picked:
                picked = loc.select_option(label=value, timeout=5000)
            if not picked:
                opts = loc.locator("option")
                if opts.count() > 0:
                    first_val = (opts.nth(0).get_attribute("value") or "").strip()
                    if first_val:
                        picked = loc.select_option(value=first_val, timeout=5000)
            if not picked:
                return "select_option_failed"
            return ""

        if tag == "input" and input_type == "checkbox":
            if value == "true":
                loc.check(timeout=5000)
            else:
                loc.uncheck(timeout=5000)
            return ""

        loc.click(timeout=2000)
        frame.press(selector, "Control+A")
        frame.press(selector, "Backspace")
        frame.type(selector, value, delay=60)
        return ""
    except Exception:
        return "set_value_failed"


def captcha_required(page, frame) -> bool:
    has_captcha_frame = any(is_captcha_text(safe_url(f)) for f in page.frames)
    if not has_captcha_frame:
        return False

    # If a known solved-token exists and has value, captcha is likely solved.
    token_selectors = [
        "#mtcaptcha-verifiedtoken-1",
        "input[name='mtcaptcha-verifiedtoken']",
        "textarea[name='g-recaptcha-response']",
        "textarea[name='h-captcha-response']",
        "input[name='cf-turnstile-response']",
    ]

    for sel in token_selectors:
        for root in (frame, page.main_frame):
            try:
                loc = root.locator(sel).first
                if loc.count() == 0:
                    continue
                val = (loc.input_value(timeout=1200) or "").strip()
                if val:
                    return False
            except Exception:
                continue
    return True


MORNING_TARGETS_FILE = ROOT / "runtime" / "morning_targets.json"


def load_morning_targets() -> dict:
    """Load morning monetary targets JSON if present."""
    if not MORNING_TARGETS_FILE.exists():
        return {}
    try:
        data = json.loads(MORNING_TARGETS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def merge_target_values(targets: dict) -> dict:
    """Map morning targets into test values overrides. Returns field_key→value dict.

    Supports two modes:
    1. Per-program field_values in morning_targets.json programs array
    2. Global targets mapping (loan_amount, projected_income, etc.)
    """
    overrides: dict[str, str] = {}

    # Check for per-program field_values
    programs = targets.get("programs", [])
    for prog in programs:
        if not isinstance(prog, dict):
            continue
        if prog.get("name") == PROGRAM_NAME:
            fv = prog.get("field_values", {})
            if isinstance(fv, dict):
                for k, v in fv.items():
                    overrides[k] = str(v)
            break

    # Global targets as fallback
    t = targets.get("targets", targets)
    if "requested_amount_usd" in t and "loan_amount" not in overrides:
        overrides["loan_amount"] = str(t["requested_amount_usd"])
    if "monthly_stability_usd" in t and "projected_income" not in overrides:
        overrides["projected_income"] = str(t["monthly_stability_usd"])
    if "projected_income_2026" in t and "projected_income" not in overrides:
        overrides["projected_income"] = str(t["projected_income_2026"])
    if "grant_goal_usd" in t and "grant_goal" not in overrides:
        overrides["grant_goal"] = str(t["grant_goal_usd"])

    # Log unmapped overrides (fields with no matching selector)
    field_map = load_field_map()
    for key in overrides:
        if key not in field_map:
            log_line(f"morning_target_needs_mapping field={key} value={overrides[key]}")

    return overrides


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill and submit grant form")
    parser.add_argument("--skip-captcha-check", action="store_true",
                        help="Skip captcha detection (use after manual captcha solve)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fill fields but do not click submit")
    parser.add_argument("--program-id", default=os.environ.get("PROGRAM_ID", ""),
                        help="Program id for runtime/programs/<program_id> context")
    args = parser.parse_args()

    skip_captcha = args.skip_captcha_check
    dry_run = args.dry_run or os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
    program_id = (args.program_id or "").strip()
    program_state_file = (PROGRAMS_DIR / program_id / "state.json") if program_id else None

    field_map = load_field_map(program_id or None)
    failures: list[dict] = []

    # Load morning targets if available
    morning_targets = load_morning_targets()
    target_overrides = merge_target_values(morning_targets) if morning_targets else {}
    program_input_values = load_program_input_values(program_id or None)
    if program_input_values:
        # Program-scoped values take precedence over morning target/global defaults.
        target_overrides = {**target_overrides, **{k: str(v) for k, v in program_input_values.items()}}
        log_line(f"program_input_loaded program_id={program_id} keys={sorted(program_input_values.keys())}")
    if target_overrides:
        log_line(f"morning_targets_loaded overrides={json.dumps(target_overrides)}")

    if not field_map:
        status = "selector_failure"
        log_line("selector_failure reason=field_map_empty")
        write_status(status, "", "", "", "", [{"field": "field_map", "reason": "empty"}], program_state_file)
        print(json.dumps({"status": status, "reason": "field_map_empty"}))
        return 1

    selected_page_url = ""
    selected_frame_url = ""
    result_url = ""
    screenshot_path = str(LOG_DIR / f"submission_proof_{stamp()}.png")
    filled = []

    with sync_playwright() as p:
        # CDP connect with exponential backoff retries
        browser = None
        last_err = None
        for attempt in range(4):
            try:
                browser = p.chromium.connect_over_cdp(CDP_URL, timeout=15000)
                break
            except Exception as e:
                last_err = e
                wait = 2 ** attempt  # 1, 2, 4 seconds
                log_line(f"cdp_connect_retry attempt={attempt+1} wait={wait}s error={str(e)[:80]}")
                import time
                time.sleep(wait)
        if browser is None:
            status = "runtime_failure"
            log_line(f"cdp_connect_failed after 4 attempts: {str(last_err)[:120]}")
            write_status(status, "", "", "", "", [{"field": "cdp", "reason": "connect_failed"}], program_state_file)
            print(json.dumps({"status": status, "reason": "cdp_connect_failed"}))
            return 1

        page, page_urls = attach_target_page(browser)
        selected_page_url = safe_url(page)
        page.wait_for_timeout(1200)

        # Wait for invisible CAPTCHA to auto-verify (up to 20s)
        captcha_wait_deadline = 20  # seconds
        for _wait in range(captcha_wait_deadline):
            try:
                tok = page.locator("#mtcaptcha-verifiedtoken-1").first
                if tok.count() > 0:
                    val = (tok.input_value(timeout=1000) or "").strip()
                    if val:
                        log_line(f"captcha_auto_verified wait_seconds={_wait+1}")
                        break
            except Exception:
                pass
            page.wait_for_timeout(1000)
        else:
            log_line(f"captcha_auto_verify_timeout after {captcha_wait_deadline}s")

        frame, frame_stats = choose_best_frame(page)
        selected_frame_url = safe_url(frame)

        log_line(f"selected_page_url={selected_page_url}")
        log_line(f"selected_frame_url={selected_frame_url}")
        log_line(f"page_urls={json.dumps(page_urls)}")

        for key, selector in field_map.items():
            if not isinstance(selector, str) or not selector.strip():
                failures.append({"field": key, "selector": str(selector), "reason": "invalid_selector"})
                log_line(f"selector_failure field={key} reason=invalid_selector")
                continue
            if selector == SUBMIT_SELECTOR or key.lower() == "commit":
                continue
            if is_captcha_text(key) or is_captcha_text(selector):
                continue

            resolved_selector, loc = resolve_selector(frame, key, selector)
            try:
                if loc is None or resolved_selector is None:
                    failures.append({"field": key, "selector": selector, "reason": "not_found"})
                    log_line(f"selector_failure field={key} selector={selector} reason=not_found")
                    continue
                if resolved_selector != selector:
                    log_line(f"selector_fallback field={key} primary={selector} using={resolved_selector}")
                tag = (loc.evaluate("e => e.tagName") or "").lower()
                input_type = (loc.get_attribute("type") or "").lower()
                if tag == "input" and input_type == "hidden":
                    continue
                # Use morning target override if available, else infer
                if key in target_overrides:
                    value = target_overrides[key]
                    log_line(f"morning_target_override field={key} value={value}")
                else:
                    value = infer_value(key, resolved_selector, tag, input_type)

                if dry_run:
                    log_line(f"dry_run would_fill field={key} selector={resolved_selector} value={value}")
                    filled.append({"field": key, "selector": resolved_selector, "dry_run": True})
                    continue

                reason = set_value(frame, resolved_selector, value, tag, input_type)
                if reason:
                    failures.append({"field": key, "selector": resolved_selector, "reason": reason})
                    log_line(f"selector_failure field={key} selector={resolved_selector} reason={reason}")
                    continue
                filled.append({"field": key, "selector": resolved_selector})
            except Exception as exc:
                failures.append({"field": key, "selector": resolved_selector or selector, "reason": "exception", "detail": str(exc)[:180]})
                log_line(f"selector_failure field={key} selector={resolved_selector or selector} reason=exception")

        status = "success"
        has_captcha = False

        # Captcha detection (can be skipped for resume after manual solve)
        if not skip_captcha:
            has_captcha = captcha_required(page, frame)
            if has_captcha:
                log_line("captcha_detected")
        elif skip_captcha:
            log_line("captcha_check_skipped (resume mode)")

        if dry_run:
            status = "dry_run_success"
            if has_captcha:
                status = "dry_run_captcha_required"
            log_line(f"dry_run submit_skipped filled={len(filled)} failures={len(failures)} captcha={has_captcha}")
            try:
                page.screenshot(path=screenshot_path, timeout=10000)
            except Exception:
                log_line(f"screenshot_timeout path={screenshot_path}")
            result_url = safe_url(page)
        elif has_captcha:
            status = "captcha_required"
            log_line("captcha_required")
            try:
                page.screenshot(path=screenshot_path, timeout=10000)
            except Exception:
                log_line(f"screenshot_timeout path={screenshot_path}")
            result_url = safe_url(page)
        elif failures:
            status = "selector_failure"
            try:
                page.screenshot(path=screenshot_path, timeout=10000)
            except Exception:
                log_line(f"screenshot_timeout path={screenshot_path}")
            result_url = safe_url(page)
        else:
            try:
                submit_loc = frame.locator(SUBMIT_SELECTOR).first
                submit_loc.wait_for(state="visible", timeout=5000)
                submit_loc.scroll_into_view_if_needed(timeout=5000)
                submit_loc.click(timeout=10000)
                try:
                    page.wait_for_load_state("networkidle", timeout=20000)
                except Exception:
                    pass
                result_url = safe_url(page)
                try:
                    page.screenshot(path=screenshot_path, timeout=10000)
                except Exception:
                    log_line(f"screenshot_timeout path={screenshot_path}")
                # Check for server-side errors after submit
                error_text = ""
                try:
                    err_loc = frame.locator("#errorExplanation, .error, .alert-error, .flash_error").first
                    if err_loc.count() > 0:
                        error_text = (err_loc.inner_text(timeout=3000) or "").strip()[:300]
                except Exception:
                    pass
                if error_text:
                    status = "submit_rejected"
                    failures.append({"field": "server_validation", "reason": "submit_rejected", "detail": error_text})
                    log_line(f"submit_rejected errors={error_text!r}")
                else:
                    status = "success"
                log_line(f"submit_clicked selector={SUBMIT_SELECTOR} result_url={result_url}")
            except Exception as exc:
                status = "submit_failed"
                failures.append({"field": "submit", "selector": SUBMIT_SELECTOR, "reason": "submit_failed", "detail": str(exc)[:180]})
                log_line("submit_failed")
                result_url = safe_url(page)
                try:
                    page.screenshot(path=screenshot_path, timeout=10000)
                except Exception:
                    log_line(f"screenshot_timeout path={screenshot_path}")

        write_status(status, screenshot_path, result_url, selected_page_url, selected_frame_url, failures, program_state_file)

        out = {
            "status": status,
            "program_id": program_id or "legacy_default",
            "timestamp_utc": now_utc(),
            "selected_page_url": selected_page_url,
            "selected_frame_url": selected_frame_url,
            "result_url": result_url,
            "screenshot": screenshot_path,
            "filled_count": len(filled),
            "failure_count": len(failures),
            "failures": failures,
            "submit_selector": SUBMIT_SELECTOR,
            "frame_stats": frame_stats,
        }
        print(json.dumps(out))

    if status in {"success", "captcha_required", "dry_run_success", "dry_run_captcha_required"}:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
