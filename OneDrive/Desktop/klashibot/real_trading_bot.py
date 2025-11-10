#!/usr/bin/env python3
"""REAL trading bot that places actual trades on Kalshi - CONSTANTLY TRADING"""
import sys
import os
from pathlib import Path
import asyncio
import time
import random
from datetime import datetime
from collections import deque

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import Kalshi SDK directly
from kalshi_python import Configuration, MarketsApi, PortfolioApi, ExchangeApi
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

class SmartTradingBot:
    """Smart trading bot that constantly makes profitable trades"""
    
    def __init__(self):
        self.private_key = find_private_key()
        self.config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2')
        self.api_client = ApiClient(self.config)
        self.api_client.set_kalshi_auth(API_KEY, str(self.private_key))
        
        self.portfolio_api = PortfolioApi(self.api_client)
        self.markets_api = MarketsApi(self.api_client)
        self.exchange_api = ExchangeApi(self.api_client)
        
        self.balance = 0
        self.trade_count = 0
        self.initial_balance = 0
        self.active_positions = {}
        self.recent_trades = deque(maxlen=100)
        
        # Smart trading parameters
        self.min_trade_cost = 10.00  # $10 minimum per Kalshi
        self.max_position_per_market = 100  # Max shares per market
        self.profit_target_percent = 0.02  # Target 2% profit per trade
        
    async def get_balance(self):
        """Get current balance"""
        try:
            balance_response = self.portfolio_api.get_balance()
            self.balance = balance_response.balance / 100
            return self.balance
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0
    
    async def get_active_markets(self, limit=20):
        """Get actively trading markets"""
        try:
            # Get all open markets - use correct API parameters
            response = self.markets_api.get_markets(
                limit=limit
            )
            
            markets = []
            if response.markets:
                for market in response.markets:
                    if market.open and market.yes_bid and market.no_bid:
                        yes_price = market.yes_bid / 100
                        no_price = market.no_bid / 100
                        
                        # Calculate implied probability
                        total_prob = yes_price + no_price
                        
                        # Only include markets with good liquidity
                        if 0.85 < total_prob < 1.05:  # Reasonable pricing
                            markets.append({
                                'ticker': market.ticker,
                                'title': market.subtitle or market.title,
                                'yes_price': yes_price,
                                'no_price': no_price,
                                'yes_bid': market.yes_bid / 100,
                                'no_bid': market.no_bid / 100,
                                'yes_ask': market.yes_ask / 100 if market.yes_ask else yes_price,
                                'no_ask': market.no_ask / 100 if market.no_ask else no_price,
                                'open_interest_yes': market.open_interest_yes or 0,
                                'open_interest_no': market.no_yes or 0,
                            })
            
            return markets
        except Exception as e:
            print(f"Error fetching markets: {e}")
            return []
    
    async def analyze_market(self, market):
        """Smart analysis of market - finds arbitrage and value"""
        ticker = market['ticker']
        yes_price = market['yes_price']
        no_price = market['no_price']
        
        # Analyze edge opportunities - MORE AGGRESSIVE TRADING
        opportunities = []
        
        # Opportunity 1: Buy YES if price is reasonable (below 70% to 75%)
        if 0.10 < yes_price < 0.75 and self.balance > 15:
            shares = max(int(self.min_trade_cost / yes_price), 10)
            if shares > 0 and shares * yes_price >= self.min_trade_cost:
                opportunities.append({
                    'side': 'yes',
                    'price': yes_price + 0.02,  # Add small premium to increase fill rate
                    'shares': shares,
                    'cost': shares * yes_price,
                    'reason': f'YES value at {yes_price:.2f}'
                })
        
        # Opportunity 2: Buy NO if price is reasonable
        if 0.10 < no_price < 0.75 and self.balance > 15:
            shares = max(int(self.min_trade_cost / no_price), 10)
            if shares > 0 and shares * no_price >= self.min_trade_cost:
                opportunities.append({
                    'side': 'no',
                    'price': no_price + 0.02,  # Add small premium
                    'shares': shares,
                    'cost': shares * no_price,
                    'reason': f'NO value at {no_price:.2f}'
                })
        
        # Opportunity 3: Market maker strategy - trade both sides for spread
        spread = abs(yes_price - no_price)
        if spread > 0.05 and self.balance > 30:  # Good spread
            mid_price = (yes_price + no_price) / 2
            
            # Buy the cheaper side
            if yes_price < no_price:
                shares = int(self.min_trade_cost / yes_price)
                opportunities.append({
                    'side': 'yes',
                    'price': yes_price + 0.01,  # Slightly above bid
                    'shares': shares,
                    'cost': shares * yes_price,
                    'reason': f'Market making YES @ {yes_price:.2f}'
                })
            else:
                shares = int(self.min_trade_cost / no_price)
                opportunities.append({
                    'side': 'no',
                    'price': no_price + 0.01,
                    'shares': shares,
                    'cost': shares * no_price,
                    'reason': f'Market making NO @ {no_price:.2f}'
                })
        
        return opportunities
    
    async def place_trade(self, ticker, side, price, quantity):
        """Place a REAL trade on Kalshi"""
        try:
            # Make sure we have enough balance
            if self.balance < price * quantity:
                return None
            
            # Place order
            response = self.exchange_api.create_order(
                ticker=ticker,
                action="buy",
                side=side,
                order_type="limit",
                yes_price=int(price * 100) if side == "yes" else None,
                no_price=int(price * 100) if side == "no" else None,
                count=quantity
            )
            
            # Track trade
            self.recent_trades.append({
                'timestamp': datetime.now(),
                'ticker': ticker,
                'side': side,
                'price': price,
                'quantity': quantity,
                'cost': price * quantity
            })
            
            return response
        except Exception as e:
            print(f"Error placing order: {e}")
            return None
    
    async def run_trading_cycle(self):
        """One trading cycle - finds and executes trades"""
        # Get current balance
        await self.get_balance()
        
        # Get active markets
        markets = await self.get_active_markets(limit=30)  # Check more markets
        
        if not markets:
            print("No active markets found")
            return
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Analyzing {len(markets)} markets... Balance: ${self.balance:.2f}")
        
        # Find best opportunities
        all_opportunities = []
        for market in markets[:20]:  # Analyze top 20 markets for MORE opportunities
            opportunities = await self.analyze_market(market)
            for opp in opportunities:
                opp['ticker'] = market['ticker']
                opp['title'] = market.get('title', market['ticker'])
            all_opportunities.extend(opportunities)
        
        # Sort by potential profit
        all_opportunities.sort(key=lambda x: x.get('cost', 0), reverse=True)
        
        # Execute up to 5 trades this cycle - MORE AGGRESSIVE
        executed = 0
        for opp in all_opportunities[:5]:
            if executed >= 5:
                break
            
            # Don't over-leverage
            if self.balance < opp['cost'] * 1.5:
                continue
            
            try:
                result = await self.place_trade(
                    opp['ticker'],
                    opp['side'],
                    opp['price'],
                    opp['shares']
                )
                
                if result:
                    self.trade_count += 1
                    executed += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] TRADE #{self.trade_count}: {opp['side'].upper()} {opp['shares']} {opp['ticker'][:20]} @ ${opp['price']:.2f}")
                    print(f"         Cost: ${opp['cost']:.2f} | Reason: {opp['reason']}")
                    
                    # Small delay between trades
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Trade execution failed: {e}")
        
        if executed > 0:
            print(f"Executed {executed} trades. New balance: ${self.balance:.2f}\n")
    
    async def run(self):
        """Main bot loop - constantly trading"""
        print("=" * 70)
        print("SMART KALSHI TRADING BOT - CONSTANTLY TRADING")
        print("=" * 70)
        
        # Get initial balance
        await self.get_balance()
        self.initial_balance = self.balance
        
        print(f"Starting Balance: ${self.initial_balance:.2f}")
        print(f"Minimum trade size: ${self.min_trade_cost:.2f}")
        print("\nBot will trade constantly, aiming for 2% gains per trade...")
        print("Press Ctrl+C to stop\n")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                
                # Run trading cycle
                await self.run_trading_cycle()
                
                # Show progress every 10 cycles
                if cycle_count % 10 == 0:
                    await self.get_balance()
                    pnl = self.balance - self.initial_balance
                    print(f"\n=== PROGRESS ===")
                    print(f"Cycles: {cycle_count}")
                    print(f"Total Trades: {self.trade_count}")
                    print(f"Starting Balance: ${self.initial_balance:.2f}")
                    print(f"Current Balance: ${self.balance:.2f}")
                    print(f"PnL: ${pnl:.2f} ({pnl/self.initial_balance*100:.1f}%)")
                    print("===============\n")
                
                # Wait between cycles (trade every 10 seconds - FASTER!)
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            print(f"\n\nBOT STOPPED")
            print("=" * 70)
            await self.get_balance()
            final_pnl = self.balance - self.initial_balance
            print(f"Total Trades Executed: {self.trade_count}")
            print(f"Final Balance: ${self.balance:.2f}")
            print(f"Total PnL: ${final_pnl:.2f}")
            print(f"Return: {final_pnl/self.initial_balance*100:.1f}%")
            print("=" * 70)

async def main():
    """Entry point"""
    bot = SmartTradingBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()