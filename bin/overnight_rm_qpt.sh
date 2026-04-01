#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/asbelcas/cropcircuit"
STIG="$ROOT/.stigmergy"
STATE="$STIG/dimensional_state.json"
IMPLICATE="$STIG/implicate/revenue_potential.md"
TRACE_DIR="$STIG/traces"
SHADOW_DIR="$STIG/shadows"
CRYSTAL_DIR="$STIG/crystallized"
LOG_FILE="$ROOT/logs/overnight_rm_qpt.log"

mkdir -p "$TRACE_DIR" "$SHADOW_DIR" "$CRYSTAL_DIR" "$ROOT/logs"

if [[ ! -f "$STATE" ]]; then
  cat > "$STATE" <<'JSON'
{
  "flow": 0.25,
  "transform": 0.25,
  "pattern": 0.25,
  "wholeness": 0.25,
  "harmony": 0.25,
  "dissent_shadow": null,
  "urgency_half_life_seconds": 1800,
  "context_half_life_seconds": 86400,
  "updated_at": "2026-03-05T00:00:00Z"
}
JSON
fi

if [[ ! -f "$IMPLICATE" ]]; then
  cat > "$IMPLICATE" <<'EOF_POT'
# Implicate Revenue Potential
- checkout friction and abandonment paths
- upgrade and cross-sell prompt gaps
- latency and reliability drag on conversion
- trust signals that reinforce wholeness
EOF_POT
fi

{
  echo "[$(date -Iseconds)] rm_qpt_overnight_start"
  echo "mode=safe approvals=sandboxed"
  echo "state=$STATE"
  echo "implicate=$IMPLICATE"
} >> "$LOG_FILE"

cat <<'EOF'
RM-QPT overnight environment is initialized in safe mode.
What this script does:
1) Ensures .stigmergy field is present
2) Seeds dimensional state and implicate potential
3) Logs startup artifact for morning review

Manual launch template (safe):
  codex --model gpt-5-codex --search \
    -i "Participate in RM-QPT flow. Read .stigmergy/dimensional_state.json and .stigmergy/implicate/revenue_potential.md.
        Strengthen weakest dimension, leave traces in .stigmergy/traces, and keep operations reversible."

Not used by design:
  --dangerously-bypass-approvals-and-sandbox
  --auto-accept-all
EOF
