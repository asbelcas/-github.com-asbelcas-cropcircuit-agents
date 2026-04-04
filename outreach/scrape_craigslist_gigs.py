#!/usr/bin/env python3
"""
Scrape Craigslist computer gigs for small-business automation leads.

Craigslist "computer gigs" is where non-tech businesses post one-off tasks:
  "need someone to write a script", "help with Excel automation", etc.
These are better cold-outreach targets than tech companies hiring FT engineers.

Usage:
  python scrape_craigslist_gigs.py
  python scrape_craigslist_gigs.py --cities sfbay newyork chicago --output leads.csv
  python scrape_craigslist_gigs.py --keywords "python" "excel" "automation" "script"
"""

import argparse
import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependencies: pip install requests beautifulsoup4")
    raise SystemExit(1)

# Cities with large Craigslist presence — add more as needed
DEFAULT_CITIES = [
    "sfbay", "newyork", "chicago", "losangeles", "seattle",
    "austin", "boston", "denver", "atlanta", "miami",
]

# Keywords that signal a manual-workflow / automation opportunity
OPPORTUNITY_KEYWORDS = [
    "python", "script", "automation", "automate", "excel", "spreadsheet",
    "csv", "scrape", "scraper", "scraping", "data entry", "data processing",
    "web scraping", "api", "bot", "macro", "vba", "google sheets",
    "database", "etl", "workflow", "repetitive", "parse", "extract",
]

# Negative signals — skip these (already technical / not SMB)
SKIP_KEYWORDS = [
    "senior engineer", "lead developer", "principal", "staff engineer",
    "full time", "full-time", "salary", "w2", "equity",
]

ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / "outreach"


def fetch_city_gigs(city: str, keywords: list[str], session: requests.Session) -> list[dict]:
    """Fetch computer gigs listings for one Craigslist city."""
    url = f"https://{city}.craigslist.org/search/cpg"
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [{city}] fetch failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Craigslist uses different markup versions — handle both
    results = []

    # Newer markup: <li class="cl-search-result">
    for item in soup.select("li.cl-search-result"):
        title_el = item.select_one("a.cl-app-anchor span[data-testid='title']") or \
                   item.select_one("a.cl-app-anchor")
        link_el = item.select_one("a.cl-app-anchor")
        date_el = item.select_one("div.meta span.date") or item.select_one("span.date")

        if not title_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        link = link_el.get("href", "")
        if link and not link.startswith("http"):
            link = f"https://{city}.craigslist.org{link}"
        date = date_el.get_text(strip=True) if date_el else ""

        results.append({"title": title, "link": link, "date": date, "city": city})

    # Older markup fallback: <li class="result-row">
    if not results:
        for item in soup.select("li.result-row"):
            title_el = item.select_one("a.result-title")
            date_el = item.select_one("time.result-date")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            date = date_el.get("title", "") if date_el else ""

            results.append({"title": title, "link": link, "date": date, "city": city})

    # Score and filter
    leads = []
    for r in results:
        title_lower = r["title"].lower()

        if any(skip in title_lower for skip in SKIP_KEYWORDS):
            continue

        score = sum(1 for kw in keywords if kw.lower() in title_lower)
        if score == 0:
            continue

        leads.append({**r, "score": score, "matched_keywords": [
            kw for kw in keywords if kw.lower() in title_lower
        ]})

    return sorted(leads, key=lambda x: x["score"], reverse=True)


def deduplicate(leads: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for lead in leads:
        key = lead["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            out.append(lead)
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Craigslist computer gigs for SMB automation leads"
    )
    parser.add_argument("--cities", nargs="+", default=DEFAULT_CITIES,
                        help="Craigslist city subdomains (default: 10 major US cities)")
    parser.add_argument("--keywords", nargs="+", default=OPPORTUNITY_KEYWORDS,
                        help="Keywords to match in listing titles")
    parser.add_argument("--output", default=str(OUT_DIR / "craigslist_leads.csv"),
                        help="Output CSV path")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Seconds between requests (default: 1.5)")
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; lead-scraper/1.0)"})

    all_leads = []
    print(f"Scanning {len(args.cities)} cities for computer gigs...")

    for city in args.cities:
        leads = fetch_city_gigs(city, args.keywords, session)
        print(f"  {city:<15} {len(leads)} leads")
        all_leads.extend(leads)
        time.sleep(args.delay)

    all_leads = deduplicate(all_leads)
    all_leads.sort(key=lambda x: x["score"], reverse=True)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["title", "city", "score", "matched_keywords", "link", "date",
                  "contact_attempted", "notes"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in all_leads:
            writer.writerow({
                "title": lead["title"],
                "city": lead["city"],
                "score": lead["score"],
                "matched_keywords": ", ".join(lead.get("matched_keywords", [])),
                "link": lead["link"],
                "date": lead["date"],
                "contact_attempted": "",
                "notes": "",
            })

    print(f"\nFound {len(all_leads)} unique leads → {out}")
    if all_leads:
        print("\nTop 10:")
        for i, lead in enumerate(all_leads[:10], 1):
            kws = ", ".join(lead.get("matched_keywords", []))
            print(f"  {i:2}. [{lead['city']:<10}] score={lead['score']}  {lead['title'][:55]}")
            print(f"      keywords: {kws}")
            print(f"      {lead['link']}")

    # Save raw metadata
    meta = {
        "scraped_at": datetime.now().isoformat(),
        "cities": args.cities,
        "total_leads": len(all_leads),
    }
    (out.parent / "craigslist_leads_meta.json").write_text(
        json.dumps(meta, indent=2)
    )


if __name__ == "__main__":
    main()
