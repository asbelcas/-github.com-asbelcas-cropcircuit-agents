#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/asbelcas/cropcircuit"
POLICY="$ROOT/runtime/monitoring_alert_policy.json"
SCHEDULE="$ROOT/runtime/weekend_24h_canary_schedule.json"
OUT="$ROOT/runtime/weekend_24h_canary_result.json"
TMP="/tmp/weekend_24h_canary.$$"

mkdir -p "$ROOT/runtime"

python3 - <<'PY' "$POLICY" "$SCHEDULE" "$OUT" "$TMP"
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

policy_path = Path(sys.argv[1])
schedule_path = Path(sys.argv[2])
out_path = Path(sys.argv[3])
tmp_tag = sys.argv[4]

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def run(cmd: str, timeout: int = 20):
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

policy = read_json(policy_path)
schedule = read_json(schedule_path)

results = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "policy_mode": policy.get("mode", "unknown"),
    "checks": {},
    "status": "unknown",
}

# 1) Core health checks
health = {}
for url in ("http://127.0.0.1:8010/healthz", "http://127.0.0.1:8788/healthz", "http://127.0.0.1:8789/healthz"):
    rc, out, err = run(f"curl -sS -m 5 {url}")
    health[url] = {"ok": rc == 0, "output": out[:400], "error": err[:200]}
results["checks"]["healthz"] = health

# 2) HA stale >24h (best-effort: requires HA token in .env.grant)
ha_check = {"ok": False, "reason": "skipped", "stale_over_24h": None}
rc, token, _ = run("bash -lc 'set -a; source /home/asbelcas/cropcircuit/.env.grant 2>/dev/null; set +a; printf %s \"$HA_TOKEN\"'")
if rc == 0 and token:
    rc, out, err = run(f"curl -sS -m 8 -H 'Authorization: Bearer {token}' http://127.0.0.1:8123/api/states")
    if rc == 0:
        try:
            states = json.loads(out)
            now = datetime.now(timezone.utc)
            stale = 0
            for s in states:
                lu = s.get("last_updated")
                if not lu:
                    continue
                dt = datetime.fromisoformat(lu.replace("Z", "+00:00"))
                if (now - dt).total_seconds() > 24 * 3600:
                    stale += 1
            ha_check = {"ok": True, "reason": "computed", "stale_over_24h": stale}
        except Exception as exc:
            ha_check = {"ok": False, "reason": f"parse_error:{exc}", "stale_over_24h": None}
    else:
        ha_check = {"ok": False, "reason": f"api_error:{err or out}", "stale_over_24h": None}
results["checks"]["ha_stale_24h"] = ha_check

# 3) SQLite quick integrity checks
sql = {}
for label, path in (
    ("donor_dedupe", "/home/asbelcas/cropcircuit/runtime/donor_dedupe.sqlite"),
    ("workforce_db", "/home/asbelcas/workforce/workforce.db"),
    ("black_kite_db", "/home/asbelcas/workforce/data/black_kite.db"),
):
    try:
        import sqlite3
        conn = sqlite3.connect(path)
        res = conn.execute("PRAGMA quick_check").fetchone()[0]
        sql[label] = {"ok": res == "ok", "result": res}
    except Exception as exc:
        sql[label] = {"ok": False, "result": str(exc)}
results["checks"]["sqlite"] = sql

health_ok = all(v["ok"] for v in health.values())
ha_ok = (ha_check["stale_over_24h"] == 0) if ha_check["ok"] else False
sqlite_ok = all(v["ok"] for v in sql.values())
results["status"] = "pass" if (health_ok and ha_ok and sqlite_ok) else "warn"
results["summary"] = {
    "health_ok": health_ok,
    "ha_stale_24h_ok": ha_ok,
    "sqlite_ok": sqlite_ok
}

out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps({"ok": True, "output": str(out_path), "status": results["status"]}))
PY
