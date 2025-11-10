#!/usr/bin/env python3
"""
Kalshi Orderbook Structure Diagnostic Tool

This script inspects the actual structure of the Kalshi SDK's orderbook response
to identify the correct attribute names for accessing bid/ask prices.
"""

import os
import sys
from pathlib import Path
from pprint import pprint
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
load_dotenv()

try:
    from kalshi_python import MarketsApi, ApiClient, Configuration
    from config import config
    import structlog
    
    logger = structlog.get_logger(__name__)

    def diagnose_orderbook_structure():
        """Fetches and analyzes the orderbook structure"""
        print("="*70)
        print("KALSHI ORDERBOOK STRUCTURE DIAGNOSTIC")
        print("="*70)
        
        try:
            # Initialize API client
            sdk_config = Configuration(host=config.api.kalshi_base_url)
            api_client = ApiClient(sdk_config)
            api_client.set_kalshi_auth(config.api.kalshi_api_key, config.api.kalshi_private_key)
            
            # Get markets API
            markets_api = MarketsApi(api_client)
            
            # Get a real active market
            print("\nStep 1: Fetching active markets...")
            markets_response = markets_api.get_markets(limit=10)
            
            if not markets_response.markets:
                print("No markets found!")
                return
            
            # Find first active market
            active_market = None
            for market in markets_response.markets:
                if market.status == 'active':
                    active_market = market
                    break
            
            if not active_market:
                print("No active markets found!")
                return
            
            ticker = active_market.ticker
            print(f"Using market: {ticker}")
            print(f"Title: {active_market.title}")
            
            # Also analyze the market object itself
            print("\n" + "="*70)
            print("MARKET OBJECT ANALYSIS (for bid/ask data)")
            print("="*70)
            print(f"\nMarket attributes with 'bid' or 'ask':")
            market_attrs = [attr for attr in dir(active_market) if 'bid' in attr.lower() or 'ask' in attr.lower()]
            for attr in market_attrs:
                try:
                    value = getattr(active_market, attr)
                    if not callable(value):
                        print(f"  {attr}: {value}")
                except:
                    pass
            
            # Fetch orderbook
            print(f"\nStep 2: Fetching orderbook for {ticker}...")
            orderbook_response = markets_api.get_market_orderbook(ticker=ticker)
            
            if not orderbook_response.orderbook:
                print("Orderbook is empty!")
                return
            
            orderbook = orderbook_response.orderbook
            
            # Analyze structure
            print("\n" + "="*70)
            print("ORDERBOOK OBJECT ANALYSIS")
            print("="*70)
            
            print(f"\nObject Type: {type(orderbook)}")
            print(f"\nObject Class: {orderbook.__class__.__name__}")
            
            # Get all attributes
            print("\nAll Attributes:")
            attrs = [attr for attr in dir(orderbook) if not attr.startswith('_')]
            for attr in attrs:
                print(f"  - {attr}")
            
            # Try to convert to dict
            print("\n" + "="*70)
            print("ORDERBOOK CONTENT (as dictionary)")
            print("="*70)
            try:
                orderbook_dict = orderbook.to_dict()
                pprint(orderbook_dict, width=70)
            except Exception as e:
                print(f"Could not convert to dict: {e}")
                # Try accessing attributes directly
                print("\nDirect attribute access:")
                for attr in attrs:
                    try:
                        value = getattr(orderbook, attr)
                        if not callable(value):
                            print(f"  {attr}: {value}")
                    except:
                        pass
            
            # Test old attribute access (should fail)
            print("\n" + "="*70)
            print("TESTING OLD ATTRIBUTE ACCESS (Expected to Fail)")
            print("="*70)
            
            old_attrs = ['yes_bid', 'yes_ask', 'no_bid', 'no_ask', 
                        'yes_bid_size', 'yes_ask_size', 'no_bid_size', 'no_ask_size']
            
            for attr in old_attrs:
                try:
                    value = getattr(orderbook, attr, None)
                    if value is not None:
                        print(f"OK {attr}: {value} (EXISTS)")
                    else:
                        print(f"NO {attr}: None (attribute exists but is None)")
                except AttributeError:
                    print(f"NO {attr}: AttributeError (does not exist)")
            
            # Suggest correct access pattern
            print("\n" + "="*70)
            print("SUGGESTED CORRECT ACCESS PATTERN")
            print("="*70)
            
            if hasattr(orderbook, 'yes') and orderbook.yes:
                print("\nFound 'yes' attribute:")
                print(f"  Type: {type(orderbook.yes)}")
                if isinstance(orderbook.yes, list) and len(orderbook.yes) > 0:
                    print(f"  First element: {orderbook.yes[0]}")
                    if hasattr(orderbook.yes[0], 'price'):
                        print(f"  Access pattern: orderbook.yes[0].price")
                else:
                    print(f"  Content: {orderbook.yes}")
            
            if hasattr(orderbook, 'no') and orderbook.no:
                print("\nFound 'no' attribute:")
                print(f"  Type: {type(orderbook.no)}")
                if isinstance(orderbook.no, list) and len(orderbook.no) > 0:
                    print(f"  First element: {orderbook.no[0]}")
                    if hasattr(orderbook.no[0], 'price'):
                        print(f"  Access pattern: orderbook.no[0].price")
                else:
                    print(f"  Content: {orderbook.no}")
            
            print("\n" + "="*70)
            print("DIAGNOSTIC COMPLETE")
            print("="*70)
            print("\nUse the information above to update src/kalshi_client.py")
            print("with the correct attribute access patterns.")
            
        except Exception as e:
            print(f"\nError during diagnostic: {e}")
            import traceback
            traceback.print_exc()

    if __name__ == "__main__":
        diagnose_orderbook_structure()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure kalshi-python is installed and config files are set up.")
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()

