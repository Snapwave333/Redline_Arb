#!/usr/bin/env python3
"""Final working bot - trades on markets with any valid pricing"""
import os
import time
from pathlib import Path
from datetime import datetime
from kalshi_python import Configuration, MarketsApi, PortfolioApi, ExchangeApi
from kalshi_python.api_client import ApiClient

API_KEY = os.getenv('KALSHI_API_KEY', '8fe1b2e5-e094-4c1c-900f-27a02248c21a')

def find_private_key():
    search_paths = ['config/kalshi_private_key.pem', 'kalshi_private_key.pem']
    for path_str in search_paths:
        path = Path(path_str)
        if path.exists():
            return path
    raise FileNotFoundError("Could not find kalshi_private_key.pem")

def main():
    print("=" * 70)
    print("KALSHI TRADING BOT - ACTIVE")
    print("=" * 70)
    
    private_key = find_private_key()
    config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
    api_client = ApiClient(config)
    api_client.set_kalshi_auth(API_KEY, str(private_key))
    
    portfolio_api = PortfolioApi(api_client)
    markets_api = MarketsApi(api_client)
    exchange_api = ExchangeApi(api_client)
    
    try:
        balance_response = portfolio_api.get_balance()
        balance = balance_response.balance / 100
        print(f"Starting Balance: ${balance:.2f}")
    except Exception as e:
        print(f"Error: {e}")
        return
    
    trade_count = 0
    
    print("\nScanning markets for trading opportunities...")
    print("=" * 70 + "\n")
    
    try:
        while True:
            try:
                response = markets_api.get_markets(limit=1000)
                
                if response.markets:
                    for market in response.markets:
                        if market.status == 'active':
                            yes_bid = getattr(market, 'yes_bid', 0)
                            no_bid = getattr(market, 'no_bid', 0)
                            
                            if yes_bid and yes_bid > 0 and no_bid and no_bid > 0:
                                yes_price = yes_bid / 100
                                no_price = no_bid / 100
                                ticker = market.ticker
                                
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] {ticker[:50]}")
                                print(f"         YES: ${yes_price:.2f}  NO: ${no_price:.2f}")
                                
                                # Trade NO side when it's priced below $0.50
                                if 0.10 <= no_price < 0.50 and balance > 20:
                                    try:
                                        # Buy 100 shares to meet $10 minimum
                                        shares = 100
                                        cost = shares * no_price
                                        
                                        if cost >= 10 and balance >= cost:
                                            print(f"         -> Buying {shares} NO shares...")
                                            result = portfolio_api.create_order(
                                                ticker=ticker,
                                                action="buy",
                                                side="no",
                                                type="market",
                                                count=shares,
                                                no_price=int(no_price * 100)
                                            )
                                            
                                            trade_count += 1
                                            balance -= cost
                                            print(f"         ✓ TRADE #{trade_count}! Cost: ${cost:.2f} | Balance: ${balance:.2f}\n")
                                            break
                                    except Exception as e:
                                        print(f"         ✗ Error: {e}\n")
                
                # Update balance
                try:
                    balance_response = portfolio_api.get_balance()
                    balance = balance_response.balance / 100
                except:
                    pass
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(10)
    
    except KeyboardInterrupt:
        print(f"\n\nBOT STOPPED - {trade_count} trades placed")
        print("=" * 70)

if __name__ == "__main__":
    main()
