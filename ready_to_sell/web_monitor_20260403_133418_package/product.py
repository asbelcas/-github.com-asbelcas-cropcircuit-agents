#!/usr/bin/env python3
"""
Website Monitor - Uptime & Change Detection Tool
Monitors websites for downtime and content changes, with email alerts.

Usage:
  python web_monitor.py --url https://example.com
  python web_monitor.py --url https://example.com --interval 60 --alert-email you@gmail.com
  python web_monitor.py --urls urls.txt --interval 300 --log monitor.log
"""

import argparse
import hashlib
import json
import logging
import smtplib
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

try:
    import requests
except ImportError:
    print("Missing dependency: pip install requests")
    sys.exit(1)


def setup_logging(log_file=None):
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def send_email_alert(subject, body, to_addr, from_addr, smtp_host, smtp_port, smtp_password):
    """Send an email alert via SMTP."""
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(from_addr, smtp_password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        logging.info(f"Alert email sent to {to_addr}")
    except Exception as e:
        logging.warning(f"Failed to send email alert: {e}")


def check_site(url, expected_text=None, timeout=30):
    """
    Check a single URL.
    Returns: dict with keys: up (bool), status_code, response_ms, content_hash, error
    """
    result = {"url": url, "up": False, "status_code": None,
              "response_ms": None, "content_hash": None, "error": None}
    try:
        start = time.monotonic()
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "WebMonitor/1.0"})
        result["response_ms"] = round((time.monotonic() - start) * 1000)
        result["status_code"] = resp.status_code
        result["up"] = resp.status_code < 400

        content = resp.text.encode("utf-8", errors="replace")
        result["content_hash"] = hashlib.sha256(content).hexdigest()

        if expected_text and expected_text not in resp.text:
            result["up"] = False
            result["error"] = f"Expected text not found: {expected_text!r}"

    except requests.exceptions.Timeout:
        result["error"] = "Request timed out"
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Connection error: {e}"
    except Exception as e:
        result["error"] = str(e)

    return result


def monitor(urls, interval=300, expected_text=None, log_file=None,
            alert_email=None, from_email=None, smtp_host="smtp.gmail.com",
            smtp_port=465, smtp_password=None, state_file=".monitor_state.json"):
    """
    Continuously monitor one or more URLs.
    Sends email alert when a site goes down or its content changes.
    """
    setup_logging(log_file)

    # Load previous state (content hashes + up/down status)
    state = {}
    state_path = Path(state_file)
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text())
        except Exception:
            state = {}

    def save_state():
        state_path.write_text(json.dumps(state, indent=2))

    def alert(subject, body):
        logging.warning(f"ALERT: {subject}")
        if alert_email and from_email and smtp_password:
            send_email_alert(subject, body, alert_email, from_email,
                             smtp_host, smtp_port, smtp_password)

    logging.info(f"Monitoring {len(urls)} URL(s) every {interval}s")
    for u in urls:
        logging.info(f"  → {u}")

    while True:
        for url in urls:
            r = check_site(url, expected_text)
            prev = state.get(url, {})

            if r["up"]:
                msg = f"UP  [{r['status_code']}] {r['response_ms']}ms  {url}"

                # Detect content change
                if prev.get("content_hash") and prev["content_hash"] != r["content_hash"]:
                    logging.info(f"CHANGED  {url}")
                    alert(
                        f"Content changed: {url}",
                        f"The content of {url} has changed.\n\nPrevious hash: {prev['content_hash']}\nNew hash:      {r['content_hash']}"
                    )

                # Recovered from down
                if prev.get("up") is False:
                    alert(f"Site recovered: {url}", f"{url} is back up (HTTP {r['status_code']}).")

                logging.info(msg)

            else:
                error = r.get("error") or f"HTTP {r['status_code']}"
                logging.error(f"DOWN {url}  ({error})")

                # Only alert once per outage (not every interval)
                if prev.get("up") is not False:
                    alert(
                        f"Site DOWN: {url}",
                        f"{url} is unreachable.\nError: {error}\nTime: {datetime.now().isoformat()}"
                    )

            state[url] = {"up": r["up"], "content_hash": r["content_hash"],
                          "last_check": datetime.now().isoformat()}
            save_state()

        time.sleep(interval)


def check_once(urls, expected_text=None):
    """Check all URLs once and print a summary. Exit code 1 if any are down."""
    setup_logging()
    any_down = False
    for url in urls:
        r = check_site(url, expected_text)
        if r["up"]:
            print(f"  UP   [{r['status_code']}] {r['response_ms']}ms  {url}")
        else:
            print(f"  DOWN  {url}  ({r.get('error') or r['status_code']})")
            any_down = True
    return any_down


def main():
    parser = argparse.ArgumentParser(
        description="Monitor websites for downtime and content changes."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Single URL to monitor")
    group.add_argument("--urls", metavar="FILE",
                       help="Text file with one URL per line")

    parser.add_argument("--interval", type=int, default=300,
                        help="Check interval in seconds (default: 300)")
    parser.add_argument("--expected-text",
                        help="Text that must appear in the response body")
    parser.add_argument("--log", metavar="FILE",
                        help="Write log output to this file")
    parser.add_argument("--once", action="store_true",
                        help="Check once and exit (no continuous loop)")

    email_group = parser.add_argument_group("email alerts")
    email_group.add_argument("--alert-email", help="Send alerts to this address")
    email_group.add_argument("--from-email", help="Send alerts from this Gmail address")
    email_group.add_argument("--smtp-password",
                             help="App password for the from-email Gmail account")
    email_group.add_argument("--smtp-host", default="smtp.gmail.com")
    email_group.add_argument("--smtp-port", type=int, default=465)

    args = parser.parse_args()

    if args.url:
        urls = [args.url]
    else:
        path = Path(args.urls)
        if not path.exists():
            print(f"Error: file not found: {args.urls}")
            sys.exit(1)
        urls = []
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                urls.append(stripped)

    if not urls:
        print("Error: no URLs to monitor.")
        sys.exit(1)

    if args.once:
        any_down = check_once(urls, args.expected_text)
        sys.exit(1 if any_down else 0)

    monitor(
        urls=urls,
        interval=args.interval,
        expected_text=args.expected_text,
        log_file=args.log,
        alert_email=args.alert_email,
        from_email=args.from_email,
        smtp_host=args.smtp_host,
        smtp_port=args.smtp_port,
        smtp_password=args.smtp_password,
    )


if __name__ == "__main__":
    main()
