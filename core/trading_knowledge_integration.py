#!/usr/bin/env python3
"""
TRADING KNOWLEDGE INTEGRATION MODULE
Connects CryptoTradingKnowledgeBase to RobustGhostAgent
Enables intelligent strategy selection and risk management
"""

import sys
import json
import logging
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_base.crypto_trading_mastery import (
    CryptoTradingKnowledgeBase, TradingStrategy, StrategyType
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TradingKnowledge")


@dataclass
class TradingDecision:
    """A structured trading decision from the knowledge base"""
    action: str  # BUY, SELL, HOLD, DCA, STAKE
    asset: str
    amount: float
    strategy: str
    confidence: float  # 0.0 to 1.0
    reasons: List[str]
    risk_level: int
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class TradingKnowledgeIntegrator:
    """
    Integrates trading knowledge base with Ghost Agent
    Provides intelligent strategy selection, risk management, and decision support
    """
    
    def __init__(self, capital: float = 16.0):
        """
        Initialize with starting capital
        
        Args:
            capital: Starting capital in USD (default: $16 from Ghost Agent)
        """
        self.capital = capital
        self.kb = CryptoTradingKnowledgeBase()
        self.daily_stats = {
            'trades_today': 0,
            'wins': 0,
            'losses': 0,
            'pnl_today': 0.0,
            'max_loss_hit': False,
            'last_reset': datetime.now().date()
        }
        self.session_history = []
        
        logger.info(f"🧠 Trading Knowledge Integrator initialized with ${capital:.2f}")
        self._recommend_initial_strategy()
    
    def _recommend_initial_strategy(self):
        """Recommend strategies appropriate for current capital"""
        strategies = self.kb.get_strategy_for_capital(self.capital)
        
        print("\n" + "="*70)
        print("  📚 TRADING KNOWLEDGE BASE - STRATEGY RECOMMENDATIONS")
        print("="*70)
        print(f"\n💰 Capital: ${self.capital:.2f}")
        print(f"📊 Recommended Strategies for Your Capital:\n")
        
        for i, strat in enumerate(strategies, 1):
            print(f"  {i}. {strat.name}")
            print(f"     Type: {strat.strategy_type.value}")
            print(f"     Expected Return: {strat.expected_monthly_return}%/month")
            print(f"     Win Rate: {strat.win_rate}%")
            print(f"     Risk Level: {strat.risk_level}/10")
            print()
        
        risk_params = self.kb.get_risk_management_for_account_size(self.capital)
        print("🛡️  Risk Parameters:")
        for key, value in risk_params.items():
            print(f"     {key}: {value}")
        print("="*70 + "\n")
    
    def get_optimal_strategy(self, 
                           market_condition: str = "sideways",
                           available_hours: int = 12) -> Dict:
        """
        Get the optimal strategy for current conditions
        
        Args:
            market_condition: Current market condition (uptrend/downtrend/sideways)
            available_hours: Hours available for trading
            
        Returns:
            Dict with strategy details and execution rules
        """
        strategies = self.kb.get_strategy_for_capital(self.capital)
        
        if not strategies:
            return self._fallback_strategy()
        
        primary_strategy = strategies[0]
        
        return {
            "strategy_name": primary_strategy.name,
            "strategy_type": primary_strategy.strategy_type.value,
            "timeframe": primary_strategy.timeframe,
            "entry_rules": primary_strategy.entry_rules,
            "exit_rules": primary_strategy.exit_rules,
            "risk_management": primary_strategy.risk_management,
            "expected_return": primary_strategy.expected_monthly_return,
            "win_rate": primary_strategy.win_rate,
            "risk_level": primary_strategy.risk_level,
            "assets": primary_strategy.assets,
            "max_daily_trades": min(5, available_hours // 2),
            "capital_allocation": self._calculate_allocation()
        }
    
    def _fallback_strategy(self) -> Dict:
        """Fallback strategy for very small capital"""
        return {
            "strategy_name": "Micro-Cap DCA & Earn",
            "strategy_type": "accumulation",
            "timeframe": "Daily",
            "entry_rules": [
                "Buy $1-2 of BTC daily",
                "Complete all Learn & Earn lessons",
                "Stake any earned crypto"
            ],
            "exit_rules": [
                "Hold for minimum 1 year",
                "Take 50% profit at 3x",
                "Never sell at loss"
            ],
            "risk_management": [
                "Only invest what you can lose",
                "Never touch emergency fund",
                "DCA removes timing risk"
            ],
            "expected_return": 8,
            "win_rate": 95,
            "risk_level": 2,
            "assets": ["BTC", "ETH"],
            "max_daily_trades": 1,
            "capital_allocation": {"BTC": 0.6, "ETH": 0.35, "CASH": 0.05}
        }
    
    def _calculate_allocation(self) -> Dict[str, float]:
        """Calculate optimal asset allocation based on capital"""
        if self.capital < 100:
            # Conservative: Mostly BTC
            return {"BTC": 0.60, "ETH": 0.30, "EARN": 0.05, "CASH": 0.05}
        elif self.capital < 500:
            # Moderate: Diversified
            return {"BTC": 0.40, "ETH": 0.30, "ALTS": 0.15, "STAKE": 0.10, "CASH": 0.05}
        elif self.capital < 2000:
            # Balanced: More alts
            return {"BTC": 0.30, "ETH": 0.25, "ALTS": 0.25, "DEFI": 0.10, "STAKE": 0.05, "CASH": 0.05}
        else:
            # Aggressive: Full portfolio
            return {"BTC": 0.25, "ETH": 0.20, "ALTS": 0.25, "DEFI": 0.15, "NFT": 0.05, "STAKE": 0.05, "CASH": 0.05}
    
    def calculate_position_size(self, 
                               trade_risk: float = 0.01,
                               stop_loss_pct: float = 0.03) -> float:
        """
        Calculate position size using fixed fractional method
        
        Args:
            trade_risk: Risk per trade (default 1%)
            stop_loss_pct: Stop loss percentage (default 3%)
            
        Returns:
            Position size in USD
        """
        risk_amount = self.capital * trade_risk
        position_size = risk_amount / stop_loss_pct
        
        # Cap at 50% of capital per trade
        max_position = self.capital * 0.50
        position_size = min(position_size, max_position)
        
        # For very small capital, ensure minimum viable trade
        if position_size < 1.0 and self.capital >= 2.0:
            position_size = min(2.0, self.capital * 0.25)
        
        return round(position_size, 2)
    
    def evaluate_opportunity(self, 
                           opportunity: Dict,
                           current_positions: List[Dict] = None) -> TradingDecision:
        """
        Evaluate a trading opportunity using knowledge base
        
        Args:
            opportunity: Dict with opportunity details
            current_positions: List of current positions
            
        Returns:
            TradingDecision with action recommendation
        """
        if current_positions is None:
            current_positions = []
        
        # Check daily limits
        if self._daily_limits_reached():
            return TradingDecision(
                action="SKIP",
                asset=opportunity.get('asset', 'UNKNOWN'),
                amount=0,
                strategy="Risk Management",
                confidence=1.0,
                reasons=["Daily loss limit reached", "Risk management override"],
                risk_level=0
            )
        
        # Check if we have capacity
        open_positions = len(current_positions)
        risk_params = self.kb.get_risk_management_for_account_size(self.capital)
        max_positions = risk_params.get('max_open_positions', 2)
        
        if open_positions >= max_positions:
            return TradingDecision(
                action="SKIP",
                asset=opportunity.get('asset', 'UNKNOWN'),
                amount=0,
                strategy="Portfolio Management",
                confidence=0.8,
                reasons=[f"Max positions ({max_positions}) reached"],
                risk_level=0
            )
        
        # Get optimal strategy
        strategy = self.get_optimal_strategy(
            market_condition=opportunity.get('market_condition', 'sideways')
        )
        
        # Calculate position size
        position_size = self.calculate_position_size()
        
        # Evaluate based on strategy
        confidence = 0.5
        reasons = []
        
        # Check entry rules
        if self._meets_entry_criteria(opportunity, strategy):
            confidence += 0.3
            reasons.append("Meets strategy entry criteria")
        
        # Check risk level
        if strategy['risk_level'] <= 5:
            confidence += 0.1
            reasons.append("Acceptable risk level")
        
        # Check win rate
        if strategy['win_rate'] >= 50:
            confidence += 0.1
            reasons.append(f"Good historical win rate ({strategy['win_rate']}%)")
        
        # Make decision
        if confidence >= 0.7:
            action = "BUY"
            # Calculate stops
            entry = opportunity.get('price', 0)
            stop = entry * 0.97  # 3% stop
            target = entry * 1.06  # 6% target (1:2 R:R)
        else:
            action = "SKIP"
            stop = None
            target = None
        
        return TradingDecision(
            action=action,
            asset=opportunity.get('asset', 'BTC'),
            amount=position_size,
            strategy=strategy['strategy_name'],
            confidence=confidence,
            reasons=reasons,
            risk_level=strategy['risk_level'],
            entry_price=opportunity.get('price'),
            stop_loss=stop,
            take_profit=target
        )
    
    def _daily_limits_reached(self) -> bool:
        """Check if daily trading limits have been reached"""
        today = datetime.now().date()
        
        # Reset if new day
        if today != self.daily_stats['last_reset']:
            self.daily_stats = {
                'trades_today': 0,
                'wins': 0,
                'losses': 0,
                'pnl_today': 0.0,
                'max_loss_hit': False,
                'last_reset': today
            }
        
        # Check daily loss limit (3-5% of capital)
        daily_loss_limit = self.capital * 0.05
        if self.daily_stats['pnl_today'] <= -daily_loss_limit:
            return True
        
        return False
    
    def _meets_entry_criteria(self, opportunity: Dict, strategy: Dict) -> bool:
        """Check if opportunity meets strategy entry criteria"""
        # Simplified check - in production would verify all technical criteria
        required_signals = len(strategy['entry_rules'])
        matched_signals = 0
        
        # Check for common signals
        if opportunity.get('trend_aligned', False):
            matched_signals += 1
        if opportunity.get('volume_confirmed', False):
            matched_signals += 1
        if opportunity.get('support_hold', False):
            matched_signals += 1
        
        return matched_signals >= max(1, required_signals // 2)
    
    def get_psychology_reminder(self) -> str:
        """Get a random trading psychology reminder"""
        reminders = self.kb.psychology['mindset_principles']
        return random.choice(reminders)
    
    def get_risk_reminder(self) -> str:
        """Get a risk management reminder"""
        reminders = self.kb.risk_management['stop_loss_rules']
        return random.choice(reminders)
    
    def generate_daily_briefing(self) -> str:
        """Generate a daily trading briefing"""
        strategy = self.get_optimal_strategy()
        risk_params = self.kb.get_risk_management_for_account_size(self.capital)
        
        briefing = f"""
╔══════════════════════════════════════════════════════════════════╗
║              DAILY TRADING BRIEFING - Ghost Agent                ║
╠══════════════════════════════════════════════════════════════════╣
  📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
  💰 Capital: ${self.capital:.2f}
  
  🎯 PRIMARY STRATEGY: {strategy['strategy_name']}
     Type: {strategy['strategy_type'].upper()}
     Expected Return: {strategy['expected_return']}%/month
     Win Rate: {strategy['win_rate']}%
     Risk Level: {strategy['risk_level']}/10
  
  🛡️  RISK PARAMETERS:
     Max Risk/Trade: {risk_params['max_risk_per_trade']*100}%
     Max Open Positions: {risk_params['max_open_positions']}
     Daily Loss Limit: ${self.capital * risk_params['daily_loss_limit']:.2f}
  
  💵 POSITION SIZING:
     Recommended Size: ${self.calculate_position_size():.2f}
     Max per Trade: ${self.capital * 0.5:.2f}
  
  🧠 PSYCHOLOGY:
     "{self.get_psychology_reminder()}"
  
  ⚠️  RISK REMINDER:
     {self.get_risk_reminder()}
  
  📋 TODAY'S RULES:
     1. Follow the strategy exactly
     2. Stop if daily loss limit hit
     3. Journal every trade
     4. Take breaks between trades
     5. No revenge trading
╚══════════════════════════════════════════════════════════════════╝
"""
        return briefing
    
    def log_trade(self, decision: TradingDecision, outcome: Optional[str] = None):
        """Log a trade to history"""
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'decision': asdict(decision),
            'outcome': outcome,
            'capital_at_time': self.capital
        }
        
        self.session_history.append(trade_record)
        self.daily_stats['trades_today'] += 1
        
        if outcome == 'WIN':
            self.daily_stats['wins'] += 1
        elif outcome == 'LOSS':
            self.daily_stats['losses'] += 1
        
        logger.info(f"📝 Trade logged: {decision.action} {decision.asset} @ ${decision.amount:.2f}")
    
    def update_capital(self, new_capital: float):
        """Update capital and re-evaluate strategies"""
        old_capital = self.capital
        self.capital = new_capital
        
        if abs(new_capital - old_capital) / old_capital > 0.20:  # 20% change
            logger.info(f"💰 Capital updated: ${old_capital:.2f} → ${new_capital:.2f}")
            self._recommend_initial_strategy()
    
    def export_knowledge_summary(self) -> Dict:
        """Export a summary of integrated knowledge"""
        return {
            "strategies_loaded": len(self.kb.strategies),
            "risk_rules": len(self.kb.risk_management['stop_loss_rules']),
            "psychology_principles": len(self.kb.psychology['mindset_principles']),
            "technical_indicators": sum(len(v) for v in self.kb.market_analysis['technical_indicators'].values()),
            "chart_patterns": sum(len(v) for v in self.kb.market_analysis['chart_patterns'].values()),
            "capital": self.capital,
            "recommended_strategies": [s.name for s in self.kb.get_strategy_for_capital(self.capital)],
            "risk_profile": self.kb.get_risk_management_for_account_size(self.capital)
        }


# ============================================================================
# GHOST AGENT HOOK
# ============================================================================

def initialize_trading_knowledge(capital: float = 16.0) -> TradingKnowledgeIntegrator:
    """
    Initialize trading knowledge for Ghost Agent
    
    This is the main entry point - call this from Ghost Agent
    to integrate all trading knowledge
    
    Args:
        capital: Starting capital in USD
        
    Returns:
        TradingKnowledgeIntegrator instance
    """
    integrator = TradingKnowledgeIntegrator(capital=capital)
    
    # Print daily briefing
    print(integrator.generate_daily_briefing())
    
    return integrator


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("  TRADING KNOWLEDGE INTEGRATION - DEMO")
    print("="*70)
    print()
    
    # Initialize with $16 capital
    integrator = initialize_trading_knowledge(capital=16.0)
    
    # Show knowledge summary
    print("\n" + "="*70)
    print("  KNOWLEDGE BASE SUMMARY")
    print("="*70)
    summary = integrator.export_knowledge_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Simulate an opportunity evaluation
    print("\n" + "="*70)
    print("  SAMPLE OPPORTUNITY EVALUATION")
    print("="*70)
    
    opportunity = {
        "asset": "BTC",
        "price": 67500,
        "trend_aligned": True,
        "volume_confirmed": True,
        "support_hold": True,
        "market_condition": "uptrend"
    }
    
    decision = integrator.evaluate_opportunity(opportunity)
    
    print(f"\n  Opportunity: {opportunity['asset']} @ ${opportunity['price']:,}")
    print(f"  Decision: {decision.action}")
    print(f"  Amount: ${decision.amount:.2f}")
    print(f"  Confidence: {decision.confidence*100:.0f}%")
    print(f"  Strategy: {decision.strategy}")
    print(f"  Risk Level: {decision.risk_level}/10")
    print(f"\n  Reasons:")
    for reason in decision.reasons:
        print(f"    ✓ {reason}")
    
    if decision.stop_loss:
        print(f"\n  Stop Loss: ${decision.stop_loss:,.2f}")
        print(f"  Take Profit: ${decision.take_profit:,.2f}")
    
    print("\n" + "="*70)
    print("  INTEGRATION COMPLETE")
    print("="*70)
    print("\n✅ Trading knowledge is now integrated with Ghost Agent")
    print("✅ All strategies, risk rules, and psychology loaded")
    print("✅ Ready for intelligent trading decisions")
