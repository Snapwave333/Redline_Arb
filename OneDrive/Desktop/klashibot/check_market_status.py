#!/usr/bin/env python3
"""Check market statuses"""
import os
from pathlib import Path
from kalshi_python import Configuration, MarketsApi
from kalshi_python.api_client import ApiClient
from collections import Counter

API_KEY = os.getenv('KALSHI_API_KEY', '8fe1b2e5-e094-4c1c-900f-27a02248c21a')

def find_private_key():
    search_paths = ['config/kalshi_private_key.pem', 'kalshi_private_key.pem']
    for path_str in search_paths:
        path = Path(path_str)
        if path.exists():
            return path
    raise FileNotFoundError("Could not find kalshi_private_key.pem")

private_key = find_private_key()
config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
api_client = ApiClient(config)
api_client.set_kalshi_auth(API_KEY, str(private_key))
markets_api = MarketsApi(api_client)

try:
    response = markets_api.get_markets(limit=500)
    
    if response.markets:
        print(f"\nTotal markets: {len(response.markets)}\n")
        
        statuses = Counter()
        for m in response.markets:
            status = m.status
            statuses[status] += 1
        
        print("Market Status Breakdown:")
        for status, count in statuses.items():
            print(f"  {status}: {count}")
        
        # Show sample markets from each status
        print("\nSample markets by status:")
        for status in statuses.keys():
            for m in response.markets:
                if m.status == status:
                    yes_b = getattr(m, 'yes_bid', 0) / 100 if getattr(m, 'yes_bid', 0) else 0
                    no_b = getattr(m, 'no_bid', 0) / 100 if getattr(m, 'no_bid', 0) else 0
                    print(f"\n  {status}: {m.ticker[:50]}")
                    print(f"    YES: ${yes_b:.2f}  NO: ${no_b:.2f}")
                    break
                    
except Exception as e:
    print(f"Error: {e}")


