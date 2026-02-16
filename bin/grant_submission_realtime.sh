#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f "$ROOT_DIR/.env.grant" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.grant"
fi

exec python3 "$ROOT_DIR/bin/ha_grant_submission_relay.py" "$@"
