#!/usr/bin/env python3
"""Public donor landing service for CropCircuit."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import html
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
LOG_JSONL = ROOT / "logs" / "donor_web.log.jsonl"
LOG_PLAIN = ROOT / "logs" / "donor_web.log"
CONVERSION_LOG = ROOT / "logs" / "donor_conversion.log"
TRAFFIC_LOG = ROOT / "logs" / "traffic_tracking.log"
DB_PATH = ROOT / "runtime" / "donor_dedupe.sqlite"
PROOF_LEDGER_PATH = ROOT / "runtime" / "proof_ledger.json"
BUILD_FEED_PATH = ROOT / "runtime" / "build_feed.json"
MILESTONE_PROGRESS_PATH = ROOT / "runtime" / "milestone_progress.json"
TRAFFIC_METRICS_PATH = ROOT / "runtime" / "traffic_metrics.json"
INGEST_URL = os.environ.get("DONOR_INGEST_URL", "http://127.0.0.1:8777/donor")
HOST = os.environ.get("DONOR_WEB_HOST", "127.0.0.1")
PORT = int(os.environ.get("DONOR_WEB_PORT", "8788"))
RATE_LIMIT_COUNT = int(os.environ.get("DONOR_RATE_LIMIT_COUNT", "5"))
RATE_LIMIT_SECONDS = int(os.environ.get("DONOR_RATE_LIMIT_SECONDS", "600"))
DEDUPE_SECONDS = int(os.environ.get("DONOR_DEDUPE_SECONDS", str(24 * 3600)))
IP_HASH_SALT = os.environ.get("DONOR_IP_HASH_SALT", "cropcircuit-local-salt")
DONOR_WEBHOOK_SECRET = os.environ.get("DONOR_WEBHOOK_SECRET", "")
DONATION_LINK = os.environ.get("DONATION_LINK", os.environ.get("PAYPAL_DONATION_URL", "https://www.paypal.com/donate"))
MAX_MESSAGE_LEN = 1000

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DB_LOCK = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dirs() -> None:
    LOG_JSONL.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS events ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "ts INTEGER NOT NULL, "
        "ip_hash TEXT NOT NULL, "
        "lead_hash TEXT, "
        "accepted INTEGER NOT NULL, "
        "reason TEXT NOT NULL)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ip_ts ON events (ip_hash, ts)")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS dedupe ("
        "lead_hash TEXT PRIMARY KEY, "
        "ts INTEGER NOT NULL)"
    )
    return conn


def append_log(payload: dict) -> None:
    with LOG_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def append_submission_log(ip: str, outcome: str, email: str = "") -> None:
    with LOG_PLAIN.open("a", encoding="utf-8") as f:
        f.write(f"{now_iso()} ip={ip or '-'} outcome={outcome} email={email[:120]}\n")


def append_conversion_log(event: str, ip: str = "", email: str = "", amount: str = "", reason: str = "") -> None:
    with CONVERSION_LOG.open("a", encoding="utf-8") as f:
        f.write(
            f"{now_iso()} event={event} ip={ip or '-'} email={email[:120]} amount={amount[:32]} reason={reason[:120]}\n"
        )


def append_traffic_log(event: str, source: str = "", ip: str = "", detail: str = "") -> None:
    with TRAFFIC_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{now_iso()} event={event} source={source[:64]} ip={ip or '-'} detail={detail[:180]}\n")


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_json_list(path: Path, key: str) -> list[dict]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(raw, dict):
        rows = raw.get(key, [])
        return rows if isinstance(rows, list) else []
    if isinstance(raw, list):
        return raw
    return []


def bump_traffic_metric(event: str, source: str = "") -> None:
    payload = load_json(TRAFFIC_METRICS_PATH, {"updated_at": "", "totals": {}, "by_source": {}})
    totals = payload.get("totals", {})
    by_source = payload.get("by_source", {})
    if not isinstance(totals, dict):
        totals = {}
    if not isinstance(by_source, dict):
        by_source = {}
    totals[event] = int(totals.get(event, 0) or 0) + 1
    src = source.strip() or "direct"
    src_blob = by_source.get(src, {})
    if not isinstance(src_blob, dict):
        src_blob = {}
    src_blob[event] = int(src_blob.get(event, 0) or 0) + 1
    by_source[src] = src_blob
    payload["totals"] = totals
    payload["by_source"] = by_source
    payload["updated_at"] = now_iso()
    write_json(TRAFFIC_METRICS_PATH, payload)


def ip_from_headers(handler: BaseHTTPRequestHandler) -> str:
    fwd = handler.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return handler.client_address[0] if handler.client_address else ""


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_phone(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def truncate(value: str, size: int) -> str:
    if len(value) <= size:
        return value
    return value[:size]


def compute_lead_hash(email: str, phone: str, amount_range: str, message: str) -> str:
    raw = f"{email.lower()}|{normalize_phone(phone)}|{amount_range.strip().lower()}|{truncate(message.strip().lower(), 200)}"
    return sha256_hex(raw)


def parse_body(handler: BaseHTTPRequestHandler) -> tuple[dict, str]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw_bytes = handler.rfile.read(length)
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    content_type = (handler.headers.get("Content-Type") or "").lower()

    if content_type.startswith("application/json"):
        return (json.loads(raw_text or "{}"), raw_text)

    parsed = urllib.parse.parse_qs(raw_text, keep_blank_values=True)
    payload = {k: (v[0] if isinstance(v, list) and v else "") for k, v in parsed.items()}
    return payload, raw_text


def verify_signature(raw_body: str, header_sig: str) -> bool:
    if not DONOR_WEBHOOK_SECRET:
        return True
    if not header_sig:
        return True
    expected = hmac.new(
        DONOR_WEBHOOK_SECRET.encode("utf-8"),
        raw_body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    provided = header_sig.strip().lower()
    if provided.startswith("sha256="):
        provided = provided.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)


def get_rate_count(conn: sqlite3.Connection, ip_hash: str, now_ts: int) -> int:
    cutoff = now_ts - RATE_LIMIT_SECONDS
    row = conn.execute(
        "SELECT COUNT(*) FROM events WHERE ip_hash = ? AND ts >= ?",
        (ip_hash, cutoff),
    ).fetchone()
    return int(row[0] if row else 0)


def is_duplicate(conn: sqlite3.Connection, lead_hash: str, now_ts: int) -> bool:
    conn.execute("DELETE FROM dedupe WHERE ts < ?", (now_ts - DEDUPE_SECONDS,))
    row = conn.execute("SELECT ts FROM dedupe WHERE lead_hash = ?", (lead_hash,)).fetchone()
    return row is not None


def record_event(conn: sqlite3.Connection, now_ts: int, ip_hash: str, lead_hash: str, accepted: bool, reason: str) -> None:
    conn.execute(
        "INSERT INTO events (ts, ip_hash, lead_hash, accepted, reason) VALUES (?, ?, ?, ?, ?)",
        (now_ts, ip_hash, lead_hash, 1 if accepted else 0, reason),
    )
    conn.commit()


def record_dedupe(conn: sqlite3.Connection, now_ts: int, lead_hash: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO dedupe (lead_hash, ts) VALUES (?, ?)",
        (lead_hash, now_ts),
    )
    conn.commit()


def post_to_ingest(payload: dict) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        INGEST_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            code = int(resp.status)
            txt = resp.read().decode("utf-8", errors="replace")
            return code, txt
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


FORM_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Support Crop Circuit</title>
  <style>
    body {font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 0; background:#f7f8fb; color:#1c2635;}
    .wrap {max-width: 720px; margin: 0 auto; padding: 20px;}
    .card {background:#fff; border-radius:14px; padding:20px; box-shadow:0 8px 28px rgba(0,0,0,.08);}
    h1 {font-size:1.5rem; margin:0 0 8px;}
    p {line-height:1.45;}
    label {font-weight:600; display:block; margin:12px 0 6px;}
    input, select, textarea {width:100%; padding:12px; border:1px solid #c8d3e1; border-radius:10px; font-size:16px;}
    textarea {min-height: 120px;}
    .row {display:grid; gap:10px; grid-template-columns:1fr;}
    .momentum {background:#eef8f1; border:1px solid #b8dfc2; border-radius:12px; padding:12px; margin: 10px 0 14px;}
    .barwrap {background:#e1e7ef; border-radius:999px; height:10px; overflow:hidden; margin-top:6px;}
    .bar {height:100%; background:#0b7a4f;}
    .quick {display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:8px;}
    .quick label {margin:0; font-weight:600; border:1px solid #c8d3e1; border-radius:10px; padding:10px; text-align:center; cursor:pointer; background:#f8fbff;}
    .quick input {width:auto; margin-right:6px;}
    .btn {margin-top:16px; border:none; border-radius:10px; padding:12px 16px; background:#0b7a4f; color:#fff; font-size:16px; font-weight:600; width:100%;}
    .hp {position:absolute; left:-10000px; width:1px; height:1px; overflow:hidden;}
    @media (min-width: 640px) {
      .row.two {grid-template-columns:1fr 1fr;}
      .quick {grid-template-columns:1fr 1fr 1fr 1fr;}
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      __MOMENTUM_STRIP__
      <h1>Help build a regenerative farm in Michigan.</h1>
      <p>We're building a working farm in Michigan designed to restore soil, grow real food, and create a model others can replicate across the country.</p>
      <p>Early supporters help fund infrastructure, land prep, animals, and systems.</p>
      <p>This isn't theoretical.</p>
      <p>This is happening now.</p>
      <p><strong>Every contribution directly builds something physical.</strong></p>
      <p><strong>Where your money is going right now</strong></p>
      __PROOF_LEDGER_BLOCK__
      <p><strong>Farm forming in real time</strong></p>
      __BUILD_FEED_BLOCK__
      <p><strong>Milestones:</strong></p>
      <ul>
        <li>$500 -> soil testing</li>
        <li>$1,200 -> fencing</li>
        <li>$2,500 -> irrigation prep</li>
        <li>$5,000 -> livestock infrastructure</li>
      </ul>
      <p><strong>What your money builds:</strong></p>
      <ul>
        <li>land prep and soil-restoration inputs</li>
        <li>farm infrastructure and equipment readiness</li>
        <li>animal-system setup and operational support</li>
      </ul>
      <ul>
        <li><strong>Michigan location:</strong> active farm base in Augusta, Michigan</li>
        <li><strong>Regenerative methods:</strong> soil-first, restoration-oriented practices</li>
        <li><strong>Transparency statement:</strong> we publish progress and funding alignment openly</li>
        <li><strong>Live logs:</strong> operational evidence updates daily</li>
      </ul>
      <p><strong>Founding supporter lane:</strong> your early support helps prove this model works at full speed.</p>
      <form method="post" action="/submit">
        <div class="hp" aria-hidden="true">
          <label for="website">Company website</label>
          <input id="website" name="website" type="text" autocomplete="off" tabindex="-1"/>
        </div>
        <div class="row">
          <label for="name">Name</label>
          <input id="name" name="name" type="text" maxlength="120" placeholder="Your name"/>
          <input type="hidden" name="source" value="__SOURCE__"/>
        </div>
        <div class="row two">
          <div>
            <label for="email">Email *</label>
            <input id="email" name="email" type="email" maxlength="200" required placeholder="you@example.com"/>
          </div>
          <div>
            <label for="phone">Phone</label>
            <input id="phone" name="phone" type="tel" maxlength="30" placeholder="(optional)"/>
          </div>
        </div>
        <div class="row">
          <label>Founding supporter quick options</label>
          <div class="quick">
            <label><input type="radio" name="amount_range" value="5">$5 - Seed Supporter</label>
            <label><input type="radio" name="amount_range" value="25">$25 - Soil Builder</label>
            <label><input type="radio" name="amount_range" value="100">$100 - Infrastructure Backer</label>
            <label><input type="radio" name="amount_range" value="500">$500 - Founding Contributor</label>
          </div>
        </div>
        <div class="row">
          <label for="message">Message</label>
          <textarea id="message" name="message" maxlength="1000" placeholder="Tell us what you're hoping this helps create."></textarea>
        </div>
        <button class="btn" type="submit">Support the mission</button>
      </form>
      <p><a href="__DONATION_LINK__" target="_blank" rel="noopener">Prefer to donate directly?</a></p>
      <p><a href="/story">See why this matters now</a></p>
      <p><a href="/proof">Live proof ledger</a> | <a href="/share">Share this mission</a></p>
      <p>We'll never sell your info. If you leave an email, you'll only get occasional updates and a receipt/thank-you.</p>
      <p><small>Not in a position to donate? Sharing this page helps more than you think.</small></p>
    </div>
  </div>
</body>
</html>
"""


THANKS_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Thank You</title>
  <style>
    body {font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 0; background:#f7f8fb; color:#1c2635;}
    .wrap {max-width: 640px; margin: 0 auto; padding: 24px;}
    .card {background:#fff; border-radius:14px; padding:24px; box-shadow:0 8px 28px rgba(0,0,0,.08);}
    a.btn {display:inline-block; padding:12px 16px; border-radius:10px; background:#0b7a4f; color:#fff; text-decoration:none; font-weight:600;}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>You are now part of the build.</h1>
      <p>We received your message and routed it into the operating workflow.</p>
      <p>If you want to move this faster right now, use the direct supporter link:</p>
      <p><a class="btn" href="__DONATION_LINK__" target="_blank" rel="noopener">Donate with PayPal</a></p>
      <p>Next steps: follow updates, share the mission, and consider a recurring founding-supporter contribution.</p>
      <p><a href="/story">Shareable credibility page</a></p>
      <p><a href="/proof">Live proof ledger</a></p>
      <p><a href="/">Back to form</a></p>
    </div>
  </div>
</body>
</html>
"""


STORY_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Why Crop Circuit</title>
  <style>
    body {font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 0; background:#f7f8fb; color:#1c2635;}
    .wrap {max-width: 700px; margin: 0 auto; padding: 22px;}
    .card {background:#fff; border-radius:14px; padding:22px; box-shadow:0 8px 28px rgba(0,0,0,.08);}
    li {margin-bottom:8px;}
    a.btn {display:inline-block; padding:12px 16px; border-radius:10px; background:#0b7a4f; color:#fff; text-decoration:none; font-weight:600;}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Crop Circuit: proof-in-progress</h1>
      <p>We are building future food systems with transparent execution and measurable outcomes.</p>
      <ul>
        <li><strong>Land:</strong> active farm base in Augusta, Michigan.</li>
        <li><strong>Partners:</strong> donor + institutional partner outreach and follow-up running daily.</li>
        <li><strong>Automation:</strong> intake, lead routing, and follow-up workflows are operational.</li>
        <li><strong>Grant work underway:</strong> live submission pipeline with evidence logs and screenshots.</li>
      </ul>
      <p><a class="btn" href="/">Support the mission</a></p>
    </div>
  </div>
</body>
</html>
"""


SHARE_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Share Crop Circuit</title>
  <style>
    body {font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 0; background:#f7f8fb; color:#1c2635;}
    .wrap {max-width: 720px; margin: 0 auto; padding: 22px;}
    .card {background:#fff; border-radius:14px; padding:22px; box-shadow:0 8px 28px rgba(0,0,0,.08);}
    pre {white-space: pre-wrap; background:#f4f7fb; border-radius:10px; padding:12px;}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Share this mission</h1>
      <p>Copy/paste this:</p>
      <pre>Help build the farm that feeds the future.
Crop Circuit is building a regenerative farm in Michigan that restores soil, grows real food, and creates a model others can replicate.
Every contribution directly builds something physical.
Donate: __DONATION_LINK__
Support or share: __PUBLIC_URL__</pre>
      <p><a href="/">Back</a></p>
    </div>
  </div>
</body>
</html>
"""


def build_proof_html() -> str:
    status_path = ROOT / "runtime" / "ha_grant_pipeline_status.json"
    summary_path = ROOT / "logs" / "donor_daily_summary.log"
    status_blob = "{}"
    summary_blob = "{}"
    if status_path.exists():
        status_blob = status_path.read_text(encoding="utf-8")[:2000]
    if summary_path.exists():
        lines = summary_path.read_text(encoding="utf-8").splitlines()
        if lines:
            summary_blob = lines[-1][:2000]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Proof Ledger</title>
  <style>
    body {{font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 0; background:#f7f8fb; color:#1c2635;}}
    .wrap {{max-width: 760px; margin: 0 auto; padding: 22px;}}
    .card {{background:#fff; border-radius:14px; padding:22px; box-shadow:0 8px 28px rgba(0,0,0,.08);}}
    pre {{white-space: pre-wrap; background:#f4f7fb; border-radius:10px; padding:12px;}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Live proof ledger</h1>
      <p>High-trust conversion mechanism: transparent operating evidence.</p>
      <h3>Latest pipeline status</h3>
      <pre>{html.escape(status_blob)}</pre>
      <h3>Latest daily summary</h3>
      <pre>{html.escape(summary_blob)}</pre>
      <p><a href="/">Back to support page</a></p>
    </div>
  </div>
</body>
</html>
"""


def build_ledger_block() -> str:
    rows = load_json_list(PROOF_LEDGER_PATH, "entries")
    if not rows:
        return "<p>No ledger entries yet.</p>"
    items = []
    for r in rows[:6]:
        ts = html.escape(str(r.get("timestamp", "")))
        funds = html.escape(str(r.get("funds_received", "")))
        action = html.escape(str(r.get("build_action_funded", "")))
        status = html.escape(str(r.get("status", "")))
        items.append(f"<li>{ts} | ${funds} | {action} | {status}</li>")
    return "<ul>" + "".join(items) + "</ul>"


def build_feed_block() -> str:
    rows = load_json_list(BUILD_FEED_PATH, "entries")
    if not rows:
        return "<p>No build updates yet.</p>"
    items = []
    for r in rows[:8]:
        cat = html.escape(str(r.get("category", "")))
        note = html.escape(str(r.get("note", "")))
        status = html.escape(str(r.get("status", "")))
        items.append(f"<li>{cat}: {note} ({status})</li>")
    return "<ul>" + "".join(items) + "</ul>"


def build_momentum_strip() -> str:
    proof = load_json(PROOF_LEDGER_PATH, {})
    summary = proof.get("summary", {}) if isinstance(proof, dict) else {}
    donors = int(summary.get("donors_count", 0) or 0)
    funds = float(summary.get("funds_total", 0) or 0)
    last = str(summary.get("last_funded_action", "seed funding in motion"))
    progress = load_json(MILESTONE_PROGRESS_PATH, {})
    next_target = float(progress.get("next_target_amount", 5000) or 5000)
    next_gap = float(progress.get("next_gap", max(0.0, 5000 - funds)) or 0)
    if next_target <= 0:
        pct = 100.0
    else:
        pct = max(0.0, min(100.0, ((next_target - next_gap) / next_target) * 100.0))
    return (
        '<div class="momentum">'
        f"<strong>{donors} people are building this farm right now.</strong><br/>"
        f"<strong>${funds:,.0f} already committed.</strong><br/>"
        f"Last action funded: {html.escape(last)}"
        f'<div class="barwrap"><div class="bar" style="width:{pct:.1f}%"></div></div>'
        "</div>"
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "CropCircuitDonorWeb/1.0"

    def _send(self, code: int, body: str, content_type: str = "text/html; charset=utf-8") -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code: int, payload: dict) -> None:
        self._send(code, json.dumps(payload), "application/json")

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        source = str((query.get("src", [""])[0] or query.get("source", [""])[0] or "")).strip()
        ip = ip_from_headers(self)

        if route == "/":
            if source:
                append_traffic_log("visitor", source=source, ip=ip, detail="landing")
                bump_traffic_metric("visitors", source)
            body = FORM_HTML.replace("__DONATION_LINK__", DONATION_LINK)
            body = body.replace("__SOURCE__", html.escape(source or "direct"))
            body = body.replace("__PROOF_LEDGER_BLOCK__", build_ledger_block())
            body = body.replace("__BUILD_FEED_BLOCK__", build_feed_block())
            body = body.replace("__MOMENTUM_STRIP__", build_momentum_strip())
            self._send(200, body)
            return
        if route == "/thanks":
            self._send(200, THANKS_HTML.replace("__DONATION_LINK__", DONATION_LINK))
            return
        if route == "/story":
            self._send(200, STORY_HTML)
            return
        if route == "/share":
            public_url = os.environ.get("DONOR_PUBLIC_URL", os.environ.get("PUBLIC_DONOR_URL", "https://found-tunes-complications-nirvana.trycloudflare.com"))
            html_out = SHARE_HTML.replace("__PUBLIC_URL__", public_url).replace("__DONATION_LINK__", DONATION_LINK)
            self._send(200, html_out)
            return
        if route == "/proof":
            self._send(200, build_proof_html())
            return
        if route == "/go":
            src = source or "direct"
            append_traffic_log("click", source=src, ip=ip, detail="donation_redirect")
            bump_traffic_metric("clicks", src)
            self.send_response(302)
            self.send_header("Location", DONATION_LINK)
            self.end_headers()
            return
        if route == "/healthz":
            self._json(200, {"ok": True, "service": "donor-web", "ingest_url": INGEST_URL, "time": now_iso()})
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def do_POST(self):  # noqa: N802
        if self.path != "/submit":
            self._json(404, {"ok": False, "error": "not_found"})
            return

        ip = ip_from_headers(self)
        ip_hash = sha256_hex(f"{ip}|{IP_HASH_SALT}")
        ua = truncate(self.headers.get("User-Agent", ""), 160)
        now_ts = int(time.time())

        try:
            payload, raw_body = parse_body(self)
        except Exception:
            self._json(400, {"ok": False, "error": "invalid_body"})
            return

        sig = self.headers.get("X-Donor-Signature", "")
        if sig and not verify_signature(raw_body, sig):
            append_submission_log(ip, "invalid_signature")
            append_conversion_log("submit_blocked", ip=ip, reason="invalid_signature")
            append_log(
                {
                    "timestamp_utc": now_iso(),
                    "ip_hash": ip_hash,
                    "user_agent": ua,
                    "lead_hash": "",
                    "accepted": False,
                    "reason": "invalid_signature",
                }
            )
            self._json(401, {"ok": False, "error": "invalid_signature"})
            return

        name = str(payload.get("name", "") or "").strip()
        email = str(payload.get("email", "") or "").strip()
        phone = str(payload.get("phone", "") or "").strip()
        interest = str(payload.get("interest", "") or "").strip()
        amount_range = str(payload.get("amount_range", "") or "").strip()
        source = str(payload.get("source", "") or "").strip()
        message = str(payload.get("message", "") or "").strip()
        honeypot = str(payload.get("website", "") or "").strip()
        lead_hash = compute_lead_hash(email, phone, amount_range, message)

        if honeypot:
            append_submission_log(ip, "honeypot", email)
            append_conversion_log("submit_blocked", ip=ip, email=email, amount=amount_range, reason="honeypot")
            append_log(
                {
                    "timestamp_utc": now_iso(),
                    "ip_hash": ip_hash,
                    "user_agent": ua,
                    "lead_hash": lead_hash,
                    "accepted": False,
                    "reason": "honeypot",
                }
            )
            self.send_response(204)
            self.end_headers()
            return

        if not EMAIL_RE.match(email):
            append_submission_log(ip, "invalid_email", email)
            append_conversion_log("submit_blocked", ip=ip, email=email, amount=amount_range, reason="invalid_email")
            append_log(
                {
                    "timestamp_utc": now_iso(),
                    "ip_hash": ip_hash,
                    "user_agent": ua,
                    "lead_hash": lead_hash,
                    "accepted": False,
                    "reason": "invalid_email",
                }
            )
            self._json(400, {"ok": False, "error": "invalid_email"})
            return

        phone_digits = normalize_phone(phone)
        if phone and len(phone_digits) < 7:
            append_submission_log(ip, "invalid_phone", email)
            append_conversion_log("submit_blocked", ip=ip, email=email, amount=amount_range, reason="invalid_phone")
            append_log(
                {
                    "timestamp_utc": now_iso(),
                    "ip_hash": ip_hash,
                    "user_agent": ua,
                    "lead_hash": lead_hash,
                    "accepted": False,
                    "reason": "invalid_phone",
                }
            )
            self._json(400, {"ok": False, "error": "invalid_phone"})
            return

        if len(message) > MAX_MESSAGE_LEN:
            append_submission_log(ip, "message_too_long", email)
            append_conversion_log("submit_blocked", ip=ip, email=email, amount=amount_range, reason="message_too_long")
            append_log(
                {
                    "timestamp_utc": now_iso(),
                    "ip_hash": ip_hash,
                    "user_agent": ua,
                    "lead_hash": lead_hash,
                    "accepted": False,
                    "reason": "message_too_long",
                }
            )
            self._json(400, {"ok": False, "error": "message_too_long"})
            return

        with DB_LOCK:
            conn = db()
            try:
                rate_count = get_rate_count(conn, ip_hash, now_ts)
                if rate_count >= RATE_LIMIT_COUNT:
                    append_submission_log(ip, "rate_limited", email)
                    append_conversion_log("submit_blocked", ip=ip, email=email, amount=amount_range, reason="rate_limited")
                    record_event(conn, now_ts, ip_hash, lead_hash, False, "rate_limited")
                    append_log(
                        {
                            "timestamp_utc": now_iso(),
                            "ip_hash": ip_hash,
                            "user_agent": ua,
                            "lead_hash": lead_hash,
                            "accepted": False,
                            "reason": "rate_limited",
                        }
                    )
                    self._json(429, {"ok": False, "error": "rate_limited"})
                    return

                if is_duplicate(conn, lead_hash, now_ts):
                    append_submission_log(ip, "duplicate_24h", email)
                    append_conversion_log("submit_blocked", ip=ip, email=email, amount=amount_range, reason="duplicate_24h")
                    record_event(conn, now_ts, ip_hash, lead_hash, False, "duplicate_24h")
                    append_log(
                        {
                            "timestamp_utc": now_iso(),
                            "ip_hash": ip_hash,
                            "user_agent": ua,
                            "lead_hash": lead_hash,
                            "accepted": False,
                            "reason": "duplicate_24h",
                        }
                    )
                    self._json(409, {"ok": False, "error": "duplicate_24h"})
                    return
            finally:
                conn.close()

        ingest_payload = {
            "name": name,
            "email": email,
            "phone": phone,
            "interest": interest,
            "amount_range": amount_range,
            "message": message,
            "source": "donor_web_public",
        }
        code, _body = post_to_ingest(ingest_payload)
        if code != 200:
            append_submission_log(ip, f"ingest_error_{code}", email)
            append_conversion_log("submit_blocked", ip=ip, email=email, amount=amount_range, reason=f"ingest_error_{code}")
            with DB_LOCK:
                conn = db()
                try:
                    record_event(conn, now_ts, ip_hash, lead_hash, False, f"ingest_error_{code}")
                finally:
                    conn.close()
            append_log(
                {
                    "timestamp_utc": now_iso(),
                    "ip_hash": ip_hash,
                    "user_agent": ua,
                    "lead_hash": lead_hash,
                    "accepted": False,
                    "reason": f"ingest_error_{code}",
                }
            )
            self._json(502, {"ok": False, "error": "ingest_failed"})
            return

        with DB_LOCK:
            conn = db()
            try:
                record_event(conn, now_ts, ip_hash, lead_hash, True, "accepted")
                record_dedupe(conn, now_ts, lead_hash)
            finally:
                conn.close()

        append_log(
            {
                "timestamp_utc": now_iso(),
                "ip_hash": ip_hash,
                "user_agent": ua,
                "lead_hash": lead_hash,
                "accepted": True,
                "reason": "accepted",
                "message_excerpt": truncate(message, 200),
            }
        )
        append_submission_log(ip, "accepted", email)
        append_conversion_log(
            "lead_accepted",
            ip=ip,
            email=email,
            amount=amount_range,
            reason=f"submitted source={source or 'direct'}",
        )
        append_traffic_log("conversion", source=source or "direct", ip=ip, detail=email)
        bump_traffic_metric("conversions", source or "direct")
        self.send_response(303)
        self.send_header("Location", "/thanks")
        self.end_headers()

    def log_message(self, fmt: str, *args) -> None:
        return


def main() -> int:
    ensure_dirs()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    append_log(
        {
            "timestamp_utc": now_iso(),
            "ip_hash": "",
            "user_agent": "",
            "lead_hash": "",
            "accepted": True,
            "reason": f"service_start {HOST}:{PORT}",
        }
    )
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
