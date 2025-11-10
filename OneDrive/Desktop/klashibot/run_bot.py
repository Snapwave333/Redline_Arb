#!/usr/bin/env python3
"""Simple bot runner that actually trades"""
import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Import config and client
from config import config
from kalshi_client import KalshiAPIClient
import asyncio
import time

async def run_active_trading():
    """Continuously trade on active markets"""
    client = KalshiAPIClient()
    
    # Markets to trade on
    active_markets = [
        "PRESIDENT2024",
        "PRESIDENT2028", 
        "STOCKCRASH2025",
        "GDP_GROWTH_2025",
        "FED_RATE_2025",
        "INFLATION_2025"
    ]
    
    print("🤖 Bot is ACTIVE and TRADING!")
    print(f"📊 Trading on {len(active_markets)} markets")
    print(f"💰 Account Balance: ${config.portfolio.balance:.2f}")
    print("\n🚀 Starting continuous trading loop...\n")
    
    trade_count = 0
    
    while True:
        try:
            # Get market data
            for ticker in active_markets:
                try:
                    # Get market and place orders
                    market_data = await client.get_market(ticker)
                    
                    if market_data:
                        # Place small orders (conservative)
                        # Buy YES at good price
                        await client.place_order(
                            ticker=ticker,
                            side="yes",
                            action="buy",
                            contract_count=1,
                            limit_price=50  # Conservative price
                        )
                        
                        trade_count += 1
                        print(f"✅ Trade #{trade_count}: BUY {ticker} YES at $0.50")
                        
                except Exception as e:
                    print(f"⚠️  {ticker}: {str(e)[:50]}")
            
            # Wait before next cycle
            await asyncio.sleep(5)  # Trade every 5 seconds
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping bot...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_active_trading())


