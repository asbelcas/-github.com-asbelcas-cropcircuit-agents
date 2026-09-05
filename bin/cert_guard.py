#!/usr/bin/env python3
"""FLORAL CIPHER v2 certificate guard — enforces §8 for production state files.

Implements the no-signalling rule of commerce for shared state:

    Claim[X] ≰ Cert[X]
    M(s') > M(s)  ⇒  ∃ m ∈ Γ : Authorizes(m, Φ, M)

Every protected production state file must carry a provenance block naming its
certifier and witness action, and the audit log must contain a matching witness
entry. A hand-written "claim" file (internal reasoning, no provenance, or no
auditable witness) is rejected by verify() — the transition fails at the type
boundary before truthfulness is even a question.

This is the code form of the rule that already prevented the 2026-09-05 forged
capacity snapshot (publisher refuses implicit production targets). cert_guard
adds the second half: even an explicitly-pathed write is only Cert if it is
stamped by the authorized certifier AND witnessed by the audit trail.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

CERTIFIER = "cropcircuit_operations_manager"
PROVENANCE_KEY = "provenance"
CERT_LAW = "floral_cipher_v2/§8"

# Registry of protected production files. A file kind is "protected" only when
# its path is EXPLICITLY configured (never an implicit default) — the v1 fix.
PROTECTED: Dict[str, Dict[str, str]] = {
    "capacity_snapshot": {
        "required_source": "cropcircuit_operations_manager",
        "witness_action": "capacity_snapshot_published",
        "certifier": CERTIFIER,
        "path_config_key": "capacity_snapshot_path",
        "state_timestamp_key": "generated_at_utc",
    },
}


class ProvenanceViolation(Exception):
    """Raised when a production write lacks certifiable provenance."""


def stamp(payload: Dict[str, Any], file_kind: str, actor: str = CERTIFIER) -> Dict[str, Any]:
    """Return a copy of payload with a Cert provenance block attached.

    Only the registered certifier for the file kind may stamp; anything else
    raises ProvenanceViolation (a non-certifier emitting Cert[X] is itself a
    type error).
    """
    spec = PROTECTED.get(file_kind)
    if spec is None:
        raise ProvenanceViolation(f"unknown protected file kind: {file_kind}")
    if actor != spec["certifier"]:
        raise ProvenanceViolation(
            f"actor {actor!r} is not the certifier for {file_kind!r} ({spec['certifier']!r})"
        )
    stamped = dict(payload)
    stamped[PROVENANCE_KEY] = {
        "written_by": actor,
        "witness_action": spec["witness_action"],
        "certifier": spec["certifier"],
        "cert_law": CERT_LAW,
    }
    return stamped


def _audit_witnesses(audit_log_path: Path, witness_action: str, timestamp_key: str) -> set:
    """Collect the set of state timestamps referenced by witness entries."""
    witnesses = set()
    if not audit_log_path.exists():
        return witnesses
    with audit_log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("action") != witness_action:
                continue
            details = record.get("details") or {}
            ts = details.get(timestamp_key)
            if isinstance(ts, str):
                witnesses.add(ts)
    return witnesses


def verify(path: Path, audit_log_path: Path, file_kind: str = "capacity_snapshot") -> List[str]:
    """Lint one protected file. Returns a list of violation strings (empty = Cert)."""
    spec = PROTECTED[file_kind]
    violations: List[str] = []
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        return [f"{path}: unreadable or invalid JSON ({type(e).__name__})"]
    if not isinstance(payload, dict):
        return [f"{path}: top-level value is not an object"]

    # Claim-style writes: wrong/absent source field.
    if payload.get("source") != spec["required_source"]:
        violations.append(
            f"{path}: source={payload.get('source')!r} is not the certifier source "
            f"({spec['required_source']!r}) — Claim-style write rejected"
        )

    provenance = payload.get(PROVENANCE_KEY)
    if not isinstance(provenance, dict):
        violations.append(f"{path}: missing provenance block — Claim[X], not Cert[X]")
    else:
        if provenance.get("written_by") != spec["certifier"]:
            violations.append(
                f"{path}: provenance.written_by={provenance.get('written_by')!r} is not "
                f"the certifier ({spec['certifier']!r})"
            )
        if provenance.get("witness_action") != spec["witness_action"]:
            violations.append(
                f"{path}: provenance.witness_action={provenance.get('witness_action')!r} "
                f"!= {spec['witness_action']!r}"
            )

    # Witness check: the audit log must contain the matching witness entry.
    ts_key = spec["state_timestamp_key"]
    state_ts = payload.get(ts_key)
    if not isinstance(state_ts, str):
        violations.append(f"{path}: missing/invalid {ts_key!r}")
    else:
        witnesses = _audit_witnesses(Path(audit_log_path), spec["witness_action"], ts_key)
        if state_ts not in witnesses:
            violations.append(
                f"{path}: no audit witness ({spec['witness_action']!r}) for {ts_key}={state_ts!r} "
                f"— unattested state"
            )
    return violations


def lint_config(config: Dict[str, Any], manager_dir: Optional[Path] = None) -> Dict[str, List[str]]:
    """Verify every protected file whose path is explicitly configured.

    Returns {file_kind: violations}. Kinds with no explicitly configured path
    are skipped (nothing protected to lint).
    """
    results: Dict[str, List[str]] = {}
    audit_log_path = Path(manager_dir or config.get("manager_dir", "")) / "audit.log"
    for kind, spec in PROTECTED.items():
        configured = config.get(spec["path_config_key"])
        if not configured:
            continue
        results[kind] = verify(Path(configured), audit_log_path, kind)
    return results
