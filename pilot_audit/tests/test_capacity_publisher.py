#!/usr/bin/env python3
"""Integration tests for the Operations Manager capacity-state publisher."""

import json
import os
import stat
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, "/home/asbelcas/cropcircuit/bin")
os.environ.setdefault("OPERATIONS_MANAGER_CONFIG", "")

import operations_manager as om


class CapacityPublisherTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="ops_capacity_test_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tempdir, ignore_errors=True))
        self.snapshot = self.tempdir / "audit_capacity_state.json"
        self.config = {
            "manager_dir": str(self.tempdir / "manager"),
            "pilot_capacity": 5,
            "capacity_snapshot_path": str(self.snapshot),
        }
        self.paths = om.manager_paths(self.config)
        for p in self.paths.values():
            if p.suffix == "":
                p.mkdir(parents=True, exist_ok=True)

    def _read_snapshot(self):
        with self.snapshot.open("r", encoding="utf-8") as f:
            return json.load(f)

    def test_publishes_zero_active_audits(self):
        state = {"active_cases": 0}
        self.assertTrue(om.publish_capacity_snapshot(self.config, self.paths, state))
        data = self._read_snapshot()
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["source"], "cropcircuit_operations_manager")
        self.assertEqual(data["counting_rule"], "paid_production_nonterminal_v1")
        self.assertEqual(data["capacity"], 5)
        self.assertEqual(data["active_paid_audits"], 0)
        self.assertIn("generated_at_utc", data)
        self.assertEqual(stat.S_IMODE(self.snapshot.stat().st_mode), 0o600)

    def test_publishes_four_active_audits(self):
        state = {"active_cases": 4}
        self.assertTrue(om.publish_capacity_snapshot(self.config, self.paths, state))
        self.assertEqual(self._read_snapshot()["active_paid_audits"], 4)

    def test_publishes_five_active_audits(self):
        state = {"active_cases": 5}
        self.assertTrue(om.publish_capacity_snapshot(self.config, self.paths, state))
        self.assertEqual(self._read_snapshot()["active_paid_audits"], 5)

    def test_atomic_write_never_leaves_partial_file(self):
        state = {"active_cases": 3}
        self.assertTrue(om.publish_capacity_snapshot(self.config, self.paths, state))
        # No .tmp file should remain.
        self.assertFalse(self.snapshot.with_suffix(".tmp").exists())

    def test_rejects_negative_active_count(self):
        state = {"active_cases": -1}
        self.assertFalse(om.publish_capacity_snapshot(self.config, self.paths, state))
        self.assertFalse(self.snapshot.exists())

    def test_rejects_non_five_capacity(self):
        self.config["pilot_capacity"] = 6
        state = {"active_cases": 1}
        self.assertFalse(om.publish_capacity_snapshot(self.config, self.paths, state))
        self.assertFalse(self.snapshot.exists())

    def test_unconfigured_path_never_touches_production_file(self):
        """Regression: without an explicit capacity_snapshot_path, the publisher
        must write only to a scratch location, never the live website file."""
        production = Path("/home/asbelcas/cropcircuit-site/data/audit_capacity_state.json")
        before = production.read_bytes() if production.exists() else None
        config = {
            "manager_dir": str(self.tempdir / "manager2"),
            "pilot_capacity": 5,
        }
        paths = om.manager_paths(config)
        paths["root"].mkdir(parents=True, exist_ok=True)
        self.assertTrue(om.publish_capacity_snapshot(config, paths, {"active_cases": 5}))
        scratch = paths["root"] / "state" / "audit_capacity_state.json"
        self.assertTrue(scratch.exists())
        self.assertEqual(self._read(scratch)["active_paid_audits"], 5)
        after = production.read_bytes() if production.exists() else None
        self.assertEqual(before, after)

    def _read(self, path):
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)


class WebsiteCapacityFailClosedTestCase(unittest.TestCase):
    """Mirror the website's fail-closed validation against publisher output."""

    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="web_capacity_test_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tempdir, ignore_errors=True))
        self.snapshot = self.tempdir / "capacity.json"

    def _write(self, **overrides):
        payload = {
            "schema_version": 1,
            "source": "cropcircuit_operations_manager",
            "counting_rule": "paid_production_nonterminal_v1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "capacity": 5,
            "active_paid_audits": 0,
        }
        payload.update(overrides)
        self.snapshot.write_text(json.dumps(payload), encoding="utf-8")

    def _status(self):
        sys.path.insert(0, "/home/asbelcas/worktrees/clean-candidate-20260830")
        try:
            from app import app, audit_capacity_status
            app.config["AUDIT_CAPACITY_STATE_PATH"] = str(self.snapshot)
            app.config["AUDIT_CAPACITY_MAX_AGE_SECONDS"] = "1800"
            return audit_capacity_status()
        finally:
            sys.path.remove("/home/asbelcas/worktrees/clean-candidate-20260830")

    def test_valid_zero_active_opens_checkout(self):
        self._write(active_paid_audits=0)
        self.assertTrue(self._status()["available"])

    def test_valid_four_active_opens_checkout(self):
        self._write(active_paid_audits=4)
        self.assertTrue(self._status()["available"])

    def test_five_active_closes_checkout(self):
        self._write(active_paid_audits=5)
        self.assertFalse(self._status()["available"])

    def test_stale_snapshot_fails_closed(self):
        stale = datetime.now(timezone.utc) - timedelta(seconds=1801)
        self._write(generated_at_utc=stale.isoformat().replace("+00:00", "Z"))
        self.assertFalse(self._status()["available"])

    def test_future_dated_snapshot_fails_closed(self):
        future = datetime.now(timezone.utc) + timedelta(minutes=5)
        self._write(generated_at_utc=future.isoformat().replace("+00:00", "Z"))
        self.assertFalse(self._status()["available"])

    def test_malformed_json_fails_closed(self):
        self.snapshot.write_text("not-json", encoding="utf-8")
        self.assertFalse(self._status()["available"])

    def test_missing_file_fails_closed(self):
        self.assertFalse(self._status()["available"])

    def test_wrong_counting_rule_fails_closed(self):
        self._write(counting_rule="paid_everything_v1")
        self.assertFalse(self._status()["available"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
