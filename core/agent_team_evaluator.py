#!/usr/bin/env python3
"""
AGENT TEAM EVALUATOR
Multi-agent system that evaluates and prioritizes Coinbase opportunities
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class AgentRole(Enum):
    STRATEGIST = "strategist"
    RISK_ANALYST = "risk_analyst"
    EFFICIENCY_EXPERT = "efficiency_expert"
    MARKET_ANALYST = "market_analyst"
    SECURITY_OFFICER = "security_officer"

@dataclass
class AgentEvaluation:
    """Evaluation from a single agent"""
    agent_role: AgentRole
    opportunity_id: str
    score: float  # 0-100
    reasoning: str
    confidence: float  # 0-1
    recommendation: str  # "execute", "skip", "delay"

@dataclass
class OpportunityScore:
    """Final scored opportunity"""
    opportunity_id: str
    title: str
    base_score: float
    agent_scores: Dict[AgentRole, float]
    final_score: float
    consensus: str
    risk_level: int
    time_estimate: int
    expected_roi: float
    execution_order: int


class StrategistAgent:
    """
    Strategist Agent - Evaluates strategic fit and long-term value
    """
    
    def evaluate(self, opportunity: Dict) -> AgentEvaluation:
        """Evaluate opportunity from strategic perspective"""
        
        feature = opportunity.get('feature', '')
        reward = opportunity.get('reward_amount', 0)
        
        # Strategic value scoring
        strategic_value = {
            'learn_and_earn': 95,  # High value, educational
            'staking': 80,         # Passive income
            'recurring_buys': 70,  # DCA strategy
            'referrals': 85,       # Network effects
            'cash_back': 60,       # Nice to have
            'card_rewards': 65,    # Usage incentive
        }
        
        base_score = strategic_value.get(feature, 50)
        
        # Adjust for reward amount
        if reward > 10:
            base_score += 15
        elif reward > 5:
            base_score += 10
        elif reward > 1:
            base_score += 5
        
        # Cap at 100
        score = min(base_score, 100)
        
        reasoning = f"{feature} has strategic value of {strategic_value.get(feature, 50)}. "
        if reward > 5:
            reasoning += f"High reward (${reward}) adds significant value. "
        
        return AgentEvaluation(
            agent_role=AgentRole.STRATEGIST,
            opportunity_id=opportunity.get('opp_id', ''),
            score=score,
            reasoning=reasoning,
            confidence=0.85,
            recommendation="execute" if score > 60 else "delay"
        )


class RiskAnalystAgent:
    """
    Risk Analyst - Evaluates risk vs reward
    """
    
    def evaluate(self, opportunity: Dict) -> AgentEvaluation:
        """Evaluate risk profile"""
        
        risk_level = opportunity.get('risk_level', 5)
        effort = opportunity.get('effort_level', 5)
        time_req = opportunity.get('time_required', 30)
        
        # Lower risk = higher score
        base_score = 100 - (risk_level * 8)
        
        # Effort penalty
        if effort > 7:
            base_score -= 15
        elif effort > 5:
            base_score -= 10
        
        # Time penalty for long tasks
        if time_req > 60:
            base_score -= 10
        elif time_req > 30:
            base_score -= 5
        
        score = max(base_score, 0)
        
        reasoning = f"Risk level {risk_level}/10. "
        if risk_level <= 2:
            reasoning += "Very low risk - safe execution. "
        elif risk_level <= 5:
            reasoning += "Moderate risk - proceed with caution. "
        else:
            reasoning += "Higher risk - careful evaluation needed. "
        
        recommendation = "execute" if score > 70 else ("delay" if score > 40 else "skip")
        
        return AgentEvaluation(
            agent_role=AgentRole.RISK_ANALYST,
            opportunity_id=opportunity.get('opp_id', ''),
            score=score,
            reasoning=reasoning,
            confidence=0.75,
            recommendation=recommendation
        )


class EfficiencyExpertAgent:
    """
    Efficiency Expert - Evaluates time/reward ratio
    """
    
    def evaluate(self, opportunity: Dict) -> AgentEvaluation:
        """Evaluate efficiency (reward per minute)"""
        
        reward = opportunity.get('reward_amount', 0)
        time_req = max(opportunity.get('time_required', 1), 1)
        effort = opportunity.get('effort_level', 5)
        
        # Calculate reward per minute
        reward_per_minute = reward / time_req
        
        # Score based on efficiency tiers
        if reward_per_minute >= 1.0:  # $1+ per minute
            base_score = 100
        elif reward_per_minute >= 0.5:  # $0.50+ per minute
            base_score = 85
        elif reward_per_minute >= 0.2:  # $0.20+ per minute
            base_score = 70
        elif reward_per_minute >= 0.1:  # $0.10+ per minute
            base_score = 55
        else:
            base_score = 40
        
        # Effort adjustment
        if effort <= 2:
            base_score += 10
        elif effort >= 8:
            base_score -= 15
        
        score = min(max(base_score, 0), 100)
        
        reasoning = f"${reward_per_minute:.2f} per minute. "
        if reward_per_minute >= 0.5:
            reasoning += "Excellent efficiency. "
        elif reward_per_minute >= 0.2:
            reasoning += "Good efficiency. "
        else:
            reasoning += "Lower efficiency - consider alternatives. "
        
        return AgentEvaluation(
            agent_role=AgentRole.EFFICIENCY_EXPERT,
            opportunity_id=opportunity.get('opp_id', ''),
            score=score,
            reasoning=reasoning,
            confidence=0.80,
            recommendation="execute" if score > 60 else "delay"
        )


class MarketAnalystAgent:
    """
    Market Analyst - Evaluates market conditions and timing
    """
    
    def evaluate(self, opportunity: Dict) -> AgentEvaluation:
        """Evaluate market timing"""
        
        feature = opportunity.get('feature', '')
        reward_currency = opportunity.get('reward_currency', 'USD')
        
        # Market timing factors
        score = 70  # Neutral base
        
        # Favor immediate, guaranteed rewards
        if feature == 'learn_and_earn':
            score += 20  # Guaranteed, immediate
        elif feature == 'staking':
            score += 10  # Long-term but stable
        elif feature == 'recurring_buys':
            score -= 5   # Requires ongoing commitment
        
        # Crypto rewards have upside potential
        if reward_currency != 'USD':
            score += 5  # Potential appreciation
        
        reasoning = f"Market conditions favorable for {feature}. "
        if reward_currency != 'USD':
            reasoning += f"{reward_currency} has upside potential. "
        
        return AgentEvaluation(
            agent_role=AgentRole.MARKET_ANALYST,
            opportunity_id=opportunity.get('opp_id', ''),
            score=min(score, 100),
            reasoning=reasoning,
            confidence=0.70,
            recommendation="execute" if score > 65 else "delay"
        )


class SecurityOfficerAgent:
    """
    Security Officer - Evaluates security and safety
    """
    
    def evaluate(self, opportunity: Dict) -> AgentEvaluation:
        """Evaluate security implications"""
        
        feature = opportunity.get('feature', '')
        requirements = opportunity.get('requirements', [])
        
        # Security score - higher is safer
        score = 90  # Assume safe by default
        
        # Check requirements for security concerns
        if any('password' in str(r).lower() for r in requirements):
            score -= 10
        if any('verify' in str(r).lower() for r in requirements):
            score -= 5  # Minor inconvenience
        
        # Feature-specific security
        safe_features = ['learn_and_earn', 'staking', 'cash_back']
        if feature in safe_features:
            score += 5
        
        score = min(max(score, 0), 100)
        
        reasoning = "Standard Coinbase operation. "
        if score >= 85:
            reasoning += "No security concerns. "
        else:
            reasoning += "Minor verification steps required. "
        
        return AgentEvaluation(
            agent_role=AgentRole.SECURITY_OFFICER,
            opportunity_id=opportunity.get('opp_id', ''),
            score=score,
            reasoning=reasoning,
            confidence=0.90,
            recommendation="execute" if score > 80 else "review"
        )


class AgentTeamCoordinator:
    """
    Coordinates all agents and produces final consensus
    """
    
    def __init__(self):
        self.agents = {
            AgentRole.STRATEGIST: StrategistAgent(),
            AgentRole.RISK_ANALYST: RiskAnalystAgent(),
            AgentRole.EFFICIENCY_EXPERT: EfficiencyExpertAgent(),
            AgentRole.MARKET_ANALYST: MarketAnalystAgent(),
            AgentRole.SECURITY_OFFICER: SecurityOfficerAgent(),
        }
        
        # Weight for each agent type
        self.agent_weights = {
            AgentRole.STRATEGIST: 0.25,
            AgentRole.RISK_ANALYST: 0.25,
            AgentRole.EFFICIENCY_EXPERT: 0.20,
            AgentRole.MARKET_ANALYST: 0.15,
            AgentRole.SECURITY_OFFICER: 0.15,
        }
    
    def evaluate_opportunities(self, opportunities: List[Dict]) -> List[OpportunityScore]:
        """
        Have agent team evaluate all opportunities
        """
        print("\n" + "="*80)
        print("  🧠 AGENT TEAM DELIBERATION")
        print("="*80)
        print(f"\n  Evaluating {len(opportunities)} opportunities...")
        print()
        
        scored_opportunities = []
        
        for opp in opportunities:
            opp_id = opp.get('opp_id', 'unknown')
            title = opp.get('title', 'Unknown')
            
            print(f"  📊 Evaluating: {title[:50]}...")
            
            # Get evaluation from each agent
            agent_scores = {}
            evaluations = []
            
            for role, agent in self.agents.items():
                eval_result = agent.evaluate(opp)
                agent_scores[role] = eval_result.score
                evaluations.append(eval_result)
            
            # Calculate weighted final score
            final_score = sum(
                agent_scores[role] * self.agent_weights[role]
                for role in self.agent_weights
            )
            
            # Determine consensus
            recommendations = [e.recommendation for e in evaluations]
            if recommendations.count("execute") >= 3:
                consensus = "STRONG_EXECUTE"
            elif recommendations.count("execute") >= 2:
                consensus = "EXECUTE"
            elif recommendations.count("delay") >= 3:
                consensus = "DELAY"
            else:
                consensus = "SKIP"
            
            # Calculate expected ROI
            reward = opp.get('reward_amount', 0)
            time_req = max(opp.get('time_required', 1), 1)
            hourly_rate = (reward / time_req) * 60
            
            scored_opp = OpportunityScore(
                opportunity_id=opp_id,
                title=title,
                base_score=opp.get('priority_score', 0),
                agent_scores={role.value: score for role, score in agent_scores.items()},
                final_score=final_score,
                consensus=consensus,
                risk_level=opp.get('risk_level', 5),
                time_estimate=time_req,
                expected_roi=hourly_rate,
                execution_order=0  # Will be set later
            )
            
            scored_opportunities.append(scored_opp)
        
        # Sort by final score
        scored_opportunities.sort(key=lambda x: x.final_score, reverse=True)
        
        # Set execution order
        for i, opp in enumerate(scored_opportunities, 1):
            opp.execution_order = i
        
        return scored_opportunities
    
    def display_evaluation_report(self, scored_opportunities: List[OpportunityScore]):
        """Display detailed evaluation report"""
        
        print("\n" + "="*80)
        print("  📋 AGENT TEAM EVALUATION REPORT")
        print("="*80)
        
        # Summary statistics
        execute_count = sum(1 for o in scored_opportunities if "EXECUTE" in o.consensus)
        delay_count = sum(1 for o in scored_opportunities if o.consensus == "DELAY")
        skip_count = sum(1 for o in scored_opportunities if o.consensus == "SKIP")
        
        total_potential = sum(o.expected_roi for o in scored_opportunities if "EXECUTE" in o.consensus)
        
        print(f"\n  SUMMARY:")
        print(f"    Opportunities Evaluated: {len(scored_opportunities)}")
        print(f"    Execute Now: {execute_count}")
        print(f"    Delay: {delay_count}")
        print(f"    Skip: {skip_count}")
        print(f"    Total Hourly ROI Potential: ${total_potential:.2f}/hr")
        
        print(f"\n  TOP 10 RECOMMENDED OPPORTUNITIES:")
        print("-" * 80)
        
        for i, opp in enumerate(scored_opportunities[:10], 1):
            status_icon = "✅" if "EXECUTE" in opp.consensus else ("⏳" if opp.consensus == "DELAY" else "❌")
            
            print(f"\n  {i}. {status_icon} {opp.title[:45]}")
            print(f"     Final Score: {opp.final_score:.1f}/100 | Consensus: {opp.consensus}")
            print(f"     Agent Scores: Strat:{opp.agent_scores.get('strategist', 0):.0f} " +
                  f"Risk:{opp.agent_scores.get('risk_analyst', 0):.0f} " +
                  f"Eff:{opp.agent_scores.get('efficiency_expert', 0):.0f}")
            print(f"     Expected ROI: ${opp.expected_roi:.2f}/hr | Time: {opp.time_estimate}min")


def main():
    """Test the agent team evaluator"""
    
    # Sample opportunities for testing
    test_opportunities = [
        {
            "opp_id": "learn_comp",
            "feature": "learn_and_earn",
            "title": "What is Compound?",
            "reward_amount": 3.00,
            "reward_currency": "COMP",
            "time_required": 3,
            "effort_level": 2,
            "risk_level": 1,
            "requirements": ["Watch video", "Answer question"],
            "priority_score": 85.0
        },
        {
            "opp_id": "stake_eth",
            "feature": "staking",
            "title": "ETH Staking",
            "reward_amount": 0.02,
            "reward_currency": "ETH",
            "time_required": 1,
            "effort_level": 1,
            "risk_level": 2,
            "requirements": ["Hold ETH"],
            "priority_score": 70.0
        },
        {
            "opp_id": "referral",
            "feature": "referrals",
            "title": "Referral Program",
            "reward_amount": 10.00,
            "reward_currency": "USD",
            "time_required": 10,
            "effort_level": 3,
            "risk_level": 1,
            "requirements": ["Share link", "Friend signs up"],
            "priority_score": 90.0
        }
    ]
    
    coordinator = AgentTeamCoordinator()
    scored = coordinator.evaluate_opportunities(test_opportunities)
    coordinator.display_evaluation_report(scored)


if __name__ == "__main__":
    main()
