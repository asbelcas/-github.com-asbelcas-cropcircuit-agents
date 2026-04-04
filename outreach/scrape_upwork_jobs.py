#!/usr/bin/env python3
"""
Scrape Upwork job browse for Python/automation/data script requests.

Two strategies attempted in order:
  1. Public category pages (/freelance-jobs/python/ etc.) — no auth needed,
     more stable markup
  2. Search results via Playwright — JS-rendered, may hit login wall

Output: outreach/upwork_leads.csv
Debug screenshots: outreach/debug/upwork_*.png  (first run only)
"""

import csv
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

# Public category pages — no login required, stable HTML
CATEGORY_URLS = [
    "https://www.upwork.com/freelance-jobs/python/",
    "https://www.upwork.com/freelance-jobs/automation/",
    "https://www.upwork.com/freelance-jobs/data-entry/",
    "https://www.upwork.com/freelance-jobs/excel/",
    "https://www.upwork.com/freelance-jobs/web-scraping/",
]

SEARCH_QUERIES = [
    "python script automation",
    "excel automation script",
    "google sheets automation",
    "web scraping python",
    "csv data processing python",
]

SKIP_WORDS = [
    "senior", "full-time", "full time", "equity", "co-founder",
    "react", "node.js", "mobile app", "ios", "android", "blockchain",
]

SCORE_KEYWORDS = [
    "python", "script", "automation", "automate", "excel",
    "spreadsheet", "csv", "scrape", "api", "data", "workflow",
    "google sheets", "repetitive",
]

OUT = Path(__file__).parent / "upwork_leads.csv"
DEBUG_DIR = Path(__file__).parent / "debug"


def score(title: str, snippet: str = "") -> int:
    text = (title + " " + snippet).lower()
    return sum(1 for kw in SCORE_KEYWORDS if kw in text)


def scrape_category_pages(session: requests.Session) -> list[dict]:
    """Scrape Upwork public category pages — no JS, no auth needed."""
    leads = []
    seen: set[str] = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for url in CATEGORY_URLS:
        print(f"  Category: {url}")
        try:
            resp = session.get(url, headers=headers, timeout=20)
            if resp.status_code != 200:
                print(f"    HTTP {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Upwork category page job cards
            cards = (
                soup.select("article.job-tile") or
                soup.select("[data-test='job-tile']") or
                soup.select(".jobs-list article")
            )
            print(f"    {len(cards)} cards (HTML)")

            for card in cards:
                title_el = card.select_one("h2 a, .job-tile-title a, h3 a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                job_url = f"https://www.upwork.com{href}" if href.startswith("/") else href

                if not title or job_url in seen:
                    continue
                if any(skip in title.lower() for skip in SKIP_WORDS):
                    continue
                seen.add(job_url)

                budget_el = card.select_one("[data-test='budget'], .js-budget, .budget")
                budget = budget_el.get_text(strip=True) if budget_el else ""

                desc_el = card.select_one("[data-test='job-description-text'], .job-description, p")
                snippet = desc_el.get_text(strip=True)[:200].replace("\n", " ") if desc_el else ""

                s = score(title, snippet)
                leads.append({
                    "title": title, "score": s, "budget": budget,
                    "url": job_url, "source": "category_page",
                    "snippet": snippet, "contact_attempted": "", "notes": "",
                })

        except Exception as e:
            print(f"    failed: {e}")

        time.sleep(1.5)

    return leads


def scrape_search_playwright(queries: list[str]) -> list[dict]:
    """
    Playwright-based search scraper.
    Upwork may redirect to login — we detect that and bail gracefully.
    Saves a debug screenshot on the first query for diagnostics.
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("  Playwright not installed, skipping search scrape.")
        return []

    leads = []
    seen: set[str] = set()
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        for i, query in enumerate(queries):
            print(f"  Search: {query!r}")
            params = {"q": query, "sort": "recency", "payment_verified": "1"}
            url = "https://www.upwork.com/nx/jobs/search/?" + urlencode(params)

            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")

                # Save screenshot on first query for debugging
                if i == 0:
                    page.screenshot(path=str(DEBUG_DIR / "upwork_first_search.png"))
                    print(f"    debug screenshot → {DEBUG_DIR}/upwork_first_search.png")

                # Detect login wall
                if "/login" in page.url or "/ab/account-security" in page.url:
                    print("    ⚠ Redirected to login — Upwork requires auth for search.")
                    print("    Skipping remaining search queries.")
                    break

                # Wait for job cards or timeout gracefully
                try:
                    page.wait_for_selector(
                        "[data-test='job-tile-list'], .job-tile, article.job-tile",
                        timeout=8000
                    )
                except PWTimeout:
                    print("    No job cards appeared (possible bot detection or empty results)")
                    page.screenshot(path=str(DEBUG_DIR / f"upwork_query_{i}_empty.png"))
                    time.sleep(2)
                    continue

                cards = (
                    page.query_selector_all("[data-test='job-tile-list'] section") or
                    page.query_selector_all("article.job-tile") or
                    page.query_selector_all(".job-tile")
                )
                print(f"    {len(cards)} cards")

                for card in cards:
                    try:
                        title_el = card.query_selector("h2 a, .job-tile-title a")
                        title = title_el.inner_text().strip() if title_el else ""
                        href = title_el.get_attribute("href") if title_el else ""
                        job_url = f"https://www.upwork.com{href}" if href and href.startswith("/") else href

                        if not title or job_url in seen:
                            continue
                        if any(skip in title.lower() for skip in SKIP_WORDS):
                            continue
                        seen.add(job_url)

                        budget_el = card.query_selector("[data-test='budget'], .js-budget")
                        budget = budget_el.inner_text().strip() if budget_el else ""

                        desc_el = card.query_selector("[data-test='job-description-text']")
                        snippet = desc_el.inner_text().strip()[:200].replace("\n", " ") if desc_el else ""

                        s = score(title, snippet)
                        leads.append({
                            "title": title, "score": s, "budget": budget,
                            "url": job_url, "source": f"search:{query}",
                            "snippet": snippet, "contact_attempted": "", "notes": "",
                        })
                    except Exception:
                        continue

            except Exception as e:
                print(f"    failed: {e}")
                continue

            time.sleep(2)

        browser.close()

    return leads


def main():
    session = requests.Session()
    all_leads: list[dict] = []

    print("Strategy 1: public category pages (requests + BeautifulSoup)...")
    all_leads.extend(scrape_category_pages(session))

    print("\nStrategy 2: search via Playwright...")
    all_leads.extend(scrape_search_playwright(SEARCH_QUERIES))

    # Deduplicate by title and sort
    seen: set[str] = set()
    unique = []
    for lead in sorted(all_leads, key=lambda x: x["score"], reverse=True):
        key = lead["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(lead)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["title", "score", "budget", "url", "source",
                  "snippet", "contact_attempted", "notes"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique)

    meta = {"scraped_at": datetime.now().isoformat(), "total_leads": len(unique),
            "category_urls": CATEGORY_URLS, "search_queries": SEARCH_QUERIES}
    (OUT.parent / "upwork_leads_meta.json").write_text(json.dumps(meta, indent=2))

    print(f"\nFound {len(unique)} leads → {OUT}")
    if unique:
        for i, lead in enumerate(unique[:10], 1):
            print(f"  {i:2}. score={lead['score']}  {lead['budget'] or '?':>8}  "
                  f"[{lead['source'].split(':')[0]}]  {lead['title'][:55]}")
    else:
        print("  0 leads — check debug screenshots in outreach/debug/ for diagnostics")


if __name__ == "__main__":
    main()
