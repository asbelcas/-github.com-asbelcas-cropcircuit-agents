#!/bin/bash
# MONEY_NOW - The only script you need to make money
# Cut through all the staging and simulation

cd /home/asbelcas/rm-qpt

while true; do
    clear
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                          ║"
    echo "║   💰 MONEY NOW - Zero BS Income Generator                                ║"
    echo "║                                                                          ║"
    echo "║   ⚡ FASTEST PATH: Manual Upwork + AI Proposals                          ║"
    echo "║                                                                          ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Show current earnings
    python3 << 'PYEOF' 2>/dev/null
import sqlite3
try:
    conn = sqlite3.connect('emergency_money.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(status='applied'), SUM(status='won'), SUM(result_amount) FROM leads")
    total, applied, won, earnings = c.fetchone()
    earnings = earnings or 0
    print(f"📊 Current Stats: {total or 0} tracked | {applied or 0} applied | {won or 0} won | 💵 ${earnings:.2f} earned")
    conn.close()
except:
    print("📊 No data yet - Let's make some money!")
PYEOF
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "🚀 I WANT TO:"
    echo ""
    echo "  1) MAKE MONEY NOW (Recommended)"
    echo "     → Browse Upwork → Get proposals → Submit → Track earnings"
    echo ""
    echo "  2) Scrape Upwork automatically (Slower, may need login)"
    echo "     → Use browser automation to find Python jobs"
    echo ""
    echo "  3) Record money I earned"
    echo "     → Log a completed job payment"
    echo ""
    echo "  4) View all tracked jobs"
    echo ""
    echo "  5) Exit"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""
    
    read -p "Select (1-5): " choice
    
    case $choice in
        1)
            python3 EMERGENCY_MONEY_MODE.py
            ;;
        2)
            python3 REAL_MONEY_ENGINE.py run
            ;;
        3)
            python3 EMERGENCY_MONEY_MODE.py 3
            ;;
        4)
            python3 EMERGENCY_MONEY_MODE.py 4
            ;;
        5)
            echo ""
            echo "💪 Go make that money!"
            exit 0
            ;;
        *)
            echo "Invalid option"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
