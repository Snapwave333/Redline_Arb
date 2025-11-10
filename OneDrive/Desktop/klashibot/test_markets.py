#!/usr/bin/env python3
"""Quick test to see what markets are available"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from kalshi_python import MarketsApi, ApiClient, Configuration
from config import config

sdk_config = Configuration(host=config.api.kalshi_base_url)
api_client = ApiClient(sdk_config)
api_client.set_kalshi_auth(config.api.kalshi_api_key, config.api.kalshi_private_key)
markets_api = MarketsApi(api_client)

response = markets_api.get_markets(limit=20)
print(f"\nTotal markets: {len(response.markets) if response.markets else 0}")
print("\nSample markets:")

if response.markets:
    for market in response.markets[:5]:
        print(f"\nTicker: {market.ticker}")
        print(f"Title: {market.title}")
        print(f"Status: {market.status}")
        print(f"Has volume: {hasattr(market, 'volume')}")
else:
    print("No markets returned")

