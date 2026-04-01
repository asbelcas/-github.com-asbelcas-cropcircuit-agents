#!/usr/bin/env python3
"""Build no-API social momentum assets for CropCircuit.

Outputs:
- Expanded follow targets database (handles + search-resolve targets)
- Deferred follow queue optimized for rate-reset execution
- Partner prospect expansion CSV
- Future post drafts (draft only, never publish)
- Outreach script append pack
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"

TARGETS_JSON = RUNTIME / "follow_targets_agriculture.json"
TARGETS_CSV = RUNTIME / "follow_targets_agriculture.csv"
FOLLOW_QUEUE = RUNTIME / "x_follow_queue.jsonl"
POST_DRAFTS = RUNTIME / "x_future_posts_drafts.json"
PROSPECTS_CSV = RUNTIME / "partner_prospects_social.csv"
OUTREACH_SCRIPTS = RUNTIME / "outreach_scripts_social.md"
PARTNERS_CONTACTS = ROOT / "partners_contacts.csv"

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

HANDLE_RE = re.compile(
    r"https?://(?:www\.)?(?:x\.com|twitter\.com)/([A-Za-z0-9_]{1,15})(?:[/?#]|$)",
    flags=re.IGNORECASE,
)
IGNORE_HANDLES = {
    "home",
    "share",
    "intent",
    "search",
    "i",
    "hashtag",
    "explore",
    "privacy",
    "tos",
    "settings",
    "login",
}


@dataclass(frozen=True)
class Seed:
    org: str
    url: str
    segment: str
    region: str
    priority: int


SEEDS: list[Seed] = [
    Seed("USDA", "https://www.usda.gov", "usda", "national", 1),
    Seed("USDA NRCS", "https://www.nrcs.usda.gov", "usda", "national", 1),
    Seed("USDA FSA", "https://www.fsa.usda.gov", "usda", "national", 1),
    Seed("USDA Climate Hubs", "https://www.climatehubs.usda.gov", "usda", "national", 2),
    Seed(
        "Michigan Department of Agriculture and Rural Development (MDARD)",
        "https://www.michigan.gov/mdard",
        "michigan_agency",
        "michigan",
        1,
    ),
    Seed("Michigan Farm Bureau", "https://www.michfb.com", "michigan_org", "michigan", 1),
    Seed(
        "Michigan Association of Conservation Districts",
        "https://macd.org",
        "conservation",
        "michigan",
        1,
    ),
    Seed(
        "Calhoun Conservation District",
        "https://www.calhouncd.org",
        "conservation",
        "michigan",
        1,
    ),
    Seed(
        "Michigan State University Extension",
        "https://www.canr.msu.edu/outreach",
        "michigan_org",
        "michigan",
        1,
    ),
]

# Verified/official handles from browser-read sources.
CONFIRMED_HANDLES = [
    {
        "handle": "FarmersGov",
        "source_org": "Farmers.gov",
        "source_url": "https://www.farmers.gov/connect",
        "segment": "usda",
        "region": "national",
        "priority": 1,
        "notes": "Listed as official Farmers.gov X account",
    },
    {
        "handle": "usdafsa",
        "source_org": "USDA Farm Service Agency",
        "source_url": "https://www.farmers.gov/connect",
        "segment": "usda",
        "region": "national",
        "priority": 1,
        "notes": "Listed as official FSA mission-area account",
    },
    {
        "handle": "USDA_NRCS",
        "source_org": "USDA NRCS",
        "source_url": "https://www.farmers.gov/connect",
        "segment": "conservation",
        "region": "national",
        "priority": 1,
        "notes": "Listed as official NRCS mission-area account",
    },
    {
        "handle": "usdaRMA",
        "source_org": "USDA Risk Management Agency",
        "source_url": "https://www.farmers.gov/connect",
        "segment": "usda",
        "region": "national",
        "priority": 2,
        "notes": "Listed as official RMA mission-area account",
    },
    {
        "handle": "USDA",
        "source_org": "U.S. Department of Agriculture",
        "source_url": "https://www.nrcs.usda.gov/conservation-basics/conservation-by-state/arizona/arizona-nrcs-media-resources",
        "segment": "usda",
        "region": "national",
        "priority": 1,
        "notes": "Referenced by NRCS media resources as USDA Twitter/X",
    },
    {
        "handle": "SecRollins",
        "source_org": "USDA Secretary",
        "source_url": "https://www.usda.gov/our-agency/about-usda/our-secretary",
        "segment": "usda",
        "region": "national",
        "priority": 3,
        "notes": "USDA secretary page points to official account",
    },
    {
        "handle": "MichDeptofAg",
        "source_org": "MDARD",
        "source_url": "https://www.michigan.gov/mdard/-/media/Project/Websites/mdard/documents/business-development/mi_ag_facts_figures.pdf",
        "segment": "michigan_agency",
        "region": "michigan",
        "priority": 1,
        "notes": "MDARD facts PDF lists official social accounts",
    },
    {
        "handle": "MSUExtension",
        "source_org": "Michigan State University Extension",
        "source_url": "https://www.canr.msu.edu/facultystaff/uploads/files/Faculty-Staff-HR-Documents/New%20Employee%20Slideshow_SS_time-sensitive_information_updated2021.pdf",
        "segment": "michigan_org",
        "region": "michigan",
        "priority": 1,
        "notes": "CANR orientation deck lists MSU Extension Twitter/X",
    },
    {
        "handle": "MSUAgBio",
        "source_org": "MSU AgBioResearch",
        "source_url": "https://www.canr.msu.edu/facultystaff/uploads/files/Faculty-Staff-HR-Documents/New%20Employee%20Slideshow_SS_time-sensitive_information_updated2021.pdf",
        "segment": "michigan_org",
        "region": "michigan",
        "priority": 2,
        "notes": "CANR orientation deck lists AgBioResearch Twitter/X",
    },
    {
        "handle": "michfarmbureau",
        "source_org": "Michigan Farm Bureau",
        "source_url": "https://www.michfb.com/sites/default/files/2023-11/annual-meeting-guidebook.pdf",
        "segment": "michigan_org",
        "region": "michigan",
        "priority": 1,
        "notes": "MFB annual meeting guidebook lists official X handle",
    },
    {
        "handle": "NRCS_MI",
        "source_org": "NRCS-Michigan",
        "source_url": "https://twitter.com/NRCS_MI/with_replies",
        "segment": "conservation",
        "region": "michigan",
        "priority": 1,
        "notes": "NRCS Michigan profile page",
    },
]

MICHIGAN_COUNTIES = [
    "Alcona", "Alger", "Allegan", "Alpena", "Antrim", "Arenac", "Baraga", "Barry", "Bay",
    "Benzie", "Berrien", "Branch", "Calhoun", "Cass", "Charlevoix", "Cheboygan", "Chippewa",
    "Clare", "Clinton", "Crawford", "Delta", "Dickinson", "Eaton", "Emmet", "Genesee", "Gladwin",
    "Gogebic", "Grand Traverse", "Gratiot", "Hillsdale", "Houghton", "Huron", "Ingham", "Ionia",
    "Iosco", "Iron", "Isabella", "Jackson", "Kalamazoo", "Kalkaska", "Kent", "Keweenaw", "Lake",
    "Lapeer", "Leelanau", "Lenawee", "Livingston", "Luce", "Mackinac", "Macomb", "Manistee",
    "Marquette", "Mason", "Mecosta", "Menominee", "Midland", "Missaukee", "Monroe", "Montcalm",
    "Montmorency", "Muskegon", "Newaygo", "Oakland", "Oceana", "Ogemaw", "Ontonagon", "Osceola",
    "Oscoda", "Otsego", "Ottawa", "Presque Isle", "Roscommon", "Saginaw", "St. Clair", "St. Joseph",
    "Sanilac", "Schoolcraft", "Shiawassee", "Tuscola", "Van Buren", "Washtenaw", "Wayne", "Wexford",
]

COMMODITY_GROUPS = [
    "Michigan Cattlemen's Association",
    "Michigan Milk Producers Association",
    "Michigan Sheep Producers Association",
    "Michigan Forage Council",
    "Michigan Corn Growers Association",
    "Michigan Soybean Committee",
    "Michigan Wheat Program",
    "Michigan Bean Commission",
    "Michigan Pork Producers Association",
    "Michigan Vegetable Council",
    "Michigan Apple Committee",
    "Michigan Blueberry Commission",
    "Michigan Cherry Committee",
    "Michigan Grape Society",
    "Michigan Christmas Tree Association",
    "Michigan Potato Industry Commission",
    "Michigan Organic Food and Farm Alliance",
    "National Grazing Lands Coalition Michigan",
    "Practical Farmers of Iowa",
    "Savanna Institute",
]

MICHIGAN_AG_NONPROFITS = [
    "Crosshatch Center for Art and Ecology",
    "Groundwork Center for Resilient Communities",
    "SEEDS Ecology and Education Centers",
    "Michigan Organic Food and Farm Alliance",
    "Taste the Local Difference",
    "Michigan Food and Farming Systems",
    "Barry County United Way food initiatives",
    "Battle Creek Food Reimagined",
    "Fair Food Network",
    "Sprout Urban Farms",
    "Michigan Sustainable Farm Mentors",
    "The Steward",
    "Ecology Center Ann Arbor",
    "Detroit Black Community Food Security Network",
    "Washtenaw Food Hub",
]

USDA_LOCAL_OFFICE_QUERIES = [
    "USDA Service Center Battle Creek Michigan",
    "USDA Service Center Marshall Michigan",
    "USDA Service Center Kalamazoo Michigan",
    "USDA Service Center Jackson Michigan",
    "USDA Service Center Lansing Michigan",
    "USDA Service Center Allegan Michigan",
    "USDA Service Center Barry Michigan",
    "USDA Service Center Branch Michigan",
    "USDA Service Center Berrien Michigan",
    "USDA Service Center Cass Michigan",
    "USDA Service Center Eaton Michigan",
    "USDA Service Center Ingham Michigan",
    "USDA Service Center Calhoun Michigan",
    "USDA Service Center Van Buren Michigan",
    "USDA Service Center Washtenaw Michigan",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_html(url: str, timeout: int = 15) -> tuple[str | None, str | None]:
    req = Request(url, headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=timeout) as resp:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                return None, f"non_html_content_type:{content_type}"
            body = resp.read(2_000_000)
            return body.decode("utf-8", errors="ignore"), None
    except HTTPError as e:
        return None, f"http_error:{e.code}"
    except URLError as e:
        return None, f"url_error:{e.reason}"
    except TimeoutError:
        return None, "timeout"
    except Exception as e:  # noqa: BLE001
        return None, f"error:{type(e).__name__}"


def extract_handles(html: str) -> list[str]:
    found = []
    for handle in HANDLE_RE.findall(html):
        h = handle.strip()
        if not h:
            continue
        lower = h.lower()
        if lower in IGNORE_HANDLES:
            continue
        found.append(h)
    return sorted({h for h in found}, key=lambda x: x.lower())


def score(priority: int, segment: str, target_mode: str, verified: bool) -> int:
    base = 100 - (priority * 10)
    segment_bonus = {
        "usda": 8,
        "conservation": 8,
        "michigan_agency": 7,
        "michigan_org": 6,
        "commodity": 5,
        "grant_partner": 7,
        "extension": 7,
    }.get(segment, 4)
    mode_bonus = 10 if target_mode == "handle" else 2
    verified_bonus = 6 if verified else 0
    return max(1, min(100, base + segment_bonus + mode_bonus + verified_bonus))


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def add_target(targets: list[dict], seen: set[str], row: dict) -> None:
    mode = row["target_mode"]
    if mode == "handle":
        key = f"h:{row['handle'].lower()}"
    else:
        key = f"q:{row['org_name'].strip().lower()}"
    if key in seen:
        return
    seen.add(key)
    targets.append(row)


def build_search_resolve_targets(run_ts: str) -> list[dict]:
    rows: list[dict] = []

    for county in MICHIGAN_COUNTIES:
        org = f"{county} Conservation District"
        rows.append(
            {
                "target_mode": "search_resolve",
                "handle": "",
                "org_name": org,
                "profile_url": "",
                "lookup_query": f'"{org}" Michigan x.com',
                "source_org": "Michigan county conservation district expansion",
                "source_url": "https://macd.org",
                "segment": "conservation",
                "region": "michigan",
                "priority": 1 if county in {"Calhoun", "Barry", "Kalamazoo", "Jackson"} else 2,
                "verified_source": False,
                "method": "browser_read_seed_plus_local_expansion",
                "notes": "Resolve handle during rate-reset execution window",
                "last_verified_at": run_ts,
                "status": "candidate",
                "tags": ["county_cd", "michigan", "search_resolve"],
            }
        )

    for county in [
        "Calhoun", "Barry", "Kalamazoo", "Jackson", "Eaton", "Ingham", "Allegan", "Van Buren",
        "Washtenaw", "Kent", "Ottawa", "Muskegon", "Genesee", "Saginaw", "Monroe", "Branch",
        "Cass", "Berrien", "St. Joseph", "Lenawee",
    ]:
        org = f"MSU Extension {county} County"
        rows.append(
            {
                "target_mode": "search_resolve",
                "handle": "",
                "org_name": org,
                "profile_url": "",
                "lookup_query": f'"{org}" x.com',
                "source_org": "MSU Extension county outreach expansion",
                "source_url": "https://www.canr.msu.edu/outreach",
                "segment": "extension",
                "region": "michigan",
                "priority": 1 if county in {"Calhoun", "Barry", "Kalamazoo", "Jackson"} else 2,
                "verified_source": False,
                "method": "browser_read_seed_plus_local_expansion",
                "notes": "Resolve local extension accounts",
                "last_verified_at": run_ts,
                "status": "candidate",
                "tags": ["msu_extension", "michigan", "search_resolve"],
            }
        )

    for org in COMMODITY_GROUPS:
        rows.append(
            {
                "target_mode": "search_resolve",
                "handle": "",
                "org_name": org,
                "profile_url": "",
                "lookup_query": f'"{org}" Michigan x.com',
                "source_org": "Commodity group expansion",
                "source_url": "https://www.michigan.gov/mdard",
                "segment": "commodity",
                "region": "michigan",
                "priority": 2,
                "verified_source": False,
                "method": "browser_read_seed_plus_local_expansion",
                "notes": "Beef/dairy/sheep/forage/regenerative commodity mapping",
                "last_verified_at": run_ts,
                "status": "candidate",
                "tags": ["commodity", "michigan", "search_resolve"],
            }
        )

    for org in MICHIGAN_AG_NONPROFITS:
        rows.append(
            {
                "target_mode": "search_resolve",
                "handle": "",
                "org_name": org,
                "profile_url": "",
                "lookup_query": f'"{org}" Michigan agriculture x.com',
                "source_org": "Michigan ag nonprofit expansion",
                "source_url": "https://www.michigan.gov/mdard",
                "segment": "michigan_org",
                "region": "michigan",
                "priority": 2,
                "verified_source": False,
                "method": "browser_read_seed_plus_local_expansion",
                "notes": "Nonprofit/community partner prospecting",
                "last_verified_at": run_ts,
                "status": "candidate",
                "tags": ["nonprofit", "michigan", "search_resolve"],
            }
        )

    for query in USDA_LOCAL_OFFICE_QUERIES:
        rows.append(
            {
                "target_mode": "search_resolve",
                "handle": "",
                "org_name": query,
                "profile_url": "",
                "lookup_query": f'"{query}" "x.com"',
                "source_org": "USDA local office expansion",
                "source_url": "https://www.farmers.gov/service-center-locator",
                "segment": "usda",
                "region": "michigan",
                "priority": 1,
                "verified_source": False,
                "method": "browser_read_seed_plus_local_expansion",
                "notes": "USDA local office social discovery queue",
                "last_verified_at": run_ts,
                "status": "candidate",
                "tags": ["usda_local", "michigan", "search_resolve"],
            }
        )

    # Partner contacts currently tracked in repo.
    if PARTNERS_CONTACTS.exists():
        try:
            with open(PARTNERS_CONTACTS, "r", encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    org = (row.get("Org_Name") or "").strip()
                    if not org:
                        continue
                    rows.append(
                        {
                            "target_mode": "search_resolve",
                            "handle": "",
                            "org_name": org,
                            "profile_url": "",
                            "lookup_query": f'"{org}" x.com',
                            "source_org": "existing_partner_contacts",
                            "source_url": row.get("Website") or "",
                            "segment": "grant_partner",
                            "region": "michigan",
                            "priority": int(row.get("Priority") or 2),
                            "verified_source": False,
                            "method": "local_repo_expansion",
                            "notes": "Imported from partners_contacts.csv",
                            "last_verified_at": run_ts,
                            "status": "candidate",
                            "tags": ["grant_partner", "search_resolve"],
                        }
                    )
        except Exception:
            pass

    return rows


def build_post_drafts(run_ts: str) -> list[dict]:
    base_10 = [
        ("regenerative_agriculture", "Soil update from Michigan: we are tracking infiltration, residue cover, and root depth before every major field decision. Building proof, not hype.", "weekday_morning"),
        ("conservation_practices", "Prioritizing conservation-district collaboration this week so every farm action ties back to measurable soil outcomes.", "weekday_evening"),
        ("cropcircuit_mission", "CropCircuit is documenting every infrastructure milestone publicly: what was funded, what was built, and what changed in the field.", "weekday_morning"),
        ("michigan_farming", "Goal: grow a practical Michigan regenerative network where growers share what actually worked, what failed, and what to test next.", "weekday_evening"),
        ("conservation_practices", "Water planning is farm resilience. This week is focused on drainage checks, irrigation prep, and runoff-reduction layout.", "weekday_morning"),
        ("sheep_small_farm_systems", "Regenerative livestock planning means better forage cycles, better soil biology, and cleaner economics for small farms.", "weekday_evening"),
        ("cropcircuit_mission", "Grant work should end in field outcomes. Every application step is mapped to a concrete on-farm deliverable.", "weekday_morning"),
        ("michigan_farming", "Michigan ag progress moves faster when farmers, extension, and conservation teams coordinate on execution, not just ideas.", "weekday_evening"),
        ("sheep_small_farm_systems", "Today’s operations focus: fencing sequence, soil amendment timing, and labor planning for spring readiness.", "weekday_morning"),
        ("cropcircuit_mission", "If you work in conservation, extension, or local ag support, let’s align around practical regenerative outcomes for 2026.", "weekday_evening"),
    ]

    add_20 = [
        ("regenerative_agriculture", "Regenerative farming starts with biology: roots in the ground, residue on top, and disturbance kept low.", "weekday_morning"),
        ("michigan_farming", "Michigan farms are resilient when planning includes soil, water, market access, and practical collaboration.", "weekday_evening"),
        ("conservation_practices", "Cover crop decisions this season are being made by field conditions, not generic templates.", "weekday_morning"),
        ("sheep_small_farm_systems", "Small flock management is about timing: pasture moves, forage density, and parasite pressure tracking.", "weekday_evening"),
        ("cropcircuit_mission", "CropCircuit exists to turn funding and partnerships into visible field outcomes.", "weekday_morning"),
        ("regenerative_agriculture", "Healthy soil is an operating advantage: better infiltration, better structure, better drought tolerance.", "weekday_evening"),
        ("michigan_farming", "Battle Creek is the base, but the model is built for replication across Michigan counties.", "weekday_morning"),
        ("conservation_practices", "This week’s conservation focus: runoff control zones, residue retention, and root-first planning.", "weekday_evening"),
        ("sheep_small_farm_systems", "Integrated sheep systems can accelerate nutrient cycling when pasture rotation is disciplined.", "weekday_morning"),
        ("cropcircuit_mission", "We are building in public so partners can verify progress without chasing updates.", "weekday_evening"),
        ("regenerative_agriculture", "Regeneration is not branding. It is measurement, adaptation, and execution over time.", "weekday_morning"),
        ("michigan_farming", "Michigan producers need practical playbooks, not theory dumps. We are documenting what works.", "weekday_evening"),
        ("conservation_practices", "Conservation outcomes improve when districts, extension, and growers share operating data.", "weekday_morning"),
        ("sheep_small_farm_systems", "Forage-first sheep planning reduces purchased inputs and improves resilience on small acreage.", "weekday_evening"),
        ("cropcircuit_mission", "Mission lock: soil restoration, food production, and transparent execution in one operating loop.", "weekday_morning"),
        ("regenerative_agriculture", "No-till where feasible, living roots as long as possible, and clear field records every cycle.", "weekday_evening"),
        ("michigan_farming", "Local partnerships are the multiplier for Michigan regenerative projects in 2026.", "weekday_morning"),
        ("conservation_practices", "Nutrient management and water planning are being aligned before spring acceleration.", "weekday_evening"),
        ("sheep_small_farm_systems", "Sheep and small farm systems work best when grazing plans are mapped before growth spikes.", "weekday_morning"),
        ("cropcircuit_mission", "The goal is simple: credible outcomes that producers, partners, and communities can trust.", "weekday_evening"),
    ]

    all_posts = base_10 + add_20
    drafts = []
    for idx, (theme, text, window) in enumerate(all_posts, start=1):
        drafts.append(
            {
                "id": f"draft_{idx:02d}",
                "created_at": run_ts,
                "status": "draft",
                "publish_blocked": True,
                "theme": theme,
                "text": text,
                "scheduled_window": window,
            }
        )
    return drafts


def append_outreach_assets(run_ts: str) -> None:
    marker = f"## Expansion Pack {run_ts[:10]}"
    existing = ""
    if OUTREACH_SCRIPTS.exists():
        existing = OUTREACH_SCRIPTS.read_text(encoding="utf-8")
    if marker in existing:
        return

    block = "\n".join(
        [
            marker,
            "",
            "### Twitter DM variants",
            "1) Conservation district: Hi [Name], Casey from CropCircuit in Battle Creek. We are aligning field execution with measurable conservation outcomes. Open to connecting so we can stay synced on priority practices this season?",
            "2) MSU Extension: Hi [Name], I run CropCircuit and we are documenting regenerative implementation in Michigan. Would value following your updates and sharing concise field milestones.",
            "3) USDA local office: Hello [Team], we are tracking CropCircuit farm planning against USDA-aligned conservation goals. Open to connecting for updates and producer resource alignment.",
            "4) Commodity group: Hi [Name], Casey at CropCircuit. We are building practical content around sheep/small-farm regenerative systems and would like to stay connected with your producer community.",
            "",
            "### Email templates",
            "Subject: Michigan regenerative collaboration",
            "Hi [Name], I run CropCircuit in Battle Creek. We are building transparent, measurable regenerative workflows for 2026 and mapping strategic partners across conservation, extension, and producer groups. Open to a 15-minute intro next week to identify one practical collaboration point?",
            "",
            "Subject: Producer-facing partnership inquiry",
            "Hi [Name], I am reaching out to align on producer-support efforts in Michigan. We are focused on conservation practice execution, small-farm livestock integration, and shared learning. If relevant, I can send a one-page summary and suggested next step.",
            "",
            "### Partner intro script",
            "Hi [Name], this is Casey with CropCircuit. Quick context: we are coordinating regenerative implementation support across Michigan and want to align with organizations already serving growers. Could we schedule a short intro call to identify one immediate collaboration opportunity?",
            "",
            "### Grant collaboration pitch",
            "CropCircuit is building an execution-first regenerative program in Michigan that ties grant activity to visible field outcomes. We are seeking partners who can support conservation practice adoption, producer engagement, or technical review. Collaboration options include: co-hosted producer sessions, advisory input, letters of support, and coordinated outreach to eligible growers.",
            "",
        ]
    )

    if existing and not existing.endswith("\n"):
        existing += "\n"
    OUTREACH_SCRIPTS.write_text(existing + block, encoding="utf-8")


def main() -> int:
    run_ts = now_iso()
    RUNTIME.mkdir(parents=True, exist_ok=True)

    source_records = []
    targets: list[dict] = []
    seen: set[str] = set()

    # Attempt live browser-read scrape first.
    for seed in SEEDS:
        html, err = fetch_html(seed.url)
        handles = extract_handles(html) if html else []
        source_records.append(
            {
                "org": seed.org,
                "url": seed.url,
                "segment": seed.segment,
                "region": seed.region,
                "priority": seed.priority,
                "scrape_status": "ok" if html else "error",
                "error": err,
                "handles_found": handles,
            }
        )
        for handle in handles:
            row = {
                "target_mode": "handle",
                "handle": handle,
                "org_name": seed.org,
                "profile_url": f"https://x.com/{handle}",
                "lookup_query": f"@{handle}",
                "source_org": seed.org,
                "source_url": seed.url,
                "segment": seed.segment,
                "region": seed.region,
                "priority": seed.priority,
                "verified_source": True,
                "method": "website_link_scrape",
                "notes": "No API call used",
                "last_verified_at": run_ts,
                "status": "candidate",
                "tags": [seed.segment, seed.region, "direct_handle"],
            }
            add_target(targets, seen, row)

    dns_blocked = bool(source_records) and all(
        (src.get("error") or "").startswith("url_error:[Errno -3]") for src in source_records
    )

    # Always load confirmed handles (browser-read evidence).
    for row in CONFIRMED_HANDLES:
        item = {
            "target_mode": "handle",
            "handle": row["handle"],
            "org_name": row["source_org"],
            "profile_url": f"https://x.com/{row['handle']}",
            "lookup_query": f"@{row['handle']}",
            "source_org": row["source_org"],
            "source_url": row["source_url"],
            "segment": row["segment"],
            "region": row["region"],
            "priority": row["priority"],
            "verified_source": True,
            "method": "browser_read_fallback",
            "notes": row["notes"],
            "last_verified_at": run_ts,
            "status": "candidate",
            "tags": [row["segment"], row["region"], "verified_handle"],
        }
        add_target(targets, seen, item)

    # Add large search-resolve expansion.
    for row in build_search_resolve_targets(run_ts):
        add_target(targets, seen, row)

    # Score and tag high-value accounts.
    for row in targets:
        relevance = score(
            priority=int(row["priority"]),
            segment=row["segment"],
            target_mode=row["target_mode"],
            verified=bool(row["verified_source"]),
        )
        row["relevance_score"] = relevance
        high_value = relevance >= 90 or (
            row["segment"] in {"usda", "conservation", "michigan_agency", "grant_partner"}
            and int(row["priority"]) == 1
        )
        row["high_value"] = high_value
        if high_value and "high_value" not in row["tags"]:
            row["tags"].append("high_value")

    targets.sort(key=lambda r: (-int(r["relevance_score"]), int(r["priority"]), r["org_name"].lower()))

    payload = {
        "generated_at": run_ts,
        "constraint_mode": "no_api",
        "dns_blocked": dns_blocked,
        "seed_count": len(SEEDS),
        "target_count": len(targets),
        "sources": source_records,
        "targets": targets,
    }
    TARGETS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    write_csv(
        TARGETS_CSV,
        [
            {
                "target_mode": r["target_mode"],
                "handle": r["handle"],
                "org_name": r["org_name"],
                "profile_url": r["profile_url"],
                "lookup_query": r["lookup_query"],
                "source_org": r["source_org"],
                "source_url": r["source_url"],
                "segment": r["segment"],
                "region": r["region"],
                "priority": r["priority"],
                "relevance_score": r["relevance_score"],
                "high_value": r["high_value"],
                "verified_source": r["verified_source"],
                "status": r["status"],
                "last_verified_at": r["last_verified_at"],
                "method": r["method"],
                "tags": "|".join(r["tags"]),
                "notes": r["notes"],
            }
            for r in targets
        ],
        [
            "target_mode",
            "handle",
            "org_name",
            "profile_url",
            "lookup_query",
            "source_org",
            "source_url",
            "segment",
            "region",
            "priority",
            "relevance_score",
            "high_value",
            "verified_source",
            "status",
            "last_verified_at",
            "method",
            "tags",
            "notes",
        ],
    )

    # Queue follows for later execution (no live follow actions).
    reset_date = str(date.today() + timedelta(days=1))
    queue_rows = []
    for idx, row in enumerate(targets, start=1):
        wave = "wave_1" if idx <= 30 else ("wave_2" if idx <= 80 else "wave_3")
        action = "follow" if row["target_mode"] == "handle" else "resolve_profile_then_follow"
        queue_rows.append(
            {
                "queued_at": run_ts,
                "execute_after": f"{reset_date}T23:59:00Z",
                "queue_rank": idx,
                "execution_wave": wave,
                "action": action,
                "target_mode": row["target_mode"],
                "handle": row["handle"],
                "org_name": row["org_name"],
                "lookup_query": row["lookup_query"],
                "status": "queued",
                "reason": "await_rate_limit_reset",
                "source_org": row["source_org"],
                "relevance_score": row["relevance_score"],
                "high_value": row["high_value"],
                "tags": row["tags"],
            }
        )
    with open(FOLLOW_QUEUE, "w", encoding="utf-8") as fh:
        for row in queue_rows:
            fh.write(json.dumps(row) + "\n")

    # Build 30 drafts total (existing 10 + 20 additional requested).
    post_drafts = build_post_drafts(run_ts)
    POST_DRAFTS.write_text(
        json.dumps(
            {
                "generated_at": run_ts,
                "status": "draft_only",
                "do_not_publish": True,
                "count": len(post_drafts),
                "posts": post_drafts,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Partner prospect expansion.
    prospects = []
    for row in targets:
        if row["segment"] not in {
            "conservation",
            "michigan_org",
            "michigan_agency",
            "grant_partner",
            "extension",
            "commodity",
        }:
            continue
        src = row["source_url"]
        domain = urlparse(src).netloc if src else ""
        prospects.append(
            {
                "logged_at": run_ts,
                "org_name": row["org_name"],
                "x_handle": row["handle"],
                "target_mode": row["target_mode"],
                "lookup_query": row["lookup_query"],
                "segment": row["segment"],
                "region": row["region"],
                "website": src,
                "domain": domain,
                "priority": row["priority"],
                "prospect_score": row["relevance_score"],
                "high_value": row["high_value"],
                "status": "prospect_new",
                "next_step": "queue_follow_and_outreach_after_reset",
                "notes": row["notes"],
            }
        )

    prospects.sort(key=lambda r: (-int(r["prospect_score"]), int(r["priority"]), r["org_name"].lower()))
    write_csv(
        PROSPECTS_CSV,
        prospects,
        [
            "logged_at",
            "org_name",
            "x_handle",
            "target_mode",
            "lookup_query",
            "segment",
            "region",
            "website",
            "domain",
            "priority",
            "prospect_score",
            "high_value",
            "status",
            "next_step",
            "notes",
        ],
    )

    # Append outreach automation assets.
    append_outreach_assets(run_ts)

    print(
        json.dumps(
            {
                "ok": True,
                "targets_json": str(TARGETS_JSON),
                "targets_csv": str(TARGETS_CSV),
                "follow_queue": str(FOLLOW_QUEUE),
                "post_drafts": str(POST_DRAFTS),
                "prospects_csv": str(PROSPECTS_CSV),
                "outreach_scripts": str(OUTREACH_SCRIPTS),
                "counts": {
                    "targets": len(targets),
                    "follows_queued": len(queue_rows),
                    "post_drafts": len(post_drafts),
                    "prospects": len(prospects),
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
