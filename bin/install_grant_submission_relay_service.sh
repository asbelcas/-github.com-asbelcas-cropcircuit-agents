#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="grant-submission-relay.service"
SERVICE_PATH="$HOME/.config/systemd/user/$SERVICE_NAME"

mkdir -p "$HOME/.config/systemd/user"

cat > "$SERVICE_PATH" <<UNIT
[Unit]
Description=CropCircuit Grant Submission Realtime Relay (Non-MDARD)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/asbelcas/cropcircuit
EnvironmentFile=/home/asbelcas/cropcircuit/.env.grant
ExecStart=/home/asbelcas/cropcircuit/bin/grant_submission_realtime.sh --watch --force --interval 30
Restart=always
RestartSec=5
StandardOutput=append:/home/asbelcas/cropcircuit/logs/grant_submission_relay.service.log
StandardError=append:/home/asbelcas/cropcircuit/logs/grant_submission_relay.service.log

[Install]
WantedBy=default.target
UNIT

mkdir -p /home/asbelcas/cropcircuit/logs
systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME"
systemctl --user status "$SERVICE_NAME" --no-pager

echo "Installed and started $SERVICE_NAME"
echo "Log file: /home/asbelcas/cropcircuit/logs/grant_submission_relay.service.log"
