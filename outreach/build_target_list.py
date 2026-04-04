#!/usr/bin/env python3
"""
Build outreach target list from collected job data.

Scans all collected_data/*.json files, finds companies hiring for
roles relevant to Python automation / data work, and outputs a
deduplicated CSV ready for manual outreach.

Usage:
  python build_target_list.py
  python build_target_list.py --output outreach/targets.csv --min-hits 2
"""

import argparse
import csv
import json
import re
from pathlib import Path

TITLE_SKILL_KEYWORDS = [
    "python", "automation", "data", "scraping", "scraper",
    "etl", "pipeline", "backend", "api", "integration",
    "script", "developer", "engineer", "full stack", "devops",
]

TITLE_ROLE_KEYWORDS = [
    "engineer", "developer", "analyst", "automation",
]

EXCLUDED_TITLE_KEYWORDS = [
    "account executive", "counsel", "representative", "marketing",
    "designer", "support", "sales", "trader", "recruiter",
    "product manager", "customer success", "account manager",
]

DESCRIPTION_KEYWORDS = [
    "python", "automation", "etl", "pipeline", "api",
    "integration", "scraping", "data platform", "data engineering",
    "backend", "scripting",
]

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "collected_data"


def extract_company_from_wwr_title(title: str) -> str:
    """WWR titles are formatted as 'Company: Job Title'."""
    if ":" in title:
        return title.split(":", 1)[0].strip()
    return ""


def keyword_hits(text: str, keywords: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", lowered))


def is_target_role(title: str, description: str = "") -> bool:
    """Keep technical automation/data roles and reject obvious non-target roles."""
    title_lower = title.lower()
    if any(kw in title_lower for kw in EXCLUDED_TITLE_KEYWORDS):
        return False

    title_skill_hits = keyword_hits(title, TITLE_SKILL_KEYWORDS)
    title_role_hits = keyword_hits(title, TITLE_ROLE_KEYWORDS)
    desc_hits = keyword_hits(description, DESCRIPTION_KEYWORDS)

    return (
        (title_skill_hits >= 2 and title_role_hits >= 1) or
        (title_role_hits >= 1 and desc_hits >= 2)
    )


def score_job(title: str, description: str = "") -> int:
    """Weight title matches more than description matches for ranking."""
    return keyword_hits(title, TITLE_SKILL_KEYWORDS) * 2 + keyword_hits(description, DESCRIPTION_KEYWORDS)


def load_jobs() -> list[dict]:
    jobs = []
    for f in sorted(DATA_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, list):
            continue

        source = "remoteok" if "remoteok" in f.name else "wwr"

        for item in data:
            title = item.get("title", "")
            link = item.get("link", "")
            description = item.get("description", "")
            scraped_at = item.get("scraped_at", "")

            if source == "remoteok":
                company = item.get("company", "")
            else:
                company = extract_company_from_wwr_title(title)
                # Clean job title (remove company prefix)
                if ":" in title:
                    title = title.split(":", 1)[1].strip()

            if not is_target_role(title, description):
                continue

            score = score_job(title, description)
            if score <= 0:
                continue

            jobs.append({
                "company": company,
                "job_title": title,
                "link": link,
                "source": source,
                "score": score,
                "scraped_at": scraped_at,
            })

    return jobs


def deduplicate(jobs: list[dict]) -> list[dict]:
    """Keep the highest-scoring entry per company."""
    best: dict[str, dict] = {}
    for job in jobs:
        company = job["company"].strip().lower()
        if not company:
            continue
        if company not in best or job["score"] > best[company]["score"]:
            best[company] = job
    return sorted(best.values(), key=lambda j: j["score"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description="Build outreach target CSV from job data")
    parser.add_argument("--output", default=str(ROOT / "outreach" / "target_companies.csv"))
    parser.add_argument("--min-hits", type=int, default=1,
                        help="Minimum keyword matches to include a company (default: 1)")
    parser.add_argument("--top", type=int, default=0,
                        help="Only output top N companies (default: all)")
    args = parser.parse_args()

    print(f"Scanning {DATA_DIR} ...")
    jobs = load_jobs()
    print(f"Found {len(jobs)} relevant job postings")

    targets = deduplicate(jobs)
    targets = [t for t in targets if t["score"] >= args.min_hits]

    if args.top:
        targets = targets[:args.top]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["company", "job_title", "source", "score", "link", "scraped_at",
                  "contact_email", "outreach_sent", "notes"]

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in targets:
            writer.writerow({
                "company": t["company"],
                "job_title": t["job_title"],
                "source": t["source"],
                "score": t["score"],
                "link": t["link"],
                "scraped_at": t["scraped_at"],
                "contact_email": "",
                "outreach_sent": "",
                "notes": "",
            })

    print(f"\nWrote {len(targets)} companies → {out}")
    print(f"\nTop 10 targets:")
    for i, t in enumerate(targets[:10], 1):
        print(f"  {i:2}. {t['company']:<35} score={t['score']}  [{t['source']}]  {t['job_title'][:50]}")

    print(f"\nNext step: open {out} and fill in contact_email for each company.")
    print("Use the email template in DO_THIS_TO_MAKE_MONEY_NOW.txt (Option 2, Step 3).")


if __name__ == "__main__":
    main()
