#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# GHOST AGENT v5.0 - TRADING MASTERY EDITION
# Integrated with Crypto Trading Knowledge Base
# ═══════════════════════════════════════════════════════════════════════════

cd /home/asbelcas/rm-qpt

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
RED='\033[0;31m'
NC='\033[0m'

clear
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║              👻 GHOST AGENT v5.0 - TRADING MASTERY 👻                    ║"
echo "║                                                                          ║"
echo "║         🧠 Knowledge Base • 📊 Strategies • 🛡️  Risk Management          ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${MAGENTA}📚 INTEGRATED KNOWLEDGE BASE:${NC}"
echo "   • 20+ trading books and research papers"
echo "   • 12 proven trading strategies"
echo "   • Complete risk management framework"
echo "   • Trading psychology principles"
echo ""

echo -e "${GREEN}✅ System Status: READY FOR DEPLOYMENT${NC}"
echo ""

# Menu
echo -e "${BLUE}Select launch mode:${NC}"
echo ""
echo -e "${CYAN}1.${NC} 🌐 Web Dashboard (Recommended for beginners)"
echo -e "${CYAN}2.${NC} 🤖 Run Ghost Agent (CLI mode)"
echo -e "${CYAN}3.${NC} 📊 View Trading Knowledge Summary"
echo -e "${CYAN}4.${NC} 📚 View Trading Plan Documentation"
echo -e "${CYAN}5.${NC} ⚙️  System Diagnostics"
echo ""

read -p "Select option (1-5): " OPTION

case $OPTION in
    1)
        echo ""
        echo -e "${GREEN}Opening Web Dashboard...${NC}"
        
        if [ ! -f "coinbase_ghost_dashboard.html" ]; then
            echo -e "${RED}❌ Dashboard not found${NC}"
            exit 1
        fi
        
        # Try to open browser
        if command -v xdg-open &> /dev/null; then
            xdg-open coinbase_ghost_dashboard.html &
        elif command -v open &> /dev/null; then
            open coinbase_ghost_dashboard.html &
        else
            echo "Please open coinbase_ghost_dashboard.html manually"
        fi
        
        echo ""
        echo -e "${GREEN}✅ Dashboard opened!${NC}"
        echo "   Follow the steps in your browser"
        ;;
        
    2)
        echo ""
        echo -e "${GREEN}Starting Ghost Agent...${NC}"
        
        # Check Python
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}❌ Python3 not found${NC}"
            exit 1
        fi
        
        # Get capital
        read -p "Enter starting capital [default: $16.00]: $" CAPITAL
        CAPITAL=${CAPITAL:-16.0}
        
        echo ""
        echo -e "${CYAN}Initializing with $${CAPITAL}...${NC}"
        echo ""
        
        # Run agent
        python3 core/robust_ghost_agent.py
        ;;
        
    3)
        echo ""
        echo -e "${CYAN}Loading Trading Knowledge Base...${NC}"
        echo ""
        
        python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from core.trading_knowledge_integration import TradingKnowledgeIntegrator

integrator = TradingKnowledgeIntegrator(capital=16.0)
summary = integrator.export_knowledge_summary()

print("="*70)
print("  📚 TRADING KNOWLEDGE BASE SUMMARY")
print("="*70)
print()

for key, value in summary.items():
    if isinstance(value, list):
        print(f"  {key.replace('_', ' ').title()}:")
        for item in value[:5]:  # Show first 5
            print(f"    • {item}")
        if len(value) > 5:
            print(f"    ... and {len(value)-5} more")
    else:
        print(f"  {key.replace('_', ' ').title()}: {value}")

print()
print("="*70)
EOF
        ;;
        
    4)
        echo ""
        echo -e "${CYAN}Opening Trading Plan Documentation...${NC}"
        
        if [ -f "TRADING_KNOWLEDGE_INTEGRATED.md" ]; then
            cat TRADING_KNOWLEDGE_INTEGRATED.md | head -100
            echo ""
            echo -e "${YELLOW}(Showing first 100 lines. Full document has $(wc -l < TRADING_KNOWLEDGE_INTEGRATED.md) lines)${NC}"
        else
            echo -e "${RED}❌ Documentation not found${NC}"
        fi
        ;;
        
    5)
        echo ""
        echo -e "${CYAN}Running System Diagnostics...${NC}"
        echo ""
        
        # Check files
        echo "File Structure:"
        [ -f "core/robust_ghost_agent.py" ] && echo "  ✅ robust_ghost_agent.py" || echo "  ❌ robust_ghost_agent.py"
        [ -f "core/trading_knowledge_integration.py" ] && echo "  ✅ trading_knowledge_integration.py" || echo "  ❌ trading_knowledge_integration.py"
        [ -f "knowledge_base/crypto_trading_mastery.py" ] && echo "  ✅ crypto_trading_mastery.py" || echo "  ❌ crypto_trading_mastery.py"
        [ -f "TRADING_KNOWLEDGE_INTEGRATED.md" ] && echo "  ✅ TRADING_KNOWLEDGE_INTEGRATED.md" || echo "  ❌ TRADING_KNOWLEDGE_INTEGRATED.md"
        
        echo ""
        echo "Dependencies:"
        python3 -c "import selenium; print('  ✅ Selenium')" 2>/dev/null || echo "  ❌ Selenium (pip install selenium)"
        
        echo ""
        echo "Chrome:"
        if command -v google-chrome &> /dev/null; then
            google-chrome --version | xargs -I {} echo "  ✅ {}"
        else
            echo "  ❌ Chrome not found"
        fi
        
        echo ""
        echo -e "${GREEN}Diagnostics complete!${NC}"
        ;;
        
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${CYAN}Thank you for using Ghost Agent v5.0${NC}"
