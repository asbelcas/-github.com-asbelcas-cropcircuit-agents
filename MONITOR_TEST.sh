#!/bin/bash
# Monitor the hour-long test progress

cd /home/asbelcas/rm-qpt

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  HOUR-LONG TEST MONITOR"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Find the test log
TEST_LOG=$(ls -t test_logs/hour_test_*.log 2>/dev/null | head -1)

if [ -z "$TEST_LOG" ]; then
    echo "No test log found. Test may not be running."
    exit 1
fi

echo "Monitoring: $TEST_LOG"
echo ""

# Show latest progress
tail -30 "$TEST_LOG" 2>/dev/null

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  CURRENT SYSTEM STATUS"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

python3 << 'PYEOF'
import sqlite3
from pathlib import Path
from datetime import datetime

print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Check process
import subprocess
result = subprocess.run(['pgrep', '-f', 'REAL_SLEEP_MONEY.py'], capture_output=True, text=True)
if result.stdout.strip():
    pids = result.stdout.strip().split('\n')
    print(f"✅ Main process running: PID {pids[0]}")
else:
    print("❌ Main process not running")

# Check files
data = len(list(Path('collected_data').glob('*.json')))
products = len(list(Path('generated_products').glob('*.py')))
for_sale = len(list(Path('products_for_sale').glob('*.py')))

print(f"📁 Data files:      {data}")
print(f"📁 Products:        {products}")
print(f"📁 For sale:        {for_sale}")

# Check DB
try:
    conn = sqlite3.connect('real_sleep_money.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM actions")
    print(f"🗄️  Actions:         {c.fetchone()[0]}")
    conn.close()
except:
    print("🗄️  Actions:         N/A")

try:
    conn = sqlite3.connect('actual_revenue.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM actual_sales")
    sales = c.fetchone()[0]
    c.execute("SELECT SUM(sale_price) FROM actual_sales")
    revenue = c.fetchone()[0] or 0
    print(f"💰 Sales:           {sales} (${revenue:.2f})")
    conn.close()
except:
    print("💰 Sales:           N/A")

PYEOF

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  To see full progress: tail -f $TEST_LOG"
echo "═══════════════════════════════════════════════════════════════════════════════"
