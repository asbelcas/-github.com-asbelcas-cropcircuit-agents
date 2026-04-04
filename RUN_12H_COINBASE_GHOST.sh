#!/bin/bash

# RM-QPT COINBASE GHOST AGENT
# 12-Hour Autonomous Sessions

cd /home/asbelcas/rm-qpt

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m'

echo -e "${MAGENTA}"
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║           👻 COINBASE GHOST AGENT v4.0 👻                                ║"
echo "║                                                                          ║"
echo "║     12-Hour Autonomous Sessions • Full Feature Discovery                ║"
echo "║     Ghost in the Machine • Agent Team Evaluation                        ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check dependencies
echo -e "${BLUE}🔧 Checking System...${NC}"

python3 -c "import selenium" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Selenium installed${NC}"
else
    echo -e "${YELLOW}  ⚠ Installing Selenium...${NC}"
    pip install -q selenium webdriver-manager pyotp requests
fi

# Create directories
mkdir -p logs sessions screenshots

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check for credentials
if [ ! -f ~/.rm-qpt/coinbase_credentials.json ]; then
    echo -e "${YELLOW}🔐 COINBASE CREDENTIALS REQUIRED${NC}"
    echo ""
    echo "The Ghost Agent needs your Coinbase login to:"
    echo "  • Discover all earning opportunities"
    echo "  • Execute Learn & Earn lessons"
    echo "  • Enable staking"
    echo "  • Optimize your portfolio"
    echo ""
    
    read -p "Coinbase Email: " CB_EMAIL
    read -s -p "Coinbase Password: " CB_PASSWORD
    echo ""
    read -p "2FA Secret (optional): " CB_TOTP
    echo ""
    
    # Save credentials
    mkdir -p ~/.rm-qpt
    cat > ~/.rm-qpt/coinbase_credentials.json << EOF
{
  "email": "$CB_EMAIL",
  "password": "$CB_PASSWORD",
  "totp_secret": "$CB_TOTP",
  "updated_at": "$(date -Iseconds)"
}
EOF
    chmod 600 ~/.rm-qpt/coinbase_credentials.json
    echo -e "${GREEN}✅ Credentials saved securely${NC}"
    echo ""
fi

# Menu
echo -e "${WHITE}SELECT OPERATION MODE:${NC}"
echo ""
echo "1. 🚀 START 12-HOUR SESSION"
echo "   • Full autonomous operation"
echo "   • Discovers ALL Coinbase features"
echo "   • Executes highest-priority opportunities"
echo "   • Saves detailed session report"
echo ""
echo "2. 🔍 DISCOVERY ONLY (30 min)"
echo "   • Scans all Coinbase features"
echo "   • Lists ALL opportunities"
echo "   • Agent team evaluation"
echo "   • No execution (preview mode)"
echo ""
echo "3. 📊 VIEW PREVIOUS SESSION"
echo "   • Shows last 12-hour results"
echo "   • Displays earnings breakdown"
echo "   • Reviews executed actions"
echo ""
echo "4. ⚙️  CONFIGURATION"
echo "   • Update credentials"
echo "   • Set safety limits"
echo "   • Configure notifications"
echo ""

read -p "Select mode (1-4): " MODE

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

case $MODE in
    1)
        echo -e "${GREEN}🚀 STARTING 12-HOUR AUTONOMOUS SESSION${NC}"
        echo ""
        echo "The Ghost Agent will:"
        echo "  • Log into your Coinbase"
        echo "  • Scan ALL features (Learn & Earn, Staking, etc.)"
        echo "  • Evaluate opportunities with Agent Team"
        echo "  • Execute highest-priority actions"
        echo "  • Run continuously for 12 hours"
        echo "  • Save detailed results"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
        echo "  • Keep your computer ON"
        echo "  • Don't close the browser window"
        echo "  • Check results after 12 hours"
        echo "  • You can stop anytime with Ctrl+C"
        echo ""
        read -p "Press Enter to start..."
        echo ""
        
        # Set environment
        export CRYPTO_MODE="mainnet"
        export BTC_WALLET_ADDRESS="1yQdHkfK3FRh2ChqMGdWcrxjqhtqbz4v2"
        export ETH_WALLET_ADDRESS="0x0D4c35BA7BcC639EfDC36e5e1102aaC3519E06b3"
        export USDC_WALLET_ADDRESS="0xa75Fd66FFd702987c892CAF3E9D894D0CC7a02d6"
        
        # Run the ghost agent
        echo -e "${CYAN}👻 Ghost Agent activating...${NC}"
        echo ""
        
        python3 core/coinbase_automation_system.py 2>&1 | tee logs/coinbase_session_$(date +%y%m%d_%H%M).log
        
        echo ""
        echo -e "${GREEN}✅ 12-Hour Session Complete!${NC}"
        echo ""
        echo "Results saved to:"
        ls -t coinbase_session_*.json | head -1
        echo ""
        echo "Log saved to:"
        ls -t logs/coinbase_session_*.log | head -1
        ;;
        
    2)
        echo -e "${GREEN}🔍 RUNNING DISCOVERY MODE${NC}"
        echo ""
        echo "This will scan your Coinbase and show all opportunities"
        echo "without executing anything."
        echo ""
        
        python3 << 'PYEOF'
import json
import sys
sys.path.insert(0, 'core')

# Import and run discovery
from coinbase_automation_system import CoinbaseGhostAgent

agent = CoinbaseGhostAgent(headless=False)

# Login
if agent.login():
    # Just discover, don't execute
    opportunities = agent.discover_all_opportunities()
    
    print("\n" + "="*80)
    print("  DISCOVERY COMPLETE - OPPORTUNITY SUMMARY")
    print("="*80)
    
    total_potential = sum(o.reward_amount for o in opportunities)
    total_time = sum(o.time_required for o in opportunities)
    
    print(f"\n  Total Opportunities: {len(opportunities)}")
    print(f"  Total Potential Value: ${total_potential:.2f}")
    print(f"  Total Time Required: {total_time} minutes")
    print(f"  Average Priority Score: {sum(o.priority_score for o in opportunities) / len(opportunities):.1f}")
    
    # Group by feature
    by_feature = {}
    for opp in opportunities:
        feature = opp.feature.value
        if feature not in by_feature:
            by_feature[feature] = []
        by_feature[feature].append(opp)
    
    print("\n  By Feature:")
    for feature, opps in sorted(by_feature.items(), key=lambda x: sum(o.priority_score for o in x[1]), reverse=True):
        total = sum(o.reward_amount for o in opps)
        print(f"    {feature}: {len(opps)} opportunities, ${total:.2f} potential")
    
    print("\n" + "="*80)
    print("  Run mode 1 (12-hour session) to execute these opportunities")
    print("="*80)
    
    # Save discovery results
    results = {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "mode": "discovery",
        "opportunities_count": len(opportunities),
        "total_potential": total_potential,
        "total_time": total_time,
        "opportunities": [{
            "id": o.opp_id,
            "feature": o.feature.value,
            "title": o.title,
            "reward": o.reward_amount,
            "time": o.time_required,
            "priority": o.priority_score
        } for o in opportunities]
    }
    
    with open(f"discovery_{__import__('datetime').datetime.now().strftime('%y%m%d_%H%M')}.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    agent.stop()
else:
    print("❌ Login failed")
PYEOF
        ;;
        
    3)
        echo -e "${GREEN}📊 VIEWING PREVIOUS SESSION${NC}"
        echo ""
        
        # Find most recent session file
        LATEST_SESSION=$(ls -t coinbase_session_*.json 2>/dev/null | head -1)
        
        if [ -n "$LATEST_SESSION" ]; then
            echo "Loading: $LATEST_SESSION"
            echo ""
            
            python3 << PYEOF
import json

with open('$LATEST_SESSION') as f:
    data = json.load(f)

print("="*80)
print("  SESSION RESULTS")
print("="*80)
print(f"\n  Session Start: {data.get('session_start', 'Unknown')}")
print(f"  Session End: {data.get('session_end', 'Unknown')}")
print(f"  Duration: {data.get('duration_hours', 12)} hours")
print(f"\n  💰 TOTAL EARNINGS: \${data.get('total_earnings', 0):.2f}")
print(f"  🎯 Actions Executed: {data.get('actions_count', 0)}")
print(f"  ✅ Opportunities Completed: {data.get('opportunities_executed', 0)}")

opportunities = data.get('opportunities', [])
executed = [o for o in opportunities if o.get('executed')]

print(f"\n  Successful Executions:")
for opp in executed[:10]:
    print(f"    ✓ {opp.get('title', 'Unknown')}: \${opp.get('reward_amount', 0):.2f}")

print("\n" + "="*80)
PYEOF
        else
            echo "❌ No previous session found"
            echo "   Run a session first (option 1)"
        fi
        ;;
        
    4)
        echo -e "${GREEN}⚙️  CONFIGURATION${NC}"
        echo ""
        echo "1. Update Coinbase Credentials"
        echo "2. Set Safety Limits"
        echo "3. Back"
        echo ""
        read -p "Select (1-3): " CONFIG_MODE
        
        case $CONFIG_MODE in
            1)
                echo ""
                read -p "New Coinbase Email: " NEW_EMAIL
                read -s -p "New Coinbase Password: " NEW_PASS
                echo ""
                read -p "New 2FA Secret (optional): " NEW_TOTP
                
                cat > ~/.rm-qpt/coinbase_credentials.json << EOF
{
  "email": "$NEW_EMAIL",
  "password": "$NEW_PASS",
  "totp_secret": "$NEW_TOTP",
  "updated_at": "$(date -Iseconds)"
}
EOF
                chmod 600 ~/.rm-qpt/coinbase_credentials.json
                echo -e "${GREEN}✅ Credentials updated${NC}"
                ;;
            2)
                echo ""
                echo "Safety Limits:"
                echo "  • Max transaction: $50"
                echo "  • Require confirmation: Can be enabled"
                echo "  • Session timeout: 12 hours"
                echo ""
                echo "Edit core/coinbase_automation_system.py to change limits"
                ;;
        esac
        ;;
        
    *)
        echo "Invalid selection"
        ;;
esac

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}System ready for next 12-hour session.${NC}"
echo ""
echo "Quick commands:"
echo "  bash RUN_12H_COINBASE_GHOST.sh  # Start new session"
echo "  ls -t coinbase_session_*.json   # View session files"
echo "  tail -f logs/coinbase_*.log     # Watch live log"
echo ""
