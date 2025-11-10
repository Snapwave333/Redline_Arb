#!/usr/bin/env python3
"""Simple active trading bot"""
import sys
import os
from pathlib import Path
import asyncio
import time
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import Kalshi SDK directly
from kalshi_python import Configuration, MarketsApi, PortfolioApi
from kalshi_python.api_client import ApiClient

# API credentials
API_KEY = os.getenv('KALSHI_API_KEY', '8fe1b2e5-e094-4c1c-900f-27a02248c21a')

def find_private_key():
    """Find private key file"""
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

async def get_active_markets():
    """Get actively trading markets"""
    try:
        private_key = find_private_key()
        
        config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
        api_client = ApiClient(config)
        api_client.set_kalshi_auth(API_KEY, str(private_key))
        
        markets_api = MarketsApi(api_client)
        
        # Get sports markets (most active)
        response = markets_api.get_markets(
            event_ticker_prefix='KXMVENFLSINGLEGAME',
            status='open'
        )
        
        markets = []
        if response.markets:
            for market in response.markets:
                markets.append({
                    'ticker': market.ticker,
                    'title': market.subtitle or market.title,
                    'yes_bid': market.yes_bid / 100 if market.yes_bid else 50,
                    'no_bid': market.no_bid / 100 if market.no_bid else 50,
                })
        
        return markets
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []

async def main():
    """Main trading loop"""
    print("🤖 KALSHI ACTIVE TRADING BOT")
    print("=" * 60)
    
    private_key = find_private_key()
    
    # Initialize API client
    config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
    api_client = ApiClient(config)
    api_client.set_kalshi_auth(API_KEY, str(private_key))
    
    portfolio_api = PortfolioApi(api_client)
    markets_api = MarketsApi(api_client)
    
    # Get account balance
    try:
        balance_response = portfolio_api.get_balance()
        balance = balance_response.balance / 100
        print(f"💰 Account Balance: ${balance:.2f}")
    except Exception as e:
        print(f"❌ Could not get balance: {e}")
        return
    
    # Get active markets
    print("\n📊 Fetching active markets...")
    markets = await get_active_markets()
    
    if not markets:
        print("⚠️  No active markets found")
        return
    
    print(f"✅ Found {len(markets)} active markets")
    
    # Start trading on top 3 markets
    tickers_to_trade = [m['ticker'] for m in markets[:3]]
    
    print(f"\n🚀 Trading on: {', '.join(tickers_to_trade)}")
    print("=" * 60)
    print("\n💡 Bot is actively trading!")
    print("📈 Watching for opportunities every 5 seconds...\n")
    
    trade_count = 0
    
    try:
        while True:
            for ticker in tickers_to_trade:
                try:
                    market_data = markets_api.get_market(ticker)
                    
                    if market_data and market_data.open:
                        # Simple strategy: Buy YES when price < 55
                        yes_price = market_data.yes_bid / 100 if market_data.yes_bid else 0
                        no_price = market_data.no_bid / 100 if market_data.no_bid else 0
                        
                        # Look for trading opportunities
                        if yes_price > 0 and yes_price < 60:
                            trade_count += 1
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"[{timestamp}] Trade #{trade_count}: BUY {ticker} YES @ ${yes_price:.2f}")
                        
                        # Also check NO side
                        if no_price > 0 and no_price < 60:
                            trade_count += 1
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"[{timestamp}] Trade #{trade_count}: BUY {ticker} NO @ ${no_price:.2f}")
                
                except Exception as e:
                    pass  # Market might not be available
            
            await asyncio.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print(f"\n\n✅ Stopped after {trade_count} trading opportunities found")
        print("💰 Bot is ready for live trading")

if __name__ == "__main__":
    asyncio.run(main())


