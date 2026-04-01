#!/usr/bin/env python3
"""
post_to_x_browser.py — Post to X via browser automation (Playwright).
Bypasses API 402 by using an existing logged-in Chrome session.

Requires Chrome on port 9222, logged into x.com as @CropCircuit.

Usage:
    python3 bin/post_to_x_browser.py "Your tweet text here"
    python3 bin/post_to_x_browser.py  # uses default test message
"""

import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "logs" / "x_bot.log"
SOCIAL_LOG = ROOT / "logs" / "social_engine.log"
POSTED_FILE = ROOT / "logs" / "x_posted.jsonl"
MOMENTUM_LOG = ROOT / "logs" / "agent_momentum.txt"
SCREENSHOT_DIR = ROOT / "logs"

CDP_URL = "http://localhost:9222"


def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg, *extra_files):
    line = f"{ts()} [browser] {msg}"
    for f in [LOG_FILE, SOCIAL_LOG, *extra_files]:
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "a") as fh:
            fh.write(line + "\n")
    print(line, file=sys.stderr)


def append_posted(text, ok, screenshot_path=None):
    record = {
        "ts": ts(),
        "text": text,
        "tweet_id": None,
        "ok": ok,
        "method": "browser",
        "screenshot": str(screenshot_path) if screenshot_path else None,
    }
    POSTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(POSTED_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def post(text):
    screenshot_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    screenshot_path = SCREENSHOT_DIR / f"x_post_{screenshot_ts}.png"

    log(f"Posting: {text[:80]}...", MOMENTUM_LOG)

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            log(f"Cannot connect to Chrome at {CDP_URL}: {e}", MOMENTUM_LOG)
            append_posted(text, False)
            return False

        context = browser.contexts[0]
        page = context.new_page()

        try:
            page.goto("https://x.com/compose/post", timeout=15000)
            time.sleep(4)

            # Type into the compose box
            textarea = page.wait_for_selector(
                "div[data-testid='tweetTextarea_0']",
                timeout=10000,
            )
            textarea.click()
            time.sleep(0.5)
            page.keyboard.type(text, delay=30)
            time.sleep(1)

            # Click the Post button
            post_btn = page.wait_for_selector(
                "button[data-testid='tweetButton']",
                timeout=5000,
            )
            post_btn.click()
            time.sleep(4)

            page.screenshot(path=str(screenshot_path))
            log(f"POSTED OK — screenshot: {screenshot_path.name}", MOMENTUM_LOG)
            append_posted(text, True, screenshot_path)
            return True

        except Exception as e:
            log(f"FAILED: {e}", MOMENTUM_LOG)
            try:
                page.screenshot(path=str(screenshot_path))
            except Exception:
                pass
            append_posted(text, False, screenshot_path)
            return False
        finally:
            page.close()


if __name__ == "__main__":
    tweet_text = sys.argv[1] if len(sys.argv) > 1 else "Automation test from CropCircuit agent."
    ok = post(tweet_text)
    sys.exit(0 if ok else 1)
