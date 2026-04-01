#!/usr/bin/env python3
"""
post_to_x.py — Minimal standalone X poster. OAuth 1.0a only.

Usage:
    source .env.x
    python3 bin/post_to_x.py "Your tweet text here"

Env vars required:
    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
"""

import os
import sys
import json
import requests
from requests_oauthlib import OAuth1

def post(text):
    auth = OAuth1(
        os.environ["X_API_KEY"],
        os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"],
        os.environ["X_ACCESS_TOKEN_SECRET"],
    )

    resp = requests.post(
        "https://api.x.com/2/tweets",
        json={"text": text},
        auth=auth,
        timeout=30,
    )

    print(f"HTTP {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))
    return resp.status_code == 201

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 post_to_x.py \"tweet text\"")
        sys.exit(1)
    ok = post(sys.argv[1])
    sys.exit(0 if ok else 1)
