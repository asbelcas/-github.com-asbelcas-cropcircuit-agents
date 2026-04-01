#!/usr/bin/env python3
"""
x_bot.py — OAuth 1.0a X/Twitter bot for @CropCircuit.

All API calls use OAuth 1.0a signing (no bearer tokens).

Commands:
    post_one TEXT         Post a single tweet
    post_from_queue      Post next FIFO item (remove on success, keep on fail)
    queue TEXT            Add text to the post queue
    fetch_mentions       Pull mentions, store digest
    status               Show queue + post + mention stats
    scheduler            Run the daily scheduler (2 posts/day loop)

Env vars (all required):
    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

# Allow importing ha_config from same directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ha_config import get_website_url

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env.x"
QUEUE_FILE = ROOT / "logs" / "x_queue.jsonl"
POSTED_FILE = ROOT / "logs" / "x_posted.jsonl"
MENTIONS_FILE = ROOT / "logs" / "x_mentions.json"
LOG_FILE = ROOT / "logs" / "x_bot.log"

API_BASE = "https://api.x.com/2"
TWEET_URL = f"{API_BASE}/tweets"
ME_URL = f"{API_BASE}/users/me"
MENTIONS_URL = API_BASE + "/users/{user_id}/mentions"

MAX_TWEET_LEN = 280


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str):
    ts = now_iso()
    line = f"{ts} {msg}"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line, file=sys.stderr)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

def load_env():
    """Load .env.x into os.environ (does not overwrite existing vars)."""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip().removeprefix("export ").strip()
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)


# ---------------------------------------------------------------------------
# OAuth 1.0a — the only auth method
# ---------------------------------------------------------------------------

def get_oauth() -> OAuth1:
    """Build OAuth 1.0a signer. Requires all 4 env vars."""
    keys = {
        "X_API_KEY": os.environ.get("X_API_KEY", "").strip(),
        "X_API_SECRET": os.environ.get("X_API_SECRET", "").strip(),
        "X_ACCESS_TOKEN": os.environ.get("X_ACCESS_TOKEN", "").strip(),
        "X_ACCESS_TOKEN_SECRET": os.environ.get("X_ACCESS_TOKEN_SECRET", "").strip(),
    }
    missing = [k for k, v in keys.items() if not v]
    if missing:
        raise RuntimeError(f"Missing OAuth 1.0a env vars: {', '.join(missing)}")
    return OAuth1(
        keys["X_API_KEY"],
        keys["X_API_SECRET"],
        keys["X_ACCESS_TOKEN"],
        keys["X_ACCESS_TOKEN_SECRET"],
    )


def api_request(method: str, url: str, json_payload: dict = None,
                params: dict = None) -> dict:
    """Make a signed OAuth 1.0a request to the X API."""
    try:
        auth = get_oauth()
    except RuntimeError as e:
        log(f"AUTH ERROR: {e}")
        return {"error": str(e), "_status": 0, "ok": False}

    kwargs = {"auth": auth, "timeout": 30}
    if json_payload is not None:
        kwargs["json"] = json_payload
        kwargs["headers"] = {"Content-Type": "application/json"}
    if params is not None:
        kwargs["params"] = params

    try:
        resp = requests.request(method, url, **kwargs)
    except requests.RequestException as e:
        log(f"NETWORK ERROR: {e}")
        return {"error": str(e), "_status": 0, "ok": False}

    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text[:2000]}
    body["_status"] = resp.status_code
    body["ok"] = resp.ok
    return body


# ---------------------------------------------------------------------------
# JSONL helpers
# ---------------------------------------------------------------------------

def append_jsonl(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")


# ---------------------------------------------------------------------------
# 1. post_one — post a single tweet
# ---------------------------------------------------------------------------

def _append_cta(text: str) -> str:
    """Append website CTA if it fits and isn't already present."""
    url = get_website_url()
    if url in text:
        return text
    cta = f"\n\n{url}"
    if len(text) + len(cta) <= MAX_TWEET_LEN:
        return text + cta
    return text


def post_one(text: str, no_cta: bool = False) -> dict:
    text = text.strip()
    if not text:
        log("ERROR: empty tweet text")
        return {"ok": False, "error": "empty text"}
    if not no_cta:
        text = _append_cta(text)
    if len(text) > MAX_TWEET_LEN:
        log(f"ERROR: tweet too long ({len(text)} chars)")
        return {"ok": False, "error": f"too long: {len(text)} chars"}

    log(f"POST: {text[:80]}...")
    result = api_request("POST", TWEET_URL, json_payload={"text": text})

    record = {
        "ts": now_iso(),
        "text": text,
        "tweet_id": None,
        "ok": False,
        "http": result.get("_status", 0),
    }

    if result.get("_status") == 201 and "data" in result:
        record["tweet_id"] = result["data"].get("id")
        record["ok"] = True
        log(f"OK tweet_id={record['tweet_id']}")
    else:
        record["error"] = result.get("detail", result.get("error", "unknown"))
        log(f"FAIL HTTP {record['http']}: {record['error']}")

    append_jsonl(POSTED_FILE, record)
    return record


# ---------------------------------------------------------------------------
# 2. queue — add text to post queue
# ---------------------------------------------------------------------------

def queue_post(text: str, category: str = "manual"):
    text = text.strip()
    if not text:
        log("ERROR: cannot queue empty text")
        return
    if len(text) > MAX_TWEET_LEN:
        log(f"WARNING: queued text is {len(text)} chars (over {MAX_TWEET_LEN})")
    entry = {"queued_at": now_iso(), "text": text, "category": category}
    append_jsonl(QUEUE_FILE, entry)
    log(f"QUEUED [{category}]: {text[:80]}...")


# ---------------------------------------------------------------------------
# 3. post_from_queue — FIFO, remove on success, keep on failure
# ---------------------------------------------------------------------------

def post_from_queue() -> dict:
    if not QUEUE_FILE.exists() or not QUEUE_FILE.read_text().strip():
        log("Queue empty")
        return {"ok": True, "status": "empty_queue"}

    lines = QUEUE_FILE.read_text().splitlines()

    # Find first valid line
    for idx, raw in enumerate(lines):
        raw = raw.strip()
        if not raw:
            continue

        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            log(f"Removing invalid JSON at queue line {idx}")
            lines.pop(idx)
            QUEUE_FILE.write_text("\n".join(lines) + "\n" if lines else "")
            return {"ok": False, "status": "invalid_json"}

        text = (item.get("text") or "").strip()
        if not text:
            log("Removing queue item with empty text")
            lines.pop(idx)
            QUEUE_FILE.write_text("\n".join(lines) + "\n" if lines else "")
            return {"ok": False, "status": "empty_text"}

        result = post_one(text)

        if result.get("ok"):
            lines.pop(idx)
            QUEUE_FILE.write_text("\n".join(lines) + "\n" if lines else "")
            log("Queue item posted and removed")
        else:
            log("Queue item FAILED — keeping for retry")

        return result

    log("Queue has no valid items")
    return {"ok": True, "status": "empty_queue"}


# ---------------------------------------------------------------------------
# 4. fetch_mentions — pull mentions via OAuth 1.0a
# ---------------------------------------------------------------------------

def fetch_mentions() -> dict:
    me = api_request("GET", ME_URL)
    if me.get("_status") != 200 or "data" not in me:
        log(f"Cannot get user info: {me.get('detail', me.get('error', 'unknown'))}")
        return {"ok": False, "error": "cannot get user id"}

    user_id = me["data"]["id"]
    username = me["data"].get("username", "unknown")
    log(f"Fetching mentions for @{username} (id={user_id})")

    prev = {}
    if MENTIONS_FILE.exists():
        try:
            prev = json.loads(MENTIONS_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            pass

    params = {
        "max_results": 50,
        "tweet.fields": "created_at,author_id,text,conversation_id",
    }
    since_id = prev.get("newest_id")
    if since_id:
        params["since_id"] = since_id

    result = api_request("GET", MENTIONS_URL.format(user_id=user_id), params=params)

    if result.get("_status") != 200:
        log(f"Mentions fetch failed: HTTP {result.get('_status')}")
        return {"ok": False, "error": f"HTTP {result.get('_status')}"}

    tweets = result.get("data", [])
    meta = result.get("meta", {})
    newest_id = meta.get("newest_id", since_id)

    digest = {
        "fetched_at": now_iso(),
        "user_id": user_id,
        "username": username,
        "newest_id": newest_id,
        "count": len(tweets),
        "mentions": tweets,
    }

    MENTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    MENTIONS_FILE.write_text(json.dumps(digest, indent=2, default=str) + "\n")
    log(f"Stored {len(tweets)} mentions (newest_id={newest_id})")
    return {"ok": True, "count": len(tweets)}


# ---------------------------------------------------------------------------
# 5. status
# ---------------------------------------------------------------------------

def show_status() -> dict:
    pending = 0
    if QUEUE_FILE.exists():
        pending = sum(1 for l in QUEUE_FILE.read_text().splitlines() if l.strip())

    total_posted = 0
    last_posted = None
    if POSTED_FILE.exists():
        posted_lines = [l for l in POSTED_FILE.read_text().splitlines() if l.strip()]
        total_posted = len(posted_lines)
        if posted_lines:
            last_posted = json.loads(posted_lines[-1])

    last_mentions = None
    if MENTIONS_FILE.exists():
        try:
            last_mentions = json.loads(MENTIONS_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            pass

    status = {
        "queue_pending": pending,
        "total_posted": total_posted,
        "last_posted": {
            "ts": last_posted.get("ts") if last_posted else None,
            "text": (last_posted.get("text", "")[:80]) if last_posted else None,
            "ok": last_posted.get("ok") if last_posted else None,
        },
        "mentions_last_check": last_mentions.get("fetched_at") if last_mentions else None,
        "mentions_count": last_mentions.get("count", 0) if last_mentions else 0,
    }
    print(json.dumps(status, indent=2, ensure_ascii=False))
    return status


# ---------------------------------------------------------------------------
# 6. scheduler — long-running process, posts 2x/day from queue
# ---------------------------------------------------------------------------

def scheduler():
    """Run as a daemon. Posts from queue at 08:30 and 18:30 UTC.
    Fetches mentions at 12:00 and 20:00 UTC.
    Polls every 60 seconds."""
    log("Scheduler started")

    posted_hours = set()   # track which hours we've posted this day
    mention_hours = set()  # track which hours we've fetched this day
    current_day = None

    POST_HOURS = {8, 18}       # 08:30 and 18:30 UTC (~morning/evening ET)
    MENTION_HOURS = {12, 20}   # noon and 8pm UTC
    TRIGGER_MINUTE = 30        # fire at :30

    def handle_signal(sig, frame):
        log("Scheduler stopped by signal")
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    while True:
        now = datetime.now(timezone.utc)

        # Reset daily trackers at midnight
        today = now.strftime("%Y-%m-%d")
        if current_day != today:
            current_day = today
            posted_hours.clear()
            mention_hours.clear()
            log(f"New day: {today}")

        hour = now.hour
        minute = now.minute

        # Post from queue at scheduled hours
        if hour in POST_HOURS and minute >= TRIGGER_MINUTE and hour not in posted_hours:
            posted_hours.add(hour)
            log(f"Scheduler: posting from queue (hour={hour})")
            post_from_queue()

        # Fetch mentions at scheduled hours
        if hour in MENTION_HOURS and minute >= TRIGGER_MINUTE and hour not in mention_hours:
            mention_hours.add(hour)
            log(f"Scheduler: fetching mentions (hour={hour})")
            fetch_mentions()

        time.sleep(60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    load_env()

    parser = argparse.ArgumentParser(description="OAuth 1.0a X bot for @CropCircuit")

    # Flag-style (HA shell_command compatible)
    parser.add_argument("--post-text", type=str, help="Post tweet immediately")
    parser.add_argument("--post-from-queue", action="store_true")
    parser.add_argument("--fetch-mentions", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--queue-text", type=str, help="Add to queue")
    parser.add_argument("--category", default="manual")
    parser.add_argument("--scheduler", action="store_true", help="Run daily scheduler daemon")

    # Subcommands
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("post_one")
    p.add_argument("text")
    p = sub.add_parser("queue")
    p.add_argument("text")
    p.add_argument("--category", default="manual")
    sub.add_parser("post_from_queue")
    sub.add_parser("fetch_mentions")
    sub.add_parser("status")
    sub.add_parser("scheduler")

    args = parser.parse_args()

    # Flag dispatch
    if args.post_text:
        r = post_one(args.post_text)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        sys.exit(0 if r.get("ok") else 2)
    if args.post_from_queue:
        r = post_from_queue()
        print(json.dumps(r, indent=2, ensure_ascii=False))
        sys.exit(0 if r.get("ok") else 2)
    if args.fetch_mentions:
        r = fetch_mentions()
        print(json.dumps(r, indent=2, ensure_ascii=False))
        sys.exit(0 if r.get("ok") is not False else 2)
    if args.status:
        show_status()
        sys.exit(0)
    if args.queue_text:
        queue_post(args.queue_text, category=args.category)
        sys.exit(0)
    if args.scheduler:
        scheduler()

    # Subcommand dispatch
    cmd = args.command
    if cmd == "post_one":
        r = post_one(args.text)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        sys.exit(0 if r.get("ok") else 1)
    elif cmd == "queue":
        queue_post(args.text, category=getattr(args, "category", "manual"))
    elif cmd == "post_from_queue":
        r = post_from_queue()
        print(json.dumps(r, indent=2, ensure_ascii=False))
        sys.exit(0 if r.get("ok") else 1)
    elif cmd == "fetch_mentions":
        r = fetch_mentions()
        print(json.dumps(r, indent=2, ensure_ascii=False))
        sys.exit(0 if r.get("ok") is not False else 1)
    elif cmd == "status":
        show_status()
    elif cmd == "scheduler":
        scheduler()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
