#!/bin/bash
# MAKE MONEY WHILE SLEEPING
# The ultimate passive income launcher

cd /home/asbelcas/rm-qpt

clear
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║   💰 MAKE MONEY WHILE YOU SLEEP                                          ║"
echo "║                                                                          ║"
echo "║   24/7 Automated Income Generation                                       ║"
echo "║   NO Manual Work Required                                                ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Show current passive income
python3 << 'PYEOF'
import sqlite3
try:
    conn = sqlite3.connect('sleep_money.db')
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM earnings")
    total = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM earnings WHERE date(timestamp) = date('now')")
    today = c.fetchone()[0] or 0
    print(f"📊 PASSIVE INCOME: ${total:.2f} total | ${today:.2f} today")
    conn.close()
except:
    print("📊 Ready to generate passive income")
PYEOF

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "SELECT MONEY-MAKING MODE:"
echo ""
echo "  1) 🚀 START PASSIVE INCOME ENGINE (Recommended)"
echo "     → Runs 24/7 automatically"
echo "     → Multiple revenue streams"
echo "     → Makes money while you sleep"
echo ""
echo "  2) 📊 VIEW PASSIVE INCOME DASHBOARD"
echo "     → Check total earnings"
echo "     → See which streams are working"
echo ""
echo "  3) 🏭 CREATE DIGITAL PRODUCTS"
echo "     → Auto-generate products to sell"
echo "     → One-time creation, forever sales"
echo ""
echo "  4) 📈 ANALYZE INCOME STREAMS"
echo "     → See all possible revenue sources"
echo "     → Choose your passive income mix"
echo ""
echo "  5) 💼 ACTIVE INCOME (Freelance)"
echo "     → Browse and apply to jobs"
echo "     → Higher effort, immediate pay"
echo ""
echo "  6) ❌ EXIT"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

read -p "Select mode (1-6): " choice

case $choice in
    1)
        echo ""
        echo "🚀 STARTING 24/7 PASSIVE INCOME ENGINE..."
        echo "This will run continuously making money."
        echo "Press Ctrl+C to stop."
        echo ""
        sleep 2
        python3 SLEEP_MONEY.py start
        ;;
    
    2)
        echo ""
        python3 SLEEP_MONEY.py status
        ;;
    
    3)
        echo ""
        echo "🏭 Creating digital products..."
        python3 streams/digital_product_automation.py
        ;;
    
    4)
        echo ""
        python3 PASSIVE_INCOME_ENGINE.py analyze
        ;;
    
    5)
        echo ""
        echo "Switching to active income mode..."
        ./MONEY_NOW.sh
        ;;
    
    6)
        echo ""
        echo "Sleep well. Money will be here when you wake up. 💰"
        exit 0
        ;;
    
    *)
        echo ""
        echo "Invalid option. Select 1-6."
        ;;
esac

echo ""
read -p "Press Enter to return to menu..."
exec "$0"
