#!/bin/bash
# MASTER DASHBOARD - Unified view of all money-making systems

cd /home/asbelcas/rm-qpt

clear
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║   💰 MASTER MONEY DASHBOARD                                              ║"
echo "║                                                                          ║"
echo "║   Unified view of all income streams                                     ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check active process
PID=$(pgrep -f "REAL_SLEEP_MONEY.py start" | head -1)
if [ -n "$PID" ]; then
    RUNTIME=$(ps -p $PID -o etime= 2>/dev/null | tr -d ' ')
    echo "🟢 ACTIVE PROCESS: PID $PID | Running: $RUNTIME"
else
    echo "🔴 NO ACTIVE PROCESS - System not running"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "📊 REAL SLEEP MONEY ENGINE (ACTIVE SYSTEM)"
echo "═══════════════════════════════════════════════════════════════════════════"

python3 << 'PYEOF'
import sqlite3
import os
from pathlib import Path
from datetime import datetime

try:
    conn = sqlite3.connect('real_sleep_money.db')
    c = conn.cursor()
    
    # Total stats
    c.execute("SELECT COUNT(*), SUM(value_estimate) FROM actions")
    actions, value = c.fetchone()
    actions = actions or 0
    value = value or 0
    
    # Today's stats
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*), SUM(value_estimate) FROM actions WHERE date(timestamp) = ?", (today,))
    today_actions, today_value = c.fetchone()
    today_actions = today_actions or 0
    today_value = today_value or 0
    
    # Data collection
    c.execute("SELECT COUNT(*), SUM(records) FROM collected_data")
    data_files, records = c.fetchone()
    data_files = data_files or 0
    records = records or 0
    
    # Products
    c.execute("SELECT COUNT(*), SUM(lines_of_code) FROM products")
    products, loc = c.fetchone()
    products = products or 0
    loc = loc or 0
    
    # Market data
    c.execute("SELECT COUNT(*) FROM market_data")
    market = c.fetchone()[0] or 0
    
    conn.close()
    
    # Check actual files
    actual_data = len(list(Path('collected_data').glob('*.json')))
    actual_products = len(list(Path('generated_products').glob('*.py')))
    
    print(f"  💵 Total Value:        ${value:,.2f}")
    print(f"  📅 Today:              ${today_value:,.2f} ({today_actions} actions)")
    print(f"  📊 Total Actions:      {actions}")
    print("-" * 67)
    print(f"  📁 Data Files:         {actual_data} files | {records} records")
    print(f"  🏭 Products:           {actual_products} files | {loc} lines")
    print(f"  📈 Market Data:        {market} points")
    
except Exception as e:
    print(f"  ⚠️  Error reading database: {e}")
PYEOF

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "📁 RECENT FILE ACTIVITY"
echo "═══════════════════════════════════════════════════════════════════════════"

echo ""
echo "Latest data files:"
ls -lt collected_data/*.json 2>/dev/null | head -3 | awk '{print "  " $6, $7, $8, "-", $9, "(" $5 " bytes)"}' || echo "  No data files"

echo ""
echo "Latest products:"
ls -lt generated_products/*.py 2>/dev/null | head -3 | awk '{print "  " $6, $7, $8, "-", $9, "(" $5 " bytes)"}' || echo "  No products"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🎯 QUICK ACTIONS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "  1) 🚀 Start/Restart 24/7 Engine"
echo "  2) 📊 View Full Status"
echo "  3) 🧪 Run Test Cycle"
echo "  4) 📁 Browse Files"
echo "  5) 🔍 View Logs"
echo "  6) 🛑 Stop Engine"
echo "  7) ❌ Exit"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

read -p "Select action (1-7): " choice

case $choice in
    1)
        echo ""
        PID=$(pgrep -f "REAL_SLEEP_MONEY.py start" | head -1)
        if [ -n "$PID" ]; then
            echo "Process already running (PID $PID)"
            read -p "Restart? (yes/no): " restart
            if [ "$restart" = "yes" ]; then
                kill $PID 2>/dev/null
                sleep 2
                ./RUN_REAL_MONEY.sh
            fi
        else
            ./RUN_REAL_MONEY.sh
        fi
        ;;
    2)
        echo ""
        python3 REAL_SLEEP_MONEY.py status
        ;;
    3)
        echo ""
        python3 << 'PYEOF'
import sys
sys.path.insert(0, '/home/asbelcas/rm-qpt')
from REAL_SLEEP_MONEY import RealSleepMoneyEngine

engine = RealSleepMoneyEngine()
print("Running test cycle...\n")

print("1. Scraping WWR...")
engine._scrape_weworkremotely()

print("2. Scraping RemoteOK...")
engine._scrape_remoteok()

print("3. Creating product...")
engine._create_automation_script()

print("4. Checking crypto...")
engine._check_crypto_prices()

print("5. Analyzing opportunities...")
engine._analyze_job_opportunities()

print("\n✅ Test complete!")
engine.show_status()
PYEOF
        ;;
    4)
        echo ""
        echo "📁 DATA FILES:"
        ls -lh collected_data/*.json 2>/dev/null | tail -5 || echo "  None"
        echo ""
        echo "📁 PRODUCTS:"
        ls -lh generated_products/*.py 2>/dev/null | tail -5 || echo "  None"
        ;;
    5)
        echo ""
        python3 << 'PYEOF'
import sqlite3
try:
    conn = sqlite3.connect('real_sleep_money.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, stream, action, result FROM actions ORDER BY timestamp DESC LIMIT 10")
    rows = c.fetchall()
    print("Recent activity:")
    print(f"{'TIME':<20} {'STREAM':<15} {'ACTION':<25} {'RESULT'}")
    print("-" * 80)
    for row in rows:
        ts = row[0][:19] if row[0] else ''
        print(f"{ts:<20} {row[1]:<15} {row[2]:<25} {row[3]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
PYEOF
        ;;
    6)
        echo ""
        PID=$(pgrep -f "REAL_SLEEP_MONEY.py start" | head -1)
        if [ -n "$PID" ]; then
            kill $PID 2>/dev/null
            echo "🛑 Engine stopped (PID $PID)"
        else
            echo "No engine running"
        fi
        ;;
    7)
        echo ""
        echo "Dashboard closed."
        exit 0
        ;;
    *)
        echo ""
        echo "Invalid option"
        ;;
esac

echo ""
read -p "Press Enter to return to dashboard..."
exec "$0"
