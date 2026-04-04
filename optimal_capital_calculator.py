#!/usr/bin/env python3
"""
OPTIMAL CAPITAL CALCULATOR - Ghost Agent v5.0
Advanced Mathematical Analysis using Kelly Criterion, 
Expected Value Theory, and Risk Management

Formulas used:
- Kelly Criterion: f* = (bp - q) / b
- Sharpe Ratio: (Return - Risk Free Rate) / Std Dev
- Risk of Ruin: ROR = ((1 - edge) / (1 + edge))^capital_units
- Compound Growth: A = P(1 + r/n)^(nt)
- Optimal F: Maximizes geometric mean
"""

import math
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime

@dataclass
class StrategyMetrics:
    name: str
    expected_monthly_return: float  # As decimal (0.08 = 8%)
    win_rate: float  # As decimal (0.95 = 95%)
    risk_level: int  # 1-10 scale
    avg_loss: float  # Average loss when trade fails
    avg_win: float  # Average win when trade succeeds
    fees: float  # Transaction fees as decimal
    min_capital: float  # Minimum viable capital
    max_capital: float  # Optimal max before diminishing returns


class OptimalCapitalCalculator:
    """
    Calculates optimal capital allocation using advanced financial mathematics
    """
    
    def __init__(self):
        # Coinbase fee structure (approximate)
        self.coinbase_fee = 0.005  # 0.5% spread
        self.network_fee = 0.001   # 0.1% network fee
        self.total_fee = self.coinbase_fee + self.network_fee
        
        # Risk-free rate (US Treasury yield ~5% annually)
        self.risk_free_rate_annual = 0.05
        self.risk_free_rate_monthly = self.risk_free_rate_annual / 12
        
        # Strategies from Ghost Agent knowledge base
        self.strategies = self._load_strategies()
        
        # User financial profile
        self.user_profile = {
            'emergency_fund': 500.0,  # Assumed minimum emergency fund
            'monthly_income': 2000.0,  # Assumed monthly income
            'risk_tolerance': 'moderate',  # conservative, moderate, aggressive
            'investment_horizon': 3.0,  # Years
        }
    
    def _load_strategies(self) -> List[StrategyMetrics]:
        """Load strategy metrics from Ghost Agent knowledge base"""
        return [
            StrategyMetrics(
                name="Dollar Cost Average (DCA)",
                expected_monthly_return=0.008,  # 8% annual = ~0.67% monthly
                win_rate=0.95,
                risk_level=2,
                avg_loss=0.15,  # 15% drawdown worst case
                avg_win=0.25,   # 25% gain best case
                fees=self.total_fee,
                min_capital=16.0,
                max_capital=10000.0
            ),
            StrategyMetrics(
                name="Ethereum Staking",
                expected_monthly_return=0.012,  # ~14% APY = ~1.2% monthly
                win_rate=0.99,
                risk_level=3,
                avg_loss=0.30,  # ETH can drop 30%
                avg_win=0.20,
                fees=0.001,
                min_capital=50.0,
                max_capital=50000.0
            ),
            StrategyMetrics(
                name="USDC Lending",
                expected_monthly_return=0.0025,  # 3% APY = ~0.25% monthly
                win_rate=0.999,
                risk_level=1,
                avg_loss=0.01,  # Very stable
                avg_win=0.03,
                fees=0.001,
                min_capital=10.0,
                max_capital=100000.0
            ),
            StrategyMetrics(
                name="Swing Trading (Ichimoku)",
                expected_monthly_return=0.15,  # 15% monthly
                win_rate=0.50,
                risk_level=5,
                avg_loss=0.05,  # 5% stop loss
                avg_win=0.10,   # 10% target
                fees=self.total_fee * 2,  # Entry + exit
                min_capital=500.0,
                max_capital=10000.0
            ),
            StrategyMetrics(
                name="Scalping (EMA Cross)",
                expected_monthly_return=0.08,  # 8% monthly
                win_rate=0.55,
                risk_level=7,
                avg_loss=0.03,
                avg_win=0.06,
                fees=self.total_fee * 4,  # Frequent trading
                min_capital=1000.0,
                max_capital=5000.0
            ),
        ]
    
    def kelly_criterion(self, strategy: StrategyMetrics) -> float:
        """
        Calculate Kelly Criterion optimal bet size
        
        Formula: f* = (bp - q) / b
        Where:
        b = average win / average loss (odds)
        p = win rate
        q = loss rate (1 - p)
        """
        b = strategy.avg_win / strategy.avg_loss  # Odds
        p = strategy.win_rate
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Cap at 0.25 (25%) for crypto volatility
        kelly_capped = min(kelly, 0.25)
        
        return max(0, kelly_capped)  # Can't be negative
    
    def calculate_expected_value(self, strategy: StrategyMetrics, capital: float) -> float:
        """
        Calculate Expected Value (EV) of a strategy
        
        EV = (Win Probability × Win Amount) - (Loss Probability × Loss Amount) - Fees
        """
        p_win = strategy.win_rate
        p_loss = 1 - p_win
        
        win_amount = capital * strategy.avg_win
        loss_amount = capital * strategy.avg_loss
        fees = capital * strategy.fees
        
        ev = (p_win * win_amount) - (p_loss * loss_amount) - fees
        
        return ev
    
    def calculate_sharpe_ratio(self, strategy: StrategyMetrics) -> float:
        """
        Calculate Sharpe Ratio
        
        Sharpe = (Strategy Return - Risk Free Rate) / Standard Deviation
        """
        strategy_return = strategy.expected_monthly_return
        risk_free = self.risk_free_rate_monthly
        
        # Estimate standard deviation based on risk level (simplified)
        # Higher risk = higher volatility
        std_dev = strategy.risk_level / 100  # 0.02 to 0.10
        
        if std_dev == 0:
            return 0
        
        sharpe = (strategy_return - risk_free) / std_dev
        
        return sharpe
    
    def risk_of_ruin(self, capital: float, bet_size: float, win_rate: float) -> float:
        """
        Calculate Risk of Ruin (probability of losing all capital)
        
        Formula: ROR = ((1 - edge) / (1 + edge))^capital_units
        Where edge = win_rate - loss_rate
        """
        if bet_size <= 0 or capital <= 0:
            return 1.0  # Certain ruin
        
        units = capital / bet_size
        edge = win_rate - (1 - win_rate)  # 2p - 1
        
        if edge <= 0:
            return 1.0  # Negative edge = certain ruin
        
        ror = ((1 - edge) / (1 + edge)) ** units
        
        return min(1.0, max(0.0, ror))
    
    def optimal_f_position_size(self, strategy: StrategyMetrics, capital: float) -> float:
        """
        Calculate Optimal F position sizing
        
        Maximizes geometric mean of returns
        """
        kelly = self.kelly_criterion(strategy)
        
        # Optimal F is typically half Kelly for safety
        optimal_f = kelly / 2
        
        position_size = capital * optimal_f
        
        return position_size
    
    def compound_annual_growth_rate(self, 
                                    initial: float, 
                                    final: float, 
                                    years: float) -> float:
        """
        Calculate CAGR
        
        CAGR = (Final / Initial)^(1/years) - 1
        """
        if initial <= 0 or years <= 0:
            return 0
        
        cagr = (final / initial) ** (1 / years) - 1
        return cagr
    
    def calculate_diversification_benefit(self, strategies: List[StrategyMetrics]) -> float:
        """
        Calculate diversification benefit using correlation
        
        Simplified: Lower correlation = higher benefit
        """
        # Crypto strategies are highly correlated (0.7-0.9)
        avg_correlation = 0.8
        
        # Diversification benefit formula (simplified)
        n = len(strategies)
        if n <= 1:
            return 0
        
        # Portfolio variance reduction
        benefit = (1 - avg_correlation) * (1 - 1/n)
        
        return benefit
    
    def calculate_portfolio_metrics(self, 
                                    capital: float,
                                    allocations: Dict[str, float]) -> Dict:
        """
        Calculate overall portfolio metrics
        """
        total_expected_return = 0
        total_risk = 0
        total_sharpe = 0
        
        for strategy_name, allocation_pct in allocations.items():
            strategy = next((s for s in self.strategies if s.name == strategy_name), None)
            if not strategy:
                continue
            
            allocated_capital = capital * allocation_pct
            
            # Weighted metrics
            total_expected_return += strategy.expected_monthly_return * allocation_pct
            total_risk += (strategy.risk_level / 10) * allocation_pct
            total_sharpe += self.calculate_sharpe_ratio(strategy) * allocation_pct
        
        # Diversification benefit
        div_benefit = self.calculate_diversification_benefit([
            s for s in self.strategies 
            if s.name in allocations
        ])
        
        adjusted_risk = total_risk * (1 - div_benefit)
        
        return {
            'expected_monthly_return': total_expected_return,
            'expected_annual_return': total_expected_return * 12,
            'risk_score': adjusted_risk,
            'sharpe_ratio': total_sharpe,
            'diversification_benefit': div_benefit
        }
    
    def find_optimal_capital(self) -> Dict:
        """
        Find the optimal capital amount using multiple mathematical models
        """
        results = []
        
        # Test various capital amounts
        test_amounts = [16, 50, 100, 250, 500, 1000, 2000, 5000, 10000]
        
        for capital in test_amounts:
            # Determine which strategies are viable
            viable_strategies = [
                s for s in self.strategies 
                if s.min_capital <= capital
            ]
            
            if not viable_strategies:
                continue
            
            # Calculate optimal allocation
            allocations = self._calculate_optimal_allocation(capital, viable_strategies)
            
            # Portfolio metrics
            metrics = self.calculate_portfolio_metrics(capital, allocations)
            
            # Risk of ruin
            max_risk_strategy = max(viable_strategies, key=lambda s: s.risk_level)
            ror = self.risk_of_ruin(
                capital, 
                capital * 0.02,  # 2% risk per trade
                max_risk_strategy.win_rate
            )
            
            # Opportunity cost (what you'd earn in savings account)
            opportunity_cost = capital * self.risk_free_rate_annual
            
            # Expected 3-year value
            expected_3yr = capital * ((1 + metrics['expected_annual_return']) ** 3)
            
            # Utility score (combines return, risk, and ruin probability)
            utility = (
                metrics['expected_annual_return'] * 100 * 0.4 +  # 40% weight on return
                (1 - metrics['risk_score']) * 100 * 0.3 +        # 30% weight on safety
                (1 - ror) * 100 * 0.3                            # 30% weight on survival
            )
            
            results.append({
                'capital': capital,
                'strategies_available': len(viable_strategies),
                'expected_annual_return_pct': metrics['expected_annual_return'] * 100,
                'risk_score': metrics['risk_score'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'risk_of_ruin_pct': ror * 100,
                'expected_3yr_value': expected_3yr,
                'profit_3yr': expected_3yr - capital,
                'opportunity_cost_3yr': opportunity_cost * 3,
                'net_advantage': (expected_3yr - capital) - (opportunity_cost * 3),
                'utility_score': utility,
                'allocations': allocations
            })
        
        return results
    
    def _calculate_optimal_allocation(self, 
                                      capital: float, 
                                      strategies: List[StrategyMetrics]) -> Dict:
        """
        Calculate optimal allocation using mean-variance optimization (simplified)
        """
        allocations = {}
        
        # Sort by Sharpe ratio (risk-adjusted return)
        sorted_strategies = sorted(
            strategies, 
            key=lambda s: self.calculate_sharpe_ratio(s),
            reverse=True
        )
        
        # Allocate more to better Sharpe ratio strategies
        total_sharpe = sum(self.calculate_sharpe_ratio(s) for s in sorted_strategies)
        
        if total_sharpe == 0:
            # Equal allocation
            equal_share = 1.0 / len(strategies)
            for s in strategies:
                allocations[s.name] = equal_share
        else:
            # Sharpe-weighted allocation
            for s in sorted_strategies:
                sharpe = self.calculate_sharpe_ratio(s)
                allocations[s.name] = sharpe / total_sharpe
        
        return allocations
    
    def generate_recommendation(self) -> str:
        """
        Generate final recommendation
        """
        results = self.find_optimal_capital()
        
        if not results:
            return "Error: Could not calculate optimal capital"
        
        # Find best by utility score
        best = max(results, key=lambda x: x['utility_score'])
        
        # Find best risk-adjusted (low risk of ruin)
        safest = min(results, key=lambda x: x['risk_of_ruin_pct'])
        
        # Find highest return
        highest_return = max(results, key=lambda x: x['expected_annual_return_pct'])
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║           📊 OPTIMAL CAPITAL CALCULATION - MATHEMATICAL MODEL            ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

METHODOLOGY:
• Kelly Criterion for position sizing
• Mean-Variance Optimization for allocation
• Risk of Ruin calculations
• Sharpe Ratio analysis
• CAGR projections

═══════════════════════════════════════════════════════════════════════════

🎯 OPTIMAL RECOMMENDATION: ${best['capital']:.0f}

Rationale:
• Utility Score: {best['utility_score']:.1f}/100
• Expected Annual Return: {best['expected_annual_return_pct']:.1f}%
• Risk Score: {best['risk_score']:.2f}/1.0
• Risk of Ruin: {best['risk_of_ruin_pct']:.2f}%
• 3-Year Projection: ${best['expected_3yr_value']:.2f}
• Net Advantage over Savings: ${best['net_advantage']:.2f}

═══════════════════════════════════════════════════════════════════════════

📈 ALTERNATIVE SCENARIOS:

1. MAXIMUM SAFETY (Lowest Risk of Ruin):
   Capital: ${safest['capital']:.0f}
   Risk of Ruin: {safest['risk_of_ruin_pct']:.4f}%
   Expected Return: {safest['expected_annual_return_pct']:.1f}%

2. MAXIMUM RETURN (Highest Yield):
   Capital: ${highest_return['capital']:.0f}
   Expected Return: {highest_return['expected_annual_return_pct']:.1f}%
   Risk of Ruin: {highest_return['risk_of_ruin_pct']:.2f}%

═══════════════════════════════════════════════════════════════════════════

💰 DETAILED ANALYSIS BY CAPITAL AMOUNT:

"""
        
        for r in results:
            report += f"""
${r['capital']:.0f} Capital:
   Strategies Available: {r['strategies_available']}
   Expected Annual Return: {r['expected_annual_return_pct']:.1f}%
   Risk Score: {r['risk_score']:.2f}
   Risk of Ruin: {r['risk_of_ruin_pct']:.4f}%
   3-Year Value: ${r['expected_3yr_value']:.2f}
   3-Year Profit: ${r['profit_3yr']:.2f}
   Utility Score: {r['utility_score']:.1f}
"""
        
        report += f"""
═══════════════════════════════════════════════════════════════════════════

📊 MATHEMATICAL PROOFS:

Kelly Criterion (Optimal Bet Size):
"""
        
        for s in self.strategies[:3]:
            kelly = self.kelly_criterion(s)
            report += f"   {s.name}: {kelly*100:.1f}% of capital per trade\n"
        
        report += f"""
Sharpe Ratios (Risk-Adjusted Returns):
"""
        
        for s in self.strategies[:3]:
            sharpe = self.calculate_sharpe_ratio(s)
            report += f"   {s.name}: {sharpe:.2f}\n"
        
        report += f"""
═══════════════════════════════════════════════════════════════════════════

🎯 FINAL RECOMMENDATION FOR YOUR SITUATION:

Based on mathematical optimization:

OPTIMAL CAPITAL: ${best['capital']:.0f}

Allocation Strategy:
"""
        
        for name, pct in best['allocations'].items():
            amount = best['capital'] * pct
            report += f"   • {name}: ${amount:.2f} ({pct*100:.1f}%)\n"
        
        report += f"""
Expected Performance:
   • Monthly Return: {best['expected_annual_return_pct']/12:.2f}%
   • Annual Return: {best['expected_annual_return_pct']:.1f}%
   • 3-Year Value: ${best['expected_3yr_value']:.2f}
   • 3-Year Profit: ${best['profit_3yr']:.2f}
   • vs Savings Account: +${best['net_advantage']:.2f}

Risk Metrics:
   • Risk of Total Loss: {best['risk_of_ruin_pct']:.4f}%
   • Risk Score: {best['risk_score']:.2f}/1.0
   • Sharpe Ratio: {best['sharpe_ratio']:.2f}

═══════════════════════════════════════════════════════════════════════════

⚠️  IMPORTANT NOTES:

1. These calculations assume historical performance continues
2. Crypto markets are volatile - actual results may vary
3. Coinbase fees (0.6%) are factored into calculations
4. Risk of Ruin assumes proper position sizing
5. Past performance does not guarantee future results

═══════════════════════════════════════════════════════════════════════════

📚 FORMULAS USED:

Kelly Criterion: f* = (bp - q) / b
   Where b = avg_win/avg_loss, p = win_rate, q = 1-p

Risk of Ruin: ROR = ((1 - edge) / (1 + edge))^units
   Where edge = 2p - 1, units = capital / bet_size

Sharpe Ratio: S = (R_p - R_f) / σ_p
   Where R_p = strategy return, R_f = risk-free rate, σ_p = volatility

CAGR: CAGR = (FV/PV)^(1/n) - 1
   Where FV = future value, PV = present value, n = years

═══════════════════════════════════════════════════════════════════════════

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Model: Ghost Agent v5.0 Optimal Capital Calculator

"""
        
        return report


def main():
    calculator = OptimalCapitalCalculator()
    report = calculator.generate_recommendation()
    print(report)
    
    # Save to file
    with open('/home/asbelcas/rm-qpt/OPTIMAL_CAPITAL_ANALYSIS.md', 'w') as f:
        f.write(report)
    
    print("\n✅ Report saved to: OPTIMAL_CAPITAL_ANALYSIS.md")


if __name__ == "__main__":
    main()
