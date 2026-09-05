#!/usr/bin/env python3
"""Test Operations Manager state machine for the Small Farm Systems Audit pilot."""
import csv
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/home/asbelcas/cropcircuit/bin")


def make_temp_manager() -> tuple:
    """Return (temp_root, config_path). Does not depend on operations_manager."""
    temp_root = Path(tempfile.mkdtemp(prefix="funnel_manager_"))
    manager_dir = temp_root / "manager"
    manager_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("incoming", "incoming_sales", "processed_sales", "waitlisted_sales", "cases", "approvals"):
        (manager_dir / sub).mkdir(parents=True, exist_ok=True)

    tracker_path = temp_root / "03_CASE_TRACKER.csv"
    header = [
        "customer_id", "received_date", "due_date", "customer_name", "farm_name",
        "region", "primary_goal", "payment_status", "intake_status", "current_stage",
        "missing_info", "draft_location", "casey_approval_status", "delivery_status",
        "delivery_date", "followup_status", "notes", "test_case", "sale_id",
        "order_number", "customer_email",
    ]
    with tracker_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

    state_path = manager_dir / "state.json"
    state_path.write_text(json.dumps({
        "active_cases": 0,
        "completed_cases": 0,
        "revenue_usd": 0,
        "slots_remaining": 5,
        "last_check_utc": None,
        "last_digest_utc": None,
        "changes_since_digest": False,
        "daily_cost_usd": 0.0,
        "daily_cost_reset_utc": datetime.utcnow().isoformat() + "Z",
        "monthly_cost_usd": 0.0,
        "monthly_cost_reset_utc": datetime.utcnow().isoformat() + "Z",
        "pending_codex_jobs": [],
        "capacity_pause_notified": False,
        "gumroad_verification_last_check": {},
        "processed_email_message_ids": [],
    }), encoding="utf-8")

    config = {
        "pilot_capacity": 5,
        "pilot_price_usd": 95,
        "delivery_business_days": 3,
        "manager_dir": str(manager_dir),
        "case_tracker": str(tracker_path),
        "intake_template": "/home/asbelcas/cropcircuit/pilot_audit/01_INTAKE_FORM.md",
        "audit_template": "/home/asbelcas/cropcircuit/pilot_audit/02_AUDIT_TEMPLATE.md",
        "gumroad_url": "https://asbelcas.gumroad.com/l/zgdlec",
        "public_url_file": "/home/asbelcas/cropcircuit/runtime/donor_public_url.txt",
        "offer_path": "/small-farm-systems-audit",
        "max_retries": 2,
        "daily_budget_usd": 1.0,
        "monthly_budget_usd": 10.0,
        "pause_flag": str(manager_dir / "pause.flag"),
        "agent_name": "cropcircuit-operations-manager-test",
        "bridge_workspace": str(temp_root),
        "capacity_snapshot_path": str(manager_dir / "audit_capacity_state.json"),
        "enable_kimi": False,
        "enable_codex": False,
        "enable_gumroad_api_verify": False,
        "enable_imap_intake": False,
        "gumroad_product_id": "1UsXOZ9CAl3Zb0jd9IHbTw",
        "gumroad_expected_price_cents": 9500,
        "gumroad_env_file": "/nonexistent/.env",
        "imap_env_file": "/nonexistent/.env",
        "imap_mailbox": "test@example.com",
        "imap_server": "imap.gmail.com",
        "notification_method": "daily_digest_file",
        "ha_env_file": "/nonexistent/.env",
    }
    config_path = manager_dir / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    return temp_root, config_path


def main() -> int:
    temp_root, config_path = make_temp_manager()
    # operations_manager reads CONFIG_PATH at import time; set the env var first.
    os.environ["OPERATIONS_MANAGER_CONFIG"] = str(config_path)
    import operations_manager as om  # noqa: E402

    failures = 0

    def load_tracker_rows():
        return om.read_case_tracker(Path(config["case_tracker"]))

    def load_state():
        return om.load_state(paths)

    def write_event(sale_id, email, order_number, test=False):
        event = {
            "source": "gumroad_webhook",
            "received_at_utc": datetime.utcnow().isoformat() + "Z",
            "sale_id": sale_id,
            "order_number": order_number,
            "email": email,
            "permalink": "zgdlec",
            "price_cents": 9500,
            "currency": "usd",
            "product_name": "Small Farm Systems Audit",
            "full_name": "Test Customer" if test else "Pilot Customer",
            "country": "US",
            "raw_payload": {},
        }
        if test:
            event["sale_id"] = f"TEST-{sale_id}"
            event["order_number"] = f"TEST-{order_number}"
            event["email"] = f"test-{email}@example.com"
        path = paths["incoming_sales"] / f"sale_{event['sale_id']}.json"
        path.write_text(json.dumps(event), encoding="utf-8")
        return event

    config = om.load_config()
    paths = om.manager_paths(config)
    state = om.load_state(paths)

    # 1. Capacity starts at 5
    om.recalculate_capacity(config, paths, state)
    state = load_state()
    ok = state["slots_remaining"] == 5 and state["active_cases"] == 0 and state["revenue_usd"] == 0
    print(f"{'PASS' if ok else 'FAIL'} capacity starts at 5 with no production cases")
    if not ok:
        print(f"  state: {state}")
        failures += 1

    # 2. Production sale signal creates an unverified case; capacity unchanged
    write_event("PROD-001", "prod001", "ORDER-001", test=False)
    om.check_incoming_sales(config, paths, state)
    rows = load_tracker_rows()
    prod_rows = [r for r in rows if not om.is_test_case(r)]
    state = load_state()
    ok = (
        len(prod_rows) == 1
        and prod_rows[0]["payment_status"] == "unverified"
        and prod_rows[0]["test_case"] == "false"
        and state["slots_remaining"] == 5
    )
    print(f"{'PASS' if ok else 'FAIL'} production sale signal creates unverified case, capacity stays 5")
    if not ok:
        print(f"  rows: {rows}\n  state: {state}")
        failures += 1

    # 3. Fictional sale_id cannot be verified against Gumroad; status stays unverified
    config["enable_gumroad_api_verify"] = True
    fictional_sale_id = "NO-SUCH-SALE-123"
    write_event(fictional_sale_id, "synthetic.buyer", "ORDER-SYN", test=False)
    om.check_incoming_sales(config, paths, state)
    rows = load_tracker_rows()
    fic_row = next(r for r in rows if r.get("sale_id") == fictional_sale_id)

    def mock_api_get(config, endpoint, params=None):
        return {"sales": []}

    original_get = om._gumroad_api_get
    om._gumroad_api_get = mock_api_get
    try:
        result = om.verify_payment_via_gumroad_api(config, "synthetic.buyer@mailinator.com", fictional_sale_id, "ORDER-SYN")
        ok = not result.get("verified") and result.get("reason") == "no_matching_sale"
        print(f"{'PASS' if ok else 'FAIL'} fictional sale_id cannot be verified; status stays unverified")
        if not ok:
            print(f"  result: {result}")
            failures += 1
    finally:
        om._gumroad_api_get = original_get

    # Remove the synthetic fictional row so it does not interfere with capacity tests.
    rows = load_tracker_rows()
    rows = [r for r in rows if r.get("sale_id") != fictional_sale_id]
    om.write_case_tracker(Path(config["case_tracker"]), rows)

    # 4. Test fixture sale signal creates a test case, excluded from capacity
    write_event("FIXTURE-001", "fixture001", "ORDER-F-001", test=True)
    om.check_incoming_sales(config, paths, state)
    rows = load_tracker_rows()
    test_rows = [r for r in rows if om.is_test_case(r)]
    prod_rows = [r for r in rows if not om.is_test_case(r)]
    state = load_state()
    ok = (
        len(test_rows) == 1
        and test_rows[0]["test_case"] == "true"
        and state["slots_remaining"] == 5
        and state["active_cases"] == 0
        and state["revenue_usd"] == 0
    )
    print(f"{'PASS' if ok else 'FAIL'} test fixture excluded from capacity, revenue, and counts")
    if not ok:
        print(f"  rows: {rows}\n  state: {state}")
        failures += 1

    # 5. Mark 5 production cases paid; capacity decreases by 1 each time
    for i in range(2, 6):
        write_event(f"PROD-{i:03d}", f"prod{i:03d}", f"ORDER-{i:03d}", test=False)
        om.check_incoming_sales(config, paths, state)
    rows = load_tracker_rows()
    prod_rows = [r for r in rows if not om.is_test_case(r)]
    for row in prod_rows:
        row["payment_status"] = "paid"
        om.update_case_state(config, paths, row["customer_id"], {"payment_status": "paid"})
    om.recalculate_capacity(config, paths, state)
    state = load_state()
    ok = state["slots_remaining"] == 0 and state["active_cases"] == 5 and state["revenue_usd"] == 475
    print(f"{'PASS' if ok else 'FAIL'} capacity decreases by 1 per verified production order, reaching 0")
    if not ok:
        print(f"  state: {state}")
        failures += 1

    # 6. 6th production sale signal is preserved as an explicit capacity hold
    write_event("PROD-006", "prod006", "ORDER-006", test=False)
    om.check_incoming_sales(config, paths, state)
    rows = load_tracker_rows()
    prod_rows = [r for r in rows if not om.is_test_case(r)]
    held = next((r for r in prod_rows if r.get("sale_id") == "PROD-006"), None)
    state = load_state()
    ok = (
        len(prod_rows) == 6
        and held is not None
        and held.get("current_stage") == "capacity_hold"
        and held.get("due_date") == ""
        and state["slots_remaining"] == 0
        and state["active_cases"] == 5
    )
    print(f"{'PASS' if ok else 'FAIL'} 6th production signal preserved on capacity hold outside fulfillment")
    if not ok:
        print(f"  prod_rows: {len(prod_rows)}, held: {held}, state: {state}")
        failures += 1

    # 7. Deadline is calculated from verified payment + complete intake, not received_date
    prod_cid = prod_rows[0]["customer_id"]
    om.update_case_state(config, paths, prod_cid, {"received_date": "2026-01-01", "payment_status": "paid"})
    case_dir = paths["cases"] / prod_cid
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "intake_email_initial.md").write_text("# Intake\n\nProperty: 5 acres\n", encoding="utf-8")
    om.update_case_state(config, paths, prod_cid, {"intake_status": "complete"})
    om.process_deadlines(config, paths, state)
    rows = load_tracker_rows()
    row = next(r for r in rows if r["customer_id"] == prod_cid)
    today = datetime.utcnow().date()
    expected_due = om.add_business_days(today.isoformat(), 3)
    ok = row.get("due_date") == expected_due and row.get("due_date") != "2026-01-06"
    print(f"{'PASS' if ok else 'FAIL'} deadline calculated from verified payment + complete intake (today), not received_date")
    if not ok:
        print(f"  due_date: {row.get('due_date')}, expected: {expected_due}, received_date: {row.get('received_date')}")
        failures += 1

    # Cleanup
    shutil.rmtree(temp_root)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
