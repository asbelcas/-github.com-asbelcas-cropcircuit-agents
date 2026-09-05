#!/usr/bin/env python3
"""FLORAL CIPHER v2 certificate guard tests.

Verifies the Claim[X] ≰ Cert[X] boundary for the capacity snapshot:
- the manager publisher stamps provenance and self-attests against the audit log
- hand-forged Claim-style writes (no provenance, wrong certifier, unattested
  timestamp) are all rejected by cert_guard.verify
- the production capacity file and audit log are byte-identical after the
  whole test module (regression: tests never touch live state)
"""
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_DIR))
sys.path.insert(0, "/home/asbelcas/cropcircuit/bin")

from test_manager_state_machine import make_temp_manager  # noqa: E402

PRODUCTION_SNAPSHOT = Path("/home/asbelcas/cropcircuit-site/data/audit_capacity_state.json")
PRODUCTION_AUDIT = Path("/home/asbelcas/cropcircuit/pilot_audit/manager/audit.log")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"


_PROD_BEFORE = {}


def setup_module():
    _PROD_BEFORE["snapshot"] = _sha(PRODUCTION_SNAPSHOT)
    _PROD_BEFORE["audit"] = _sha(PRODUCTION_AUDIT)
    # operations_manager reads its config path at import time; point it at a
    # throwaway config (tests pass config dicts directly to publish anyway).
    os.environ["OPERATIONS_MANAGER_CONFIG"] = str(
        Path(tempfile.mkdtemp(prefix="cert_guard_boot_")) / "config.json")


def teardown_module():
    assert _sha(PRODUCTION_SNAPSHOT) == _PROD_BEFORE["snapshot"], \
        "TEST POLLUTED PRODUCTION CAPACITY FILE"
    assert _sha(PRODUCTION_AUDIT) == _PROD_BEFORE["audit"], \
        "TEST POLLUTED PRODUCTION AUDIT LOG"


def _publish():
    """Build a temp manager, import the real manager, publish a snapshot."""
    import importlib
    import cert_guard
    if "operations_manager" in sys.modules:
        om = importlib.reload(sys.modules["operations_manager"])
    else:
        import operations_manager as om
    temp_root, config_path = make_temp_manager()
    os.environ["OPERATIONS_MANAGER_CONFIG"] = str(config_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    paths = om.manager_paths(config)
    ok = om.publish_capacity_snapshot(config, paths, {"active_cases": 0})
    snapshot = Path(config["capacity_snapshot_path"])
    return om, cert_guard, config, paths, snapshot, ok


def test_publish_stamps_provenance_and_self_attests():
    om, cert_guard, config, paths, snapshot, ok = _publish()
    assert ok, "publisher returned False"
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    prov = payload.get("provenance")
    assert isinstance(prov, dict), "published snapshot missing provenance block"
    assert prov["written_by"] == cert_guard.CERTIFIER
    assert prov["witness_action"] == "capacity_snapshot_published"
    # audit witness exists and matches
    assert cert_guard.verify(snapshot, paths["audit_log"], "capacity_snapshot") == []
    # self-attestation recorded ok=true
    entries = [json.loads(l) for l in paths["audit_log"].read_text().splitlines() if l.strip()]
    attest = [e for e in entries if e.get("action") == "cert_attestation"]
    assert attest and attest[-1]["details"]["ok"] is True


def test_hand_forged_claim_rejected():
    om, cert_guard, config, paths, snapshot, ok = _publish()
    forged = json.loads(snapshot.read_text(encoding="utf-8"))
    forged.pop("provenance", None)
    forged["source"] = "internal_reasoning"  # the 2026-09-05 forgery signature
    forged["generated_at_utc"] = "2026-09-05T11:36:19.123456Z"
    snapshot.write_text(json.dumps(forged, indent=2), encoding="utf-8")
    violations = cert_guard.verify(snapshot, paths["audit_log"], "capacity_snapshot")
    assert violations, "Claim-style forged snapshot was NOT rejected"
    assert any("provenance" in v for v in violations)
    assert any("Claim-style" in v for v in violations)


def test_wrong_certifier_rejected():
    om, cert_guard, config, paths, snapshot, ok = _publish()
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    payload["provenance"]["written_by"] = "test_agent"
    snapshot.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    violations = cert_guard.verify(snapshot, paths["audit_log"], "capacity_snapshot")
    assert any("not the certifier" in v for v in violations), violations


def test_unattested_timestamp_rejected():
    om, cert_guard, config, paths, snapshot, ok = _publish()
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    # keep provenance but rotate the state timestamp: no audit witness exists
    payload["generated_at_utc"] = "2099-01-01T00:00:00.000001Z"
    snapshot.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    violations = cert_guard.verify(snapshot, paths["audit_log"], "capacity_snapshot")
    assert any("no audit witness" in v for v in violations), violations


def test_stamp_refuses_non_certifier():
    import cert_guard
    try:
        cert_guard.stamp({"schema_version": 1}, "capacity_snapshot", actor="rogue_agent")
    except cert_guard.ProvenanceViolation:
        return
    raise AssertionError("stamp() accepted a non-certifier actor — Cert minted by Claim")
