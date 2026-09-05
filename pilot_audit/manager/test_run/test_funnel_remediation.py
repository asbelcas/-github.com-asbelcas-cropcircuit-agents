#!/usr/bin/env python3
import csv
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[3] / "bin" / "operations_manager.py"
FIELDS = [
    "customer_id", "received_date", "due_date", "customer_name", "farm_name",
    "region", "primary_goal", "payment_status", "intake_status", "current_stage",
    "missing_info", "draft_location", "casey_approval_status", "delivery_status",
    "delivery_date", "followup_status", "notes", "test_case", "sale_id",
    "order_number", "customer_email", "payment_verified_at_utc",
    "intake_accepted_at_utc", "fulfillment_ready_at_utc", "fulfillment_deadline_at",
]


class FunnelRemediationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cc_funnel_")
        root = Path(self.tmp.name)
        manager = root / "manager"
        for sub in ("incoming", "incoming_sales", "waitlisted_sales", "cases", "approvals"):
            (manager / sub).mkdir(parents=True, exist_ok=True)
        self.tracker = root / "tracker.csv"
        with self.tracker.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()
        self.config = {
            "pilot_capacity": 5, "pilot_price_usd": 95, "delivery_business_days": 3,
            "manager_dir": str(manager), "case_tracker": str(self.tracker),
            "pause_flag": str(manager / "pause.flag"), "audit_template": str(root / "template.md"),
            "gumroad_url": "https://example.invalid", "public_url_file": str(root / "url"),
            "offer_path": "/audit", "enable_gumroad_api_verify": False,
            "enable_imap_intake": False, "enable_codex": False, "enable_kimi": False,
            "daily_budget_usd": 1, "monthly_budget_usd": 10,
        }
        config_path = manager / "config.json"
        config_path.write_text(json.dumps(self.config), encoding="utf-8")
        os.environ["OPERATIONS_MANAGER_CONFIG"] = str(config_path)
        spec = importlib.util.spec_from_file_location(f"operations_manager_test_{id(self)}", SOURCE)
        self.om = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.om)
        self.paths = self.om.manager_paths(self.config)
        self.state = self.om.load_state(self.paths)
        self.om.gumroad_remaining_capacity = lambda _config: None

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self):
        return self.om.read_case_tracker(self.tracker)

    def add_case(self, cid, paid="unverified", intake="incomplete", stage="new", test=False, **extra):
        row = {k: "" for k in FIELDS}
        row.update({"customer_id": cid, "received_date": "2025-01-01", "payment_status": paid,
                    "intake_status": intake, "current_stage": stage,
                    "test_case": "true" if test else "false"})
        row.update(extra)
        rows = self.rows() + [row]
        self.om.write_case_tracker(self.tracker, rows)

    def sale(self, number, test=False):
        sale_id = f"{'TEST-' if test else ''}SALE-{number}"
        event = {"sale_id": sale_id, "order_number": f"ORDER-{number}",
                 "email": f"buyer{number}@{'example.com' if test else 'mail.test'}",
                 "full_name": "Fixture", "country": "US"}
        (self.paths["incoming_sales"] / f"{sale_id}.json").write_text(json.dumps(event), encoding="utf-8")
        return sale_id

    def test_deadline_requires_both_timestamps_and_does_not_drift(self):
        self.add_case("C1", paid="paid", intake="incomplete", payment_verified_at_utc="2026-08-14T14:00:00Z")
        self.add_case("C2", paid="unverified", intake="complete", intake_accepted_at_utc="2026-08-15T15:00:00Z")
        self.om.process_deadlines(self.config, self.paths, self.state)
        self.assertEqual("", self.rows()[0]["due_date"])
        self.assertEqual("", self.rows()[1]["due_date"])

        self.add_case("C3", paid="paid", intake="complete",
                      payment_verified_at_utc="2026-08-14T14:00:00Z",
                      intake_accepted_at_utc="2026-08-15T15:00:00Z")
        self.om.process_deadlines(self.config, self.paths, self.state)
        ready = next(r for r in self.rows() if r["customer_id"] == "C3")
        self.assertEqual("2026-08-15T15:00:00Z", ready["fulfillment_ready_at_utc"])
        self.assertEqual("2026-08-19", ready["due_date"])
        snapshot = (ready["fulfillment_ready_at_utc"], ready["due_date"], ready["fulfillment_deadline_at"])
        self.om.process_deadlines(self.config, self.paths, self.state)
        ready = next(r for r in self.rows() if r["customer_id"] == "C3")
        self.assertEqual(snapshot, (ready["fulfillment_ready_at_utc"], ready["due_date"], ready["fulfillment_deadline_at"]))

    def test_tracker_schema_extends_without_losing_later_row_fields(self):
        rows = [{"customer_id": "old"}, {"customer_id": "new", "fulfillment_ready_at_utc": "stamp"}]
        self.om.write_case_tracker(self.tracker, rows)
        self.assertEqual("stamp", self.rows()[1]["fulfillment_ready_at_utc"])

    def test_intake_validation_states_and_test_isolation(self):
        self.assertEqual("incomplete", self.om.assess_intake_text(""))
        self.assertEqual("pending_review", self.om.assess_intake_text("Region: Michigan. Acres: five. Goal: improve chores."))
        valid = ("Region Michigan, 5 acres; animals sheep; layout pasture map; facilities barn and equipment; "
                 "chore workflow and labor; bottleneck problem; safety and welfare seasonal concerns; "
                 "budget low-cost; desired outcome and decision goal.")
        self.assertEqual("complete", self.om.assess_intake_text(valid))
        self.add_case("TEST-9", test=True)
        (self.paths["incoming"] / "TEST-9_intake.md").write_text(valid, encoding="utf-8")
        self.om.check_incoming(self.config, self.paths, self.state)
        row = self.rows()[0]
        self.assertEqual("complete", row["intake_status"])
        self.assertTrue(row["intake_accepted_at_utc"])
        self.assertFalse(self.paths["approvals"].exists())
        self.assertTrue(self.paths["diagnostic_approvals"].exists())
        self.assertFalse(self.paths["tasks"].exists())

    def test_sixth_verified_signal_is_idempotent_capacity_hold(self):
        for i in range(1, 6):
            self.add_case(f"C{i}", paid="paid", stage="new")
        self.om.recalculate_capacity(self.config, self.paths, self.state)
        sale_id = self.sale(6)
        self.om.check_incoming_sales(self.config, self.paths, self.state)
        held = next(r for r in self.rows() if r["sale_id"] == sale_id)
        self.assertEqual("capacity_hold", held["current_stage"])
        self.assertEqual("unverified", held["payment_status"])

        self.om.verify_payment_via_gumroad_api = lambda *a, **k: {"verified": True, "sale": {}}
        self.config["enable_gumroad_api_verify"] = True
        self.om.check_gumroad_api_verification(self.config, self.paths, self.state)
        held = next(r for r in self.rows() if r["sale_id"] == sale_id)
        self.assertEqual("paid", held["payment_status"])
        self.assertEqual("capacity_hold", held["current_stage"])
        self.assertEqual("", held["due_date"])
        self.om.recalculate_capacity(self.config, self.paths, self.state)
        self.assertEqual(5, self.om.load_state(self.paths)["active_cases"])
        before = len(self.rows())
        self.om.check_incoming_sales(self.config, self.paths, self.state)
        self.assertEqual(before, len(self.rows()))
        approvals = self.paths["approvals"].read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, sum("capacity-hold:" in line for line in approvals))

        self.om.update_case_state(self.config, self.paths, "C1", {"delivery_status": "delivered"})
        self.om.recalculate_capacity(self.config, self.paths, self.state)
        held = next(r for r in self.rows() if r["sale_id"] == sale_id)
        self.assertEqual("capacity_hold", held["current_stage"])
        self.assertEqual("", held["due_date"])

    def test_synthetic_approvals_and_digest_are_production_clean(self):
        self.sale(99, test=True)
        events = self.om.check_incoming_sales(self.config, self.paths, self.state)
        self.assertTrue(events[0]["test_case"])
        self.assertFalse(self.paths["approvals"].exists())
        diagnostics = self.paths["diagnostic_approvals"].read_text(encoding="utf-8")
        self.assertIn('"test_case": true', diagnostics)
        test_row = self.rows()[0]
        legacy = {"approval_id": "legacy-test", "type": "payment_verification_required",
                  "description": f"Verify {test_row['customer_id']}", "status": "pending"}
        self.paths["approvals"].write_text(json.dumps(legacy) + "\n", encoding="utf-8")
        self.assertEqual(1, self.om.separate_test_approvals(self.paths, self.rows()))
        self.assertEqual("", self.paths["approvals"].read_text(encoding="utf-8"))
        self.assertIn("legacy-test", self.paths["diagnostic_approvals"].read_text(encoding="utf-8"))
        self.om.process_deadlines(self.config, self.paths, self.state)
        self.om.recalculate_capacity(self.config, self.paths, self.state)
        state = self.om.load_state(self.paths)
        self.assertEqual((0, 0, 5), (state["active_cases"], state["completed_cases"], state["slots_remaining"]))

    def test_email_intake_failure_is_surfaced_as_event(self):
        self.config["enable_imap_intake"] = True

        def _broken_login(_config):
            raise RuntimeError("[AUTHENTICATIONFAILED] Invalid credentials")

        original = self.om._imap_login
        self.om._imap_login = _broken_login
        try:
            events = self.om.check_email_intake(self.config, self.paths, self.state)
        finally:
            self.om._imap_login = original
        failures = [e for e in events if e.get("type") == "intake_channel_failed"]
        self.assertEqual(1, len(failures))
        self.assertIn("RuntimeError", failures[0]["error"])

    def test_intake_channel_failure_privacy_safe_notification(self):
        safe = self.om._privacy_safe_notification_text([
            "- Intake channel failure: email intake unreachable (RuntimeError); customer replies may be missed"
        ])
        self.assertIn("Email intake channel failure", safe)
        self.assertNotIn("AUTHENTICATIONFAILED", safe)

    def test_imap_auth_failures_pause_login_after_ten(self):
        self.config["enable_imap_intake"] = True
        calls = {"login": 0}

        def _broken_login(_config):
            calls["login"] += 1
            raise RuntimeError("[AUTHENTICATIONFAILED] Invalid credentials")

        original = self.om._imap_login
        self.om._imap_login = _broken_login
        try:
            for _ in range(10):
                self.om.check_email_intake(self.config, self.paths, self.state)
            self.assertEqual(10, calls["login"])
            self.assertIn("imap_failure_pause_until_utc", self.state)
            events = self.om.check_email_intake(self.config, self.paths, self.state)
        finally:
            self.om._imap_login = original
        self.assertEqual(10, calls["login"])
        failures = [e for e in events if e.get("type") == "intake_channel_failed"]
        self.assertEqual(1, len(failures))
        self.assertEqual("paused", failures[0]["error"])
        self.assertIn(self.state["imap_failure_pause_until_utc"], failures[0]["message"])

    def test_imap_non_auth_error_does_not_count_toward_pause(self):
        self.config["enable_imap_intake"] = True

        def _broken_login(_config):
            raise RuntimeError("temporary network unreachable")

        original = self.om._imap_login
        self.om._imap_login = _broken_login
        try:
            for _ in range(12):
                self.om.check_email_intake(self.config, self.paths, self.state)
        finally:
            self.om._imap_login = original
        self.assertNotIn("imap_consecutive_auth_failures", self.state)
        self.assertNotIn("imap_failure_pause_until_utc", self.state)


if __name__ == "__main__":
    unittest.main()
