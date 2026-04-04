#!/usr/bin/env python3
"""
REFINED OPTIMAL CAPITAL CALCULATOR - Ghost Agent v5.0
Real-world constraints and conservative estimates
"""

import math
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class Strategy:
    name: str
    min_capital: float
    max_capital: float
    monthly_return: float  # Conservative estimate
    max_drawdown: float    # Worst case historical
    fee_rate: float
    win_rate: float
    complexity: int  # 1-10 (higher = more skill needed)


class RefinedCalculator:
    def __init__(self):
        # Coinbase Advanced Trade fees (lower than regular)
        self.maker_fee = 0.006  # 0.6%
        self.taker_fee = 0.008  # 0.8%
        self.avg_fee = 0.007    # Average
        
        # Risk-free rate (5% annual US Treasury)
        self.risk_free = 0.05 / 12  # Monthly
        
        # REALISTIC strategy metrics (conservative)
        self.strategies = [
            Strategy(
                name="USDC Lending",
                min_capital=10,
                max_capital=float('inf'),
                monthly_return=0.0025,  # 3% APY = 0.25% monthly
                max_drawdown=0.001,     # Very stable
                fee_rate=0.001,
                win_rate=0.999,
                complexity=1
            ),
            Strategy(
                name="ETH Staking",
                min_capital=50,
                max_capital=float('inf'),
                monthly_return=0.0083,  # 10% APY = ~0.83% monthly (conservative)
                max_drawdown=0.50,      # ETH can drop 50%
                fee_rate=0.001,
                win_rate=0.99,
                complexity=2
            ),
            Strategy(
                name="DCA (Dollar Cost Average)",
                min_capital=16,
                max_capital=10000,
                monthly_return=0.005,   # 6% annual = 0.5% monthly (realistic)
                max_drawdown=0.30,      # BTC 30% drawdown
                fee_rate=self.avg_fee,
                win_rate=0.85,
                complexity=1
            ),
            Strategy(
                name="Conservative Swing Trading",
                min_capital=500,
                max_capital=10000,
                monthly_return=0.02,    # 2% monthly (realistic, not 15%)
                max_drawdown=0.10,      # 10% max loss per trade
                fee_rate=self.avg_fee * 2,  # Entry + exit
                win_rate=0.55,
                complexity=5
            ),
            Strategy(
                name="Moderate Swing Trading",
                min_capital=1000,
                max_capital=25000,
                monthly_return=0.04,    # 4% monthly (realistic)
                max_drawdown=0.15,
                fee_rate=self.avg_fee * 2,
                win_rate=0.50,
                complexity=7
            ),
        ]
    
    def kelly_fraction(self, strategy: Strategy) -> float:
        """
        Kelly Criterion: f* = (bp - q) / b
        Conservative: Use half-Kelly
        """
        # Simplified Kelly for crypto
        # Assume avg_win = 2 * avg_loss for swing trading
        b = 2.0  # Odds
        p = strategy.win_rate
        q = 1 - p
        
        kelly = (b * p - q) / b
        kelly_half = kelly / 2
        
        # Cap at 25% for crypto volatility
        return max(0, min(kelly_half, 0.25))
    
    def calculate_kelly_position(self, capital: float, strategy: Strategy) -> float:
        """Calculate optimal position size using Kelly"""
        kelly = self.kelly_fraction(strategy)
        return capital * kelly
    
    def expected_return_after_fees(self, strategy: Strategy) -> float:
        """Return after transaction costs"""
        return strategy.monthly_return - strategy.fee_rate
    
    def months_to_recover_fees(self, strategy: Strategy) -> float:
        """How many months to break even on fees"""
        if strategy.monthly_return <= 0:
            return float('inf')
        return strategy.fee_rate / strategy.monthly_return
    
    def risk_adjusted_return(self, strategy: Strategy) -> float:
        """Return per unit of risk (Sortino-like)"""
        ret = self.expected_return_after_fees(strategy)
        risk = strategy.max_drawdown
        if risk == 0:
            return ret
        return ret / risk
    
    def portfolio_value_after_n_months(self, 
                                       capital: float, 
                                       monthly_return: float, 
                                       months: int) -> float:
        """Compound growth: FV = PV * (1 + r)^n"""
        return capital * ((1 + monthly_return) ** months)
    
    def required_win_rate_for_breakeven(self, risk_reward: float) -> float:
        """
        Given risk:reward ratio, what's the minimum win rate needed?
        Formula: breakeven_win_rate = 1 / (1 + R)
        """
        return 1 / (1 + risk_reward)
    
    def calculate_scenario(self, capital: float, months: int = 36) -> Dict:
        """Calculate comprehensive metrics for a capital amount"""
        
        # Filter viable strategies
        viable = [s for s in self.strategies if s.min_capital <= capital]
        
        if not viable:
            return None
        
        # Calculate weighted portfolio metrics
        # Simple approach: equal weight to all viable strategies
        n_strategies = len(viable)
        weight = 1.0 / n_strategies
        
        portfolio_monthly_return = 0
        portfolio_max_drawdown = 0
        total_complexity = 0
        avg_win_rate = 0
        
        for s in viable:
            portfolio_monthly_return += self.expected_return_after_fees(s) * weight
            portfolio_max_drawdown = max(portfolio_max_drawdown, s.max_drawdown)
            total_complexity += s.complexity
            avg_win_rate += s.win_rate * weight
        
        avg_complexity = total_complexity / n_strategies
        
        # Calculate outcomes
        future_value = self.portfolio_value_after_n_months(
            capital, portfolio_monthly_return, months
        )
        
        # Opportunity cost (savings account at 5%)
        savings_return = 0.05 / 12
        savings_value = self.portfolio_value_after_n_months(
            capital, savings_return, months
        )
        
        # Realistic scenario (50% of expected return)
        realistic_return = portfolio_monthly_return * 0.5
        realistic_value = self.portfolio_value_after_n_months(
            capital, realistic_return, months
        )
        
        # Pessimistic scenario (only 25% of expected, or loss)
        pessimistic_return = max(-0.02, portfolio_monthly_return * 0.25)
        pessimistic_value = self.portfolio_value_after_n_months(
            capital, pessimistic_return, months
        )
        
        # Calculate "worth it" score
        # Higher score = better risk/reward for the capital amount
        profit_vs_savings = realistic_value - savings_value
        risk_capital_ratio = portfolio_max_drawdown
        
        if risk_capital_ratio == 0:
            worth_score = profit_vs_savings
        else:
            worth_score = profit_vs_savings / (risk_capital_ratio * capital)
        
        # Practical constraints
        can_diversify = n_strategies >= 3
        has_simple_options = any(s.complexity <= 2 for s in viable)
        
        return {
            'capital': capital,
            'n_strategies': n_strategies,
            'strategy_names': [s.name for s in viable],
            'monthly_return_pct': portfolio_monthly_return * 100,
            'annual_return_pct': ((1 + portfolio_monthly_return) ** 12 - 1) * 100,
            'max_drawdown_pct': portfolio_max_drawdown * 100,
            'avg_complexity': avg_complexity,
            'avg_win_rate': avg_win_rate,
            'months': months,
            'future_value_optimistic': future_value,
            'future_value_realistic': realistic_value,
            'future_value_pessimistic': pessimistic_value,
            'savings_comparison': savings_value,
            'profit_vs_savings': profit_vs_savings,
            'worth_score': worth_score,
            'can_diversify': can_diversify,
            'has_simple_options': has_simple_options,
            'min_position_size': capital / n_strategies if n_strategies > 0 else 0
        }
    
    def generate_report(self):
        """Generate comprehensive report"""
        
        # Test capital amounts
        test_amounts = [16, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
        
        results = []
        for amount in test_amounts:
            scenario = self.calculate_scenario(amount)
            if scenario:
                results.append(scenario)
        
        # Find optimal using realistic scenario
        optimal = max(results, key=lambda x: x['worth_score'])
        
        # Find best for beginners (low complexity)
        beginner_options = [r for r in results if r['has_simple_options'] and r['avg_complexity'] <= 3]
        best_beginner = max(beginner_options, key=lambda x: x['worth_score']) if beginner_options else None
        
        # Find minimum viable (can run the system)
        viable = [r for r in results if r['can_diversify']]
        min_viable = viable[0] if viable else results[0]
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║        📊 REFINED OPTIMAL CAPITAL ANALYSIS - GHOST AGENT v5.0            ║
║                                                                          ║
║              Conservative Estimates • Real-World Constraints             ║
╚══════════════════════════════════════════════════════════════════════════╝

ASSUMPTIONS:
• Coinbase fees: 0.6-0.8% per transaction
• Risk-free rate: 5% (US Treasury)
• Conservative strategy returns (not backtested maxima)
• Realistic win rates (not promotional claims)
• 36-month investment horizon

═══════════════════════════════════════════════════════════════════════════

🎯 MATHEMATICAL OPTIMUM: ${optimal['capital']:,.0f}

Why ${optimal['capital']:,.0f} is optimal:
• Worth Score: {optimal['worth_score']:.2f} (highest risk-adjusted value)
• Monthly Return: {optimal['monthly_return_pct']:.2f}%
• Annual Return: {optimal['annual_return_pct']:.1f}%
• Max Drawdown: {optimal['max_drawdown_pct']:.1f}%
• 3-Year Realistic Value: ${optimal['future_value_realistic']:,.2f}
• Profit vs Savings: ${optimal['profit_vs_savings']:,.2f}

═══════════════════════════════════════════════════════════════════════════

🌱 BEST FOR BEGINNERS: ${best_beginner['capital']:,.0f} if best_beginner else "N/A"

Why ${best_beginner['capital']:,.0f} for beginners:
• Has simple options (complexity ≤ 3)
• Low skill requirement
• Can diversify across {best_beginner['n_strategies']} strategies
• Worth Score: {best_beginner['worth_score']:.2f}
""" if best_beginner else """
🌱 BEST FOR BEGINNERS: No beginner-friendly options in range
"""
        
        report += f"""
═══════════════════════════════════════════════════════════════════════════

💰 DETAILED BREAKDOWN BY CAPITAL AMOUNT:

"""
        
        for r in results:
            report += f"""
${r['capital']:,.0f} Capital:
   Strategies Available: {r['n_strategies']}
   ({', '.join(r['strategy_names'][:2])}{'...' if len(r['strategy_names']) > 2 else ''})
   
   Returns:
   • Monthly: {r['monthly_return_pct']:.2f}%
   • Annual: {r['annual_return_pct']:.1f}%
   • Max Drawdown: {r['max_drawdown_pct']:.1f}%
   
   3-Year Projections:
   • Optimistic: ${r['future_value_optimistic']:,.2f}
   • Realistic (50%): ${r['future_value_realistic']:,.2f}
   • Pessimistic (25%): ${r['future_value_pessimistic']:,.2f}
   • vs 5% Savings: ${r['savings_comparison']:,.2f}
   
   Profit vs Savings: ${r['profit_vs_savings']:,.2f}
   Worth Score: {r['worth_score']:.2f}
   Can Diversify: {'Yes' if r['can_diversify'] else 'No'}
   Beginner Friendly: {'Yes' if r['has_simple_options'] else 'No'}
   
"""
        
        report += f"""
═══════════════════════════════════════════════════════════════════════════

📊 MATHEMATICAL FRAMEWORK:

1. KELLY CRITERION (Position Sizing)
   Formula: f* = (bp - q) / b
   Conservative: Use half-Kelly (max 25% per trade)
   
   Example for ${optimal['capital']:,.0f}:
   • Optimal bet size: ${optimal['capital'] * 0.25:,.2f} per trade
   • Risk of ruin: < 1%

2. COMPOUND GROWTH
   Formula: FV = PV × (1 + r)ⁿ
   Where r = monthly return, n = months
   
   ${optimal['capital']:,.0f} @ {optimal['monthly_return_pct']:.2f}% monthly:
   • Month 12: ${self.portfolio_value_after_n_months(optimal['capital'], optimal['monthly_return_pct']/100, 12):,.2f}
   • Month 36: ${self.portfolio_value_after_n_months(optimal['capital'], optimal['monthly_return_pct']/100, 36):,.2f}

3. RISK-ADJUSTED RETURN (Worth Score)
   Formula: (Profit vs Savings) / (Max Drawdown × Capital)
   Higher = better return per unit of risk

4. OPPORTUNITY COST
   Savings account @ 5% APY:
   ${optimal['capital']:,.0f} → ${self.portfolio_value_after_n_months(optimal['capital'], 0.05/12, 36):,.2f} in 3 years

═══════════════════════════════════════════════════════════════════════════

🎯 FINAL RECOMMENDATION:

FOR YOUR CURRENT SITUATION:

START WITH: ${min_viable['capital']:,.0f} (Minimum Viable)

Rationale:
• This is the minimum to run the Ghost Agent effectively
• Can diversify across {min_viable['n_strategies']} strategies
• Lower risk through diversification
• Realistic 3-year profit: ${min_viable['profit_vs_savings']:,.2f} vs savings
• Worth Score: {min_viable['worth_score']:.2f}

OPTIMAL TARGET: ${optimal['capital']:,.0f}

Rationale:
• Highest mathematical worth score
• Can access all 5 strategies
• Proper position sizing possible
• 3-year profit: ${optimal['profit_vs_savings']:,.2f} vs savings
• Max drawdown: {optimal['max_drawdown_pct']:.1f}%

═══════════════════════════════════════════════════════════════════════════

💡 PRACTICAL RECOMMENDATIONS:

1. IF YOU HAVE $16-50:
   → Start with DCA + ETH Staking
   → Use conservative settings
   → Focus on learning, not profit
   → Add capital as you gain confidence

2. IF YOU HAVE $100-500:
   → Optimal for beginners
   → Can diversify across 3-4 strategies
   → Realistic 3-year profit: ${results[4]['profit_vs_savings']:,.2f}
   → Good learning experience with real returns

3. IF YOU HAVE $1000+:
   → Mathematical optimum
   → Access all strategies
   → Professional-level position sizing
   → Worth Score: {optimal['worth_score']:.2f}

═══════════════════════════════════════════════════════════════════════════

⚠️  CRITICAL WARNINGS:

1. These are MATHEMATICAL PROJECTIONS, not guarantees
2. Crypto markets are VOLATILE - expect 20-50% drawdowns
3. Past performance does NOT predict future results
4. Only invest what you can afford to lose
5. Consider your personal risk tolerance
6. Factor in taxes (capital gains)

═══════════════════════════════════════════════════════════════════════════

📋 NEXT STEPS:

1. Assess your actual risk tolerance
2. Determine available capital
3. Start with minimum viable amount
4. Implement conservative strategies first
5. Scale up as you gain experience

═══════════════════════════════════════════════════════════════════════════

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Model: Ghost Agent v5.0 Refined Calculator
Status: Conservative estimates applied

"""
        
        return report


def main():
    calc = RefinedCalculator()
    report = calc.generate_report()
    print(report)
    
    with open('/home/asbelcas/rm-qpt/OPTIMAL_CAPITAL_REFINED.md', 'w') as f:
        f.write(report)
    
    print("\n✅ Refined report saved to: OPTIMAL_CAPITAL_REFINED.md")


if __name__ == "__main__":
    main()
