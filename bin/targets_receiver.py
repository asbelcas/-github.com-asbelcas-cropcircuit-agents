#!/usr/bin/env python3
"""Authenticated targets receiver for Home Assistant morning payloads."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse


ROOT = Path("/home/asbelcas/cropcircuit")
TARGETS_FILE = ROOT / "runtime" / "morning_targets.json"
INGEST_LOG = ROOT / "logs" / "targets_ingest.log"
TOKEN_ENV = "CROPCIRCUIT_TARGETS_TOKEN"

app = FastAPI(title="CropCircuit Targets Receiver", version="1.0.0")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def log_line(payload: dict) -> None:
    INGEST_LOG.parent.mkdir(parents=True, exist_ok=True)
    with INGEST_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def check_auth(authorization: str | None) -> None:
    expected = os.environ.get(TOKEN_ENV, "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail=f"{TOKEN_ENV} is not set")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer authorization")
    provided = authorization.split(" ", 1)[1].strip()
    if provided != expected:
        raise HTTPException(status_code=401, detail="invalid token")


@app.post("/ha/targets")
async def receive_targets(request: Request, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid_json: {exc}") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be object")

    atomic_write(TARGETS_FILE, payload)
    log_line(
        {
            "timestamp_utc": now_iso(),
            "event": "targets_ingested",
            "path": str(TARGETS_FILE),
            "targets_keys": sorted((payload.get("targets") or {}).keys()) if isinstance(payload.get("targets"), dict) else [],
            "program_count": len(payload.get("programs") or []) if isinstance(payload.get("programs"), list) else 0,
        }
    )
    return JSONResponse({"ok": True, "stored": str(TARGETS_FILE)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7777)
