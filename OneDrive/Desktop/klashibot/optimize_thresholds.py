#!/usr/bin/env python3
"""
Threshold Optimization Tool

This tool helps optimize trading thresholds by analyzing different configurations
and their impact on trading performance.
"""

import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from src.edge_calculator import EdgeCalculator, EdgeResult
from src.config import config, TradingThresholdConfig

@dataclass
class OptimizationResult:
    """Result of threshold optimization"""
    profile_name: str
    total_trades: int
    winning_trades: int
    win_rate: float
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    avg_edge: float
    avg_position_size: float
    trades_per_day: float

class ThresholdOptimizer:
    """Optimizes trading thresholds using simulation"""
    
    def __init__(self):
        self.results: List[OptimizationResult] = []
    
    def load_threshold_profiles(self) -> Dict[str, Dict]:
        """Load threshold profiles from config file"""
        try:
            with open('config/threshold_profiles.json', 'r') as f:
                profiles_data = json.load(f)
            return profiles_data['profiles']
        except FileNotFoundError:
            print("Warning: threshold_profiles.json not found, using default profiles")
            return self._get_default_profiles()
    
    def _get_default_profiles(self) -> Dict[str, Dict]:
        """Default threshold profiles if config file is missing"""
        return {
            "conservative": {
                "MIN_EDGE_THRESHOLD": 0.05,
                "MIN_MODEL_CONFIDENCE": 0.65,
                "BASE_KELLY_FRACTION": 0.03,
                "MIN_LIQUIDITY_CENTS": 200,
                "MAX_SPREAD_PERCENT": 0.08,
                "MIN_VOLUME": 20
            },
            "balanced": {
                "MIN_EDGE_THRESHOLD": 0.02,
                "MIN_MODEL_CONFIDENCE": 0.55,
                "BASE_KELLY_FRACTION": 0.05,
                "MIN_LIQUIDITY_CENTS": 100,
                "MAX_SPREAD_PERCENT": 0.10,
                "MIN_VOLUME": 10
            },
            "aggressive": {
                "MIN_EDGE_THRESHOLD": 0.01,
                "MIN_MODEL_CONFIDENCE": 0.52,
                "BASE_KELLY_FRACTION": 0.08,
                "MIN_LIQUIDITY_CENTS": 50,
                "MAX_SPREAD_PERCENT": 0.15,
                "MIN_VOLUME": 5
            }
        }
    
    def simulate_trading_performance(self, profile_name: str, profile_config: Dict) -> OptimizationResult:
        """
        Simulate trading performance with given threshold profile
        
        This is a simplified simulation - in a real implementation, you would:
        1. Load historical market data
        2. Run the bot with different thresholds
        3. Calculate actual performance metrics
        """
        
        # Create TradingThresholdConfig object from profile config
        threshold_config = TradingThresholdConfig(
            min_edge_threshold=profile_config.get('MIN_EDGE_THRESHOLD', 0.02),
            optimal_edge_threshold=profile_config.get('OPTIMAL_EDGE_THRESHOLD', 0.05),
            max_edge_threshold=profile_config.get('MAX_EDGE_THRESHOLD', 0.15),
            base_kelly_fraction=profile_config.get('BASE_KELLY_FRACTION', 0.05),
            max_kelly_fraction=profile_config.get('MAX_KELLY_FRACTION', 0.25),
            kelly_scaling_factor=profile_config.get('KELLY_SCALING_FACTOR', 2.0),
            min_model_confidence=profile_config.get('MIN_MODEL_CONFIDENCE', 0.55),
            high_confidence_threshold=profile_config.get('HIGH_CONFIDENCE_THRESHOLD', 0.70),
            min_liquidity_cents=profile_config.get('MIN_LIQUIDITY_CENTS', 100),
            max_spread_percent=profile_config.get('MAX_SPREAD_PERCENT', 0.10),
            min_volume=profile_config.get('MIN_VOLUME', 10)
        )
        
        # Create edge calculator with profile config
        edge_calc = EdgeCalculator(threshold_config)
        
        # Simulate market scenarios
        scenarios = self._generate_test_scenarios()
        
        trades = []
        total_pnl = 0.0
        account_balance = 100.0  # Start with $100
        
        for scenario in scenarios:
            market_data = scenario['market_data']
            model_prob = scenario['model_probability']
            model_conf = scenario['model_confidence']
            
            # Calculate edge
            edge_result = edge_calc.calculate_comprehensive_edge(
                market_data=market_data,
                model_probability=model_prob,
                model_confidence=model_conf,
                account_balance=account_balance
            )
            
            if edge_result.meets_threshold:
                # Simulate trade outcome
                trade_pnl = self._simulate_trade_outcome(edge_result, scenario)
                trades.append({
                    'edge': edge_result.edge,
                    'position_size': edge_result.recommended_position,
                    'pnl': trade_pnl,
                    'confidence': edge_result.confidence_score,
                    'market_quality': edge_result.market_quality_score
                })
                
                total_pnl += trade_pnl
                account_balance += trade_pnl
        
        # Calculate performance metrics
        if trades:
            winning_trades = sum(1 for t in trades if t['pnl'] > 0)
            win_rate = winning_trades / len(trades)
            avg_edge = np.mean([t['edge'] for t in trades])
            avg_position = np.mean([t['position_size'] for t in trades])
            
            # Calculate Sharpe ratio (simplified)
            returns = [t['pnl'] for t in trades]
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
            
            # Calculate max drawdown (simplified)
            cumulative_pnl = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative_pnl)
            drawdowns = running_max - cumulative_pnl
            max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
            
            trades_per_day = len(trades) / 30  # Assume 30-day simulation
        else:
            winning_trades = 0
            win_rate = 0.0
            avg_edge = 0.0
            avg_position = 0.0
            sharpe_ratio = 0.0
            max_drawdown = 0.0
            trades_per_day = 0.0
        
        return OptimizationResult(
            profile_name=profile_name,
            total_trades=len(trades),
            winning_trades=winning_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            avg_edge=avg_edge,
            avg_position_size=avg_position,
            trades_per_day=trades_per_day
        )
    
    def _generate_test_scenarios(self) -> List[Dict]:
        """Generate test market scenarios for simulation"""
        scenarios = []
        
        # High edge scenarios
        scenarios.extend([
            {
                'market_data': {
                    'ticker': f'HIGH-EDGE-{i}',
                    'yes_bid': 40, 'yes_ask': 45,
                    'no_bid': 50, 'no_ask': 55,
                    'volume': 200, 'open_interest': 1000
                },
                'model_probability': 0.65,
                'model_confidence': 0.75,
                'outcome_probability': 0.70  # Higher chance of winning
            }
            for i in range(10)
        ])
        
        # Medium edge scenarios
        scenarios.extend([
            {
                'market_data': {
                    'ticker': f'MED-EDGE-{i}',
                    'yes_bid': 45, 'yes_ask': 50,
                    'no_bid': 50, 'no_ask': 55,
                    'volume': 100, 'open_interest': 500
                },
                'model_probability': 0.60,
                'model_confidence': 0.65,
                'outcome_probability': 0.60
            }
            for i in range(15)
        ])
        
        # Low edge scenarios
        scenarios.extend([
            {
                'market_data': {
                    'ticker': f'LOW-EDGE-{i}',
                    'yes_bid': 48, 'yes_ask': 52,
                    'no_bid': 48, 'no_ask': 52,
                    'volume': 50, 'open_interest': 200
                },
                'model_probability': 0.55,
                'model_confidence': 0.60,
                'outcome_probability': 0.55
            }
            for i in range(20)
        ])
        
        # Poor quality markets
        scenarios.extend([
            {
                'market_data': {
                    'ticker': f'POOR-QUALITY-{i}',
                    'yes_bid': 0, 'yes_ask': 0,
                    'no_bid': 0, 'no_ask': 0,
                    'volume': 5, 'open_interest': 50
                },
                'model_probability': 0.70,
                'model_confidence': 0.80,
                'outcome_probability': 0.50
            }
            for i in range(5)
        ])
        
        return scenarios
    
    def _simulate_trade_outcome(self, edge_result: EdgeResult, scenario: Dict) -> float:
        """Simulate the outcome of a trade"""
        # Use scenario outcome probability to determine if trade wins
        outcome_prob = scenario['outcome_probability']
        
        # Add some randomness
        import random
        actual_outcome = random.random() < outcome_prob
        
        if actual_outcome:
            # Winning trade - profit based on edge and position size
            profit_factor = abs(edge_result.edge) * 2  # Scale profit by edge
            return edge_result.recommended_position * profit_factor / 100
        else:
            # Losing trade - loss based on position size
            return -edge_result.recommended_position / 100
    
    def optimize_thresholds(self) -> List[OptimizationResult]:
        """Run optimization across all threshold profiles"""
        profiles = self.load_threshold_profiles()
        
        print("Running Threshold Optimization")
        print("="*60)
        
        for profile_name, profile_config in profiles.items():
            print(f"\nTesting {profile_name} profile...")
            
            result = self.simulate_trading_performance(profile_name, profile_config)
            self.results.append(result)
            
            print(f"  Trades: {result.total_trades}")
            print(f"  Win Rate: {result.win_rate:.1%}")
            print(f"  Total PnL: ${result.total_pnl:.2f}")
            print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"  Max Drawdown: ${result.max_drawdown:.2f}")
            print(f"  Avg Edge: {result.avg_edge:.1%}")
            print(f"  Trades/Day: {result.trades_per_day:.1f}")
        
        return self.results
    
    def print_optimization_summary(self):
        """Print optimization results summary"""
        if not self.results:
            print("No optimization results available")
            return
        
        print("\n" + "="*60)
        print("OPTIMIZATION SUMMARY")
        print("="*60)
        
        # Sort by Sharpe ratio (best risk-adjusted returns)
        sorted_results = sorted(self.results, key=lambda x: x.sharpe_ratio, reverse=True)
        
        print(f"\n{'Profile':<12} {'Trades':<6} {'Win%':<6} {'PnL':<8} {'Sharpe':<7} {'Drawdown':<9} {'Trades/Day':<10}")
        print("-" * 70)
        
        for result in sorted_results:
            print(f"{result.profile_name:<12} {result.total_trades:<6} "
                  f"{result.win_rate:<6.1%} ${result.total_pnl:<7.2f} "
                  f"{result.sharpe_ratio:<7.2f} ${result.max_drawdown:<8.2f} "
                  f"{result.trades_per_day:<10.1f}")
        
        # Recommendations
        best_overall = sorted_results[0]
        best_win_rate = max(self.results, key=lambda x: x.win_rate)
        most_trades = max(self.results, key=lambda x: x.trades_per_day)
        
        print(f"\nRECOMMENDATIONS:")
        print(f"  Best Overall (Sharpe): {best_overall.profile_name}")
        print(f"  Highest Win Rate: {best_win_rate.profile_name} ({best_win_rate.win_rate:.1%})")
        print(f"  Most Active: {most_trades.profile_name} ({most_trades.trades_per_day:.1f} trades/day)")
        
        print(f"\nTo use the recommended profile, update your .env file:")
        print(f"  MIN_EDGE_THRESHOLD={best_overall.profile_name.upper()}_MIN_EDGE_THRESHOLD")
        print(f"  MIN_MODEL_CONFIDENCE={best_overall.profile_name.upper()}_MIN_MODEL_CONFIDENCE")
        print(f"  BASE_KELLY_FRACTION={best_overall.profile_name.upper()}_BASE_KELLY_FRACTION")

def main():
    """Main optimization function"""
    optimizer = ThresholdOptimizer()
    results = optimizer.optimize_thresholds()
    optimizer.print_optimization_summary()

if __name__ == "__main__":
    main()
