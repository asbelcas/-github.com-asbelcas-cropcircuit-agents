#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Source env file for GMAIL_APP_PASSWORD and HA credentials
if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  source "$ROOT_DIR/.env.grant"
fi

RUN_DATE="${1:-}"
DRY_RUN="${DRY_RUN:-0}"

if [[ -n "$RUN_DATE" ]] && ! [[ "$RUN_DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "ERROR: RUN_DATE must be YYYY-MM-DD"
  exit 2
fi

if [[ "$DRY_RUN" != "0" && "$DRY_RUN" != "1" ]]; then
  echo "ERROR: DRY_RUN must be 0 or 1"
  exit 2
fi

args=()
if [[ -n "$RUN_DATE" ]]; then
  args+=("--date" "$RUN_DATE")
fi
if [[ "$DRY_RUN" == "1" ]]; then
  args+=("--dry-run")
fi

python3 bin/grant_orchestrator.py "${args[@]}"
