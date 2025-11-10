#!/usr/bin/env python3
"""Test the new edge calculator integration"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from src.edge_calculator import EdgeCalculator, EdgeResult
from src.config import config

def test_edge_calculator():
    print("Testing Edge Calculator Integration")
    print("="*50)
    
    # Initialize edge calculator
    edge_calc = EdgeCalculator(config.thresholds)
    
    # Test market data
    market_data = {
        'ticker': 'TEST-MARKET',
        'yes_bid': 45,
        'yes_ask': 50,
        'no_bid': 50,
        'no_ask': 55,
        'volume': 100,
        'open_interest': 500
    }
    
    # Test parameters
    model_probability = 0.60  # Model thinks 60% chance
    model_confidence = 0.70   # 70% confident
    account_balance = 100.0   # $100 balance
    
    print(f"Market Data: {market_data}")
    print(f"Model Probability: {model_probability:.1%}")
    print(f"Model Confidence: {model_confidence:.1%}")
    print(f"Account Balance: ${account_balance}")
    print()
    
    # Calculate comprehensive edge
    result = edge_calc.calculate_comprehensive_edge(
        market_data=market_data,
        model_probability=model_probability,
        model_confidence=model_confidence,
        account_balance=account_balance
    )
    
    print("Edge Analysis Results:")
    print(f"  Edge: {result.edge:.3f} ({result.edge*100:.1f}%)")
    print(f"  Implied Probability: {result.implied_probability:.1%}")
    print(f"  Model Probability: {result.model_probability:.1%}")
    print(f"  Meets Threshold: {result.meets_threshold}")
    print(f"  Recommended Position: ${result.recommended_position/100:.2f}")
    print(f"  Confidence Score: {result.confidence_score:.1%}")
    print(f"  Market Quality Score: {result.market_quality_score:.2f}")
    
    print("\nThreshold Configuration:")
    print(f"  Min Edge Threshold: {config.thresholds.min_edge_threshold:.1%}")
    print(f"  Min Confidence: {config.thresholds.min_model_confidence:.1%}")
    print(f"  Base Kelly Fraction: {config.thresholds.base_kelly_fraction:.1%}")
    
    if result.meets_threshold:
        print("\n[SUCCESS] Edge meets threshold - trade would be recommended!")
    else:
        print("\n[INFO] Edge does not meet threshold - no trade recommended")
    
    print("\n" + "="*50)
    print("Edge Calculator Integration Test Complete")

if __name__ == "__main__":
    test_edge_calculator()
