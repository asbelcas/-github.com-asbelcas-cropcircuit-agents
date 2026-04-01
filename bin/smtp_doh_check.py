#!/usr/bin/env python3
"""Quick DoH check for SMTP host resolution without relying on local DNS."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from send_grant_email import doh_resolve_a  # noqa: E402


def main():
    host = "smtp.gmail.com"
    ips = doh_resolve_a(host)
    if not ips:
        print(f"DOH FAIL: no A records for {host}")
        raise SystemExit(1)
    print(f"DOH OK: {host} -> {', '.join(ips)}")


if __name__ == "__main__":
    main()
