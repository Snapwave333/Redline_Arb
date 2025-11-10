#!/usr/bin/env python3
"""Quick test of optimization tool"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from optimize_thresholds import ThresholdOptimizer

def quick_test():
    print("Quick Optimization Test")
    print("="*30)
    
    optimizer = ThresholdOptimizer()
    
    # Test just one profile
    profiles = optimizer.load_threshold_profiles()
    conservative = profiles['conservative']
    
    print(f"Testing conservative profile...")
    result = optimizer.simulate_trading_performance('conservative', conservative)
    
    print(f"Results:")
    print(f"  Trades: {result.total_trades}")
    print(f"  Win Rate: {result.win_rate:.1%}")
    print(f"  Total PnL: ${result.total_pnl:.2f}")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
    
    print("\nOptimization tool is working!")

if __name__ == "__main__":
    quick_test()
