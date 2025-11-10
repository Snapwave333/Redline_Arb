#!/usr/bin/env python3
"""
Start Kalshi Trading Bot

This script starts the bot with proper initialization.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    import asyncio
    from main import KalshiTradingBot
    
    async def run():
        bot = KalshiTradingBot()
        try:
            print("Initializing bot...")
            await bot.initialize()
            print("[OK] Bot initialized")
            
            # Get tickers from active_markets.txt
            tickers = []
            if Path("active_markets.txt").exists():
                with open("active_markets.txt") as f:
                    tickers = [line.strip() for line in f if line.strip()][:3]
            
            if not tickers:
                tickers = ["TRUMP2024"]  # Fallback
                
            print(f"Starting trading with: {tickers}")
            await bot.start_trading(tickers)
            
        except KeyboardInterrupt:
            print("\nStopping bot...")
            await bot.stop_trading()
            await bot.cleanup()
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run())


