#!/usr/bin/env python3
"""Preflight IMAP resolver/connectivity gate for outbound email flows."""

from __future__ import annotations

import argparse
import imaplib
import json
import os
import socket
import time
from typing import Any

from pull_targets_imap import imap_connect, resolve_host_ipv4

BACKOFF_SECONDS = [2, 5, 12]


def _resolve_all(host: str, port: int) -> list[str]:
    out = []
    infos = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        ip = str(sockaddr[0]).strip()
        if ip and ip not in out:
            out.append(ip)
    return out


def run_preflight(verbose: bool = False, retries: int = 3) -> tuple[bool, dict[str, Any]]:
    host = os.environ.get("IMAP_HOST", "imap.gmail.com").strip()
    port = int(os.environ.get("IMAP_PORT", "993"))
    user = os.environ.get("IMAP_USER", "asbelcas@gmail.com").strip()
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

    attempts = 0
    last_error = ""
    resolved: list[str] = []

    max_attempts = max(1, retries + 1)
    for idx in range(max_attempts):
        attempts = idx + 1
        try:
            # Resolve via system DNS first, then DoH helper fallback used by IMAP client.
            try:
                resolved = _resolve_all(host, port)
            except socket.gaierror:
                resolved = resolve_host_ipv4(host)
            if not resolved:
                raise RuntimeError("no_dns_records")

            conn = imap_connect(host, port)
            try:
                if not app_password:
                    raise RuntimeError("missing_gmail_app_password")
                typ, _ = conn.login(user, app_password)
                if typ != "OK":
                    raise RuntimeError("imap_login_failed")
                conn.select("INBOX", readonly=True)
                conn.noop()
            finally:
                try:
                    conn.logout()
                except Exception:
                    pass

            detail = {
                "ok": True,
                "attempts": attempts,
                "imap_host": host,
                "imap_port": port,
                "imap_user": user,
                "resolved": resolved,
            }
            if verbose:
                print(f"resolver host={host} port={port} resolved={resolved}")
                print(f"imap_check host={host} port={port} user={user} attempts={attempts}")
            return True, detail
        except (socket.gaierror, OSError, imaplib.IMAP4.error, RuntimeError) as exc:
            last_error = str(exc)
            if verbose:
                print(f"attempt={attempts} error={last_error}")
            if idx < len(BACKOFF_SECONDS) and idx < max_attempts - 1:
                time.sleep(BACKOFF_SECONDS[idx])
            continue

    detail = {
        "ok": False,
        "attempts": attempts,
        "imap_host": host,
        "imap_port": port,
        "imap_user": user,
        "resolved": resolved,
        "error": last_error or "preflight_failed",
    }
    if verbose:
        print(f"resolver host={host} port={port} resolved={resolved}")
        print(f"imap_check_failed host={host} port={port} user={user} attempts={attempts} error={detail['error']}")
    return False, detail


def main() -> int:
    ap = argparse.ArgumentParser(description="IMAP preflight for outbound send gates")
    ap.add_argument("--verbose", action="store_true", help="Print resolver and IMAP details before summary JSON")
    args = ap.parse_args()

    ok, detail = run_preflight(verbose=args.verbose, retries=3)
    print(json.dumps(detail, ensure_ascii=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
