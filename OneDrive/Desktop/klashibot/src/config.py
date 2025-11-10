"""
Kalshi Trading Bot - Configuration Management

This module handles all configuration settings for the trading bot,
including API credentials, trading parameters, and risk management settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class APIConfig(BaseSettings):
    """API configuration settings"""
    kalshi_api_key: str = Field(..., env="KALSHI_API_KEY")
    kalshi_private_key: str = Field(..., env="KALSHI_PRIVATE_KEY")
    kalshi_base_url: str = Field("https://api.elections.kalshi.com/trade-api/v2", env="KALSHI_BASE_URL")
    kalshi_ws_url: str = Field("wss://api.elections.kalshi.com/trade-api/v2/ws", env="KALSHI_WS_URL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class BotConfig(BaseSettings):
    """Bot configuration settings"""
    bot_name: str = Field("kalshi_trading_bot", env="BOT_NAME")
    environment: str = Field("sandbox", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class TradingConfig(BaseSettings):
    """Trading parameters configuration - Micro-position sizing for $20 start"""
    default_kelly_fraction: float = Field(0.05, env="DEFAULT_KELLY_FRACTION")
    min_probability_delta: float = Field(0.02, env="MIN_PROBABILITY_DELTA")
    max_position_size: int = Field(5, env="MAX_POSITION_SIZE")
    min_liquidity_threshold: int = Field(100, env="MIN_LIQUIDITY_THRESHOLD")
    min_position_size: int = Field(1, env="MIN_POSITION_SIZE")
    max_daily_positions: int = Field(10, env="MAX_DAILY_POSITIONS")
    min_trade_notional: float = Field(10.0, env="MIN_TRADE_NOTIONAL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class RiskConfig(BaseSettings):
    """Risk management configuration - Conservative for $20 start"""
    max_daily_loss: float = Field(2.0, env="MAX_DAILY_LOSS")
    max_portfolio_risk: float = Field(0.1, env="MAX_PORTFOLIO_RISK")
    position_timeout_hours: int = Field(24, env="POSITION_TIMEOUT_HOURS")
    max_single_position_risk: float = Field(0.5, env="MAX_SINGLE_POSITION_RISK")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class DataConfig(BaseSettings):
    """Data collection configuration"""
    market_data_interval: int = Field(60, env="MARKET_DATA_INTERVAL")
    historical_data_days: int = Field(30, env="HISTORICAL_DATA_DAYS")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class CashSafetyConfig(BaseSettings):
    """Cash safety configuration - For $20 starting balance"""
    min_cash_reserve: float = Field(2.0, env="MIN_CASH_RESERVE")
    max_cash_usage_pct: float = Field(0.9, env="MAX_CASH_USAGE_PCT")
    cash_update_interval: int = Field(30, env="CASH_UPDATE_INTERVAL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"




class DualStrategyConfig(BaseSettings):
    """Dual income + compounding strategy configuration - Starting with $20"""
    dual_strategy_enabled: bool = Field(True, env="DUAL_STRATEGY_ENABLED")
    daily_income_target: float = Field(400.0, env="DAILY_INCOME_TARGET")
    daily_compounding_target: float = Field(0.1, env="DAILY_COMPOUNDING_TARGET")
    daily_withdrawal_pct: float = Field(0.8, env="DAILY_WITHDRAWAL_PCT")
    reinvestment_pct: float = Field(0.95, env="REINVESTMENT_PCT")
    emergency_reserve: float = Field(5.0, env="EMERGENCY_RESERVE")
    max_daily_risk: float = Field(2.0, env="MAX_DAILY_RISK")
    min_balance_for_compounding: float = Field(50.0, env="MIN_BALANCE_FOR_COMPOUNDING")
    starting_balance: float = Field(20.0, env="STARTING_BALANCE")

    class Config:
        env_file = ".env"
        extra = "ignore"


class TradingThresholdConfig(BaseSettings):
    """Advanced trading threshold configuration"""
    
    # Probability Delta Thresholds
    min_edge_threshold: float = Field(0.02, env="MIN_EDGE_THRESHOLD")
    optimal_edge_threshold: float = Field(0.05, env="OPTIMAL_EDGE_THRESHOLD")
    max_edge_threshold: float = Field(0.15, env="MAX_EDGE_THRESHOLD")
    
    # Kelly Fraction Scaling
    base_kelly_fraction: float = Field(0.05, env="BASE_KELLY_FRACTION")
    max_kelly_fraction: float = Field(0.25, env="MAX_KELLY_FRACTION")
    kelly_scaling_factor: float = Field(2.0, env="KELLY_SCALING_FACTOR")
    
    # Confidence Thresholds
    min_model_confidence: float = Field(0.55, env="MIN_MODEL_CONFIDENCE")
    high_confidence_threshold: float = Field(0.70, env="HIGH_CONFIDENCE_THRESHOLD")
    
    # Market Quality Filters
    min_liquidity_cents: int = Field(100, env="MIN_LIQUIDITY_CENTS")
    max_spread_percent: float = Field(0.10, env="MAX_SPREAD_PERCENT")
    min_volume: int = Field(10, env="MIN_VOLUME")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class PayPalConfig(BaseSettings):
    """PayPal integration configuration - Gradual income growth from $20"""
    paypal_enabled: bool = Field(True, env="PAYPAL_ENABLED")
    paypal_client_id: str = Field("", env="PAYPAL_CLIENT_ID")
    paypal_client_secret: str = Field("", env="PAYPAL_CLIENT_SECRET")
    paypal_mode: str = Field("sandbox", env="PAYPAL_MODE")
    paypal_recipient_email: str = Field("", env="PAYPAL_RECIPIENT_EMAIL")
    daily_transfer_enabled: bool = Field(True, env="DAILY_TRANSFER_ENABLED")
    daily_transfer_amount: float = Field(400.0, env="DAILY_TRANSFER_AMOUNT")
    daily_deposit_target: float = Field(400.00, env="DAILY_DEPOSIT_TARGET")
    min_transfer_amount: float = Field(10.0, env="MIN_TRANSFER_AMOUNT")
    max_transfer_amount: float = Field(400.0, env="MAX_TRANSFER_AMOUNT")
    transfer_frequency: str = Field("daily", env="TRANSFER_FREQUENCY")
    transfer_time: str = Field("18:00", env="TRANSFER_TIME")
    auto_transfer_enabled: bool = Field(True, env="AUTO_TRANSFER_ENABLED")
    gradual_income_enabled: bool = Field(True, env="GRADUAL_INCOME_ENABLED")

    class Config:
        env_file = ".env"
        extra = "ignore"


class FirebaseConfig(BaseSettings):
    """Firebase configuration settings"""
    firebase_enabled: bool = Field(True, env="FIREBASE_ENABLED")
    firebase_credentials_path: str = Field("config/firebase_service_account.json", env="FIREBASE_CREDENTIALS_PATH")
    firebase_region: str = Field("us-central1", env="FIREBASE_REGION")
    firebase_database_id: str = Field("kalshi-trading", env="FIREBASE_DATABASE_ID")
    firebase_app_id: str = Field("kalshi-trading-bot", env="FIREBASE_APP_ID")
    firebase_user_id: str = Field("user-123", env="FIREBASE_USER_ID")

    class Config:
        env_file = ".env"
        extra = "ignore"


class DataConfig(BaseSettings):
    """Data collection configuration settings"""
    market_data_interval: int = Field(60, env="MARKET_DATA_INTERVAL")
    historical_data_days: int = Field(30, env="HISTORICAL_DATA_DAYS")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class ModelConfig(BaseSettings):
    """Model configuration settings"""
    model_retrain_interval: int = Field(3600, env="MODEL_RETRAIN_INTERVAL")
    feature_window_hours: int = Field(24, env="FEATURE_WINDOW_HOURS")
    
    class Config:
        env_file = ".env"
        extra = "ignore"




class Config:
    """Main configuration class that combines all settings"""
    
    def __init__(self):
        self.api = APIConfig()
        self.bot = BotConfig()
        self.trading = TradingConfig()
        self.risk = RiskConfig()
        self.data = DataConfig()
        self.model = ModelConfig()
        self.cash_safety = CashSafetyConfig()
        self.dual_strategy = DualStrategyConfig()
        self.paypal = PayPalConfig()
        self.firebase = FirebaseConfig()
        self.thresholds = TradingThresholdConfig()
    
    def validate_config(self) -> bool:
        """Validate that all required configuration is present"""
        try:
            # Check API credentials
            if not self.api.kalshi_api_key or self.api.kalshi_api_key == "your_api_key_here":
                raise ValueError("KALSHI_API_KEY not set or using default value")
            
            if not self.api.kalshi_private_key or self.api.kalshi_private_key == "your_private_key_here":
                raise ValueError("KALSHI_PRIVATE_KEY not set or using default value")
            
            # Validate trading parameters
            if self.trading.default_kelly_fraction <= 0 or self.trading.default_kelly_fraction > 1:
                raise ValueError("DEFAULT_KELLY_FRACTION must be between 0 and 1")
            
            if self.trading.min_probability_delta <= 0 or self.trading.min_probability_delta > 1:
                raise ValueError("MIN_PROBABILITY_DELTA must be between 0 and 1")
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False


# Global config instance
config = Config()
