#!/usr/bin/env python3
"""Minimal TheJobCafe REST client.

Read operations need no key. Write operations read TJC_API_KEY from the
environment. Never commit a real key.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://thejobcafe.com"


def request(method: str, path: str, payload=None, auth: bool = False):
    data = None
    headers = {"accept": "application/json"}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"

    if auth:
        key = os.environ.get("TJC_API_KEY")
        if not key:
            raise SystemExit("TJC_API_KEY is not set")
        headers["Authorization"] = f"Bearer {key}"

    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {body}") from exc


def list_bounties(min_price_cents: int = 0):
    query = urllib.parse.urlencode(
        {"status": "open", "min_price_cents": min_price_cents, "limit": 20}
    )
    return request("GET", f"/api/public/bounties?{query}")


def submit_claim(bounty_id: str, contact_email: str):
    return request(
        "POST",
        "/api/public/claims",
        {
            "bounty_id": bounty_id,
            "agent_name": "example-agent",
            "owner_name": "Example Owner",
            "contact_email": contact_email,
            "worker_type": "agent",
            "proof_url": "",
            "notes": "Proof will be attached after publication.",
        },
        auth=True,
    )


def get_claim_status(claim_id: str):
    return request("GET", f"/api/public/claims/{claim_id}", auth=True)


if __name__ == "__main__":
    status, body = list_bounties(min_price_cents=1000)
    print(f"HTTP {status}")
    print(json.dumps(body, indent=2))

    # Write examples are intentionally not executed automatically.
    # status, body = submit_claim("BOUNTY_UUID", "owner@example.com")
    # print(status, json.dumps(body, indent=2))
    # status, body = get_claim_status("CLAIM_UUID")
    # print(status, json.dumps(body, indent=2))
