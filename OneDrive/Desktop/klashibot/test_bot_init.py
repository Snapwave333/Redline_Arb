#!/usr/bin/env python3
"""
Test Bot Initialization

This script tests the bot initialization process to identify
where the 404 error is actually occurring.
"""

import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

try:
    from src.main import KalshiTradingBot
    
    async def test_bot_init():
        print("="*70)
        print("BOT INITIALIZATION TEST")
        print("="*70)
        
        try:
            bot = KalshiTradingBot()
            print("SUCCESS: Bot instance created")
            
            print("\nInitializing bot...")
            await bot.initialize()
            print("SUCCESS: Bot initialization completed successfully!")
            
        except Exception as e:
            print(f"FAILED: Bot initialization failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    asyncio.run(test_bot_init())
    
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

