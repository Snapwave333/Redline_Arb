"""
Data Manager for Kalshi Trading Bot

This module handles data collection, storage, and retrieval for market data,
including real-time updates, historical data, and feature engineering.
"""

import asyncio
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass, asdict
import json

from .kalshi_client import KalshiAPIClient, MarketData
from .config import config

logger = structlog.get_logger(__name__)


@dataclass
class HistoricalData:
    """Historical market data structure"""
    ticker: str
    timestamp: datetime
    yes_price: float
    no_price: float
    volume: int
    open_interest: int
    last_price: Optional[float]
    implied_probability: float


@dataclass
class FeatureData:
    """Feature data for ML model"""
    ticker: str
    timestamp: datetime
    features: Dict[str, float]
    target: Optional[float] = None  # Actual outcome for training


class DatabaseManager:
    """Manages SQLite database for storing market data"""
    
    def __init__(self, db_path: str = "data/kalshi_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Market data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                yes_price REAL NOT NULL,
                no_price REAL NOT NULL,
                volume INTEGER NOT NULL,
                open_interest INTEGER NOT NULL,
                last_price REAL,
                implied_probability REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, timestamp)
            )
        """)
        
        # Features table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                features_json TEXT NOT NULL,
                target REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, timestamp)
            )
        """)
        
        # Outcomes table (for training data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                event_date DATETIME NOT NULL,
                outcome INTEGER NOT NULL,  -- 0 for No, 1 for Yes
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, event_date)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_data_ticker_time ON market_data(ticker, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_features_ticker_time ON features(ticker, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_ticker_date ON outcomes(ticker, event_date)")
        
        conn.commit()
        conn.close()
    
    def save_market_data(self, data: MarketData):
        """Save market data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        implied_prob = data.yes_price / (data.yes_price + data.no_price) if (data.yes_price + data.no_price) > 0 else 0.5
        
        cursor.execute("""
            INSERT OR REPLACE INTO market_data 
            (ticker, timestamp, yes_price, no_price, volume, open_interest, last_price, implied_probability)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.ticker,
            data.timestamp,
            data.yes_price,
            data.no_price,
            data.volume,
            data.open_interest,
            data.last_price,
            implied_prob
        ))
        
        conn.commit()
        conn.close()
    
    def save_features(self, data: FeatureData):
        """Save feature data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO features 
            (ticker, timestamp, features_json, target)
            VALUES (?, ?, ?, ?)
        """, (
            data.ticker,
            data.timestamp,
            json.dumps(data.features),
            data.target
        ))
        
        conn.commit()
        conn.close()
    
    def save_outcome(self, ticker: str, event_date: datetime, outcome: int):
        """Save market outcome for training"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO outcomes 
            (ticker, event_date, outcome)
            VALUES (?, ?, ?)
        """, (ticker, event_date, outcome))
        
        conn.commit()
        conn.close()
    
    def get_historical_data(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """Get historical market data"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT * FROM market_data 
            WHERE ticker = ? AND timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp
        """.format(days)
        
        df = pd.read_sql_query(query, conn, params=(ticker,))
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def get_features_data(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """Get historical features data"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT * FROM features 
            WHERE ticker = ? AND timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp
        """.format(days)
        
        df = pd.read_sql_query(query, conn, params=(ticker,))
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Parse features JSON
            df['features'] = df['features_json'].apply(json.loads)
        
        return df


class FeatureEngineer:
    """Engineers features from market data for ML models"""
    
    def __init__(self):
        self.feature_window_hours = config.model.feature_window_hours
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators from price data"""
        if len(df) < 2:
            return {}
        
        features = {}
        
        # Price-based features
        features['current_yes_price'] = df['yes_price'].iloc[-1]
        features['current_no_price'] = df['no_price'].iloc[-1]
        features['current_implied_prob'] = df['implied_probability'].iloc[-1]
        
        # Price changes
        if len(df) >= 2:
            features['yes_price_change'] = df['yes_price'].iloc[-1] - df['yes_price'].iloc[-2]
            features['no_price_change'] = df['no_price'].iloc[-1] - df['no_price'].iloc[-2]
            features['prob_change'] = df['implied_probability'].iloc[-1] - df['implied_probability'].iloc[-2]
        
        # Moving averages
        if len(df) >= 5:
            features['yes_price_ma5'] = df['yes_price'].rolling(5).mean().iloc[-1]
            features['no_price_ma5'] = df['no_price'].rolling(5).mean().iloc[-1]
            features['prob_ma5'] = df['implied_probability'].rolling(5).mean().iloc[-1]
        
        if len(df) >= 10:
            features['yes_price_ma10'] = df['yes_price'].rolling(10).mean().iloc[-1]
            features['no_price_ma10'] = df['no_price'].rolling(10).mean().iloc[-1]
            features['prob_ma10'] = df['implied_probability'].rolling(10).mean().iloc[-1]
        
        # Volatility
        if len(df) >= 5:
            features['yes_price_volatility'] = df['yes_price'].rolling(5).std().iloc[-1]
            features['no_price_volatility'] = df['no_price'].rolling(5).std().iloc[-1]
            features['prob_volatility'] = df['implied_probability'].rolling(5).std().iloc[-1]
        
        # Volume features
        features['current_volume'] = df['volume'].iloc[-1]
        features['current_open_interest'] = df['open_interest'].iloc[-1]
        
        if len(df) >= 5:
            features['volume_ma5'] = df['volume'].rolling(5).mean().iloc[-1]
            features['open_interest_ma5'] = df['open_interest'].rolling(5).mean().iloc[-1]
        
        # Price ratios
        total_price = features['current_yes_price'] + features['current_no_price']
        if total_price > 0:
            features['yes_price_ratio'] = features['current_yes_price'] / total_price
            features['no_price_ratio'] = features['current_no_price'] / total_price
        
        # Time-based features
        features['hour_of_day'] = df['timestamp'].iloc[-1].hour
        features['day_of_week'] = df['timestamp'].iloc[-1].weekday()
        
        # Market microstructure features
        if len(df) >= 2:
            features['price_spread'] = abs(features['yes_price_change'] - features['no_price_change'])
            features['prob_momentum'] = features['prob_change']
        
        return features
    
    def calculate_market_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate market-specific features"""
        features = {}
        
        if len(df) < 2:
            return features
        
        # Market efficiency features
        features['price_efficiency'] = 1 - abs(df['implied_probability'].iloc[-1] - 0.5)
        
        # Liquidity features
        features['liquidity_score'] = (df['volume'].iloc[-1] + df['open_interest'].iloc[-1]) / 1000
        
        # Trend features
        if len(df) >= 3:
            prob_trend = np.polyfit(range(3), df['implied_probability'].iloc[-3:], 1)[0]
            features['prob_trend'] = prob_trend
        
        return features
    
    def engineer_features(self, ticker: str, db_manager: DatabaseManager) -> FeatureData:
        """Engineer features for a specific ticker"""
        # Get historical data
        df = db_manager.get_historical_data(ticker, days=config.data.historical_data_days)
        
        if df.empty:
            logger.warning("No historical data available for ticker", ticker=ticker)
            return FeatureData(ticker=ticker, timestamp=datetime.now(), features={})
        
        # Calculate features
        technical_features = self.calculate_technical_indicators(df)
        market_features = self.calculate_market_features(df)
        
        # Combine all features
        all_features = {**technical_features, **market_features}
        
        return FeatureData(
            ticker=ticker,
            timestamp=datetime.now(),
            features=all_features
        )


class DataManager:
    """Main data manager that coordinates data collection and storage"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.feature_engineer = FeatureEngineer()
        self.client: Optional[KalshiAPIClient] = None
    
    async def initialize(self):
        """Initialize the data manager"""
        self.client = KalshiAPIClient()
        await self.client.__aenter__()
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.__aexit__(None, None, None)
    
    async def collect_market_data(self, tickers: List[str]) -> Dict[str, MarketData]:
        """Collect current market data for multiple tickers"""
        if not self.client:
            await self.initialize()
        
        market_data = {}
        
        for ticker in tickers:
            try:
                data = await self.client.get_market_data(ticker)
                market_data[ticker] = data
                
                # Save to database
                self.db_manager.save_market_data(data)
                
                logger.info("Collected market data", ticker=ticker, 
                           yes_price=data.yes_price, no_price=data.no_price)
                
            except Exception as e:
                logger.error("Failed to collect market data", ticker=ticker, error=str(e))
        
        return market_data
    
    async def collect_and_engineer_features(self, tickers: List[str]) -> Dict[str, FeatureData]:
        """Collect market data and engineer features"""
        # Collect current market data
        await self.collect_market_data(tickers)
        
        # Engineer features
        features = {}
        for ticker in tickers:
            try:
                feature_data = self.feature_engineer.engineer_features(ticker, self.db_manager)
                features[ticker] = feature_data
                
                # Save features to database
                self.db_manager.save_features(feature_data)
                
            except Exception as e:
                logger.error("Failed to engineer features", ticker=ticker, error=str(e))
        
        return features
    
    def get_training_data(self, ticker: str, days: int = 30) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get training data for ML model"""
        # Get features data
        features_df = self.db_manager.get_features_data(ticker, days)
        
        if features_df.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Get outcomes data
        conn = sqlite3.connect(self.db_manager.db_path)
        outcomes_df = pd.read_sql_query("""
            SELECT * FROM outcomes 
            WHERE ticker = ? AND event_date >= datetime('now', '-{} days')
            ORDER BY event_date
        """.format(days), conn, params=(ticker,))
        conn.close()
        
        if not outcomes_df.empty:
            outcomes_df['event_date'] = pd.to_datetime(outcomes_df['event_date'])
        
        return features_df, outcomes_df
    
    async def start_real_time_collection(self, tickers: List[str], callback):
        """Start real-time data collection via WebSocket"""
        if not self.client:
            await self.initialize()
        
        # Connect to WebSocket
        await self.client.connect_websocket()
        
        # Subscribe to markets
        for ticker in tickers:
            await self.client.subscribe_to_market(ticker)
        
        # Listen for updates
        async def handle_update(data):
            try:
                if data.get("type") == "market_update":
                    ticker = data.get("ticker")
                    market_data = MarketData(
                        ticker=ticker,
                        yes_price=data.get("yes_price", 0),
                        no_price=data.get("no_price", 0),
                        volume=data.get("volume", 0),
                        open_interest=data.get("open_interest", 0),
                        last_price=data.get("last_price"),
                        timestamp=datetime.now()
                    )
                    
                    # Save to database
                    self.db_manager.save_market_data(market_data)
                    
                    # Call callback
                    await callback(market_data)
                    
            except Exception as e:
                logger.error("Error handling real-time update", error=str(e))
        
        # Start listening
        await self.client.listen_for_updates(handle_update)
    
    def add_outcome_data(self, ticker: str, event_date: datetime, outcome: int):
        """Add outcome data for training"""
        self.db_manager.save_outcome(ticker, event_date, outcome)
        logger.info("Added outcome data", ticker=ticker, event_date=event_date, outcome=outcome)
