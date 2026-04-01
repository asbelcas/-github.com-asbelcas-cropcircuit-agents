#!/usr/bin/env python3
"""
ha_config.py — Pull centralized config values from Home Assistant.

Usage:
    from ha_config import get_website_url, get_ha_entity

Never hardcode cropcircuit.com — always pull from HA.
"""

import os
import requests

HA_URL = os.environ.get("HA_URL", "http://localhost:8123").rstrip("/")
HA_TOKEN = os.environ.get("HA_TOKEN", "")

FALLBACK_WEBSITE = "https://cropcircuit.com"


def get_ha_entity(entity_id: str, fallback: str = "") -> str:
    """Fetch an entity state from HA. Returns fallback on any error."""
    if not HA_TOKEN:
        return fallback
    try:
        resp = requests.get(
            f"{HA_URL}/api/states/{entity_id}",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            timeout=5,
        )
        if resp.ok:
            state = resp.json().get("state", "")
            if state and state not in ("unknown", "unavailable"):
                return state
    except Exception:
        pass
    return fallback


def get_website_url() -> str:
    """Get the canonical CropCircuit website URL from HA."""
    return get_ha_entity("input_text.cropcircuit_website_url", FALLBACK_WEBSITE)
