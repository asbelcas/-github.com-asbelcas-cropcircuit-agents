#!/bin/bash
# =============================================================================
# CROPCIRCUIT AGENT SETUP
# =============================================================================
# This script sets up the complete CropCircuit agent system
# Run once to initialize everything
# =============================================================================

set -e  # Exit on error

echo "============================================================================="
echo "  🌱 CROPCIRCUIT AGENT SETUP"
echo "============================================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check working directory
AGENT_DIR="/home/asbelcas/rm-qpt"
cd "$AGENT_DIR"

echo "✅ Working directory: $(pwd)"

# =============================================================================
# STEP 1: Verify existing systems
# =============================================================================
echo ""
echo "STEP 1: Verifying existing systems..."

if [ -f "REAL_SLEEP_MONEY.py" ]; then
    echo "✅ Asset creation system: REAL_SLEEP_MONEY.py"
else
    echo "❌ REAL_SLEEP_MONEY.py not found"
    exit 1
fi

if [ -f "MAKE_MONEY_PRACTICAL.py" ]; then
    echo "✅ Product packaging system: MAKE_MONEY_PRACTICAL.py"
else
    echo "❌ MAKE_MONEY_PRACTICAL.py not found"
    exit 1
fi

if [ -d "collected_data" ]; then
    DATA_COUNT=$(ls -1 collected_data/*.json 2>/dev/null | wc -l)
    echo "✅ Data directory: ${DATA_COUNT} files"
else
    echo "⚠️  Data directory not found (will be created)"
fi

if [ -d "generated_products" ]; then
    PRODUCT_COUNT=$(ls -1 generated_products/*.py 2>/dev/null | wc -l)
    echo "✅ Products directory: ${PRODUCT_COUNT} files"
else
    echo "⚠️  Products directory not found (will be created)"
fi

# =============================================================================
# STEP 2: Initialize agent database
# =============================================================================
echo ""
echo "STEP 2: Initializing agent database..."

python3 << 'PYEOF'
import sqlite3
import os

db_path = "/home/asbelcas/rm-qpt/agent_central.db"

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create all tables
tables = [
    '''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        priority INTEGER DEFAULT 5,
        status TEXT DEFAULT 'pending',
        type TEXT,
        description TEXT,
        source TEXT,
        estimated_value REAL,
        actual_value REAL,
        started_at TEXT,
        completed_at TEXT,
        output_file TEXT,
        error_message TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY,
        discovered_at TEXT,
        source TEXT,
        title TEXT,
        description TEXT,
        url TEXT,
        budget TEXT,
        skills TEXT,
        status TEXT DEFAULT 'new',
        applied_at TEXT,
        hired BOOLEAN DEFAULT 0,
        paid_amount REAL DEFAULT 0
    )''',
    '''CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY,
        date TEXT,
        source TEXT,
        amount REAL,
        task_id INTEGER,
        platform TEXT,
        transaction_id TEXT,
        confirmed BOOLEAN DEFAULT 0
    )''',
    '''CREATE TABLE IF NOT EXISTS confirmed_revenue (
        id INTEGER PRIMARY KEY,
        date TEXT,
        source TEXT,
        platform TEXT,
        item_type TEXT,
        description TEXT,
        amount REAL,
        fee_amount REAL DEFAULT 0,
        net_amount REAL,
        transaction_id TEXT,
        proof_file TEXT,
        notes TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS pending_payments (
        id INTEGER PRIMARY KEY,
        expected_date TEXT,
        source TEXT,
        description TEXT,
        expected_amount REAL,
        status TEXT DEFAULT 'pending',
        actual_revenue_id INTEGER
    )''',
    '''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        source TEXT,
        status TEXT DEFAULT 'lead',
        first_contact TEXT,
        last_contact TEXT,
        total_paid REAL DEFAULT 0,
        notes TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        client_id INTEGER,
        created_at TEXT,
        title TEXT,
        description TEXT,
        scope TEXT,
        agreed_price REAL,
        status TEXT DEFAULT 'inquiry',
        deadline TEXT,
        deliverables TEXT,
        completed_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS communications (
        id INTEGER PRIMARY KEY,
        client_id INTEGER,
        project_id INTEGER,
        timestamp TEXT,
        direction TEXT,
        channel TEXT,
        message TEXT,
        requires_response BOOLEAN DEFAULT 0,
        responded_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS agent_log (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        level TEXT,
        message TEXT,
        task_id INTEGER
    )'''
]

for table_sql in tables:
    c.execute(table_sql)

conn.commit()
conn.close()

print(f"✅ Agent database created: {db_path}")
PYEOF

# =============================================================================
# STEP 3: Create necessary directories
# =============================================================================
echo ""
echo "STEP 3: Creating directories..."

mkdir -p agent_work
mkdir -p agent_deliveries
mkdir -p ready_to_sell
mkdir -p collected_data
mkdir -p generated_products

echo "✅ Directories created"

# =============================================================================
# STEP 4: Make scripts executable
# =============================================================================
echo ""
echo "STEP 4: Making scripts executable..."

chmod +x CROPCIRCUIT_AGENT.py
chmod +x AGENT_REVENUE.py
chmod +x AGENT_CLIENT.py

echo "✅ Scripts made executable"

# =============================================================================
# STEP 5: Import existing data
# =============================================================================
echo ""
echo "STEP 5: Importing existing data..."

python3 << 'PYEOF'
import sqlite3
import json
from pathlib import Path
from datetime import datetime

db_path = "/home/asbelcas/rm-qpt/agent_central.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Import data files as opportunities
imported = 0
for data_file in Path("collected_data").glob("*.json"):
    try:
        with open(data_file) as f:
            data = json.load(f)
        
        if isinstance(data, list) and len(data) > 0:
            for item in data[:3]:  # First 3 items
                title = item.get('title', 'Unknown')
                c.execute('''INSERT OR IGNORE INTO opportunities 
                    (discovered_at, source, title, description, url, budget, skills, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (datetime.now().isoformat(), 
                     'data_file',
                     title,
                     item.get('description', '')[:500],
                     item.get('link', ''),
                     'Unknown',
                     'python',
                     'new'))
                imported += 1
    except:
        pass

conn.commit()
print(f"✅ Imported {imported} opportunities from data files")

# Count current assets
data_count = len(list(Path("collected_data").glob("*.json")))
product_count = len(list(Path("generated_products").glob("*.py")))
package_count = len(list(Path("ready_to_sell").glob("*.zip")))

print(f"✅ Assets: {data_count} data files, {product_count} products, {package_count} packages")

conn.close()
PYEOF

# =============================================================================
# STEP 6: Create command aliases
# =============================================================================
echo ""
echo "STEP 6: Creating command shortcuts..."

cat << 'BASHEOF' >> ~/.bashrc

# CropCircuit Agent Commands
alias cca='python3 /home/asbelcas/rm-qpt/CROPCIRCUIT_AGENT.py'
alias cca-status='python3 /home/asbelcas/rm-qpt/CROPCIRCUIT_AGENT.py status'
alias cca-run='python3 /home/asbelcas/rm-qpt/CROPCIRCUIT_AGENT.py run'
alias cca-scan='python3 /home/asbelcas/rm-qpt/CROPCIRCUIT_AGENT.py scan'

# Revenue Commands
alias cca-revenue='python3 /home/asbelcas/rm-qpt/AGENT_REVENUE.py dashboard'
alias cca-report='python3 /home/asbelcas/rm-qpt/AGENT_REVENUE.py report'
alias cca-plan='python3 /home/asbelcas/rm-qpt/AGENT_REVENUE.py plan'

# Client Commands
alias cca-clients='python3 /home/asbelcas/rm-qpt/AGENT_CLIENT.py status'

BASHEOF

echo "✅ Command aliases added to ~/.bashrc"
echo "   Run 'source ~/.bashrc' to use them"

# =============================================================================
# STEP 7: Final status
# =============================================================================
echo ""
echo "============================================================================="
echo "  ✅ SETUP COMPLETE"
echo "============================================================================="
echo ""
echo "QUICK START:"
echo ""
echo "  1. Check status:        python3 CROPCIRCUIT_AGENT.py status"
echo "  2. Start agent:         python3 CROPCIRCUIT_AGENT.py run"
echo "  3. View revenue:        python3 AGENT_REVENUE.py dashboard"
echo "  4. See action plan:     python3 AGENT_REVENUE.py plan"
echo ""
echo "IMMEDIATE ACTIONS NEEDED:"
echo ""
echo "  1. List products on Gumroad/Etsy:"
echo "     - Go to https://gumroad.com/signup"
echo "     - Upload ZIP files from ready_to_sell/"
echo "     - Set prices ($9-29)"
echo ""
echo "  2. When you make a sale, record it:"
echo "     python3 AGENT_REVENUE.py add --platform gumroad --amount 19 --desc 'Product Name'"
echo ""
echo "  3. Start monitoring:"
echo "     python3 CROPCIRCUIT_AGENT.py run"
echo ""
echo "============================================================================="
