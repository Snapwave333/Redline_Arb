#!/usr/bin/env python3
"""
Test bot portfolio functionality with elections API
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from src.kalshi_client import KalshiAPIClient

async def test_portfolio_functionality():
    """Test portfolio functionality"""
    print("Testing Portfolio Functionality with Elections API")
    print("=" * 60)
    
    try:
        # Initialize client
        client = KalshiAPIClient()
        print("SUCCESS: Client initialized")
        
        # Test portfolio
        print("\nTesting get_portfolio()...")
        portfolio = await client.get_portfolio()
        print(f"SUCCESS: Portfolio retrieved")
        print(f"  Balance: ${portfolio.get('balance', 0):.2f}")
        print(f"  Total Value: ${portfolio.get('total_value', 0):.2f}")
        print(f"  Positions: {len(portfolio.get('positions', []))}")
        
        # Test positions
        print("\nTesting get_positions()...")
        positions = await client.get_positions()
        print(f"SUCCESS: Positions retrieved - {len(positions)} positions")
        
        # Test markets
        print("\nTesting get_markets()...")
        markets = await client.get_markets(limit=5)
        print(f"SUCCESS: Markets retrieved - {len(markets)} markets")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_portfolio_functionality())
