#!/usr/bin/env python3
"""Quick test of bot with orderbook fix"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from src.kalshi_client import KalshiAPIClient

async def test():
    print("Testing orderbook fix...")
    client = KalshiAPIClient()
    
    # First get a market with actual bids
    print("\nFetching markets to find one with bids...")
    markets = await client.get_markets(limit=20)
    
    test_ticker = None
    for market in markets:
        if market.get('yes_bid', 0) > 0 or market.get('no_bid', 0) > 0:
            test_ticker = market['ticker']
            print(f"Found market with bids: {test_ticker}")
            print(f"  Yes bid: {market.get('yes_bid', 0)}, No bid: {market.get('no_bid', 0)}")
            break
    
    if not test_ticker:
        print("No markets with bids found, using default ticker")
        test_ticker = "KXMVENFLSINGLEGAME-S20258298B847C8B-635C6813EEE"
    
    print(f"\nFetching orderbook for {test_ticker}...")
    orderbook = await client.get_market_orderbook(test_ticker)
    
    print(f"\nOrderbook data:")
    print(f"  Yes best price: {orderbook['yes']['best_price']}")
    print(f"  No best price: {orderbook['no']['best_price']}")
    
    if orderbook['yes']['best_price'] > 0 or orderbook['no']['best_price'] > 0:
        print("\n[SUCCESS] Orderbook fix working!")
    else:
        print("\n[WARNING] Prices are still zero - market may have no bids")

asyncio.run(test())

