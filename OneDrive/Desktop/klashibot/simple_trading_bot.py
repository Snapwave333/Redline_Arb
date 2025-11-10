#!/usr/bin/env python3
"""SIMPLE trading bot - places market orders constantly"""
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
    print("SIMPLE KALSHI TRADING BOT - TRADING CONSTANTLY")
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
    
    print("\nBot will place MARKET orders every 5 seconds...")
    print("=" * 70 + "\n")
    
    try:
        while True:
            try:
                # Get markets
                response = markets_api.get_markets(limit=20)
                
                if response and response.markets:
                    for market in response.markets:
                        # Check if market is active and has bids
                        if market.status == 'open' and hasattr(market, 'yes_bid') and hasattr(market, 'no_bid'):
                            yes_bid = getattr(market, 'yes_bid', 0)
                            no_bid = getattr(market, 'no_bid', 0)
                            
                            if yes_bid and no_bid:
                                ticker = market.ticker
                                yes_price = yes_bid / 100
                                no_price = no_bid / 100
                                
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking {ticker[:30]}... YES: ${yes_price:.2f} NO: ${no_price:.2f}")
                                
                                # Find good opportunities (price between 0.30 and 0.70)
                                if 0.30 < yes_price < 0.70 and balance > 20:
                                    try:
                                        # Calculate shares for $10 minimum
                                        shares = max(int(10 / yes_price), 10)
                                        cost = shares * yes_price
                                        
                                        if cost >= 10 and balance >= cost:
                                            # Place market order
                                            print(f"  -> Placing BUY {shares} YES @ ${yes_price:.2f}...")
                                            result = exchange_api.create_order(
                                                ticker=ticker,
                                                action="buy",
                                                side="yes",
                                                order_type="market",
                                                count=shares
                                            )
                                            
                                            trade_count += 1
                                            balance -= cost
                                            print(f"  ✓ TRADE #{trade_count}: SUCCESS! Cost: ${cost:.2f} | Balance: ${balance:.2f}")
                                            
                                            # One trade per cycle
                                            break
                                    except Exception as e:
                                        print(f"  ✗ Trade failed: {e}")
                                
                                # Also check NO side
                                if 0.30 < no_price < 0.70 and balance > 20:
                                    try:
                                        shares = max(int(10 / no_price), 10)
                                        cost = shares * no_price
                                        
                                        if cost >= 10 and balance >= cost:
                                            print(f"  -> Placing BUY {shares} NO @ ${no_price:.2f}...")
                                            result = exchange_api.create_order(
                                                ticker=ticker,
                                                action="buy",
                                                side="no",
                                                order_type="market",
                                                count=shares
                                            )
                                            
                                            trade_count += 1
                                            balance -= cost
                                            print(f"  ✓ TRADE #{trade_count}: SUCCESS! Cost: ${cost:.2f} | Balance: ${balance:.2f}")
                                            break
                                    except Exception as e:
                                        print(f"  ✗ Trade failed: {e}")
                
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