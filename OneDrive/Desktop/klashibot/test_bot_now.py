#!/usr/bin/env python3
"""Test bot - see if we can fetch markets and place trades"""
import os
from pathlib import Path
from kalshi_python import Configuration, MarketsApi, PortfolioApi, ExchangeApi
from kalshi_python.api_client import ApiClient

API_KEY = os.getenv('KALSHI_API_KEY', '8fe1b2e5-e094-4c1c-900f-27a02248c21a')

def find_private_key():
    search_paths = [
        'config/kalshi_private_key.pem',
        'kalshi_private_key.pem',
        Path(__file__).parent / 'kalshi_private_key.pem'
    ]
    for path_str in search_paths:
        path = Path(path_str)
        if path.exists():
            return path
    raise FileNotFoundError("Could not find kalshi_private_key.pem")

print("="*70)
print("TESTING KALSHI API")
print("="*70)

private_key = find_private_key()
config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
api_client = ApiClient(config)
api_client.set_kalshi_auth(API_KEY, str(private_key))

portfolio_api = PortfolioApi(api_client)
markets_api = MarketsApi(api_client)
exchange_api = ExchangeApi(api_client)

# Test 1: Get balance
print("\nTEST 1: Get Balance")
print("-"*70)
try:
    balance_response = portfolio_api.get_balance()
    balance = balance_response.balance / 100
    print(f"SUCCESS: Balance = ${balance:.2f}")
except Exception as e:
    print(f"FAILED: {e}")

# Test 2: Get markets
print("\nTEST 2: Get Markets")
print("-"*70)
try:
    response = markets_api.get_markets(limit=5)
    if response and response.markets:
        print(f"SUCCESS: Found {len(response.markets)} markets")
        for i, market in enumerate(response.markets[:3], 1):
            print(f"  {i}. {market.ticker}: status={market.status}")
            if hasattr(market, 'yes_bid'):
                yes_bid = getattr(market, 'yes_bid', 0) / 100
                no_bid = getattr(market, 'no_bid', 0) / 100
                print(f"     YES: ${yes_bid:.2f}  NO: ${no_bid:.2f}")
    else:
        print("FAILED: No markets returned")
except Exception as e:
    print(f"FAILED: {e}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)

