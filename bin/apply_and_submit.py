#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
LOG_DIR = ROOT / "logs"
HIT_LOG = LOG_DIR / "hit_submit.log"
DEFAULT_CDP = "http://127.0.0.1:9222"
FIELD_MAP_FILE = ROOT / "runtime" / "field_map.json"


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_int(val, default=0) -> int:
    try:
        return int(str(val).replace("$", "").replace(",", "").strip())
    except Exception:
        return default


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "program"


def append_hit_log(payload: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with HIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def safe_url(page) -> str:
    try:
        return page.url or ""
    except Exception:
        return ""


def safe_title(page) -> str:
    try:
        return page.title()
    except Exception:
        return ""


def pick_visible(pages):
    for p in pages:
        try:
            if p.evaluate("() => document.visibilityState") == "visible":
                return p
        except Exception:
            continue
    return pages[0] if pages else None


def preflight_cdp(cdp_url: str) -> tuple[bool, str]:
    ep = cdp_url.rstrip("/") + "/json/version"
    try:
        with urllib.request.urlopen(ep, timeout=3) as r:
            if r.status != 200:
                return False, f"cdp_preflight_status_{r.status}"
        return True, ""
    except Exception as exc:
        return False, f"cdp_preflight_failed: {exc}"


def find_or_open_page(browser, target_url: str):
    pages = []
    for ctx in browser.contexts:
        pages.extend([pg for pg in ctx.pages if not pg.is_closed()])

    if target_url:
        lt = target_url.lower()
        matches = []
        for pg in pages:
            u = safe_url(pg).lower()
            if u.startswith(lt) or lt in u:
                matches.append(pg)
        if matches:
            return pick_visible(matches) or matches[0]

    chosen = pick_visible(pages)
    if chosen:
        return chosen

    if target_url:
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        pg = ctx.new_page()
        pg.goto(target_url, wait_until="domcontentloaded", timeout=45000)
        return pg
    return None


def fill_mapped_fields(page, targets: dict, field_map: dict) -> tuple[list[str], list[str]]:
    filled = []
    errors = []
    for key, selector in field_map.items():
        if key not in targets:
            errors.append(f"missing_target_key:{key}")
            continue
        value = targets.get(key)
        if value is None:
            errors.append(f"null_target_value:{key}")
            continue
        sval = str(parse_int(value, 0)) if isinstance(value, (int, float, str)) else str(value)
        if not str(selector).strip():
            errors.append(f"empty_selector:{key}")
            continue
        try:
            loc = page.locator(str(selector)).first
            if loc.count() == 0:
                errors.append(f"field_not_found:{key}:{selector}")
                continue
            loc.fill(sval, timeout=3000)
            filled.append(key)
        except Exception as exc:
            errors.append(f"field_fill_failed:{key}:{selector}:{exc}")
    return filled, errors


def click_submit(page, submit_selector: str) -> tuple[bool, str, str]:
    selectors = []
    if submit_selector:
        selectors.append(submit_selector)
    selectors.extend(["input[type='submit']", "button:has-text('Submit')", "button:has-text('Continue')"])
    last_err = ""
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                loc.click(timeout=5000)
                return True, sel, ""
        except Exception as exc:
            last_err = str(exc)
    return False, "", last_err


def screenshot(page, out_path: str) -> tuple[str, str]:
    try:
        page.wait_for_timeout(600)
        page.screenshot(path=out_path, full_page=False, timeout=9000)
        return out_path, ""
    except Exception as exc:
        try:
            session = page.context.new_cdp_session(page)
            data = session.send("Page.captureScreenshot", {"format": "png"}).get("data", "")
            if data:
                Path(out_path).write_bytes(base64.b64decode(data))
                return out_path, f"screenshot_fallback_used:{exc}"
        except Exception as cdp_exc:
            return "", f"screenshot_failed:{exc};cdp_fallback_failed:{cdp_exc}"
        return "", f"screenshot_failed:{exc}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--program-index", type=int, required=True)
    args = ap.parse_args()

    session_path = Path(args.session)
    payload = json.loads(session_path.read_text(encoding="utf-8"))
    targets = payload.get("targets", {}) if isinstance(payload, dict) else {}
    programs = payload.get("programs", []) if isinstance(payload, dict) else []
    if not isinstance(programs, list) or args.program_index < 0 or args.program_index >= len(programs):
        out = {
            "status": "error",
            "program": "",
            "selected_page_url": "",
            "filled_fields": [],
            "click_selector": "",
            "screenshot_path": "",
            "errors": [f"invalid_program_index:{args.program_index}"],
        }
        print(json.dumps(out))
        append_hit_log(out)
        return 2

    program = programs[args.program_index] if isinstance(programs[args.program_index], dict) else {}
    name = str(program.get("name", "")).strip() or f"program_{args.program_index}"
    target_url = str(program.get("target_url", "")).strip()
    submit_selector = str(program.get("submit_selector", "")).strip()
    field_map = program.get("field_map", {}) if isinstance(program.get("field_map", {}), dict) else {}
    # Merge discovered field-map selectors from runtime/field_map.json if present.
    if FIELD_MAP_FILE.exists():
        try:
            fm = json.loads(FIELD_MAP_FILE.read_text(encoding="utf-8"))
            if isinstance(fm, dict):
                # Supports both per-program map and top-level direct keys.
                per_prog = fm.get(name, {})
                if isinstance(per_prog, dict):
                    merged = dict(per_prog)
                    merged.update(field_map)
                    field_map = merged
                else:
                    merged = {k: v for k, v in fm.items() if isinstance(v, str)}
                    merged.update(field_map)
                    field_map = merged
        except Exception:
            pass
    cdp_url = os.environ.get("CDP_URL", DEFAULT_CDP).strip()
    dry_run = os.environ.get("DRY_RUN", "0") == "1"

    ok, pre_err = preflight_cdp(cdp_url)
    if not ok:
        out = {
            "status": "error",
            "program": name,
            "selected_page_url": "",
            "filled_fields": [],
            "click_selector": "",
            "screenshot_path": "",
            "errors": [pre_err],
        }
        print(json.dumps(out))
        append_hit_log(out)
        return 3

    screenshot_path = str(LOG_DIR / f"submission_proof_{now_stamp()}_{slugify(name)}.png")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        out = {
            "status": "error",
            "program": name,
            "selected_page_url": "",
            "filled_fields": [],
            "click_selector": "",
            "screenshot_path": "",
            "errors": [f"playwright_import_failed:{exc}"],
        }
        print(json.dumps(out))
        append_hit_log(out)
        return 4

    errors = []
    filled_fields = []
    click_selector = ""
    selected_url = ""
    selected_title = ""
    status = "error"

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(cdp_url, timeout=15000)
        except Exception as exc:
            out = {
                "status": "error",
                "program": name,
                "selected_page_url": "",
                "filled_fields": [],
                "click_selector": "",
                "screenshot_path": "",
                "errors": [f"cdp_connect_failed:{exc}"],
            }
            print(json.dumps(out))
            append_hit_log(out)
            return 5

        page = find_or_open_page(browser, target_url)
        if page is None:
            out = {
                "status": "error",
                "program": name,
                "selected_page_url": "",
                "filled_fields": [],
                "click_selector": "",
                "screenshot_path": "",
                "errors": ["no_target_page_found"],
            }
            print(json.dumps(out))
            append_hit_log(out)
            return 6

        try:
            page.bring_to_front()
            page.wait_for_load_state("domcontentloaded", timeout=8000)
        except Exception:
            pass

        selected_url = safe_url(page)
        selected_title = safe_title(page)

        filled_fields, fill_errors = fill_mapped_fields(page, targets, field_map)
        errors.extend(fill_errors)

        page.wait_for_timeout(400)
        if errors:
            status = "error"
        elif dry_run:
            status = "dry_run"
        else:
            clicked, used_sel, click_err = click_submit(page, submit_selector)
            click_selector = used_sel
            if clicked:
                status = "clicked"
            else:
                status = "not_found"
                errors.append(f"submit_not_found:{click_err}" if click_err else "submit_not_found")

        shot, serr = screenshot(page, screenshot_path)
        if serr:
            errors.append(serr)
        screenshot_path = shot

    out = {
        "status": status,
        "program": name,
        "selected_page_url": selected_url,
        "selected_page_title": selected_title,
        "filled_fields": filled_fields,
        "click_selector": click_selector,
        "screenshot_path": screenshot_path,
        "errors": errors,
    }
    print(json.dumps(out))
    append_hit_log(out)
    return 0 if status in {"clicked", "dry_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
