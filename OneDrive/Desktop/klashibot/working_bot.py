#!/usr/bin/env python3
"""WORKING trading bot - places trades on OPEN markets with valid prices"""
import os
import time
from pathlib import Path
from datetime import datetime
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

def main():
    print("=" * 70)
    print("WORKING KALSHI TRADING BOT")
    print("=" * 70)
    
    private_key = find_private_key()
    config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
    api_client = ApiClient(config)
    api_client.set_kalshi_auth(API_KEY, str(private_key))
    
    portfolio_api = PortfolioApi(api_client)
    markets_api = MarketsApi(api_client)
    exchange_api = ExchangeApi(api_client)
    
    # Get balance
    try:
        balance_response = portfolio_api.get_balance()
        balance = balance_response.balance / 100
        initial_balance = balance
        print(f"Starting Balance: ${balance:.2f}")
    except Exception as e:
        print(f"Error getting balance: {e}")
        return
    
    trade_count = 0
    
    print("\nBot will trade every 5 seconds on OPEN markets with valid pricing...")
    print("=" * 70 + "\n")
    
    try:
        while True:
            try:
                # Get markets
                response = markets_api.get_markets(limit=50)
                
                if response and response.markets:
                    for market in response.markets:
                        # Only trade on OPEN markets with valid pricing
                        if market.status == 'open':
                            yes_bid = getattr(market, 'yes_bid', 0)
                            no_bid = getattr(market, 'no_bid', 0)
                            
                            if yes_bid and no_bid:
                                yes_price = yes_bid / 100
                                no_price = no_bid / 100
                                
                                # VALID pricing means: YES + NO should sum to ~1.00 AND prices are reasonable (10-90)
                                if 0.10 <= yes_price <= 0.90 and 0.10 <= no_price <= 0.90:
                                    ticker = market.ticker
                                    
                                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {ticker[:40]}")
                                    print(f"         YES: ${yes_price:.2f}  NO: ${no_price:.2f}")
                                    
                                    # Trade on YES if price is reasonable
                                    if 0.25 < yes_price < 0.75 and balance > 20:
                                        try:
                                            shares = max(int(10 / yes_price), 10)
                                            cost = shares * yes_price
                                            
                                            if cost >= 10 and balance >= cost:
                                                print(f"         -> Placing BUY {shares} YES...")
                                                result = exchange_api.create_order(
                                                    ticker=ticker,
                                                    action="buy",
                                                    side="yes",
                                                    order_type="market",
                                                    count=shares
                                                )
                                                
                                                trade_count += 1
                                                balance -= cost
                                                print(f"         ✓ TRADE #{trade_count} PLACED! Cost: ${cost:.2f}")
                                                print(f"         Remaining Balance: ${balance:.2f}\n")
                                                
                                                break
                                        except Exception as e:
                                            print(f"         ✗ Error: {e}\n")
                                    
                                    # Trade on NO if price is reasonable
                                    elif 0.25 < no_price < 0.75 and balance > 20:
                                        try:
                                            shares = max(int(10 / no_price), 10)
                                            cost = shares * no_price
                                            
                                            if cost >= 10 and balance >= cost:
                                                print(f"         -> Placing BUY {shares} NO...")
                                                result = exchange_api.create_order(
                                                    ticker=ticker,
                                                    action="buy",
                                                    side="no",
                                                    order_type="market",
                                                    count=shares
                                                )
                                                
                                                trade_count += 1
                                                balance -= cost
                                                print(f"         ✓ TRADE #{trade_count} PLACED! Cost: ${cost:.2f}")
                                                print(f"         Remaining Balance: ${balance:.2f}\n")
                                                
                                                break
                                        except Exception as e:
                                            print(f"         ✗ Error: {e}\n")
                                    else:
                                        print(f"         (price outside trading range)\n")
                
                # Update balance from API
                try:
                    balance_response = portfolio_api.get_balance()
                    balance = balance_response.balance / 100
                except:
                    pass
                
                time.sleep(5)  # Trade every 5 seconds
                
            except Exception as e:
                print(f"Error in trading cycle: {e}")
                time.sleep(5)
    
    except KeyboardInterrupt:
        print(f"\n\nBOT STOPPED")
        print("=" * 70)
        print(f"Total Trades: {trade_count}")
        print("=" * 70)

if __name__ == "__main__":
    main()

