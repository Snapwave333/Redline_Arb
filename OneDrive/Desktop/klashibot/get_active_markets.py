#!/usr/bin/env python3
"""
Get Active Kalshi Markets

This script fetches currently active and liquid markets from Kalshi API
to help identify real tickers for testing the trading bot.
"""

import sys
from dotenv import load_dotenv
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
load_dotenv()

try:
    from kalshi_python import MarketsApi, PortfolioApi
    from kalshi_python.api_client import ApiClient
    from kalshi_python import Configuration
    from config import config
    import structlog
    
    logger = structlog.get_logger(__name__)

    def get_active_markets():
        """Fetch active and liquid markets from Kalshi"""
        print("="*70)
        print("FETCHING ACTIVE KALSHI MARKETS")
        print("="*70)
        
        try:
            # Initialize API client
            sdk_config = Configuration(host=config.api.kalshi_base_url)
            api_client = ApiClient(sdk_config)
            api_client.set_kalshi_auth(config.api.kalshi_api_key, config.api.kalshi_private_key)
            
            # Get markets API
            markets_api = MarketsApi(api_client)
            
            # Fetch markets
            print("\nFetching markets from Kalshi API...")
            response = markets_api.get_markets(limit=50)
            
            if not response.markets:
                print("No markets found!")
                return []
            
            # Filter for active markets (relax volume requirement for testing)
            liquid_markets = []
            for market in response.markets:
                # Only include markets that are active or open
                if market.status in ['active', 'open']:
                    liquid_markets.append({
                        'ticker': market.ticker,
                        'title': market.title,
                        'volume': getattr(market, 'volume', 0) or 0,
                        'yes_bid': getattr(market, 'yes_bid', 0),
                        'yes_ask': getattr(market, 'yes_ask', 0),
                        'no_bid': getattr(market, 'no_bid', 0),
                        'no_ask': getattr(market, 'no_ask', 0),
                        'open_interest': getattr(market, 'open_interest', 0),
                        'close_time': getattr(market, 'close_time', 'N/A')
                    })
            
            # Sort by volume (most liquid first), or by ticker if no volume data
            liquid_markets.sort(key=lambda x: (x['volume'], x['ticker']), reverse=True)
            
            # Display top markets
            print(f"\nFound {len(liquid_markets)} active markets with liquidity")
            print("\nTop 10 Most Liquid Markets:")
            print("="*70)
            
            for i, market in enumerate(liquid_markets[:10], 1):
                print(f"\n{i}. {market['ticker']}")
                print(f"   Title: {market['title']}")
                print(f"   Volume: {market['volume']:,}")
                print(f"   Open Interest: {market['open_interest']:,}")
                print(f"   Yes Bid/Ask: {market['yes_bid']} / {market['yes_ask']}")
                print(f"   No Bid/Ask: {market['no_bid']} / {market['no_ask']}")
                print(f"   Close Time: {market['close_time']}")
            
            # Save top tickers to file for easy use
            top_tickers = [m['ticker'] for m in liquid_markets[:10]]
            with open('active_markets.txt', 'w') as f:
                f.write('\n'.join(top_tickers))
            
            print(f"\n{'='*70}")
            print("Top 10 tickers saved to: active_markets.txt")
            print(f"Use these tickers to test the bot:")
            print(f"python -m src.main --tickers {' '.join(top_tickers[:3])} --dry-run")
            print("="*70)
            
            return liquid_markets
            
        except Exception as e:
            print(f"Error fetching markets: {e}")
            import traceback
            traceback.print_exc()
            return []

    if __name__ == "__main__":
        get_active_markets()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have kalshi-python installed and config files are set up.")
except Exception as e:
    print(f"Unexpected error: {e}")

