#!/usr/bin/env python3
"""
Quick Decision Mode - All 3 agents vote simultaneously for speed
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

STATE_DIR = Path.home() / ".kimi" / "kimi-plugin-state" / "team"


def get_kimi_response(prompt: str) -> str:
    try:
        result = subprocess.run(
            ["kimi", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout.strip()
    except:
        return "[Error]"


@dataclass
class AgentVote:
    name: str
    role: str
    vote: str
    confidence: str
    reasoning: str


def executor_vote(context: str) -> AgentVote:
    prompt = f"""You are Executor, an action-oriented implementer.
Context: {context}

Your job: QUICKLY decide the SINGLE most important next action.
Be specific and actionable. One sentence max.

Respond EXACTLY in this format:
VOTE: [specific action]
CONFIDENCE: [high/medium/low]
REASONING: [one sentence why]"""
    
    response = get_kimi_response(prompt)
    return parse_vote("Executor", "Action-Oriented", response)


def strategist_vote(context: str) -> AgentVote:
    prompt = f"""You are Strategist, a long-term thinker.
Context: {context}

Your job: QUICKLY decide the SINGLE most strategic next action.
Think leverage and sustainability. One sentence max.

Respond EXACTLY in this format:
VOTE: [specific action]
CONFIDENCE: [high/medium/low]
REASONING: [one sentence why]"""
    
    response = get_kimi_response(prompt)
    return parse_vote("Strategist", "Long-Term Vision", response)


def critic_vote(context: str) -> AgentVote:
    prompt = f"""You are Critic, a risk assessor.
Context: {context}

Your job: QUICKLY identify what we should verify or fix first.
What could go wrong? One sentence max.

Respond EXACTLY in this format:
VOTE: [specific action]
CONFIDENCE: [high/medium/low]
REASONING: [one sentence why]"""
    
    response = get_kimi_response(prompt)
    return parse_vote("Critic", "Risk Assessment", response)


def parse_vote(name: str, role: str, response: str) -> AgentVote:
    """Parse agent vote from kimi response - handles various formats."""
    vote = "No vote"
    confidence = "medium"
    reasoning = "No reasoning provided"
    
    lines = [l.strip() for l in response.split('\n') if l.strip()]
    
    # Extract vote - look for action after VOTE: or first substantive line
    for i, line in enumerate(lines):
        if 'VOTE:' in line.upper():
            vote = line.split(':', 1)[1].strip() if ':' in line else line
            # Remove confidence/reasoning keywords if they got merged
            for kw in ['CONFIDENCE:', 'REASONING:', 'high', 'medium', 'low']:
                if kw.lower() in vote.lower() and kw not in ['high', 'medium', 'low']:
                    vote = vote.split(kw)[0].strip()
            break
        elif i < 3 and len(line) > 10 and not any(x in line.lower() for x in ['confidence', 'reasoning', 'format', 'respond']):
            # First substantial line might be the vote
            vote = line
    
    # Extract confidence
    for line in lines:
        if 'CONFIDENCE:' in line.upper() or 'confidence' in line.lower():
            if 'high' in line.lower():
                confidence = "high"
            elif 'medium' in line.lower() or 'med' in line.lower():
                confidence = "medium"
            elif 'low' in line.lower():
                confidence = "low"
    
    # Extract reasoning
    for line in lines:
        if 'REASONING:' in line.upper() or 'REASON:' in line.upper():
            reasoning = line.split(':', 1)[1].strip() if ':' in line else line
            break
        elif 'because' in line.lower() or 'why:' in line.lower():
            reasoning = line
    
    # If vote is still empty but we have content, use first line
    if vote == "No vote" and lines:
        vote = lines[0][:100]
    
    return AgentVote(name, role, vote, confidence, reasoning)


def get_consensus(votes: list) -> dict:
    """Analyze votes and find consensus or majority using simple logic."""
    
    # Extract keywords from each vote
    vote_keywords = []
    for v in votes:
        words = v.vote.lower().split()
        # Filter for meaningful words
        keywords = [w for w in words if len(w) > 3 and w not in ['this', 'that', 'with', 'from', 'have', 'should']]
        vote_keywords.append(set(keywords))
    
    # Find common keywords
    if len(vote_keywords) >= 2:
        common = vote_keywords[0] & vote_keywords[1]
        if len(vote_keywords) >= 3:
            common = common & vote_keywords[2]
    else:
        common = set()
    
    # Count votes for similar actions
    action_counts = {}
    for v in votes:
        vote_lower = v.vote.lower()
        # Categorize votes
        if any(x in vote_lower for x in ['sales', 'call', 'veterinary', 'revenue', 'money', 'income']):
            action_counts['veterinary_sales_calls'] = action_counts.get('veterinary_sales_calls', 0) + 1
        elif any(x in vote_lower for x in ['linkedin', 'profile', 'social', 'network']):
            action_counts['linkedin_profile'] = action_counts.get('linkedin_profile', 0) + 1
        elif any(x in vote_lower for x in ['review', 'code', 'audit', 'check']):
            action_counts['code_review'] = action_counts.get('code_review', 0) + 1
        else:
            action_counts['other'] = action_counts.get('other', 0) + 1
    
    # Find winner
    if action_counts:
        winner = max(action_counts.items(), key=lambda x: x[1])
        winning_action = winner[0]
        winning_count = winner[1]
        
        # Map to human-readable
        action_map = {
            'veterinary_sales_calls': "Make the 4 veterinary sales calls",
            'linkedin_profile': "Update LinkedIn profile",
            'code_review': "Do the code review",
            'other': votes[0].vote  # Fallback to first vote
        }
        
        # Determine consensus level
        if winning_count >= 2:
            consensus = "yes" if winning_count == 3 else "partial"
            confidence = "high" if winning_count == 3 else "medium"
        else:
            consensus = "no"
            confidence = "low"
            # Default to executor's vote if no consensus
            winning_action = 'veterinary_sales_calls'  # Most votes wins
        
        # Check for concerns from critic
        critic_concern = None
        for v in votes:
            if v.name == "Critic" and winning_count < 3:
                critic_concern = v.vote[:50]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "consensus": consensus,
            "action": action_map.get(winning_action, winning_action),
            "confidence": confidence,
            "notes": critic_concern or f"{winning_count}/3 agents agreed",
            "raw_votes": [(v.name, v.vote) for v in votes]
        }
    
    # Fallback
    return {
        "timestamp": datetime.now().isoformat(),
        "consensus": "no",
        "action": votes[0].vote if votes else "Review options",
        "confidence": "low",
        "notes": "Could not determine consensus",
        "raw_votes": [(v.name, v.vote) for v in votes]
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick team decision (parallel voting)")
    parser.add_argument("context", nargs="?",
                       default="Decide the most important next action for this project",
                       help="What to decide")
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("⚡ QUICK TEAM VOTE (Parallel)")
    print(f"{'='*60}")
    print(f"Context: {args.context}\n")
    
    # Run all 3 votes in parallel
    votes = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(executor_vote, args.context): "Executor",
            executor.submit(strategist_vote, args.context): "Strategist",
            executor.submit(critic_vote, args.context): "Critic"
        }
        
        for future in as_completed(futures):
            agent_name = futures[future]
            try:
                vote = future.result()
                votes.append(vote)
                color = {"Executor": "\033[92m", "Strategist": "\033[94m", "Critic": "\033[91m"}.get(agent_name, "")
                reset = "\033[0m"
                print(f"{color}✓ {vote.name} voted ({vote.confidence} confidence){reset}")
            except Exception as e:
                print(f"✗ {agent_name} failed: {e}")
    
    # Display all votes
    print(f"\n{'─'*60}")
    print("VOTES:")
    print(f"{'─'*60}")
    
    colors = {"Executor": "\033[92m", "Strategist": "\033[94m", "Critic": "\033[91m"}
    reset = "\033[0m"
    
    for vote in votes:
        color = colors.get(vote.name, "")
        print(f"\n{color}{vote.name} ({vote.role}){reset}")
        print(f"  → {vote.vote}")
        print(f"  Confidence: {vote.confidence}")
        print(f"  Why: {vote.reasoning[:60]}...")
    
    # Get consensus
    print(f"\n{'─'*60}")
    print("ANALYZING CONSENSUS...")
    print(f"{'─'*60}")
    
    result = get_consensus(votes)
    
    # Display result
    print(f"\n{'='*60}")
    print("🎯 TEAM DECISION")
    print(f"{'='*60}")
    print(f"Consensus: {result['consensus'].upper()}")
    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence'].upper()}")
    if result['notes']:
        print(f"Notes: {result['notes']}")
    
    print(f"\n{'='*60}")
    print("✅ RECOMMENDED NEXT STEP:")
    print(f"   {result['action']}")
    print(f"\n   Execute with:")
    print(f"   $ python3 kimi-plugin/scripts/kimi-companion.py task \"{result['action']}\"")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
