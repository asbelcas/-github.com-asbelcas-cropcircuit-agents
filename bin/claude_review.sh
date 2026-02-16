#!/usr/bin/env bash
set -euo pipefail

TIMEOUT_SECONDS="${CLAUDE_REVIEW_TIMEOUT_SECONDS:-45}"
MAX_BYTES=2048

if ! command -v claude >/dev/null 2>&1; then
  echo "CLAUDE_REVIEW:TIMEOUT"
  exit 0
fi

packet="$(cat || true)"
if [[ -z "$packet" ]]; then
  echo "CLAUDE_REVIEW:TIMEOUT"
  exit 0
fi

# Bound prompt size to 2KB
packet="$(printf '%s' "$packet" | head -c "$MAX_BYTES")"
prompt=$(
cat <<EOF
Return EXACTLY this format:

IMPROVEMENT:
<one sentence>

PATCH_TYPE:
(config | retry_logic | observability | performance | funding)

RISK:
(low | medium | high)

No extra text.

$packet
EOF
)

set +e
out="$(timeout "${TIMEOUT_SECONDS}s" claude -p "$prompt" 2>&1)"
rc=$?
set -e

if [[ $rc -ne 0 ]]; then
  echo "CLAUDE_REVIEW:TIMEOUT"
  exit 0
fi

printf '%s\n' "$out"
