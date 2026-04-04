#!/usr/bin/env python3
"""
Scrape r/forhire [Hiring] posts for Python/automation/Excel requests.

Targets posts from non-technical people who need a specific task done.
Uses the Reddit JSON API (no auth required for public subreddits).

Output: outreach/reddit_forhire_leads.csv
"""

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# Search both subs: forhire (hiring posts) and slavelabour ([Task] posts)
SUBREDDITS = ["forhire", "slavelabour"]
SEARCH_TERMS = [
    "python script",
    "python automation",
    "excel automation",
    "automate excel",
    "google sheets script",
    "web scraping",
    "data entry automation",
    "csv automation",
    "automate task",
    "need script",
]

# Only want [Hiring] or [H] posts, skip [For Hire] / [FH] / offers
HIRING_FLAIRS = {"hiring", "[hiring]", "h", "[h]"}

SKIP_WORDS = [
    "senior engineer", "lead dev", "full-time", "full time",
    "equity", "co-founder", "cto", "agency",
]

OUT = Path(__file__).parent / "reddit_forhire_leads.csv"
# Reddit requires: platform:app_id:version (by /u/username)
HEADERS = {"User-Agent": "script:cropcircuit-lead-scraper:1.0 (by /u/cropcircuit_bot)"}


def search_reddit(subreddit: str, query: str, session: requests.Session, retries: int = 3) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": query,
        "restrict_sr": "1",
        "sort": "new",
        "t": "month",   # month > week so we don't miss posts between runs
        "limit": 25,
    }
    for attempt in range(retries):
        try:
            resp = session.get(url, params=params, timeout=15)
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"  rate limited on {query!r}, waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code != 200:
                print(f"  HTTP {resp.status_code} for {query!r}")
                return []
            return resp.json()["data"]["children"]
        except Exception as e:
            print(f"  attempt {attempt+1} failed for {query!r}: {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return []


def is_relevant_post(post: dict, subreddit: str) -> bool:
    """
    Relaxed filter — accept any post that looks like a client request.
    r/forhire: keep [Hiring]/[H] flair OR title, skip [For Hire]/[FH]
    r/slavelabour: keep [Task]/[T] posts, skip [Completed]
    """
    flair = (post.get("link_flair_text") or "").lower().strip()
    title = post.get("title", "").lower()

    if subreddit == "slavelabour":
        # Skip completed/offering posts
        if any(x in flair for x in ["complete", "offering", "for hire"]):
            return False
        if title.startswith("[complete") or title.startswith("[fh]") or title.startswith("[for hire"):
            return False
        return True  # Accept all non-completed slavelabour posts

    # forhire: skip [For Hire] posts
    if flair in {"for hire", "[for hire]", "fh", "[fh]"}:
        return False
    if title.startswith("[fh]") or title.startswith("[for hire]"):
        return False
    # Accept if flair is hiring OR title has [H]/[Hiring] OR no flair at all
    # (many posts have no flair set but are legitimate hiring posts)
    return True


def score_post(post: dict) -> int:
    text = (post.get("title", "") + " " + post.get("selftext", "")).lower()
    keywords = [
        "python", "script", "automation", "automate", "excel", "spreadsheet",
        "csv", "scrape", "scraping", "google sheets", "api", "bot",
        "workflow", "repetitive", "data entry", "data processing",
    ]
    return sum(1 for kw in keywords if kw in text)


def extract_budget(text: str) -> str:
    import re
    match = re.search(r"\$\s*(\d[\d,]*)", text)
    return f"${match.group(1)}" if match else ""


def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    seen_ids: set[str] = set()
    leads: list[dict] = []
    total_fetched = total_filtered_flair = total_filtered_skip = total_filtered_score = 0

    print(f"Searching {SUBREDDITS} for {len(SEARCH_TERMS)} queries each...")

    for subreddit in SUBREDDITS:
        for term in SEARCH_TERMS:
            posts = search_reddit(subreddit, term, session)
            print(f"  r/{subreddit} {term!r}: {len(posts)} raw posts")
            total_fetched += len(posts)

            for item in posts:
                post = item["data"]
                pid = post.get("id", "")
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)

                if not is_relevant_post(post, subreddit):
                    total_filtered_flair += 1
                    continue

                title = post.get("title", "")
                body = post.get("selftext", "")

                if any(skip in (title + body).lower() for skip in SKIP_WORDS):
                    total_filtered_skip += 1
                    continue

                s = score_post(post)
                if s == 0:
                    total_filtered_score += 1
                    continue

                created = datetime.fromtimestamp(
                    post.get("created_utc", 0), tz=timezone.utc
                ).strftime("%Y-%m-%d")

                leads.append({
                    "title": title,
                    "score": s,
                    "subreddit": subreddit,
                    "budget": extract_budget(title + " " + body),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "posted": created,
                    "author": post.get("author", ""),
                    "snippet": body[:200].replace("\n", " "),
                    "contact_attempted": "",
                    "notes": "",
                })

            time.sleep(1.0)

    print(f"\nFunnel: {total_fetched} fetched → "
          f"{total_filtered_flair} filtered (flair) → "
          f"{total_filtered_skip} filtered (skip words) → "
          f"{total_filtered_score} filtered (score=0) → "
          f"{len(leads)} leads")

    # Deduplicate and sort
    seen_titles: set[str] = set()
    unique: list[dict] = []
    for lead in sorted(leads, key=lambda x: x["score"], reverse=True):
        key = lead["title"].lower().strip()
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(lead)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["title", "score", "subreddit", "budget", "url", "posted",
                  "author", "snippet", "contact_attempted", "notes"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique)

    meta = {
        "scraped_at": datetime.now().isoformat(),
        "total_leads": len(unique),
        "subreddits": SUBREDDITS,
        "search_terms": SEARCH_TERMS,
        "funnel": {
            "fetched": total_fetched,
            "filtered_flair": total_filtered_flair,
            "filtered_skip": total_filtered_skip,
            "filtered_score": total_filtered_score,
        },
    }
    (OUT.parent / "reddit_forhire_meta.json").write_text(json.dumps(meta, indent=2))

    print(f"Wrote {len(unique)} leads → {OUT}")
    for i, lead in enumerate(unique[:10], 1):
        print(f"  {i:2}. [{lead['subreddit']:<12}] score={lead['score']}  "
              f"{lead['budget'] or '?':>6}  {lead['title'][:55]}")


if __name__ == "__main__":
    main()
