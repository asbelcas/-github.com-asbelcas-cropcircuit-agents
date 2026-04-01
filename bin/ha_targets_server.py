#!/usr/bin/env python3
"""Receive morning monetary targets from Home Assistant."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path("/home/asbelcas/cropcircuit")
RUNTIME_JSON = ROOT / "runtime" / "morning_targets.json"
LOG_FILE = ROOT / "logs" / "morning_targets.log"
DONOR_PAYLOAD_JSON = Path("/opt/homeassistant/config/grant_triggers/donor_lead_payload.json")
HOST = "0.0.0.0"
PORT = 8777


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def append_log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        out = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def do_POST(self):  # noqa: N802
        if self.path == "/donor":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length).decode("utf-8")
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise ValueError("payload_must_be_object")
                donor = {
                    "name": str(payload.get("name", "") or "").strip(),
                    "email": str(payload.get("email", "") or "").strip(),
                    "phone": str(payload.get("phone", "") or "").strip(),
                    "interest": str(payload.get("interest", "") or "").strip(),
                    "amount_range": str(payload.get("amount_range", "") or "").strip(),
                    "message": str(payload.get("message", "") or "").strip(),
                    "source": str(payload.get("source", "ha_webhook") or "ha_webhook"),
                }
                if not donor["email"]:
                    raise ValueError("missing_email")
                atomic_write_json(DONOR_PAYLOAD_JSON, donor)
                append_log(
                    json.dumps(
                        {
                            "timestamp_utc": now_iso(),
                            "event": "donor_payload_received",
                            "path": str(DONOR_PAYLOAD_JSON),
                            "email": donor["email"],
                        },
                        ensure_ascii=True,
                    )
                )
                self._send(200, {"ok": True, "stored": str(DONOR_PAYLOAD_JSON)})
            except Exception as exc:
                append_log(
                    json.dumps({"timestamp_utc": now_iso(), "event": "donor_payload_error", "error": str(exc)}, ensure_ascii=True)
                )
                self._send(400, {"ok": False, "error": str(exc)})
            return

        if self.path != "/targets":
            self._send(404, {"ok": False, "error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("payload_must_be_object")
            atomic_write_json(RUNTIME_JSON, payload)
            append_log(
                json.dumps(
                    {
                        "timestamp_utc": now_iso(),
                        "event": "targets_received",
                        "path": str(RUNTIME_JSON),
                        "program_count": len(payload.get("programs", []) if isinstance(payload.get("programs"), list) else []),
                    },
                    ensure_ascii=True,
                )
            )
            self._send(200, {"ok": True, "stored": str(RUNTIME_JSON)})
        except Exception as exc:
            append_log(
                json.dumps({"timestamp_utc": now_iso(), "event": "targets_error", "error": str(exc)}, ensure_ascii=True)
            )
            self._send(400, {"ok": False, "error": str(exc)})

    def log_message(self, format, *args):  # noqa: A003
        return


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    append_log(json.dumps({"timestamp_utc": now_iso(), "event": "targets_server_start", "bind": f"{HOST}:{PORT}"}))
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
