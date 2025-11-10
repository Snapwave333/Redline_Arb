#!/usr/bin/env python3
"""Find markets with valid pricing"""
import os
from pathlib import Path
from kalshi_python import Configuration, MarketsApi
from kalshi_python.api_client import ApiClient

API_KEY = os.getenv('KALSHI_API_KEY', '8fe1b2e5-e094-4c1c-900f-27a02248c21a')

def find_private_key():
    search_paths = ['config/kalshi_private_key.pem', 'kalshi_private_key.pem', Path(__file__).parent / 'kalshi_private_key.pem']
    for path_str in search_paths:
        path = Path(path_str)
        if path.exists():
            return path
    raise FileNotFoundError("Could not find kalshi_private_key.pem")

print("SEARCHING FOR TRADEABLE MARKETS...")
print("="*70)

private_key = find_private_key()
config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
api_client = ApiClient(config)
api_client.set_kalshi_auth(API_KEY, str(private_key))
markets_api = MarketsApi(api_client)

try:
    response = markets_api.get_markets(limit=100)
    
    if response and response.markets:
        valid_markets = []
        for market in response.markets:
            if market.status == 'open':
                yes_bid = getattr(market, 'yes_bid', 0)
                no_bid = getattr(market, 'no_bid', 0)
                
                if yes_bid and no_bid:
                    yes_price = yes_bid / 100
                    no_price = no_bid / 100
                    
                    # Valid pricing means YES and NO are both between 0.10 and 0.90
                    if 0.10 <= yes_price <= 0.90 and 0.10 <= no_price <= 0.90:
                        valid_markets.append({
                            'ticker': market.ticker,
                            'yes_price': yes_price,
                            'no_price': no_price
                        })
        
        print(f"\nFound {len(valid_markets)} tradeable markets with valid pricing:\n")
        for i, m in enumerate(valid_markets[:10], 1):
            print(f"{i}. {m['ticker'][:50]}")
            print(f"   YES: ${m['yes_price']:.2f}  NO: ${m['no_price']:.2f}")
        
        if not valid_markets:
            print("\nNO VALID MARKETS FOUND!")
            print("All markets have YES=$0.00 or invalid pricing.")
            print("\nTrying different market categories...")
            
            # Try to get more markets
            all_markets = []
            for limit in [100, 200, 500]:
                try:
                    resp = markets_api.get_markets(limit=limit)
                    if resp.markets:
                        all_markets.extend(resp.markets)
                except:
                    pass
            
            print(f"\nChecked {len(all_markets)} total markets")
            open_markets = [m for m in all_markets if m.status == 'open']
            print(f"Found {len(open_markets)} open markets")
            
            for m in open_markets[:5]:
                yes_b = getattr(m, 'yes_bid', 0) / 100 if getattr(m, 'yes_bid', 0) else 0
                no_b = getattr(m, 'no_bid', 0) / 100 if getattr(m, 'no_bid', 0) else 0
                print(f"  {m.ticker[:40]}: YES=${yes_b:.2f} NO=${no_b:.2f}")
        
    else:
        print("No markets returned!")
        
except Exception as e:
    print(f"Error: {e}")

