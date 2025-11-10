#!/usr/bin/env python3
from kalshi_python import PortfolioApi, ApiClient, Configuration
import os

api_key = '8fe1b2e5-e094-4c1c-900f-27a02248c21a'
config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
api = ApiClient(config)
api.set_kalshi_auth(api_key, 'kalshi_private_key.pem')

portfolio_api = PortfolioApi(api)

print("Getting positions...")
resp = portfolio_api.get_positions()

print(f"Response type: {type(resp)}")
print(f"Response: {resp}")

if hasattr(resp, 'positions'):
    print(f"Number of positions: {len(resp.positions) if resp.positions else 0}")
    if resp.positions:
        for pos in resp.positions:
            print(f"  Ticker: {pos.ticker}, Position: {pos.position}")

