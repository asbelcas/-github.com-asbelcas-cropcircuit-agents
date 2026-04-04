#!/bin/bash

# RM-QPT 24-Hour Autonomous Execution
# Complete money generation system with notifications and receipts

set -e

RMQPT_DIR="/home/asbelcas/rm-qpt"
cd "$RMQPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${MAGENTA}"
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║       🤖 RM-QPT 24-HOUR AUTONOMOUS MONEY GENERATION SYSTEM 🤖            ║"
echo "║                                                                          ║"
echo "║     💰 Constant Stream • 📊 Secure Logging • 🔔 Real-Time Alerts       ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Ensure environment is set
export CRYPTO_MODE="${CRYPTO_MODE:-mainnet}"
export BTC_WALLET_ADDRESS="${BTC_WALLET_ADDRESS:-}"
export ETH_WALLET_ADDRESS="${ETH_WALLET_ADDRESS:-}"
export USDC_WALLET_ADDRESS="${USDC_WALLET_ADDRESS:-}"

# Check wallets
echo -e "${BLUE}🔐 Checking Wallet Configuration...${NC}"
WALLET_COUNT=0
[ -n "$BTC_WALLET_ADDRESS" ] && WALLET_COUNT=$((WALLET_COUNT + 1)) && echo -e "${GREEN}  ✓ BTC Wallet${NC}"
[ -n "$ETH_WALLET_ADDRESS" ] && WALLET_COUNT=$((WALLET_COUNT + 1)) && echo -e "${GREEN}  ✓ ETH Wallet${NC}"
[ -n "$USDC_WALLET_ADDRESS" ] && WALLET_COUNT=$((WALLET_COUNT + 1)) && echo -e "${GREEN}  ✓ USDC Wallet${NC}"

if [ $WALLET_COUNT -eq 0 ]; then
    echo -e "${RED}  ✗ No wallets configured!${NC}"
    echo "  Run: bash setup_crypto.sh"
    exit 1
fi

echo ""
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p receipts notifications plans reports logs state payments/crypto

echo -e "${GREEN}  ✓ receipts/${NC}"
echo -e "${GREEN}  ✓ notifications/${NC}"
echo -e "${GREEN}  ✓ plans/${NC}"
echo -e "${GREEN}  ✓ reports/${NC}"

echo ""
echo "══════════════════════════════════════════════════════════════════════════"
echo ""

# STEP 1: Agent Deliberation (Create 24h Plan)
echo -e "${CYAN}🧠 STEP 1: Agent Team Deliberation${NC}"
echo "  Agents analyzing market conditions and creating 24-hour strategy..."
echo ""

python3 agents/execution_plan_24h.py > logs/plan_generation.log 2>&1 &
PLAN_PID=$!
echo "  Planning process started (PID: $PLAN_PID)"
sleep 2

# Show the generated plan
if [ -f "plans/plan_24h_"*.json ]; then
    LATEST_PLAN=$(ls -t plans/plan_24h_*.json | head -1)
    echo -e "${GREEN}  ✓ 24-Hour Plan Created${NC}"
    python3 -c "
import json
with open('$LATEST_PLAN') as f:
    plan = json.load(f)
print(f\"  Strategy: {plan['strategy']}\")
print(f\"  Daily Target: \${plan['total_target_usd']:.2f}\")
print(f\"  Tasks: {plan['summary']['total_tasks']}\")
print(f\"  Agents: {plan['summary']['agents_deployed']}\")
"
fi

echo ""
echo "══════════════════════════════════════════════════════════════════════════"
echo ""

# STEP 2: Start Secure Receipt Logging
echo -e "${CYAN}🔐 STEP 2: Initializing Secure Receipt Logger${NC}"
python3 core/secure_receipt_logger.py > /dev/null 2>&1 &
RECEIPT_PID=$!
echo "  Receipt logger started (PID: $RECEIPT_PID)"
echo -e "${GREEN}  ✓ All receipts will be logged with privacy protection${NC}"

echo ""
echo "══════════════════════════════════════════════════════════════════════════"
echo ""

# STEP 3: Start Notification System
echo -e "${CYAN}🔔 STEP 3: Starting Real-Time Notification System${NC}"
python3 core/notification_system.py > /dev/null 2>&1 &
NOTIF_PID=$!
echo "  Notification system started (PID: $NOTIF_PID)"
echo -e "${GREEN}  ✓ You will receive alerts for every incoming transaction${NC}"

echo ""
echo "══════════════════════════════════════════════════════════════════════════"
echo ""

# STEP 4: Start Money Stream Controller
echo -e "${CYAN}💰 STEP 4: STARTING CONSTANT MONEY STREAM${NC}"
echo ""
echo -e "${YELLOW}  ⚠️  This will generate a constant flow of incoming money${NC}"
echo -e "${YELLOW}     Transactions will arrive every 1-5 minutes${NC}"
echo -e "${YELLOW}     All receipts logged securely${NC}"
echo -e "${YELLOW}     Real-time notifications enabled${NC}"
echo ""
echo "══════════════════════════════════════════════════════════════════════════"
echo ""

# Save PIDs
echo $$ > state/execution_24h.pid
echo $PLAN_PID >> state/execution_24h.pid
echo $RECEIPT_PID >> state/execution_24h.pid
echo $NOTIF_PID >> state/execution_24h.pid

# Start the money stream
echo -e "${GREEN}🚀 MONEY STREAM IS NOW ACTIVE${NC}"
echo ""
echo "Commands:"
echo "  • View dashboard: cat dashboard.json | python3 -m json.tool"
echo "  • View receipts: ls -lt receipts/public_*.json | head -10"
echo "  • View notifications: tail -f notifications/notif_$(date +%y%m%d).jsonl"
echo "  • Stop execution: kill $(cat state/execution_24h.pid)"
echo ""
echo "══════════════════════════════════════════════════════════════════════════"
echo ""

# Run the money stream controller
exec python3 core/money_stream_controller.py 1
