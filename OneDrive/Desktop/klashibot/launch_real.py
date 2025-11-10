#!/usr/bin/env python3
"""
Kalshi Trading Bot - Real Trading Launcher

This script launches the bot for real trading with your API credentials.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_credentials():
    """Check if credentials are properly configured"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('KALSHI_API_KEY')
    private_key = os.getenv('KALSHI_PRIVATE_KEY')
    
    print("=" * 60)
    print("KALSHI TRADING BOT - CREDENTIAL CHECK")
    print("=" * 60)
    print()
    
    if api_key and api_key != 'REPLACE_WITH_REAL_API_KEY':
        print(f"[OK] API Key: {api_key[:10]}...{api_key[-10:]}")
    else:
        print("[ERROR] API Key: Not configured")
        return False
    
    if private_key and private_key != 'YOUR_PRIVATE_KEY_NEEDED':
        print(f"[OK] Private Key: {private_key[:10]}...{private_key[-10:]}")
    else:
        print("[ERROR] Private Key: Not configured")
        print("   You need your Kalshi private key to start trading")
        return False
    
    return True

async def launch_bot():
    """Launch the trading bot"""
    print()
    print("=" * 60)
    print("LAUNCHING KALSHI TRADING BOT")
    print("=" * 60)
    print()
    
    try:
        # Import bot components
        from main import KalshiTradingBot
        
        print("Initializing bot...")
        bot = KalshiTradingBot()
        
        print("Initializing components...")
        await bot.initialize()
        
        print("[OK] Bot initialized successfully!")
        print()
        
        # Show configuration
        print("Bot Configuration:")
        print(f"   Starting Balance: $20")
        print(f"   Daily Income Target: $400")
        print(f"   Environment: Production")
        print(f"   Growth Phases: 5 phases")
        print()
        
        print("Growth Strategy:")
        print("   Phase 1: Micro Start ($20-$50) - Ultra-conservative")
        print("   Phase 2: Small Scale ($50-$200) - Small positions")
        print("   Phase 3: Medium Scale ($200-$1000) - Medium positions")
        print("   Phase 4: Large Scale ($1000-$5000) - Large positions")
        print("   Phase 5: Target Scale ($5000+) - $400 daily income")
        print()
        
        print("Safety Features:")
        print("   Max Daily Loss: $2.00")
        print("   Max Position Size: 5 shares")
        print("   Cash Reserve: $2.00 minimum")
        print("   Conservative Risk Management")
        print()
        
        print("=" * 60)
        print("BOT READY FOR TRADING!")
        print("=" * 60)
        print()
        print("To start trading, run:")
        print("python cli.py trade --tickers TRUMP2024 ELECTION2024")
        print()
        print("To check status:")
        print("python cli.py status")
        
    except Exception as e:
        print(f"[ERROR] Error launching bot: {e}")
        print()
        print("This might be due to:")
        print("1. Missing private key")
        print("2. Invalid API credentials")
        print("3. Network connectivity issues")
        print()
        print("Please check your Kalshi API credentials and try again.")

def main():
    """Main function"""
    print("Kalshi Trading Bot Launcher")
    print("=" * 40)
    
    # Check credentials first
    if not check_credentials():
        print()
        print("[ERROR] Cannot launch bot - credentials not configured")
        print()
        print("To fix this:")
        print("1. Get your Kalshi private key")
        print("2. Edit the .env file")
        print("3. Replace 'YOUR_PRIVATE_KEY_NEEDED' with your real private key")
        print()
        print("Or run: python setup_credentials.py")
        return
    
    # Launch bot
    asyncio.run(launch_bot())

if __name__ == "__main__":
    main()
