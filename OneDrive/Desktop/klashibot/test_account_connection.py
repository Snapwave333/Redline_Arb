#!/usr/bin/env python3
"""Test connection to actual Kalshi account"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_connection():
    from src.kalshi_client import KalshiAPIClient
    
    print("=" * 60)
    print("TESTING KALSHI ACCOUNT CONNECTION")
    print("=" * 60)
    print()
    
    try:
        client = KalshiAPIClient()
        print("✅ Initializing client...")
        await client.__aenter__()
        
        print("✅ Fetching portfolio...")
        portfolio = await client.get_portfolio()
        print()
        print("YOUR REAL ACCOUNT DATA:")
        print("-" * 60)
        print(f"Portfolio: {portfolio}")
        print()
        
        print("✅ Account connected successfully!")
        print()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
