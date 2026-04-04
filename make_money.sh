#!/bin/bash
# MAKE MONEY - Simple launcher for MONEY_MAKER system
# Real job fetching, tailored proposals, revenue tracking

cd /home/asbelcas/rm-qpt

clear
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║   💰 MONEY MAKER - Real Freelance Income System                          ║"
echo "║                                                                          ║"
echo "║   NO SIMULATION • REAL JOBS • ACTUAL REVENUE TRACKING                    ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Show current stats
echo "📊 CURRENT STATUS:"
python3 MONEY_MAKER.py stats 2>/dev/null | grep -A 20 "MONEY DASHBOARD"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "OPTIONS:"
echo ""
echo "  1) 🚀 Run Full Money Cycle"
echo "     → Fetch real jobs, analyze matches, create checkpoints"
echo ""
echo "  2) 📊 View Dashboard"
echo "     → See stats, revenue, win rate"
echo ""
echo "  3) 🔍 Fetch Jobs Only"
echo "     → Just pull new jobs from sources"
echo ""
echo "  4) 🎯 Scrape Upwork (Browser)"
echo "     → Requires login - uses browser automation"
echo ""
echo "  5) 🏆 Record a Win"
echo "     → Log completed job and revenue"
echo ""
echo "  6) 📋 Review Checkpoints"
echo "     → Approve/reject pending submissions"
echo ""
echo "  7) ❌ Exit"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

read -p "Select option (1-7): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting full money cycle..."
        echo "This will fetch REAL jobs from:"
        echo "  • We Work Remotely"
        echo "  • RemoteOK"
        echo ""
        read -p "Include Upwork scraping? Requires browser login (y/n): " upwork
        if [ "$upwork" = "y" ]; then
            python3 MONEY_MAKER.py run 10 --upwork
        else
            python3 MONEY_MAKER.py run 10
        fi
        ;;
    
    2)
        echo ""
        python3 MONEY_MAKER.py stats
        ;;
    
    3)
        echo ""
        echo "🔍 Fetching fresh jobs..."
        python3 MONEY_MAKER.py fetch 10
        ;;
    
    4)
        echo ""
        echo "🎯 Scraping Upwork via browser..."
        echo "⚠️  You will need to log into Upwork manually"
        python3 MONEY_MAKER.py upwork
        ;;
    
    5)
        echo ""
        echo "🏆 Record a job win"
        read -p "Job ID (from database): " job_id
        read -p "Amount earned ($): " amount
        if [ -n "$job_id" ] && [ -n "$amount" ]; then
            python3 MONEY_MAKER.py win "$job_id" "$amount"
        else
            echo "❌ Job ID and amount required"
        fi
        ;;
    
    6)
        echo ""
        ./autoforge_checkpoint.sh
        ;;
    
    7)
        echo ""
        echo "Keep hustling! 💪"
        exit 0
        ;;
    
    *)
        echo ""
        echo "❌ Invalid option"
        ;;
esac

echo ""
read -p "Press Enter to return to menu..."

# Re-run the launcher
exec "$0"
