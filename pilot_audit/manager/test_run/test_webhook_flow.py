#!/usr/bin/env python3
"""Test the Gumroad webhook route using a Flask test client and temp directories."""
import json
import os
import sys
import tempfile
from pathlib import Path

# Configure the webhook secret and incoming-sales queue before importing app.
TEMP_DIR = Path(tempfile.mkdtemp(prefix="funnel_webhook_"))
INCOMING_SALES_DIR = TEMP_DIR / "incoming_sales"
INCOMING_SALES_DIR.mkdir(parents=True, exist_ok=True)
os.environ["GUMROAD_WEBHOOK_SECRET_PATH"] = "test-secret-funnel"
os.environ["INCOMING_SALES_DIR"] = str(INCOMING_SALES_DIR)

# Import from the website package
sys.path.insert(0, "/home/asbelcas/cropcircuit-site")
import app as cropcircuit_app  # noqa: E402


def post_webhook(payload: dict) -> dict:
    with cropcircuit_app.app.test_client() as client:
        resp = client.post("/webhooks/gumroad/test-secret-funnel/sale", data=payload)
        return {"status_code": resp.status_code, "data": resp.get_json(silent=True) or {}}


def main() -> int:
    failures = 0

    base_payload = {
        "permalink": "zgdlec",
        "price": "9500",
        "currency": "usd",
        "sale_id": "TEST-FUNNEL-001",
        "order_number": "TEST-ORDER-FUNNEL-001",
        "email": "funnel-test@example.com",
        "full_name": "Funnel Test",
        "product_name": "Small Farm Systems Audit",
    }

    # 1. Correct payload accepted and event file written
    resp = post_webhook(base_payload)
    event_files = list(INCOMING_SALES_DIR.glob("sale_*.json"))
    ok = resp["status_code"] == 200 and resp["data"].get("status") == "recorded" and len(event_files) == 1
    print(f"{'PASS' if ok else 'FAIL'} webhook accepts correct product/price/currency and writes event file")
    if not ok:
        print(f"  response: {resp}, files: {event_files}")
        failures += 1
    file_path = event_files[0] if event_files else None

    # 2. Duplicate sale_id does not create a second file
    resp2 = post_webhook(base_payload)
    matching_files = list(INCOMING_SALES_DIR.glob("sale_*.json"))
    ok = resp2["status_code"] == 200 and resp2["data"].get("status") == "duplicate" and len(matching_files) == 1
    print(f"{'PASS' if ok else 'FAIL'} duplicate sale_id returns duplicate without creating another file")
    if not ok:
        print(f"  response: {resp2}, files: {matching_files}")
        failures += 1

    # 3. Wrong permalink rejected
    bad_permalink = {**base_payload, "permalink": "wrong", "sale_id": "TEST-FUNNEL-002"}
    resp3 = post_webhook(bad_permalink)
    ok = resp3["status_code"] == 400 and "permalink mismatch" in resp3["data"].get("errors", [])
    print(f"{'PASS' if ok else 'FAIL'} wrong permalink rejected with 400")
    if not ok:
        print(f"  response: {resp3}")
        failures += 1

    # 4. Wrong price rejected
    bad_price = {**base_payload, "price": "100", "sale_id": "TEST-FUNNEL-003"}
    resp4 = post_webhook(bad_price)
    ok = resp4["status_code"] == 400 and "price mismatch" in resp4["data"].get("errors", [])
    print(f"{'PASS' if ok else 'FAIL'} wrong price rejected with 400")
    if not ok:
        print(f"  response: {resp4}")
        failures += 1

    # 5. Event file contains expected fields and no raw customer identifiers
    if file_path and file_path.exists():
        raw = file_path.read_text(encoding="utf-8")
        event = json.loads(raw)
        ok = (
            event.get("source") == "gumroad_webhook"
            and event.get("price_cents") == 9500
            and event.get("currency") == "usd"
            and event.get("permalink") == "zgdlec"
            and bool(event.get("email_pseudonym"))
            and "TEST-FUNNEL-001" not in raw
            and "funnel-test@example.com" not in raw
            and "sale_id" not in event
            and "email" not in event
        )
        print(f"{'PASS' if ok else 'FAIL'} event file pseudonymized with correct sale fields")
        if not ok:
            print(f"  event: {event}")
            failures += 1

    # Cleanup
    for f in sorted(TEMP_DIR.rglob("*"), reverse=True):
        if f.is_file():
            f.unlink()
        elif f.is_dir():
            f.rmdir()
    TEMP_DIR.rmdir()

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
