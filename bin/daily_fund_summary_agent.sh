#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/asbelcas/cropcircuit"
LOG="$ROOT/logs/daily_fund_summary_agent.log"

mkdir -p "$ROOT/logs"
python3 "$ROOT/bin/donor_momentum_engine.py" >> "$LOG" 2>&1
echo "$(date -Is) wrote runtime/daily_fund_summary.md" >> "$LOG"
