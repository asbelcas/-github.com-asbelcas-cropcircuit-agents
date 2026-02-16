#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/asbelcas/cropcircuit')
LOG_DIR = ROOT / 'logs'
DEFAULT_CDP = 'http://127.0.0.1:9222'

AMOUNT_LABEL_RE = re.compile(r'(requested|loan amount|amount requested|grant amount|funding amount)', re.I)


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def parse_int(val, default=0):
    try:
        return int(str(val).replace('$', '').replace(',', '').strip())
    except Exception:
        return default


def safe_url(page) -> str:
    try:
        return page.url or ''
    except Exception:
        return ''


def safe_title(page) -> str:
    try:
        return page.title()
    except Exception:
        return ''


def pick_visible(pages):
    for p in pages:
        try:
            if p.evaluate('() => document.visibilityState') == 'visible':
                return p
        except Exception:
            continue
    return pages[0] if pages else None


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

    # fallback to active visible page only if no match
    chosen = pick_visible(pages)
    if chosen:
        return chosen

    # open new tab only if target_url exists
    if target_url:
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page()
        page.goto(target_url, wait_until='domcontentloaded', timeout=45000)
        return page
    return None


def fill_amount_fields(page, amount: int):
    filled = []
    amount_str = str(amount)

    # 1) Label-based matching
    try:
        labels = page.locator('label')
        count = labels.count()
        for i in range(count):
            lab = labels.nth(i)
            txt = (lab.inner_text(timeout=1000) or '').strip()
            if not txt or not AMOUNT_LABEL_RE.search(txt):
                continue
            target_input = None
            for_attr = (lab.get_attribute('for') or '').strip()
            if for_attr:
                cand = page.locator(f"#{for_attr}").first
                if cand.count() > 0:
                    target_input = cand
            if target_input is None:
                cand = lab.locator('input, textarea').first
                if cand.count() > 0:
                    target_input = cand
            if target_input is not None:
                try:
                    target_input.fill(amount_str, timeout=2000)
                    filled.append({'strategy': 'label', 'label': txt})
                except Exception:
                    pass
    except Exception:
        pass

    # 2) Name/id heuristics
    for sel in [
        "input[name*='amount' i]",
        "input[id*='amount' i]",
        "textarea[name*='amount' i]",
        "textarea[id*='amount' i]",
    ]:
        try:
            loc = page.locator(sel)
            cnt = loc.count()
            for i in range(cnt):
                el = loc.nth(i)
                try:
                    if not el.is_visible():
                        continue
                except Exception:
                    continue
                try:
                    el.fill(amount_str, timeout=1500)
                    filled.append({'strategy': 'heuristic', 'selector': sel, 'index': i})
                except Exception:
                    pass
        except Exception:
            continue

    # de-dup simple
    uniq = []
    seen = set()
    for item in filled:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            uniq.append(item)
    return uniq


def click_submit(page, submit_selector: str):
    selectors = []
    if submit_selector:
        selectors.append(submit_selector)
    selectors.extend([
        "input[type='submit']",
        "button:has-text('Submit')",
        "button:has-text('Continue')",
    ])
    last_err = ''
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                loc.click(timeout=5000)
                return True, sel, ''
        except Exception as exc:
            last_err = str(exc)
    return False, '', last_err


def screenshot_best_effort(page, path: str):
    try:
        page.wait_for_timeout(800)
        page.screenshot(path=path, full_page=False, timeout=10000)
        return path, ''
    except Exception as exc:
        # Fallback to direct CDP screenshot capture if Playwright screenshot blocks.
        try:
            session = page.context.new_cdp_session(page)
            out = session.send("Page.captureScreenshot", {"format": "png"})
            data = out.get("data", "")
            if data:
                Path(path).write_bytes(base64.b64decode(data))
                return path, f'screenshot_fallback_used: {exc}'
        except Exception as cdp_exc:
            return '', f'screenshot_failed: {exc}; cdp_fallback_failed: {cdp_exc}'
        return '', f'screenshot_failed: {exc}'


def main() -> int:
    targets_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('TARGETS_FILE', str(ROOT / 'runtime/morning_targets.json'))
    cdp_url = os.environ.get('CDP_URL', DEFAULT_CDP).strip()
    env_target_url = os.environ.get('TARGET_URL', '').strip() or os.environ.get('GRANT_TARGET_URL', '').strip()
    env_submit_selector = os.environ.get('SUBMIT_SELECTOR', '').strip() or os.environ.get('SELECTOR_HINT', '').strip()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = str(LOG_DIR / f'submission_proof_{now_stamp()}.png')

    requested_amount = 25000
    monthly = 3000
    goal = 50000
    programs = []

    if Path(targets_file).exists():
        try:
            payload = json.loads(Path(targets_file).read_text(encoding='utf-8'))
            t = payload.get('targets', {}) if isinstance(payload, dict) else {}
            requested_amount = parse_int(t.get('requested_amount_usd', 25000), 25000)
            monthly = parse_int(t.get('monthly_stability_usd', 3000), 3000)
            goal = parse_int(t.get('grant_goal_usd', 50000), 50000)
            p = payload.get('programs', []) if isinstance(payload, dict) else []
            if isinstance(p, list):
                programs = p
        except Exception:
            pass

    if not programs:
        programs = [{
            'name': 'Manual Target',
            'target_url': env_target_url,
            'submit_selector': env_submit_selector,
        }]

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        out = {
            'status': 'error',
            'selected_page_url': '',
            'selected_page_title': '',
            'filled_fields': [],
            'click_selector': '',
            'screenshot_path': '',
            'error': f'playwright_import_failed: {exc}',
        }
        print(json.dumps(out))
        return 2

    program_results = []
    overall_ok = True

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(cdp_url, timeout=15000)
        except Exception as exc:
            out = {
                'status': 'error',
                'selected_page_url': '',
                'selected_page_title': '',
                'filled_fields': [],
                'click_selector': '',
                'screenshot_path': '',
                'error': f'cdp_connect_failed: {exc}',
            }
            print(json.dumps(out))
            return 3

        for prog in programs:
            name = str(prog.get('name', '')).strip() or 'Program'
            target_url = str(prog.get('target_url', '')).strip() or env_target_url
            submit_selector = str(prog.get('submit_selector', '')).strip() or env_submit_selector

            page = find_or_open_page(browser, target_url)
            if page is None:
                program_results.append({
                    'name': name,
                    'status': 'error',
                    'selected_page_url': '',
                    'selected_page_title': '',
                    'filled_fields': [],
                    'click_selector': '',
                    'screenshot_path': '',
                    'error': 'no_target_page_found',
                })
                overall_ok = False
                continue

            try:
                page.bring_to_front()
                page.wait_for_load_state('domcontentloaded', timeout=8000)
            except Exception:
                pass

            filled = fill_amount_fields(page, requested_amount)
            # If we found nothing and this looks like a monthly/goal form, try them as fallback.
            if not filled:
                filled.extend(fill_amount_fields(page, monthly))
            if not filled:
                filled.extend(fill_amount_fields(page, goal))

            clicked, used_sel, click_err = click_submit(page, submit_selector)
            shot, serr = screenshot_best_effort(page, screenshot_path)
            err = ''
            if not clicked:
                err = f'submit_not_found: {click_err}' if click_err else 'submit_not_found'
                overall_ok = False
            if serr:
                err = f'{err}; {serr}'.strip('; ')

            program_results.append({
                'name': name,
                'status': 'clicked' if clicked else 'not_found',
                'selected_page_url': safe_url(page),
                'selected_page_title': safe_title(page),
                'filled_fields': filled,
                'click_selector': used_sel,
                'screenshot_path': shot,
                'error': err,
            })

    # Flatten primary result (first program) + include all details.
    primary = program_results[0] if program_results else {
        'status': 'error',
        'selected_page_url': '',
        'selected_page_title': '',
        'filled_fields': [],
        'click_selector': '',
        'screenshot_path': '',
        'error': 'no_programs'
    }
    out = {
        'status': 'clicked' if overall_ok else primary.get('status', 'error'),
        'selected_page_url': primary.get('selected_page_url', ''),
        'selected_page_title': primary.get('selected_page_title', ''),
        'filled_fields': primary.get('filled_fields', []),
        'click_selector': primary.get('click_selector', ''),
        'screenshot_path': primary.get('screenshot_path', ''),
        'error': primary.get('error', ''),
        'program_results': program_results,
    }
    print(json.dumps(out))
    return 0 if overall_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
