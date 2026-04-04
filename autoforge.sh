#!/bin/bash
# AUTOFORGE-LITE - Main Launcher
# Provides easy menu interface for all AUTOFORGE functions

cd /home/asbelcas/rm-qpt

clear
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║   🤖  AUTOFORGE-LITE - Autonomous Freelancer System                      ║"
echo "║                                                                          ║"
echo "║   Safety-first automation for Upwork/Fiverr with human checkpoints       ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if there are pending checkpoints
PENDING_COUNT=$(find /home/asbelcas/rm-qpt/checkpoints -name "*.json" 2>/dev/null | wc -l)

# Show quick status
if [ -f "/home/asbelcas/rm-qpt/executor_state.json" ]; then
    STATUS=$(cat /home/asbelcas/rm-qpt/executor_state.json | grep -o '"status": "[^"]*"' | cut -d'"' -f4)
    echo "📊 System Status: $STATUS"
else
    echo "📊 System Status: IDLE"
fi
echo "📋 Pending Checkpoints: $PENDING_COUNT"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "MAIN OPTIONS:"
echo ""
echo "  1) 🚀 Run Full System (Browser + Checkpoints)"
echo "     → Runs pre-flight checks, stages jobs, waits for approval"
echo "     → RECOMMENDED for first-time use"
echo ""
echo "  2) 📋 View & Approve Checkpoints"
echo "     → Review pending submissions, approve/reject"
echo "     → Use this after running Option 1"
echo ""
echo "  3) 🔍 View Dashboard"
echo "     → System status, logs, quick stats"
echo ""
echo "  4) 🛡️  Run Safe Hybrid Mode"
echo "     → System drafts, you submit manually"
echo "     → Zero risk of account ban"
echo ""
echo "  5) 🧪 Test Browser Only"
echo "     → Initialize browser without submitting"
echo "     → Verify automation works on your system"
echo ""
echo "  6) 📖 View Documentation"
echo "     → Read full usage guide"
echo ""
echo "  7) ❌ Exit"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

read -p "Select option (1-7): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting AUTOFORGE-LITE Full System..."
        echo "This will:"
        echo "  1. Run comprehensive pre-flight checks"
        echo "  2. Stage job opportunities"
        echo "  3. Create checkpoints for your approval"
        echo ""
        read -p "Continue? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            python3 AUTOFORGE_EXECUTOR.py
        else
            echo "Cancelled."
        fi
        ;;
    
    2)
        echo ""
        echo "📋 Opening Checkpoint Manager..."
        ./autoforge_checkpoint.sh
        ;;
    
    3)
        echo ""
        echo "🔍 Opening Dashboard..."
        ./autoforge_dashboard.sh
        ;;
    
    4)
        echo ""
        echo "🛡️  Starting Hybrid Mode..."
        echo "In this mode, the system will:"
        echo "  1. Draft proposals"
        echo "  2. Open job pages in browser"
        echo "  3. You copy/paste and submit manually"
        echo ""
        echo "This is the SAFEST mode - zero automation risk."
        echo ""
        read -p "Continue? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            python3 AUTOFORGE_HYBRID.py
        else
            echo "Cancelled."
        fi
        ;;
    
    5)
        echo ""
        echo "🧪 Testing Browser Initialization..."
        python3 -c "
import sys
sys.path.insert(0, '/home/asbelcas/rm-qpt')
from AUTOFORGE_BROWSER_V2 import FailureResistantBrowser

print('Initializing browser...')
browser = FailureResistantBrowser('upwork')
if browser._init_driver():
    print('✅ Browser initialized successfully!')
    print('Browser will stay open for 10 seconds...')
    import time
    time.sleep(10)
    browser.close()
    print('✅ Test complete')
else:
    print('❌ Browser initialization failed')
    sys.exit(1)
"
        ;;
    
    6)
        echo ""
        echo "📖 Opening documentation..."
        if command -v less &> /dev/null; then
            less README_AUTOFORGE_LITE.md
        else
            cat README_AUTOFORGE_LITE.md
        fi
        ;;
    
    7)
        echo ""
        echo "Goodbye!"
        exit 0
        ;;
    
    *)
        echo ""
        echo "❌ Invalid option. Please select 1-7."
        ;;
esac

echo ""
read -p "Press Enter to return to menu..."

# Re-run the launcher
exec "$0"
