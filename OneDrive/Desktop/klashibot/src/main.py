"""
Main Kalshi Trading Bot

This is the main orchestrator that coordinates all components of the trading bot,
including data collection, model prediction, strategy execution, and risk management.
"""

import asyncio
import argparse
import sys
from typing import List, Dict, Optional
from datetime import datetime, timedelta, time
import structlog
from pathlib import Path

# Import all bot components
from .config import config
from .kalshi_client import KalshiAPIClient
from .data_manager import DataManager
from .models import ModelManager, ModelPrediction, ModelPerformance
from .strategy import StrategyEngine
from .execution import ExecutionManager
from .risk_manager import RiskManager
from .monitoring import MonitoringSystem
from .realistic_growth import RealisticGrowthManager, DailyCapitalManager
from .firebase_manager import FirebaseManager

logger = structlog.get_logger(__name__)


class KalshiTradingBot:
    """Main trading bot class that orchestrates all components"""
    
    def __init__(self):
        # Initialize all components
        self.client: Optional[KalshiAPIClient] = None
        self.data_manager: Optional[DataManager] = None
        self.model_manager: Optional[ModelManager] = None
        self.strategy_engine: Optional[StrategyEngine] = None
        self.execution_manager: Optional[ExecutionManager] = None
        self.risk_manager: Optional[RiskManager] = None
        self.monitoring_system: Optional[MonitoringSystem] = None
        self.growth_manager: Optional[RealisticGrowthManager] = None
        self.capital_manager: Optional[DailyCapitalManager] = None
        self.firebase_manager: Optional[FirebaseManager] = None
        
        # Bot state
        self.is_running = False
        self.tickers_to_trade: List[str] = []
        self.last_analysis_time = None
        self.analysis_interval = 300  # 5 minutes
        self.daily_transfer_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize all bot components"""
        try:
            logger.info("Initializing Kalshi Trading Bot")
            
            # Validate configuration
            if not config.validate_config():
                raise ValueError("Configuration validation failed")
            
            # Initialize API client
            self.client = KalshiAPIClient()
            await self.client.__aenter__()
            
            # Initialize data manager
            self.data_manager = DataManager()
            await self.data_manager.initialize()
            
            # Initialize model manager
            self.model_manager = ModelManager(self.data_manager)
            
            # Initialize strategy engine
            self.strategy_engine = StrategyEngine(self.data_manager, self.model_manager)
            
            # Initialize execution manager
            self.execution_manager = ExecutionManager(self.client)
            await self.execution_manager.initialize()
            
            # Initialize risk manager
            self.risk_manager = RiskManager()
            
            # Initialize monitoring system
            self.monitoring_system = MonitoringSystem()
            await self.monitoring_system.start_monitoring()
            
            # Initialize realistic growth manager
            self.growth_manager = RealisticGrowthManager(self.client)
            await self.growth_manager.initialize()
            
            # Initialize daily capital manager
            self.capital_manager = DailyCapitalManager(self.client)
            await self.capital_manager.initialize()
            
            # Initialize Firebase Manager
            if config.firebase.firebase_enabled:
                self.firebase_manager = FirebaseManager(
                    app_id=config.firebase.firebase_app_id,
                    user_id=config.firebase.firebase_user_id,
                    region=config.firebase.firebase_region
                )
                self.firebase_manager.initialize(
                    config.firebase.firebase_credentials_path,
                    config.firebase.firebase_database_id
                )
            
            logger.info("Bot initialization completed successfully")
            
        except Exception as e:
            logger.error("Failed to initialize bot", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup all bot components"""
        try:
            logger.info("Cleaning up bot components")
            
            # Stop monitoring
            if self.monitoring_system:
                await self.monitoring_system.stop_monitoring()
            
            # Stop execution monitoring
            if self.execution_manager:
                await self.execution_manager.stop_monitoring()
            
            # Cleanup data manager
            if self.data_manager:
                await self.data_manager.cleanup()
            
            # Close API client
            if self.client:
                await self.client.__aexit__(None, None, None)
            
            logger.info("Bot cleanup completed")
            
        except Exception as e:
            logger.error("Error during cleanup", error=str(e))
    
    async def start_trading(self, tickers: List[str]):
        """Start trading for specified tickers"""
        try:
            logger.info("Starting trading", tickers=tickers)
            
            self.tickers_to_trade = tickers
            self.is_running = True
            
            # Start execution monitoring
            await self.execution_manager.start_monitoring()
            
            # Start daily transfer task
            if self.capital_manager and config.paypal.daily_transfer_enabled:
                self.daily_transfer_task = asyncio.create_task(self._daily_transfer_task())
            
            # Main trading loop
            while self.is_running:
                try:
                    await self._trading_cycle()
                    await asyncio.sleep(self.analysis_interval)
                    
                except Exception as e:
                    logger.error("Error in trading cycle", error=str(e))
                    self.monitoring_system.log_system_error("trading_cycle", e)
                    await asyncio.sleep(60)  # Wait before retrying
            
        except Exception as e:
            logger.error("Failed to start trading", error=str(e))
            raise
    
    async def stop_trading(self):
        """Stop trading"""
        logger.info("Stopping trading")
        self.is_running = False
        
        # Cancel all active orders
        if self.execution_manager:
            await self.execution_manager.cancel_all_orders()
        
        # Cancel daily transfer task
        if self.daily_transfer_task:
            self.daily_transfer_task.cancel()
            try:
                await self.daily_transfer_task
            except asyncio.CancelledError:
                pass
    
    async def _trading_cycle(self):
        """Execute one trading cycle"""
        try:
            logger.info("Starting trading cycle")
            
            # Update portfolio and positions with enhanced cash safety
            await self.execution_manager.position_manager.update_portfolio()
            await self.execution_manager.position_manager.update_positions()
            
            portfolio_value = self.execution_manager.position_manager.portfolio_value
            positions = self.execution_manager.position_manager.get_all_positions()
            
            # Log cash safety status
            cash_balance = self.execution_manager.position_manager.cash_balance
            logger.info("Cash safety check",
                       total_cash=cash_balance,
                       portfolio_value=portfolio_value,
                       n_positions=len(positions))
            
            # Update risk metrics
            risk_metrics = self.risk_manager.update_risk_metrics(
                positions, portfolio_value, 
                self.execution_manager.position_manager.cash_balance
            )
            
            # Check if we should stop trading due to risk
            if self.risk_manager.should_stop_trading():
                logger.critical("Risk limits exceeded, stopping trading")
                await self.stop_trading()
                return
            
            # Analyze markets and generate signals
            signals = await self.strategy_engine.analyze_markets(
                self.tickers_to_trade, portfolio_value
            )
            
            # Process signals with realistic growth enhancement
            for signal in signals:
                # Enhance signal for realistic growth phase
                enhanced_signal = self.growth_manager.enhance_signal_for_growth_phase(signal)
                await self._process_signal(enhanced_signal, portfolio_value, positions)
            
            # Update monitoring metrics
            self._update_monitoring_metrics(portfolio_value, positions, risk_metrics)
            
            # Update Firebase with bot state
            if self.firebase_manager:
                await self._update_firebase_state(portfolio_value, positions, risk_metrics)
            
            self.last_analysis_time = datetime.now()
            logger.info("Trading cycle completed", 
                       n_signals=len(signals),
                       portfolio_value=portfolio_value)
            
        except Exception as e:
            logger.error("Error in trading cycle", error=str(e))
            self.monitoring_system.log_system_error("trading_cycle", e)
    
    async def _process_signal(self, signal, portfolio_value: float, positions: Dict[str, any]):
        """Process a trading signal"""
        try:
            # Validate signal against risk limits
            is_valid, reasons = self.risk_manager.validate_signal(
                signal, portfolio_value, positions
            )
            
            if not is_valid:
                logger.warning("Signal rejected by risk manager", 
                             ticker=signal.ticker,
                             reasons=reasons)
                return
            
            # Execute signal
            result = await self.execution_manager.execute_signal(signal)
            
            # Track execution for growth analysis
            await self.growth_manager.track_growth_progress(signal, result, 0.0)  # PnL will be updated when trade closes
            
            # Note: Realized P&L tracking will be handled when positions close
            # The capital manager will be updated via position monitoring
            
            # Update Firebase with new position
            if self.firebase_manager and result.success:
                await self._update_firebase_position(signal, result)
            
            # Log execution
            self.monitoring_system.log_trade_execution(signal, result)
            
            if result.success:
                logger.info("Signal executed successfully with growth tracking", 
                           ticker=signal.ticker,
                           order_id=result.order_id,
                           quantity=signal.quantity,
                           expected_value=signal.expected_value)
            else:
                logger.error("Signal execution failed", 
                           ticker=signal.ticker,
                           error=result.error_message)
                
        except Exception as e:
            logger.error("Error processing signal", 
                        ticker=signal.ticker,
                        error=str(e))
            self.monitoring_system.log_system_error("signal_processing", e)
    
    def _update_monitoring_metrics(self, portfolio_value: float, 
                                  positions: Dict[str, any], risk_metrics):
        """Update monitoring metrics"""
        try:
            # Calculate metrics
            total_pnl = sum(pos.unrealized_pnl + pos.realized_pnl for pos in positions.values())
            daily_pnl = self.risk_manager.portfolio_risk_manager.get_daily_pnl()
            
            strategy_metrics = self.strategy_engine.get_strategy_metrics()
            win_rate = strategy_metrics.win_rate
            total_trades = strategy_metrics.total_trades
            active_positions = len(positions)
            
            # Get model accuracy (simplified)
            model_accuracy = 0.6  # This would be calculated from actual model performance
            
            # Record metrics
            self.monitoring_system.record_performance_metrics(
                portfolio_value=portfolio_value,
                total_pnl=total_pnl,
                daily_pnl=daily_pnl,
                win_rate=win_rate,
                total_trades=total_trades,
                active_positions=active_positions,
                risk_level=risk_metrics.risk_level.value,
                model_accuracy=model_accuracy
            )
            
        except Exception as e:
            logger.error("Error updating monitoring metrics", error=str(e))
    
    async def train_models(self, tickers: List[str]):
        """Train models for specified tickers"""
        logger.info("Training models", tickers=tickers)
        
        for ticker in tickers:
            try:
                performances = self.model_manager.train_models(ticker)
                
                logger.info("Model training completed", 
                           ticker=ticker,
                           performances=performances)
                
                # Log model retraining alert
                self.monitoring_system.alert_manager.create_alert(
                    self.monitoring_system.alert_manager.AlertType.MODEL_RETRAINED,
                    self.monitoring_system.alert_manager.LogLevel.INFO,
                    f"Model Retrained: {ticker}",
                    f"Models retrained for {ticker}",
                    {"ticker": ticker, "performances": performances}
                )
                
            except Exception as e:
                logger.error("Failed to train models", 
                           ticker=ticker,
                           error=str(e))
    
    async def _update_firebase_state(self, portfolio_value: float, positions: Dict[str, any], risk_metrics: Dict[str, any]):
        """Update Firebase with current bot state"""
        try:
            if not self.firebase_manager:
                return
            
            # Calculate daily PnL (simplified - in production this would be more sophisticated)
            daily_pnl = 0.0
            for position in positions.values():
                if hasattr(position, 'unrealized_pnl'):
                    daily_pnl += position.unrealized_pnl
            
            # Update bot state
            state_data = {
                'portfolioValue': portfolio_value,
                'dailyPnl': daily_pnl,
                'isRunning': self.is_running,
                'maxDailyLoss': config.risk.max_daily_loss,
                'maxPortfolioRisk': config.risk.max_portfolio_risk,
                'kellyFactor': config.trading.default_kelly_fraction,
                'currentExposure': risk_metrics.get('total_exposure', 0)
            }
            
            self.firebase_manager.update_bot_state(state_data)
            
            # Update daily performance record
            today = datetime.now().strftime('%Y-%m-%d')
            cumulative_pnl = portfolio_value - config.dual_strategy.starting_balance  # Simplified cumulative calculation
            self.firebase_manager.add_performance_record(today, daily_pnl, cumulative_pnl)
            
        except Exception as e:
            logger.error("Failed to update Firebase state", error=str(e))
    
    async def _update_firebase_position(self, signal, result):
        """Update Firebase with new position"""
        try:
            if not self.firebase_manager:
                return
            
            position_data = {
                'marketId': signal.ticker,
                'status': 'Active',
                'shares': signal.quantity,
                'entryPrice': signal.price,
                'currentPrice': signal.price,  # Will be updated when market data changes
                'pnl': 0.0,  # Will be updated when position closes
                'entryTime': datetime.now().isoformat(),
                'marketStatus': 'OPEN'
            }
            
            # Use order ID as position ID
            position_id = f"order_{result.order_id}"
            self.firebase_manager.update_position(position_id, position_data)
            
        except Exception as e:
            logger.error("Failed to update Firebase position", error=str(e))
    
    def get_status(self) -> Dict[str, any]:
        """Get current bot status"""
        return {
            "is_running": self.is_running,
            "tickers_to_trade": self.tickers_to_trade,
            "last_analysis_time": self.last_analysis_time,
            "analysis_interval": self.analysis_interval,
            "execution_summary": self.execution_manager.get_execution_summary() if self.execution_manager else {},
            "risk_summary": self.risk_manager.get_risk_summary() if self.risk_manager else {},
            "monitoring_summary": self.monitoring_system.get_monitoring_summary() if self.monitoring_system else {},
            "growth_summary": self.growth_manager.get_growth_summary() if self.growth_manager else {},
            "capital_manager_enabled": self.capital_manager is not None
        }
    
    async def _daily_transfer_task(self):
        """Background task that runs daily transfers at midnight UTC"""
        try:
            while self.is_running:
                # Calculate time until next midnight UTC
                now = datetime.now()
                midnight_utc = datetime.combine(now.date() + timedelta(days=1), time.min)
                time_until_midnight = (midnight_utc - now).total_seconds()
                
                logger.info("Daily transfer task sleeping until midnight UTC", 
                           sleep_seconds=time_until_midnight)
                
                # Sleep until midnight UTC
                await asyncio.sleep(time_until_midnight)
                
                if self.is_running and self.capital_manager:
                    logger.info("Executing daily capital management cycle")
                    await self.capital_manager.manage_daily_cycle()
                    
        except asyncio.CancelledError:
            logger.info("Daily transfer task cancelled")
        except Exception as e:
            logger.error("Error in daily transfer task", error=str(e))
            self.monitoring_system.log_system_error("daily_transfer_task", e)
    
    def update_realized_pnl(self, pnl: float):
        """Update realized P&L in capital manager when positions close"""
        if self.capital_manager:
            self.capital_manager.update_realized_profit(pnl)


async def main():
    """Main entry point for the bot"""
    parser = argparse.ArgumentParser(description="Kalshi Trading Bot")
    parser.add_argument("--tickers", nargs="+", required=True, 
                       help="Tickers to trade")
    parser.add_argument("--train", action="store_true", 
                       help="Train models before starting")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run in dry-run mode (no actual trades)")
    parser.add_argument("--interval", type=int, default=300, 
                       help="Analysis interval in seconds")
    
    args = parser.parse_args()
    
    # Create bot instance
    bot = KalshiTradingBot()
    
    try:
        # Initialize bot
        await bot.initialize()
        
        # Set analysis interval
        bot.analysis_interval = args.interval
        
        # Train models if requested
        if args.train:
            await bot.train_models(args.tickers)
        
        # Start trading
        await bot.start_trading(args.tickers)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Bot failed", error=str(e))
        sys.exit(1)
    finally:
        # Cleanup
        await bot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
