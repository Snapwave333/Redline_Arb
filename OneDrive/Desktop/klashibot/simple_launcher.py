#!/usr/bin/env python3
"""
Simple Bot Launcher

This script launches the Kalshi Trading Bot without relative import issues.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Now we can import the bot components
from main import KalshiTradingBot

async def main():
    """Main function to run the bot"""
    print("=" * 60)
    print("KALSHI TRADING BOT - SIMPLE LAUNCHER")
    print("=" * 60)
    print()
    
    try:
        # Create bot instance
        bot = KalshiTradingBot()
        
        # Initialize bot
        print("Initializing bot...")
        await bot.initialize()
        print("[OK] Bot initialized successfully")
        
        # Start trading with some sample tickers
        sample_tickers = ["TRUMP2024", "BIDEN2024"]  # Example tickers
        print(f"Starting trading with tickers: {sample_tickers}")
        
        # Run bot for a short time to test
        print("Bot is running... Press Ctrl+C to stop")
        
        # Start trading in a separate task
        trading_task = asyncio.create_task(bot.start_trading(sample_tickers))
        
        # Wait for user interruption or trading completion
        try:
            await trading_task
        except KeyboardInterrupt:
            print("\nStopping bot...")
            await bot.stop_trading()
            await bot.cleanup()
            print("[OK] Bot stopped successfully")
            
    except Exception as e:
        print(f"[ERROR] Bot failed to start: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[INFO] Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)
