"""
Advanced Feature Engineering Module for Kalshi Trading Bot

This module provides sophisticated feature engineering capabilities including
momentum indicators, volume-weighted metrics, market microstructure features,
temporal patterns, and cross-market correlations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class MarketMicrostructure:
    """Market microstructure data structure"""
    ticker: str
    timestamp: datetime
    yes_bid: float
    yes_ask: float
    no_bid: float
    no_ask: float
    yes_bid_size: int
    yes_ask_size: int
    no_bid_size: int
    no_ask_size: int
    volume: int
    open_interest: int


class AdvancedFeatureEngineer:
    """
    Advanced feature engineering with 20+ sophisticated features
    including momentum, volume, microstructure, and temporal patterns.
    """
    
    def __init__(self):
        self.feature_cache = {}
        self.correlation_cache = {}
    
    def create_momentum_features(self, prices: pd.Series, window: int = 5) -> Dict[str, float]:
        """
        Create price momentum features over multiple windows
        
        Args:
            prices: Price series (yes_price, no_price, or implied_probability)
            window: Base window size for calculations
            
        Returns:
            Dictionary of momentum features
        """
        features = {}
        
        if len(prices) < window:
            return features
        
        # Short-term momentum (5 periods)
        if len(prices) >= 5:
            features['momentum_5'] = (prices.iloc[-1] - prices.iloc[-5]) / prices.iloc[-5] if prices.iloc[-5] != 0 else 0
        
        # Medium-term momentum (20 periods)
        if len(prices) >= 20:
            features['momentum_20'] = (prices.iloc[-1] - prices.iloc[-20]) / prices.iloc[-20] if prices.iloc[-20] != 0 else 0
        
        # Long-term momentum (60 periods)
        if len(prices) >= 60:
            features['momentum_60'] = (prices.iloc[-1] - prices.iloc[-60]) / prices.iloc[-60] if prices.iloc[-60] != 0 else 0
        
        # Acceleration (rate of change of momentum)
        if len(prices) >= 10:
            momentum_5_prev = (prices.iloc[-6] - prices.iloc[-10]) / prices.iloc[-10] if prices.iloc[-10] != 0 else 0
            momentum_5_curr = features.get('momentum_5', 0)
            features['acceleration'] = momentum_5_curr - momentum_5_prev
        
        # Momentum persistence
        if len(prices) >= 15:
            recent_changes = prices.diff().iloc[-15:]
            features['momentum_persistence'] = (recent_changes > 0).sum() / len(recent_changes)
        
        # Momentum volatility
        if len(prices) >= 10:
            momentum_series = prices.pct_change().iloc[-10:]
            features['momentum_volatility'] = momentum_series.std()
        
        return features
    
    def create_volume_features(self, volume: pd.Series, prices: pd.Series) -> Dict[str, float]:
        """
        Create volume-weighted indicators and volume-based features
        
        Args:
            volume: Volume series
            prices: Price series (for VWAP calculation)
            
        Returns:
            Dictionary of volume features
        """
        features = {}
        
        if len(volume) < 2:
            return features
        
        # Current volume metrics
        features['current_volume'] = volume.iloc[-1]
        features['volume_change'] = volume.iloc[-1] - volume.iloc[-2] if len(volume) >= 2 else 0
        
        # Volume-weighted average price (VWAP)
        if len(volume) >= 5 and len(prices) >= 5:
            vwap_window = min(5, len(volume))
            volume_sum = volume.iloc[-vwap_window:].sum()
            if volume_sum > 0:
                features['vwap'] = (prices.iloc[-vwap_window:] * volume.iloc[-vwap_window:]).sum() / volume_sum
        
        # On-balance volume (OBV)
        if len(volume) >= 10:
            price_changes = prices.diff().iloc[-10:]
            obv = 0
            for i, change in enumerate(price_changes):
                if change > 0:
                    obv += volume.iloc[-10+i]
                elif change < 0:
                    obv -= volume.iloc[-10+i]
            features['obv'] = obv
        
        # Volume momentum
        if len(volume) >= 5:
            features['volume_momentum'] = (volume.iloc[-1] - volume.iloc[-5]) / volume.iloc[-5] if volume.iloc[-5] != 0 else 0
        
        # Volume volatility
        if len(volume) >= 10:
            features['volume_volatility'] = volume.iloc[-10:].std()
        
        # Volume-price trend
        if len(volume) >= 5 and len(prices) >= 5:
            vpt = 0
            for i in range(5):
                price_change = prices.iloc[-5+i] - prices.iloc[-6+i] if i < 4 else 0
                vpt += volume.iloc[-5+i] * price_change
            features['volume_price_trend'] = vpt
        
        # Volume ratio (current vs average)
        if len(volume) >= 10:
            avg_volume = volume.iloc[-10:].mean()
            features['volume_ratio'] = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1
        
        return features
    
    def create_microstructure_features(self, microstructure: MarketMicrostructure) -> Dict[str, float]:
        """
        Create market microstructure signals from orderbook data
        
        Args:
            microstructure: Market microstructure data
            
        Returns:
            Dictionary of microstructure features
        """
        features = {}
        
        # Bid-ask spread
        yes_spread = microstructure.yes_ask - microstructure.yes_bid
        no_spread = microstructure.no_ask - microstructure.no_bid
        features['yes_spread'] = yes_spread
        features['no_spread'] = no_spread
        features['avg_spread'] = (yes_spread + no_spread) / 2
        
        # Spread percentage
        yes_mid = (microstructure.yes_ask + microstructure.yes_bid) / 2
        no_mid = (microstructure.no_ask + microstructure.no_bid) / 2
        features['yes_spread_pct'] = yes_spread / yes_mid if yes_mid > 0 else 0
        features['no_spread_pct'] = no_spread / no_mid if no_mid > 0 else 0
        
        # Order book imbalance
        yes_imbalance = microstructure.yes_bid_size - microstructure.yes_ask_size
        no_imbalance = microstructure.no_bid_size - microstructure.no_ask_size
        features['yes_imbalance'] = yes_imbalance
        features['no_imbalance'] = no_imbalance
        features['total_imbalance'] = yes_imbalance + no_imbalance
        
        # Depth at best bid/ask
        features['yes_depth'] = microstructure.yes_bid_size + microstructure.yes_ask_size
        features['no_depth'] = microstructure.no_bid_size + microstructure.no_ask_size
        features['total_depth'] = features['yes_depth'] + features['no_depth']
        
        # Liquidity score
        features['liquidity_score'] = (
            microstructure.volume + 
            microstructure.open_interest + 
            features['total_depth']
        ) / 1000
        
        # Price impact (estimated)
        features['price_impact'] = features['avg_spread'] / features['liquidity_score'] if features['liquidity_score'] > 0 else 0
        
        return features
    
    def create_temporal_features(self, timestamp: datetime, market_close_time: Optional[datetime] = None) -> Dict[str, float]:
        """
        Create time-based pattern features
        
        Args:
            timestamp: Current timestamp
            market_close_time: Market close time (if available)
            
        Returns:
            Dictionary of temporal features
        """
        features = {}
        
        # Hour of day (cyclical encoding)
        hour = timestamp.hour
        features['hour_sin'] = np.sin(2 * np.pi * hour / 24)
        features['hour_cos'] = np.cos(2 * np.pi * hour / 24)
        features['hour_of_day'] = hour
        
        # Day of week (cyclical encoding)
        weekday = timestamp.weekday()
        features['weekday_sin'] = np.sin(2 * np.pi * weekday / 7)
        features['weekday_cos'] = np.cos(2 * np.pi * weekday / 7)
        features['day_of_week'] = weekday
        
        # Time to market close
        if market_close_time:
            time_to_close = (market_close_time - timestamp).total_seconds() / 3600  # hours
            features['time_to_close'] = time_to_close
            features['time_to_close_normalized'] = max(0, min(1, time_to_close / 24))  # normalize to 0-1
        
        # Trading session indicators
        features['is_market_hours'] = 1 if 9 <= hour <= 16 else 0  # Assume 9 AM - 4 PM
        features['is_lunch_hour'] = 1 if 12 <= hour <= 13 else 0
        features['is_end_of_day'] = 1 if hour >= 15 else 0
        
        # Weekend indicator
        features['is_weekend'] = 1 if weekday >= 5 else 0
        
        return features
    
    def create_cross_market_features(self, current_ticker: str, related_markets: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Create correlation-based features with related markets
        
        Args:
            current_ticker: Current market ticker
            related_markets: Dictionary of related market data
            
        Returns:
            Dictionary of cross-market features
        """
        features = {}
        
        if not related_markets:
            return features
        
        # Get current market data
        current_data = related_markets.get(current_ticker)
        if current_data is None or len(current_data) < 2:
            return features
        
        current_prob = current_data['implied_probability'].iloc[-1]
        
        # Calculate correlations with related markets
        correlations = []
        prob_differences = []
        
        for ticker, market_data in related_markets.items():
            if ticker == current_ticker or len(market_data) < 10:
                continue
            
            # Correlation with implied probability
            try:
                correlation = current_data['implied_probability'].corr(market_data['implied_probability'])
                if not np.isnan(correlation):
                    correlations.append(correlation)
            except:
                pass
            
            # Probability difference
            other_prob = market_data['implied_probability'].iloc[-1]
            prob_diff = current_prob - other_prob
            prob_differences.append(prob_diff)
        
        # Aggregate cross-market features
        if correlations:
            features['avg_correlation'] = np.mean(correlations)
            features['max_correlation'] = np.max(correlations)
            features['min_correlation'] = np.min(correlations)
            features['correlation_volatility'] = np.std(correlations)
        
        if prob_differences:
            features['avg_prob_difference'] = np.mean(prob_differences)
            features['max_prob_difference'] = np.max(prob_differences)
            features['min_prob_difference'] = np.min(prob_differences)
        
        # Sector momentum (if we have sector data)
        if len(related_markets) > 1:
            sector_probs = [market_data['implied_probability'].iloc[-1] for market_data in related_markets.values()]
            features['sector_momentum'] = np.mean(sector_probs) - 0.5  # deviation from 50%
            features['sector_volatility'] = np.std(sector_probs)
        
        return features
    
    def create_advanced_technical_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Create advanced technical analysis features
        
        Args:
            df: DataFrame with price and volume data
            
        Returns:
            Dictionary of technical features
        """
        features = {}
        
        if len(df) < 2:
            return features
        
        # Price-based features
        yes_prices = df['yes_price']
        no_prices = df['no_price']
        implied_probs = df['implied_probability']
        
        # Momentum features for different price series
        yes_momentum = self.create_momentum_features(yes_prices)
        no_momentum = self.create_momentum_features(no_prices)
        prob_momentum = self.create_momentum_features(implied_probs)
        
        # Add momentum features with prefixes
        for key, value in yes_momentum.items():
            features[f'yes_{key}'] = value
        for key, value in no_momentum.items():
            features[f'no_{key}'] = value
        for key, value in prob_momentum.items():
            features[f'prob_{key}'] = value
        
        # Volume features
        volume_features = self.create_volume_features(df['volume'], implied_probs)
        features.update(volume_features)
        
        # Advanced price patterns
        if len(df) >= 10:
            # Price channels
            high_10 = yes_prices.rolling(10).max().iloc[-1]
            low_10 = yes_prices.rolling(10).min().iloc[-1]
            features['yes_price_channel_position'] = (yes_prices.iloc[-1] - low_10) / (high_10 - low_10) if high_10 != low_10 else 0.5
            
            # Bollinger Bands
            ma_10 = yes_prices.rolling(10).mean().iloc[-1]
            std_10 = yes_prices.rolling(10).std().iloc[-1]
            features['yes_bollinger_position'] = (yes_prices.iloc[-1] - ma_10) / (2 * std_10) if std_10 > 0 else 0
        
        # RSI (Relative Strength Index)
        if len(df) >= 14:
            delta = yes_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
            rs = gain / loss if loss > 0 else 100
            features['yes_rsi'] = 100 - (100 / (1 + rs))
        
        # Price efficiency metrics
        features['price_efficiency'] = 1 - abs(implied_probs.iloc[-1] - 0.5)
        
        # Mean reversion indicators
        if len(df) >= 20:
            ma_20 = implied_probs.rolling(20).mean().iloc[-1]
            features['mean_reversion_signal'] = implied_probs.iloc[-1] - ma_20
        
        return features
    
    def engineer_comprehensive_features(self, ticker: str, df: pd.DataFrame, 
                                      microstructure: Optional[MarketMicrostructure] = None,
                                      related_markets: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, float]:
        """
        Engineer comprehensive features combining all feature types
        
        Args:
            ticker: Market ticker
            df: Historical market data
            microstructure: Current microstructure data
            related_markets: Related market data for cross-market features
            
        Returns:
            Dictionary of all engineered features
        """
        all_features = {}
        
        # Basic technical features
        technical_features = self.create_advanced_technical_features(df)
        all_features.update(technical_features)
        
        # Microstructure features
        if microstructure:
            microstructure_features = self.create_microstructure_features(microstructure)
            all_features.update(microstructure_features)
        
        # Temporal features
        temporal_features = self.create_temporal_features(datetime.now())
        all_features.update(temporal_features)
        
        # Cross-market features
        if related_markets:
            cross_market_features = self.create_cross_market_features(ticker, related_markets)
            all_features.update(cross_market_features)
        
        # Feature interactions (create combinations of important features)
        if 'yes_momentum_5' in all_features and 'volume_momentum' in all_features:
            all_features['momentum_volume_interaction'] = (
                all_features['yes_momentum_5'] * all_features['volume_momentum']
            )
        
        if 'yes_spread_pct' in all_features and 'liquidity_score' in all_features:
            all_features['spread_liquidity_interaction'] = (
                all_features['yes_spread_pct'] / (all_features['liquidity_score'] + 1)
            )
        
        # Feature normalization and scaling
        all_features = self._normalize_features(all_features)
        
        logger.info("Engineered comprehensive features", 
                   ticker=ticker, 
                   n_features=len(all_features),
                   feature_types=['technical', 'microstructure', 'temporal', 'cross_market'])
        
        return all_features
    
    def _normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize features to prevent extreme values
        
        Args:
            features: Raw features dictionary
            
        Returns:
            Normalized features dictionary
        """
        normalized = {}
        
        for key, value in features.items():
            # Handle NaN and infinite values
            if np.isnan(value) or np.isinf(value):
                normalized[key] = 0.0
                continue
            
            # Normalize based on feature type
            if 'momentum' in key or 'change' in key:
                # Momentum features: clip to reasonable range
                normalized[key] = np.clip(value, -2.0, 2.0)
            elif 'volatility' in key or 'std' in key:
                # Volatility features: log transform and clip
                normalized[key] = np.clip(np.log(abs(value) + 1), 0, 5)
            elif 'ratio' in key or 'pct' in key:
                # Ratio features: clip to reasonable range
                normalized[key] = np.clip(value, 0, 2)
            elif 'correlation' in key:
                # Correlation features: already bounded [-1, 1]
                normalized[key] = np.clip(value, -1, 1)
            else:
                # Other features: clip extreme values
                normalized[key] = np.clip(value, -10, 10)
        
        return normalized
    
    def get_feature_importance_weights(self) -> Dict[str, float]:
        """
        Get feature importance weights based on domain knowledge
        
        Returns:
            Dictionary of feature importance weights
        """
        return {
            # High importance features
            'prob_momentum_5': 1.0,
            'prob_momentum_20': 0.9,
            'yes_momentum_5': 0.8,
            'volume_momentum': 0.8,
            'liquidity_score': 0.7,
            'yes_spread_pct': 0.7,
            
            # Medium importance features
            'vwap': 0.6,
            'obv': 0.6,
            'yes_rsi': 0.6,
            'price_efficiency': 0.5,
            'avg_correlation': 0.5,
            'time_to_close': 0.5,
            
            # Lower importance features
            'hour_sin': 0.3,
            'weekday_sin': 0.3,
            'is_market_hours': 0.2,
            'is_weekend': 0.2,
        }
