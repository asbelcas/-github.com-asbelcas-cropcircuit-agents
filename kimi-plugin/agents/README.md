# 🤖 Agent Team - Multi-Agent Decision System

A team of 3 AI agents that discuss and decide what to do next.

## The Agents

| Agent | Role | Color | Personality |
|-------|------|-------|-------------|
| **Executor** | Action-Oriented Implementer | 🟢 Green | "Ship it now. Done is better than perfect." |
| **Strategist** | Long-Term Vision | 🔵 Blue | "What happens next year? Is this sustainable?" |
| **Critic** | Risk Assessment | 🔴 Red | "What could go wrong? Let's verify first." |

## Quick Start

### Fast Mode (Parallel Voting) - 30-60 seconds
```bash
python3 kimi-plugin/agents/quick_decision.py "Your question here"

# Example:
python3 kimi-plugin/agents/quick_decision.py \
  "Should I focus on sales calls or code cleanup?"
```

### Discussion Mode (Multi-Round Conversation) - 2-4 minutes
```bash
python3 kimi-plugin/agents/team_orchestrator.py "Your context here"

# Example:
python3 kimi-plugin/agents/team_orchestrator.py \
  "We have $1000 budget. Should we spend it on ads or infrastructure?"
```

## How It Works

### Quick Decision Mode
1. All 3 agents vote simultaneously (parallel execution)
2. System analyzes votes for consensus
3. Returns winning action with confidence score

### Discussion Mode  
1. Each agent speaks in turns (multiple rounds)
2. They respond to each other's points
3. Final synthesis produces consensus decision

## Example Output

```
⚡ QUICK TEAM VOTE (Parallel)
Context: We have 3 pending tasks: LinkedIn profile update, 4 veterinary 
sales calls, and code review. Which should we do first?

✓ Executor voted (high confidence)
✓ Strategist voted (high confidence)  
✓ Critic voted (high confidence)

VOTES:

Executor (Action-Oriented)
  → Do the 4 veterinary sales calls first
  Confidence: high
  Why: Quick revenue win, builds momentum

Strategist (Long-Term Vision)
  → 4 veterinary sales calls
  Confidence: high
  Why: Revenue-generating activities first

Critic (Risk Assessment)
  → 4 veterinary sales calls
  Confidence: high
  Why: Sales calls have time sensitivity

ANALYZING CONSENSUS...

🎯 TEAM DECISION
Consensus: PARTIAL
Action: Make the 4 veterinary sales calls
Confidence: MEDIUM
Notes: 2/3 agents agreed

✅ RECOMMENDED NEXT STEP:
   Make the 4 veterinary sales calls
   
   Execute with:
   $ python3 kimi-plugin/scripts/kimi-companion.py task \"Make the 4 veterinary sales calls\"
```

## Use Cases

- **Prioritization**: "What should I work on first?"
- **Risk assessment**: "Should I launch this feature now?"
- **Resource allocation**: "Hire sales or engineering?"
- **Technical decisions**: "Refactor or rebuild?"
- **Business strategy**: "Focus on existing customers or new market?"

## State Storage

Conversations and decisions are saved to:
- `~/.kimi/kimi-plugin-state/team/conversation.jsonl`
- `~/.kimi/kimi-plugin-state/team/decisions.json`

View history:
```bash
python3 kimi-plugin/agents/team_orchestrator.py --history
```

## Architecture

```
Agent Team
├── Executor (action, momentum, speed)
├── Strategist (planning, sustainability, leverage)
└── Critic (risks, quality, verification)
    ↓
Consensus Analysis → Decision + Confidence
```

## Compared to Single-Agent

| Aspect | Single Agent | Agent Team |
|--------|--------------|------------|
| Perspectives | 1 | 3 (action + strategy + caution) |
| Blind spots | More likely | Cross-checked |
| Speed | Faster | Slower but more robust |
| Confidence | Single opinion | Measured consensus |
| Best for | Simple tasks | Complex decisions |
