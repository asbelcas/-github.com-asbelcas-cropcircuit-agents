#!/bin/bash
# RM-QPT ACTIVATION SCRIPT
# Relentless Money-Making & Quality Performance Taskforce

set -e

RMQPT_DIR="/home/asbelcas/rm-qpt"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║           💰 RM-QPT ACTIVATION SEQUENCE 💰                       ║"
echo "║                                                                  ║"
echo "║     RELENTLESS MONEY-MAKING & QUALITY PERFORMANCE TASKFORCE      ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

cd "$RMQPT_DIR"

# PRIME DIRECTIVE CONFIRMATION
echo -e "${YELLOW}⚠️  PRIME DIRECTIVE CONFIRMATION${NC}"
echo ""
echo "RM-QPT operates under these absolute rules:"
echo ""
echo "  1. 💰 MONEY MUST FLOW CONTINUOUSLY"
echo "  2. 🚨 2+ hours without money = CRITICAL FAILURE"
echo "  3. 📊 Reassess every 2 hours automatically"
echo "  4. 📚 If stuck: Learn from business books & syllabuses"
echo "  5. 💳 All money deposits to crypto wallet (BTC/ETH/USDC)"
echo "  6. ♾️  Once first money made: NEVER STOP"
echo ""
read -p "Do you accept the PRIME DIRECTIVE? (yes/no): " confirm

if [[ $confirm != "yes" ]]; then
    echo ""
    echo -e "${RED}❌ RM-QPT requires acceptance of PRIME DIRECTIVE${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ PRIME DIRECTIVE ACCEPTED${NC}"
echo ""

# System checks
echo -e "${BLUE}🔧 System Checks...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python3 available${NC}"

# Check directories
for dir in core agents monetization learning payments logs state; do
    if [[ -d "$dir" ]]; then
        echo -e "${GREEN}✓ $dir/${NC}"
    else
        mkdir -p "$dir"
        echo -e "${YELLOW}⚠ Created $dir/${NC}"
    fi
done

# Check core file
if [[ -f "core/rm_qpt_master.py" ]]; then
    echo -e "${GREEN}✓ RM-QPT Master Core${NC}"
else
    echo -e "${RED}✗ RM-QPT Master not found${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}💰 Initializing Money Tracking...${NC}"

# Initialize state if not exists
if [[ ! -f "state/rm_qpt_state.json" ]]; then
    cat > state/rm_qpt_state.json << 'EOF'
{
  "system": "RM-QPT",
  "timestamp": "",
  "total_earned": 0.0,
  "first_money_made": false,
  "continuous_operation_required": false,
  "last_money_timestamp": null,
  "next_checkpoint": "",
  "stats": {
    "tasks_created": 0,
    "tasks_completed": 0,
    "money_attempts": 0,
    "money_successful": 0,
    "total_revenue": 0.0,
    "crypto_deposited": 0.0,
    "checkpoints_passed": 0,
    "critical_failures": 0,
    "recoveries": 0,
    "learning_sessions": 0
  },
  "transactions": [],
  "checkpoints": []
}
EOF
    echo -e "${GREEN}✓ Money tracking initialized${NC}"
fi

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}🚀 LAUNCHING RM-QPT${NC}"
echo ""
echo "Configuration:"
echo "  • Checkpoint Interval: 2 hours"
echo "  • Critical Threshold: 2 hours without money"
echo "  • Crypto Deposit: BTC/ETH/USDC wallets"
echo "  • Mode: CONTINUOUS (never stops after first money)"
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════════${NC}"
echo ""

# Launch RM-QPT
python3 core/rm_qpt_master.py &
RMQPT_PID=$!

echo $RMQPT_PID > state/rm_qpt.pid

echo -e "${GREEN}✅ RM-QPT ACTIVE (PID: $RMQPT_PID)${NC}"
echo ""
echo "Monitoring:"
echo "  tail -f $RMQPT_DIR/logs/rm_qpt_*.jsonl"
echo ""
echo "Status Check:"
echo "  cat $RMQPT_DIR/state/rm_qpt_state.json | python3 -m json.tool"
echo ""
echo -e "${YELLOW}⚠️  RM-QPT is now hunting for money. DO NOT STOP until mission complete.${NC}"
echo ""

# Keep script running to show status
sleep 2

echo "Initial Status:"
if [[ -f "state/rm_qpt_state.json" ]]; then
    python3 -c "
import json
with open('state/rm_qpt_state.json') as f:
    state = json.load(f)
print(f\"  Total Earned: \${state.get('total_earned', 0):.2f}\")
print(f\"  First Money Made: {state.get('first_money_made', False)}\")
print(f\"  Checkpoints Passed: {state.get('stats', {}).get('checkpoints_passed', 0)}\")
"
fi

echo ""
echo -e "${GREEN}💰 RM-QPT IS NOW ACTIVE AND HUNTING FOR MONEY 💰${NC}"
echo ""
