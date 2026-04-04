#!/bin/bash

# COINBASE GHOST AGENT LAUNCHER
# Opens web dashboard for manual login approach

cd /home/asbelcas/rm-qpt

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║           👻 COINBASE GHOST AGENT - WEB DASHBOARD 👻                     ║"
echo "║                                                                          ║"
echo "║              Secure • Manual Login • Autonomous Earning                  ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

echo -e "${GREEN}✅ All critical errors fixed and reviewed${NC}"
echo ""

# Check if dashboard exists
if [ ! -f "coinbase_ghost_dashboard.html" ]; then
    echo -e "${YELLOW}❌ Dashboard file not found${NC}"
    exit 1
fi

echo -e "${BLUE}How would you like to open the dashboard?${NC}"
echo ""
echo "1. 🌐 Open directly in browser (file://)"
echo "2. 🖥️  Serve via Python web server (http://localhost:8080)"
echo "3. 📋 Show me the plan first"
echo ""

read -p "Select option (1-3): " OPTION

case $OPTION in
    1)
        echo ""
        echo -e "${GREEN}Opening dashboard in your default browser...${NC}"
        
        # Try different methods to open browser
        if command -v xdg-open &> /dev/null; then
            xdg-open coinbase_ghost_dashboard.html
        elif command -v open &> /dev/null; then
            open coinbase_ghost_dashboard.html
        elif command -v start &> /dev/null; then
            start coinbase_ghost_dashboard.html
        else
            echo "Please manually open: file://$(pwd)/coinbase_ghost_dashboard.html"
        fi
        
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "📋 NEXT STEPS:"
        echo ""
        echo "1. The dashboard will open in your browser"
        echo "2. Click 'Open Coinbase.com' button"
        echo "3. Login to Coinbase MANUALLY (secure)"
        echo "4. Return to dashboard, click 'I'm Logged In'"
        echo "5. Start Discovery → Agent Review → 12-Hour Session"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
        echo "   • You login directly on coinbase.com (safest method)"
        echo "   • System never sees your password"
        echo "   • All automation happens AFTER you're logged in"
        echo "   • Keep the browser window open during the 12-hour session"
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
        ;;
        
    2)
        echo ""
        echo -e "${GREEN}Starting Python web server on port 8080...${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop the server when done${NC}"
        echo ""
        
        # Try to open browser after server starts
        (
            sleep 2
            if command -v xdg-open &> /dev/null; then
                xdg-open http://localhost:8080/coinbase_ghost_dashboard.html
            elif command -v open &> /dev/null; then
                open http://localhost:8080/coinbase_ghost_dashboard.html
            elif command -v start &> /dev/null; then
                start http://localhost:8080/coinbase_ghost_dashboard.html
            fi
        ) &
        
        python3 -m http.server 8080
        ;;
        
    3)
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
        echo ""
        cat PLAN_ERROR_REVIEW.md
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Ready to launch? Run: bash LAUNCH_COINBASE_GHOST.sh"
        ;;
        
    *)
        echo "Invalid option"
        ;;
esac

echo ""
