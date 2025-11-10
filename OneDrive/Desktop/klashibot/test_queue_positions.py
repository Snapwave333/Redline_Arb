#!/usr/bin/env python3
from kalshi_python import PortfolioApi, ApiClient, Configuration

api_key = '8fe1b2e5-e094-4c1c-900f-27a02248c21a'
config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
api = ApiClient(config)
api.set_kalshi_auth(api_key, 'kalshi_private_key.pem')

portfolio_api = PortfolioApi(api)

print("Trying get_positions...")
resp = portfolio_api.get_positions()
print(f"Positions: {resp.positions}")

print("\nTrying get_queue_positions...")
try:
    resp2 = portfolio_api.get_queue_positions()
    print(f"Queue positions: {resp2}")
except Exception as e:
    print(f"Error: {e}")

