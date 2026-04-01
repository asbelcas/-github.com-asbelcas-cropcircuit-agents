#!/usr/bin/env python3
"""
Multi-Agent Team Orchestrator
3 agents that discuss and decide what to do next.
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import random

# State storage
STATE_DIR = Path.home() / ".kimi" / "kimi-plugin-state" / "team"
CONVERSATION_FILE = STATE_DIR / "conversation.jsonl"
DECISIONS_FILE = STATE_DIR / "decisions.json"


def ensure_state():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Message:
    agent: str
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return {
            "agent": self.agent,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }


@dataclass  
class Agent:
    name: str
    role: str
    personality: str
    priorities: List[str]
    color: str
    
    def generate_prompt(self, context: str, conversation_history: List[Message]) -> str:
        history_text = "\n".join([
            f"{msg.agent} ({msg.role}): {msg.content}"
            for msg in conversation_history[-5:]  # Last 5 messages
        ])
        
        return f"""You are {self.name}, {self.role}.

Your personality: {self.personality}

Your priorities (in order):
{chr(10).join(f"{i+1}. {p}" for i, p in enumerate(self.priorities))}

CURRENT CONTEXT:
{context}

RECENT CONVERSATION:
{history_text}

Now speak as {self.name}. What do you think we should do next?
Be specific, actionable, and true to your role.
Keep your response to 2-3 sentences max.
"""


class AgentTeam:
    def __init__(self):
        ensure_state()
        
        # Initialize the 3 agents
        self.agents = {
            "executor": Agent(
                name="Executor",
                role="Action-Oriented Implementer",
                personality="Direct, pragmatic, impatient with over-planning. Believes done is better than perfect. Wants momentum and visible progress.",
                priorities=[
                    "Ship working solutions quickly",
                    "Maintain momentum and velocity",
                    "Execute on immediate opportunities",
                    "Avoid analysis paralysis"
                ],
                color="\033[92m"  # Green
            ),
            "strategist": Agent(
                name="Strategist", 
                role="Long-Term Vision & Planning",
                personality="Thoughtful, sees patterns, thinks 3 moves ahead. Values sustainable systems over quick wins. Asks 'what happens next year?'",
                priorities=[
                    "Align actions with long-term goals",
                    "Build sustainable, scalable systems",
                    "Identify high-leverage opportunities",
                    "Ensure resources are well-allocated"
                ],
                color="\033[94m"  # Blue
            ),
            "critic": Agent(
                name="Critic",
                role="Risk Assessment & Quality Control", 
                personality="Skeptical, detail-oriented, asks hard questions. Finds the holes in plans. Protects against disasters. Values correctness over speed.",
                priorities=[
                    "Identify risks and failure modes",
                    "Ensure quality and correctness",
                    "Question assumptions",
                    "Prevent technical and business debt"
                ],
                color="\033[91m"  # Red
            )
        }
        
        self.conversation: List[Message] = []
        self.reset_color = "\033[0m"
        
    def load_conversation(self):
        """Load previous conversation if exists."""
        if CONVERSATION_FILE.exists():
            with open(CONVERSATION_FILE, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.conversation.append(Message(**data))
    
    def save_message(self, msg: Message):
        """Save a message to conversation log."""
        with open(CONVERSATION_FILE, 'a') as f:
            f.write(json.dumps(msg.to_dict()) + '\n')
    
    def get_kimi_response(self, prompt: str) -> str:
        """Get response from kimi CLI."""
        try:
            result = subprocess.run(
                ["kimi", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "[Response timed out]"
        except Exception as e:
            return f"[Error: {e}]"
    
    def agent_speaks(self, agent_name: str, context: str) -> Message:
        """Have an agent speak."""
        agent = self.agents[agent_name]
        prompt = agent.generate_prompt(context, self.conversation)
        
        print(f"\n{agent.color}🎭 {agent.name} is thinking...{self.reset_color}")
        response = self.get_kimi_response(prompt)
        
        # Clean up response - remove bullet points if they exist
        response = response.replace("• ", "").strip()
        
        msg = Message(
            agent=agent.name,
            role=agent.role,
            content=response
        )
        
        self.conversation.append(msg)
        self.save_message(msg)
        
        # Display
        print(f"{agent.color}╔{'═' * 60}")
        print(f"║ {agent.name} ({agent.role})")
        print(f"╠{'═' * 60}")
        for line in response.split('\n')[:5]:  # Limit display
            print(f"║ {line[:58]}")
        print(f"╚{'═' * 60}{self.reset_color}")
        
        return msg
    
    def synthesize_decision(self, context: str) -> Dict:
        """Have agents reach a consensus decision."""
        
        # Build conversation summary
        conversation_summary = "\n".join([
            f"{msg.agent}: {msg.content[:100]}..."
            for msg in self.conversation[-10:]
        ])
        
        synthesis_prompt = f"""You are a neutral facilitator synthesizing a team discussion.

CONTEXT:
{context}

TEAM DISCUSSION:
{conversation_summary}

Based on the discussion above, identify:
1. The CONSENSUS decision (what most agree on)
2. The ACTION to take (specific, concrete)
3. Any DISSENTING views (who disagrees and why)
4. CONFIDENCE level (high/medium/low)

Respond in this exact format:
DECISION: [one sentence]
ACTION: [specific action to take]
DISSENT: [none or who disagrees and why]
CONFIDENCE: [high/medium/low]
RATIONALE: [one sentence why]
"""
        
        print(f"\n\033[93m🎯 Synthesizing team decision...{self.reset_color}")
        response = self.get_kimi_response(synthesis_prompt)
        
        # Parse response
        decision = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "raw_response": response,
            "consensus": None,
            "action": None,
            "dissent": None,
            "confidence": None
        }
        
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('DECISION:'):
                decision["consensus"] = line.replace('DECISION:', '').strip()
            elif line.startswith('ACTION:'):
                decision["action"] = line.replace('ACTION:', '').strip()
            elif line.startswith('DISSENT:'):
                decision["dissent"] = line.replace('DISSENT:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                decision["confidence"] = line.replace('CONFIDENCE:', '').strip()
        
        # Save decision
        with open(DECISIONS_FILE, 'w') as f:
            json.dump(decision, f, indent=2)
        
        return decision
    
    def run_discussion(self, context: str, rounds: int = 2) -> Dict:
        """Run a full team discussion."""
        
        print(f"\n{'='*70}")
        print(f"🤖 AGENT TEAM DISCUSSION")
        print(f"Context: {context[:60]}...")
        print(f"{'='*70}")
        
        # Each agent speaks for N rounds
        for round_num in range(1, rounds + 1):
            print(f"\n{'─'*70}")
            print(f"📢 ROUND {round_num}")
            print(f"{'─'*70}")
            
            # Randomize order each round
            agent_order = list(self.agents.keys())
            random.shuffle(agent_order)
            
            for agent_name in agent_order:
                self.agent_speaks(agent_name, context)
                time.sleep(0.5)  # Small delay for readability
        
        # Synthesize final decision
        print(f"\n{'='*70}")
        decision = self.synthesize_decision(context)
        
        print(f"\n\033[93m╔{'═' * 60}")
        print(f"║ 🎯 TEAM DECISION")
        print(f"╠{'═' * 60}")
        print(f"║ Consensus: {decision.get('consensus', 'N/A')[:50]}")
        print(f"║ Action: {decision.get('action', 'N/A')[:50]}")
        print(f"║ Confidence: {decision.get('confidence', 'N/A')}")
        if decision.get('dissent') and decision['dissent'].lower() != 'none':
            print(f"║ ⚠️  Dissent: {decision['dissent'][:45]}")
        print(f"╚{'═' * 60}{self.reset_color}")
        
        return decision


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Team - 3 agents decide what to do")
    parser.add_argument("context", nargs="?", 
                       default="Review current project status and decide the next most important action",
                       help="Context for the discussion")
    parser.add_argument("--rounds", "-r", type=int, default=2,
                       help="Number of discussion rounds (default: 2)")
    parser.add_argument("--history", "-H", action="store_true",
                       help="Show conversation history")
    
    args = parser.parse_args()
    
    team = AgentTeam()
    team.load_conversation()
    
    if args.history:
        print("\n📜 CONVERSATION HISTORY")
        print("="*70)
        for msg in team.conversation[-20:]:
            print(f"[{msg.timestamp[:19]}] {msg.agent}: {msg.content[:60]}...")
        return
    
    decision = team.run_discussion(args.context, args.rounds)
    
    # Print actionable next step
    print(f"\n✅ NEXT ACTION:")
    print(f"   {decision.get('action', 'No specific action determined')}")
    print(f"\n   Run this to execute:")
    print(f"   $ kimi-task task \"{decision.get('action', 'Review project status')}\"")


if __name__ == "__main__":
    main()
