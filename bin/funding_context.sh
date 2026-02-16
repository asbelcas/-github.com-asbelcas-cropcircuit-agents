#!/usr/bin/env bash
set -e

echo "funding_context:"
echo "current_grant_stage=$(grep stage grant_autopilot_status.md 2>/dev/null || echo unknown)"
echo "recent_failures=$(grep fail logs/runs.jsonl | wc -l)"
echo "last_outreach=$(grep outreach logs/runs.jsonl | tail -n1)"
echo "question: which funding move has highest probability this week?"
