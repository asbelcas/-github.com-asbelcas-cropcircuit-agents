#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/asbelcas/cropcircuit"
CFG_DIR="$HOME/.config/cropcircuit"
CREDS_FILE="$CFG_DIR/gmail_credentials.json"
TOKEN_FILE="$CFG_DIR/gmail_token.json"

mkdir -p "$CFG_DIR"

if [[ ! -f "$CREDS_FILE" ]]; then
  echo "Missing $CREDS_FILE"
  echo "Place Google OAuth client secret JSON there first."
  exit 2
fi

python3 - <<'PY'
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

cfg = Path.home() / ".config/cropcircuit"
creds = cfg / "gmail_credentials.json"
token = cfg / "gmail_token.json"
scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
flow = InstalledAppFlow.from_client_secrets_file(str(creds), scopes)
credentials = flow.run_local_server(port=0)
token.write_text(credentials.to_json(), encoding="utf-8")
print(f"Saved token: {token}")
PY
