#!/usr/bin/env python3
import os
from pathlib import Path
from kalshi_python import Configuration, MarketsApi
from kalshi_python.api_client import ApiClient

API_KEY = os.getenv('KALSHI_API_KEY', '8fe1b2e5-e094-4c1c-900f-27a02248c21a')

def find_private_key():
    search_paths = ['config/kalshi_private_key.pem', 'kalshi_private_key.pem']
    for path_str in search_paths:
        if Path(path_str).exists():
            return Path(path_str)
    raise FileNotFoundError("Could not find kalshi_private_key.pem")

config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
api_client = ApiClient(config)
api_client.set_kalshi_auth(API_KEY, str(find_private_key()))
markets_api = MarketsApi(api_client)

response = markets_api.get_markets(limit=1000)
print(f"Checking {len(response.markets)} markets for ANY with YES price > 0\n")

found_any = []
for m in response.markets:
    yes_bid = getattr(m, 'yes_bid', 0)
    no_bid = getattr(m, 'no_bid', 0)
    if yes_bid and yes_bid > 0 and no_bid and no_bid > 0:
        yes_price = yes_bid / 100
        no_price = no_bid / 100
        found_any.append({
            'ticker': m.ticker,
            'status': m.status,
            'yes': yes_price,
            'no': no_price
        })

if found_any:
    print(f"Found {len(found_any)} markets with valid pricing:\n")
    for i, m in enumerate(found_any[:20], 1):
        print(f"{i}. {m['ticker'][:60]}")
        print(f"   Status: {m['status']}")
        print(f"   YES: ${m['yes']:.2f}  NO: ${m['no']:.2f}\n")
else:
    print("❌ NO MARKETS WITH VALID PRICING FOUND!")
    print("\nAll 1000 markets have YES=$0.00 or settled pricing.")
    print("This is normal - Kalshi markets may be between events.")
    print("The bot will work when new markets are listed!")

