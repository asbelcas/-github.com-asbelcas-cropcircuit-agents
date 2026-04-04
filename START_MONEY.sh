#!/bin/bash
# =============================================================================
# START_MONEY.sh - Start the complete money-making system
# =============================================================================
# This script starts ALL components needed for persistent revenue generation
# =============================================================================

set -e

cd /home/asbelcas/rm-qpt

echo "============================================================================="
echo "  💰 STARTING CROPCIRCUIT MONEY SYSTEM"
echo "============================================================================="
echo ""
echo "  Target: $100/day | $2000/month"
echo "  Mode: ACTIVE REVENUE GENERATION"
echo ""

# =============================================================================
# STEP 1: Initialize money database
# =============================================================================
echo "[1/5] Initializing money database..."

python3 << 'PYEOF'
import sqlite3
import os

db_path = "/home/asbelcas/rm-qpt/money_central.db"

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Revenue tracking
c.execute('''CREATE TABLE IF NOT EXISTS revenue_goals (
    id INTEGER PRIMARY KEY,
    date TEXT,
    daily_goal REAL DEFAULT 100,
    daily_actual REAL DEFAULT 0,
    monthly_goal REAL DEFAULT 2000,
    month TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS outreach (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    channel TEXT,
    target TEXT,
    message TEXT,
    sent BOOLEAN DEFAULT 0,
    responded BOOLEAN DEFAULT 0,
    converted BOOLEAN DEFAULT 0,
    revenue REAL DEFAULT 0
)''')

c.execute('''CREATE TABLE IF NOT EXISTS proposals (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    client TEXT,
    project_title TEXT,
    value REAL,
    status TEXT DEFAULT 'draft',
    sent_at TEXT,
    accepted BOOLEAN DEFAULT 0,
    paid BOOLEAN DEFAULT 0
)''')

c.execute('''CREATE TABLE IF NOT EXISTS money_in (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    source TEXT,
    amount REAL,
    method TEXT,
    related_proposal_id INTEGER,
    confirmed BOOLEAN DEFAULT 1
)''')

c.execute('''CREATE TABLE IF NOT EXISTS hourly_activity (
    id INTEGER PRIMARY KEY,
    hour TEXT,
    data_collected INTEGER DEFAULT 0,
    outreach_sent INTEGER DEFAULT 0,
    proposals_created INTEGER DEFAULT 0,
    revenue_generated REAL DEFAULT 0
)''')

c.execute('''CREATE TABLE IF NOT EXISTS active_clients (
    id INTEGER PRIMARY KEY,
    name TEXT,
    contact TEXT,
    source TEXT,
    status TEXT DEFAULT 'lead',
    last_contact TEXT,
    potential_value REAL,
    actual_paid REAL DEFAULT 0
)''')

# Hunter tables
c.execute('''CREATE TABLE IF NOT EXISTS hunt_targets (
    id INTEGER PRIMARY KEY,
    discovered_at TEXT,
    source TEXT,
    company TEXT,
    contact_email TEXT,
    job_title TEXT,
    job_url TEXT,
    skills_needed TEXT,
    budget_hint TEXT,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'new',
    contacted_at TEXT,
    proposal_sent BOOLEAN DEFAULT 0,
    responded BOOLEAN DEFAULT 0,
    notes TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS hunt_activity (
    id INTEGER PRIMARY KEY,
    date TEXT,
    targets_found INTEGER DEFAULT 0,
    contacted INTEGER DEFAULT 0,
    proposals INTEGER DEFAULT 0,
    responses INTEGER DEFAULT 0
)''')

conn.commit()
conn.close()

print(f"  ✅ Money database ready: {db_path}")
PYEOF

# =============================================================================
# STEP 2: Check if REAL_SLEEP_MONEY is running
# =============================================================================
echo ""
echo "[2/5] Checking data collection system..."

if pgrep -f "REAL_SLEEP_MONEY.py" > /dev/null; then
    echo "  ✅ REAL_SLEEP_MONEY is running"
    PID=$(pgrep -f "REAL_SLEEP_MONEY.py" | head -1)
    UPTIME=$(ps -o etime= -p $PID)
    echo "  PID: $PID | Uptime: $UPTIME"
else
    echo "  ⚠️  REAL_SLEEP_MONEY not running, starting..."
    nohup python3 REAL_SLEEP_MONEY.py start > logs/money_data.log 2>&1 &
    sleep 2
    echo "  ✅ Started REAL_SLEEP_MONEY"
fi

# =============================================================================
# STEP 3: Create initial targets
# =============================================================================
echo ""
echo "[3/5] Scanning for initial targets..."

python3 CLIENT_HUNTER.py hunt 2>&1 | grep -E "(NEW TARGET|HUNT COMPLETE|approaches ready)" || echo "  Scan complete"

# =============================================================================
# STEP 4: Show status before starting
# =============================================================================
echo ""
echo "[4/5] Current money status:"
echo "-----------------------------------------------------------------------------"
python3 MONEY_STATUS.py --quick
echo "-----------------------------------------------------------------------------"

# =============================================================================
# STEP 5: Start money loop
# =============================================================================
echo ""
echo "[5/5] Starting MONEY_LOOP..."
echo ""
echo "  This will run 24/7, executing revenue activities every 15 minutes"
echo ""
echo "  Press Ctrl+C to stop"
echo ""
echo "============================================================================="

python3 MONEY_LOOP.py run
