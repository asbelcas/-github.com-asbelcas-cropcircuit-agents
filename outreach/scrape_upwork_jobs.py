#!/usr/bin/env python3
"""
Scrape Upwork job browse for Python/automation/data script requests.

Uses Playwright to render the public job search page (no account needed).
Targets fixed-price jobs under $500 from non-technical clients.

Output: outreach/upwork_leads.csv
"""

import csv
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

SEARCHES = [
    "python script automation",
    "excel automation script",
    "google sheets automation",
    "web scraping python",
    "csv data processing python",
    "automate repetitive task python",
]

SKIP_WORDS = [
    "senior", "full-time", "full time", "equity", "co-founder",
    "agency", "react", "node.js", "mobile app", "ios", "android",
]

OUT = Path(__file__).parent / "upwork_leads.csv"


def build_url(query: str) -> str:
    params = {
        "q": query,
        "sort": "recency",
        "payment_verified": "1",
    }
    return "https://www.upwork.com/nx/jobs/search/?" + urlencode(params)


def scrape_with_playwright(searches: list[str]) -> list[dict]:
    from playwright.sync_api import sync_playwright

    leads = []
    seen_urls: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for query in searches:
            print(f"  Searching: {query!r}")
            url = build_url(query)
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                time.sleep(3)  # let JS render

                # Upwork job cards — selector may need updating if Upwork changes markup
                cards = page.query_selector_all("[data-test='job-tile-list'] section")
                if not cards:
                    # Fallback selector
                    cards = page.query_selector_all(".job-tile")

                print(f"    {len(cards)} cards found")

                for card in cards:
                    try:
                        title_el = card.query_selector("h2 a, .job-tile-title a")
                        title = title_el.inner_text().strip() if title_el else ""
                        href = title_el.get_attribute("href") if title_el else ""
                        job_url = f"https://www.upwork.com{href}" if href and not href.startswith("http") else href

                        if not title or job_url in seen_urls:
                            continue
                        if any(skip in title.lower() for skip in SKIP_WORDS):
                            continue

                        seen_urls.add(job_url)

                        # Budget
                        budget_el = card.query_selector("[data-test='budget'], .js-budget")
                        budget = budget_el.inner_text().strip() if budget_el else ""

                        # Description snippet
                        desc_el = card.query_selector("[data-test='job-description-text'], .job-description")
                        snippet = desc_el.inner_text().strip()[:200].replace("\n", " ") if desc_el else ""

                        # Score
                        text = (title + " " + snippet).lower()
                        keywords = ["python", "script", "automation", "automate", "excel",
                                    "spreadsheet", "csv", "scrape", "api", "data", "workflow"]
                        score = sum(1 for kw in keywords if kw in text)

                        leads.append({
                            "title": title,
                            "score": score,
                            "budget": budget,
                            "url": job_url,
                            "query": query,
                            "snippet": snippet,
                            "contact_attempted": "",
                            "notes": "",
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
    print(f"Scraping Upwork for {len(SEARCHES)} queries...")
    leads = scrape_with_playwright(SEARCHES)

    # Deduplicate and sort
    seen: set[str] = set()
    unique = []
    for lead in sorted(leads, key=lambda x: x["score"], reverse=True):
        key = lead["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(lead)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["title", "score", "budget", "url", "query", "snippet",
                  "contact_attempted", "notes"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique)

    meta = {"scraped_at": datetime.now().isoformat(), "total_leads": len(unique),
            "searches": SEARCHES}
    (OUT.parent / "upwork_leads_meta.json").write_text(json.dumps(meta, indent=2))

    print(f"\nFound {len(unique)} leads → {OUT}")
    for i, lead in enumerate(unique[:10], 1):
        print(f"  {i:2}. score={lead['score']}  {lead['budget'] or '?':>8}  {lead['title'][:60]}")


if __name__ == "__main__":
    main()
