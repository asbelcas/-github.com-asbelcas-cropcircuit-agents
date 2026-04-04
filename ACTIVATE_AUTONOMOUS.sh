#!/bin/bash
# RM-QPT AUTONOMOUS ACTIVATION
# Self-directing, self-improving, continuous money-making system

set -e

RMQPT_DIR="/home/asbelcas/rm-qpt"
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$RMQPT_DIR"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║     🤖 RM-QPT AUTONOMOUS: SELF-DIRECTING MONEY MAKERS 🤖         ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

echo -e "${YELLOW}⚠️  AUTONOMOUS OPERATION CONFIRMATION${NC}"
echo ""
echo "This system operates COMPLETELY WITHOUT HUMAN INTERVENTION:"
echo ""
echo "  ✅ Agents search internet continuously for new money-making methods"
echo "  ✅ Agents deliberate as a team to decide what to do next"
echo "  ✅ Agents experiment autonomously and document outcomes"
echo "  ✅ Agents learn from successes AND failures continuously"
echo "  ✅ Agents adapt strategies based on results"
echo "  ✅ NO HUMAN CHECKPOINTS OR APPROVALS REQUIRED"
echo "  ✅ System runs 24/7 making decisions independently"
echo ""
echo "The agent swarm will:"
echo "  • Research new arbitrage opportunities"
echo "  • Test digital product ideas"
echo "  • Experiment with pricing strategies"
echo "  • Build automated revenue systems"
echo "  • Document everything they learn"
echo "  • Share knowledge across the team"
echo "  • Double down on what works"
echo "  • Abandon what doesn't"
echo ""
echo "You do NOT need to check in or approve decisions."
echo "The agents are fully autonomous and self-directing."
echo ""
read -p "Activate autonomous agent swarm? (yes/no): " confirm

if [[ $confirm != "yes" ]]; then
    echo ""
    echo -e "${RED}❌ Autonomous activation cancelled${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ AUTONOMOUS OPERATION CONFIRMED${NC}"
echo ""

# Setup directories
echo -e "${BLUE}🔧 Setting up autonomous environment...${NC}"
mkdir -p experiments ideas deliberations

# Check core file
if [[ ! -f "core/autonomous_orchestrator.py" ]]; then
    echo -e "${RED}✗ Autonomous orchestrator not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Autonomous core ready${NC}"
echo ""

# Launch
echo -e "${CYAN}══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}🚀 LAUNCHING AUTONOMOUS AGENT SWARM${NC}"
echo ""
echo "The agents are now:"
echo "  🔍 Searching the internet for money-making opportunities"
echo "  🗳️  Deliberating as a team on next actions"
echo "  🧪 Running experiments autonomously"
echo "  📚 Documenting and learning continuously"
echo "  💰 Making money without your involvement"
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════════${NC}"
echo ""

python3 core/autonomous_orchestrator.py &
PID=$!
echo $PID > state/autonomous.pid

echo -e "${GREEN}✅ AUTONOMOUS SWARM ACTIVE (PID: $PID)${NC}"
echo ""
echo "What the agents are doing:"
echo ""

# Show initial activity
sleep 3

if [[ -f "logs/autonomous_$(date +%Y%m%d).jsonl" ]]; then
    echo "Recent agent activity:"
    tail -10 "logs/autonomous_$(date +%Y%m%d).jsonl" 2>/dev/null | grep -E "(AGENT|IDEA|DELIBERATION|EXPERIMENT)" | tail -5 || echo "  (Agents initializing...)"
fi

echo ""
echo "Monitor agent activity:"
echo "  tail -f $RMQPT_DIR/logs/autonomous_*.jsonl"
echo ""
echo "View discovered ideas:"
echo "  ls -la $RMQPT_DIR/ideas/"
echo ""
echo "View deliberations:"
echo "  ls -la $RMQPT_DIR/deliberations/"
echo ""
echo "View experiments:"
echo "  ls -la $RMQPT_DIR/experiments/"
echo ""
echo -e "${YELLOW}⚠️  The agents are now fully autonomous.${NC}"
echo -e "${YELLOW}    They will make decisions, experiment, and adapt without you.${NC}"
echo ""
echo -e "${GREEN}💰 Let the agents work. They'll find ways to make money. 💰${NC}"
echo ""
