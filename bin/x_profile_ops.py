#!/usr/bin/env python3
"""
x_profile_ops.py — X profile operations via browser automation.

Commands:
    update_bio TEXT     Update profile bio
    follow USER         Follow a user by handle
    like_post URL       Like a post by URL
    search_follow QUERY Search and follow relevant accounts

All via Chrome CDP on port 9222.
"""

import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
GROWTH_LOG = ROOT / "logs" / "twitter_growth.log"
MOMENTUM_LOG = ROOT / "logs" / "agent_momentum.txt"
SCREENSHOT_DIR = ROOT / "logs"

CDP_URL = "http://localhost:9222"


def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg):
    line = f"{ts()} [profile] {msg}"
    for f in [GROWTH_LOG, MOMENTUM_LOG]:
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "a") as fh:
            fh.write(line + "\n")
    print(line, file=sys.stderr)


def get_browser():
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(CDP_URL)
    return p, browser


def update_bio(bio_text):
    """Update the X profile bio."""
    log(f"Updating bio: {bio_text[:60]}...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.new_page()
        try:
            page.goto("https://x.com/settings/profile", timeout=15000)
            time.sleep(3)

            # Find bio textarea
            bio_field = page.wait_for_selector(
                "textarea[name='description'], div[aria-label='Bio']",
                timeout=10000,
            )
            bio_field.click()
            # Select all and replace
            page.keyboard.press("Control+a")
            page.keyboard.type(bio_text, delay=20)
            time.sleep(1)

            # Save
            save_btn = page.query_selector("button[data-testid='Profile_Save_Button']")
            if not save_btn:
                save_btn = page.query_selector("div[data-testid='Profile_Save_Button']")
            if save_btn:
                save_btn.click()
                time.sleep(2)
                log("Bio updated successfully")
            else:
                log("Could not find Save button — bio typed but not saved")

            page.screenshot(path=str(SCREENSHOT_DIR / "x_bio_update.png"))
        except Exception as e:
            log(f"Bio update failed: {e}")
            page.screenshot(path=str(SCREENSHOT_DIR / "x_bio_error.png"))
        finally:
            page.close()


def follow_user(handle):
    """Follow a user by their handle."""
    handle = handle.lstrip("@")
    log(f"Following @{handle}...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.new_page()
        try:
            page.goto(f"https://x.com/{handle}", timeout=15000)
            time.sleep(3)

            # Look for Follow button (not Following)
            follow_btn = page.query_selector(
                f"div[data-testid='placementTracking'] button[aria-label*='Follow @{handle}']"
            )
            if not follow_btn:
                # Try generic follow button
                buttons = page.query_selector_all("button")
                for btn in buttons:
                    label = btn.get_attribute("aria-label") or ""
                    text = btn.inner_text().strip()
                    if text == "Follow" and "Follow @" in label:
                        follow_btn = btn
                        break

            if follow_btn:
                follow_btn.click()
                time.sleep(1)
                log(f"Followed @{handle}")
                return True
            else:
                # Check if already following
                following_check = page.query_selector(
                    f"button[aria-label*='Following @{handle}']"
                )
                if following_check:
                    log(f"Already following @{handle}")
                    return True
                log(f"Could not find Follow button for @{handle}")
                return False
        except Exception as e:
            log(f"Follow failed for @{handle}: {e}")
            return False
        finally:
            page.close()


def search_and_follow(query, max_follows=5):
    """Search X for a query, follow top relevant accounts."""
    log(f"Searching '{query}' to find accounts...")
    followed = []
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.new_page()
        try:
            # Search people
            from urllib.parse import quote
            page.goto(
                f"https://x.com/search?q={quote(query)}&src=typed_query&f=user",
                timeout=15000,
            )
            time.sleep(4)

            # Find follow buttons in search results
            buttons = page.query_selector_all("button")
            count = 0
            for btn in buttons:
                if count >= max_follows:
                    break
                text = btn.inner_text().strip()
                label = btn.get_attribute("aria-label") or ""
                if text == "Follow" and "Follow @" in label:
                    handle = label.replace("Follow @", "").strip()
                    btn.click()
                    time.sleep(2)
                    log(f"Followed @{handle} from search '{query}'")
                    followed.append(handle)
                    count += 1

            page.screenshot(
                path=str(SCREENSHOT_DIR / f"x_search_{query[:20].replace(' ','_')}.png")
            )
        except Exception as e:
            log(f"Search follow failed for '{query}': {e}")
        finally:
            page.close()
    return followed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 x_profile_ops.py <command> [args]")
        print("Commands: update_bio, follow, search_follow")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "update_bio" and len(sys.argv) > 2:
        update_bio(sys.argv[2])
    elif cmd == "follow" and len(sys.argv) > 2:
        follow_user(sys.argv[2])
    elif cmd == "search_follow" and len(sys.argv) > 2:
        max_f = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        search_and_follow(sys.argv[2], max_f)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
