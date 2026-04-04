#!/bin/bash
# MAKE MONEY NOW - Critical fix for income generation
# No fluff. Just money.

cd /home/asbelcas/rm-qpt

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║   💰 MAKE MONEY NOW - Critical Income System                             ║"
echo "║                                                                          ║"
echo "║   NO STAGING. NO SIMULATION. ACTUAL PROPOSALS. REAL MONEY.               ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Show current status
echo "📊 CURRENT REALITY CHECK:"
python3 << 'PYEOF'
import sqlite3
try:
    conn = sqlite3.connect('real_money.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(status='applied'), SUM(status='won'), SUM(won_amount) FROM opportunities")
    total, applied, won, earnings = c.fetchone()
    
    print(f"  Total Python jobs found: {total or 0}")
    print(f"  Proposals ACTUALLY sent: {applied or 0}")
    print(f"  Jobs WON:                {won or 0}")
    print(f"  REAL Money earned:       ${earnings or 0:.2f}")
    conn.close()
except:
    print("  Database not initialized yet")
PYEOF

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "OPTIONS:"
echo ""
echo "  1) 🚀 FIND & APPLY TO PYTHON JOBS (Full cycle)"
echo "     → Scrape Upwork for Python/automation jobs"
echo "     → Show you the jobs with apply commands"
echo ""
echo "  2) 🔍 JUST FIND JOBS"
echo "     → Scrape Upwork without applying"
echo ""
echo "  3) 💼 APPLY TO SAVED JOB"
echo "     → Enter job ID and apply"
echo ""
echo "  4) 🏆 RECORD MONEY EARNED"
echo "     → Log a completed job payment"
echo ""
echo "  5) 📊 VIEW STATUS"
echo "     → See pipeline and earnings"
echo ""
echo "  6) ❌ EXIT"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

read -p "Select (1-6): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting FULL MONEY CYCLE..."
        echo ""
        echo "⚠️  IMPORTANT: You need to be logged into Upwork"
        echo "   A browser will open. Log in if needed."
        echo ""
        read -p "Press Enter to continue..."
        python3 REAL_MONEY_ENGINE.py run
        ;;
    
    2)
        echo ""
        echo "🔍 Scraping Upwork for Python jobs..."
        python3 REAL_MONEY_ENGINE.py scrape
        ;;
    
    3)
        echo ""
        echo "💼 Available jobs to apply:"
        python3 << 'PYEOF'
import sqlite3
conn = sqlite3.connect('real_money.db')
c = conn.cursor()
c.execute("SELECT id, title, budget FROM opportunities WHERE status = 'new' LIMIT 10")
rows = c.fetchall()
for i, row in enumerate(rows, 1):
    print(f"  {i}. {row[0]} - {row[1][:40]}... ({row[2] or 'No budget'})")
conn.close()
PYEOF
        echo ""
        read -p "Enter job ID to apply: " job_id
        if [ -n "$job_id" ]; then
            python3 REAL_MONEY_ENGINE.py apply "$job_id"
        fi
        ;;
    
    4)
        echo ""
        echo "🏆 Record earnings"
        read -p "Job ID: " job_id
        read -p "Amount earned ($): " amount
        if [ -n "$job_id" ] && [ -n "$amount" ]; then
            python3 REAL_MONEY_ENGINE.py win "$job_id" "$amount"
        fi
        ;;
    
    5)
        echo ""
        python3 REAL_MONEY_ENGINE.py status
        ;;
    
    6)
        echo ""
        echo "Go make that money! 💪"
        exit 0
        ;;
    
    *)
        echo ""
        echo "Invalid option"
        ;;
esac

echo ""
read -p "Press Enter to return to menu..."
exec "$0"
