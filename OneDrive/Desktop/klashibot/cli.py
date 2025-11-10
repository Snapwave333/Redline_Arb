#!/usr/bin/env python3
"""
Kalshi Trading Bot CLI

Command-line interface for the Kalshi trading bot.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import KalshiTradingBot
from src.config import config


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Kalshi Trading Bot - Automated trading for prediction markets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --tickers TRUMP2024 ELECTION2024
  %(prog)s --tickers TRUMP2024 --train --interval 600
  %(prog)s --status
  %(prog)s --train-models TRUMP2024 ELECTION2024
        """
    )
    
    # Main commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Trade command
    trade_parser = subparsers.add_parser('trade', help='Start trading')
    trade_parser.add_argument('--tickers', nargs='+', required=True,
                             help='Tickers to trade')
    trade_parser.add_argument('--train', action='store_true',
                             help='Train models before starting')
    trade_parser.add_argument('--dry-run', action='store_true',
                             help='Run in dry-run mode (no actual trades)')
    trade_parser.add_argument('--interval', type=int, default=300,
                             help='Analysis interval in seconds (default: 300)')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train models')
    train_parser.add_argument('tickers', nargs='+',
                             help='Tickers to train models for')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show bot status')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_parser.add_argument('--validate', action='store_true',
                              help='Validate configuration')
    config_parser.add_argument('--show', action='store_true',
                              help='Show current configuration')
    
    return parser


async def cmd_trade(args):
    """Handle trade command"""
    bot = KalshiTradingBot()
    
    try:
        print(f"Initializing bot for tickers: {', '.join(args.tickers)}")
        await bot.initialize()
        
        if args.train:
            print("Training models...")
            await bot.train_models(args.tickers)
        
        print(f"Starting trading with {args.interval}s interval")
        if args.dry_run:
            print("DRY RUN MODE - No actual trades will be executed")
        
        await bot.start_trading(args.tickers)
        
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await bot.cleanup()


async def cmd_train(args):
    """Handle train command"""
    bot = KalshiTradingBot()
    
    try:
        print(f"Initializing bot for training: {', '.join(args.tickers)}")
        await bot.initialize()
        
        print("Training models...")
        await bot.train_models(args.tickers)
        
        print("Model training completed")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await bot.cleanup()


async def cmd_status(args):
    """Handle status command"""
    bot = KalshiTradingBot()
    
    try:
        await bot.initialize()
        status = bot.get_status()
        
        print("Bot Status:")
        print(f"  Running: {status['is_running']}")
        print(f"  Tickers: {', '.join(status['tickers_to_trade']) if status['tickers_to_trade'] else 'None'}")
        print(f"  Last Analysis: {status['last_analysis_time']}")
        print(f"  Analysis Interval: {status['analysis_interval']}s")
        
        if status['execution_summary']:
            print("\nExecution Summary:")
            for key, value in status['execution_summary'].items():
                print(f"  {key}: {value}")
        
        if status['risk_summary']:
            print("\nRisk Summary:")
            for key, value in status['risk_summary'].items():
                print(f"  {key}: {value}")
        
        if status['monitoring_summary']:
            print("\nMonitoring Summary:")
            for key, value in status['monitoring_summary'].items():
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await bot.cleanup()


def cmd_config(args):
    """Handle config command"""
    if args.validate:
        print("Validating configuration...")
        if config.validate_config():
            print("✓ Configuration is valid")
        else:
            print("✗ Configuration validation failed")
            sys.exit(1)
    
    if args.show:
        print("Current Configuration:")
        print(f"  Bot Name: {config.bot.name}")
        print(f"  Environment: {config.bot.environment}")
        print(f"  Log Level: {config.bot.log_level}")
        print(f"  Kelly Fraction: {config.trading.default_kelly_fraction}")
        print(f"  Min Probability Delta: {config.trading.min_probability_delta}")
        print(f"  Max Position Size: {config.trading.max_position_size}")
        print(f"  Max Daily Loss: {config.risk.max_daily_loss}")
        print(f"  Max Portfolio Risk: {config.risk.max_portfolio_risk}")


async def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'trade':
        await cmd_trade(args)
    elif args.command == 'train':
        await cmd_train(args)
    elif args.command == 'status':
        await cmd_status(args)
    elif args.command == 'config':
        cmd_config(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
