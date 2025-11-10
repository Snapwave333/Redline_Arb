"""
Strategy Engine for Kalshi Trading Bot

This module implements the core trading strategy using Kelly criterion
for position sizing and probability delta analysis for trade signals.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

from .config import config
from .kalshi_client import MarketData, Position
from .models import ModelPrediction
from .data_manager import FeatureData
from .edge_calculator import EdgeCalculator, EdgeResult

logger = structlog.get_logger(__name__)


@dataclass
class TradingSignal:
    """Trading signal structure"""
    ticker: str
    side: str  # 'yes' or 'no'
    quantity: int
    price: float
    model_probability: float
    implied_probability: float
    probability_delta: float
    confidence: float
    kelly_fraction: float
    expected_value: float
    timestamp: datetime
    reason: str


@dataclass
class StrategyMetrics:
    """Strategy performance metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    win_rate: float
    average_win: float
    average_loss: float
    sharpe_ratio: float
    max_drawdown: float


class KellyCalculator:
    """Kelly criterion calculator for position sizing"""
    
    @staticmethod
    def calculate_kelly_fraction(model_prob: float, implied_prob: float, 
                               kelly_multiplier: float = 0.1) -> float:
        """
        Calculate Kelly fraction for position sizing
        
        Args:
            model_prob: Model's predicted probability
            implied_prob: Market's implied probability
            kelly_multiplier: Conservative multiplier (default 0.1)
        
        Returns:
            Kelly fraction for position sizing
        """
        if model_prob <= 0 or model_prob >= 1:
            return 0.0
        
        if implied_prob <= 0 or implied_prob >= 1:
            return 0.0
        
        # Calculate odds
        model_odds = model_prob / (1 - model_prob)
        implied_odds = implied_prob / (1 - implied_prob)
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds, p = probability, q = 1 - p
        if model_prob > implied_prob:
            # Betting on Yes
            odds = 1 / implied_prob - 1  # Decimal odds
            kelly = (odds * model_prob - (1 - model_prob)) / odds
        else:
            # Betting on No
            odds = 1 / (1 - implied_prob) - 1  # Decimal odds
            kelly = (odds * (1 - model_prob) - model_prob) / odds
        
        # Apply conservative multiplier and bounds
        kelly_fraction = max(0, min(kelly * kelly_multiplier, 0.25))
        
        return kelly_fraction
    
    @staticmethod
    def calculate_expected_value(model_prob: float, implied_prob: float, 
                              bet_size: float) -> float:
        """Calculate expected value of a bet"""
        if model_prob > implied_prob:
            # Betting on Yes
            win_prob = model_prob
            win_amount = bet_size * (1 / implied_prob - 1)
            loss_amount = bet_size
        else:
            # Betting on No
            win_prob = 1 - model_prob
            win_amount = bet_size * (1 / (1 - implied_prob) - 1)
            loss_amount = bet_size
        
        expected_value = (win_prob * win_amount) - ((1 - win_prob) * loss_amount)
        return expected_value


class SignalGenerator:
    """Generates trading signals based on model predictions using advanced edge calculation"""
    
    def __init__(self):
        self.edge_calculator = EdgeCalculator(config.thresholds)
        # Legacy thresholds for backward compatibility
        self.min_probability_delta = config.trading.min_probability_delta
        self.min_confidence = 0.1
        self.min_liquidity = config.trading.min_liquidity_threshold
    
    def generate_signal(self, market_data: MarketData, 
                       prediction: ModelPrediction,
                       current_positions: List[Position],
                       portfolio_value: float) -> Optional[TradingSignal]:
        """
        Generate trading signal based on market data and model prediction using edge calculation
        
        Args:
            market_data: Current market data
            prediction: Model prediction
            current_positions: Current positions
            portfolio_value: Total portfolio value
        
        Returns:
            Trading signal if conditions are met, None otherwise
        """
        ticker = market_data.ticker
        
        # Check if we already have a position in this ticker
        existing_position = self._get_existing_position(current_positions, ticker)
        if existing_position:
            logger.info("Position already exists", ticker=ticker)
            return None
        
        # Convert market data to dictionary format for edge calculator
        market_dict = {
            'ticker': ticker,
            'yes_bid': market_data.yes_bid,
            'yes_ask': market_data.yes_ask,
            'no_bid': market_data.no_bid,
            'no_ask': market_data.no_ask,
            'volume': market_data.volume,
            'open_interest': getattr(market_data, 'open_interest', 0)
        }
        
        # Calculate comprehensive edge analysis
        edge_result = self.edge_calculator.calculate_comprehensive_edge(
            market_data=market_dict,
            model_probability=prediction.probability,
            model_confidence=prediction.confidence,
            account_balance=portfolio_value
        )
        
        # Check if edge meets threshold
        if not edge_result.meets_threshold:
            logger.debug("Edge does not meet threshold", 
                        ticker=ticker, 
                        edge=edge_result.edge,
                        threshold=self.edge_calculator.config.min_edge_threshold,
                        confidence=edge_result.confidence_score,
                        market_quality=edge_result.market_quality_score)
            return None
        
        # Determine trade side based on edge direction
        if edge_result.edge > 0:
            side = 'yes'
            price = market_data.yes_ask  # Buy at ask price
        else:
            side = 'no'
            price = market_data.no_ask  # Buy at ask price
        
        # Use recommended position size from edge calculator
        quantity = edge_result.recommended_position
        
        # Calculate Kelly fraction for logging
        kelly_fraction = quantity / (portfolio_value * 100)  # Convert to fraction
        
        # Calculate expected value
        expected_value = self._calculate_expected_value(
            edge_result.model_probability,
            edge_result.implied_probability,
            price,
            quantity
        )
        
        signal = TradingSignal(
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=price,
            model_probability=edge_result.model_probability,
            implied_probability=edge_result.implied_probability,
            probability_delta=edge_result.edge,
            confidence=edge_result.confidence_score,
            kelly_fraction=kelly_fraction,
            expected_value=expected_value,
            timestamp=datetime.now(),
            reason=f"Edge: {edge_result.edge:.3f}, Quality: {edge_result.market_quality_score:.2f}"
        )
        
        logger.info("Signal generated", 
                   ticker=ticker,
                   side=side,
                   quantity=quantity,
                   edge=edge_result.edge,
                   confidence=edge_result.confidence_score,
                   market_quality=edge_result.market_quality_score,
                   expected_value=expected_value)
        
        return signal
    
    def _get_existing_position(self, positions: List[Position], ticker: str) -> Optional[Position]:
        """Check if we already have a position in this ticker"""
        for position in positions:
            if position.ticker == ticker:
                return position
        return None
    
    def _generate_reason(self, prediction: ModelPrediction, side: str, 
                        kelly_fraction: float) -> str:
        """Generate human-readable reason for the signal"""
        delta_pct = prediction.probability_delta * 100
        
        if side == "yes":
            reason = f"Model predicts YES with {prediction.model_probability:.1%} probability "
            reason += f"(market: {prediction.implied_probability:.1%}, delta: +{delta_pct:.1f}%)"
        else:
            reason = f"Model predicts NO with {1-prediction.model_probability:.1%} probability "
            reason += f"(market: {1-prediction.implied_probability:.1%}, delta: +{delta_pct:.1f}%)"
        
        reason += f", Kelly: {kelly_fraction:.1%}"
        
        return reason


class StrategyEngine:
    """Main strategy engine that coordinates signal generation and execution"""
    
    def __init__(self, data_manager, model_manager):
        self.data_manager = data_manager
        self.model_manager = model_manager
        self.signal_generator = SignalGenerator()
        self.active_signals: Dict[str, TradingSignal] = {}
        self.completed_trades: List[TradingSignal] = []
        self.strategy_metrics = StrategyMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            total_pnl=0.0,
            win_rate=0.0,
            average_win=0.0,
            average_loss=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0
        )
    
    async def analyze_markets(self, tickers: List[str], 
                            portfolio_value: float) -> List[TradingSignal]:
        """
        Analyze multiple markets and generate trading signals
        
        Args:
            tickers: List of tickers to analyze
            portfolio_value: Current portfolio value
        
        Returns:
            List of trading signals
        """
        signals = []
        
        # Collect market data and features
        market_data_dict = await self.data_manager.collect_market_data(tickers)
        features_dict = await self.data_manager.collect_and_engineer_features(tickers)
        
        # Get current positions
        # Note: This would need to be implemented in the execution manager
        current_positions = []  # Placeholder
        
        for ticker in tickers:
            try:
                # Check if we should retrain models
                if self.model_manager.should_retrain(ticker):
                    logger.info("Retraining models", ticker=ticker)
                    self.model_manager.train_models(ticker)
                
                # Get market data and features
                market_data = market_data_dict.get(ticker)
                features = features_dict.get(ticker)
                
                if not market_data or not features:
                    logger.warning("Missing data for ticker", ticker=ticker)
                    continue
                
                # Calculate implied probability
                implied_prob = market_data.yes_price / (market_data.yes_price + market_data.no_price)
                
                # Make prediction
                prediction = self.model_manager.predict_probability(
                    ticker, features.features, implied_prob
                )
                
                # Generate signal
                signal = self.signal_generator.generate_signal(
                    market_data, prediction, current_positions, portfolio_value
                )
                
                if signal:
                    signals.append(signal)
                    self.active_signals[ticker] = signal
                
            except Exception as e:
                logger.error("Error analyzing market", ticker=ticker, error=str(e))
        
        return signals
    
    def update_signal_status(self, ticker: str, status: str, pnl: float = 0.0):
        """Update signal status after execution"""
        if ticker in self.active_signals:
            signal = self.active_signals[ticker]
            signal.status = status
            
            if status == "filled":
                self.completed_trades.append(signal)
                self._update_strategy_metrics(signal, pnl)
            
            del self.active_signals[ticker]
    
    def _update_strategy_metrics(self, signal: TradingSignal, pnl: float):
        """Update strategy performance metrics"""
        self.strategy_metrics.total_trades += 1
        
        if pnl > 0:
            self.strategy_metrics.winning_trades += 1
        else:
            self.strategy_metrics.losing_trades += 1
        
        self.strategy_metrics.total_pnl += pnl
        
        # Calculate win rate
        if self.strategy_metrics.total_trades > 0:
            self.strategy_metrics.win_rate = (
                self.strategy_metrics.winning_trades / 
                self.strategy_metrics.total_trades
            )
        
        # Calculate average win/loss
        if self.strategy_metrics.winning_trades > 0:
            winning_pnls = [t.pnl for t in self.completed_trades if t.pnl > 0]
            self.strategy_metrics.average_win = np.mean(winning_pnls) if winning_pnls else 0
        
        if self.strategy_metrics.losing_trades > 0:
            losing_pnls = [t.pnl for t in self.completed_trades if t.pnl < 0]
            self.strategy_metrics.average_loss = np.mean(losing_pnls) if losing_pnls else 0
    
    def get_strategy_metrics(self) -> StrategyMetrics:
        """Get current strategy performance metrics"""
        return self.strategy_metrics
    
    def get_active_signals(self) -> Dict[str, TradingSignal]:
        """Get currently active signals"""
        return self.active_signals
    
    def get_recent_trades(self, limit: int = 10) -> List[TradingSignal]:
        """Get recent completed trades"""
        return self.completed_trades[-limit:] if self.completed_trades else []
    
    def should_exit_position(self, ticker: str, current_price: float, 
                           entry_price: float, side: str) -> bool:
        """
        Determine if we should exit a position
        
        Args:
            ticker: Market ticker
            current_price: Current market price
            entry_price: Entry price of position
            side: Position side ('yes' or 'no')
        
        Returns:
            True if position should be exited
        """
        # Calculate current P&L
        if side == "yes":
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        # Exit conditions
        exit_conditions = [
            pnl_pct >= 0.5,  # 50% profit target
            pnl_pct <= -0.2,  # 20% stop loss
        ]
        
        return any(exit_conditions)
    
    def calculate_position_size(self, signal: TradingSignal, 
                              portfolio_value: float) -> int:
        """Calculate final position size with risk management"""
        base_size = signal.quantity
        
        # Apply maximum position size limit
        max_size = min(base_size, config.trading.max_position_size)
        
        # Apply portfolio risk limit
        max_portfolio_risk = portfolio_value * config.risk.max_portfolio_risk
        max_size_by_risk = int(max_portfolio_risk / signal.price)
        
        final_size = min(max_size, max_size_by_risk)
        
        logger.info("Calculated position size", 
                   ticker=signal.ticker,
                   base_size=base_size,
                   final_size=final_size,
                   max_position_size=config.trading.max_position_size)
        
        return final_size
