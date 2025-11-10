"""
Test suite for Kalshi Trading Bot

This module contains unit tests for all bot components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Import components to test
from src.config import config
from src.kalshi_client import KalshiAPIClient, MarketData
from src.data_manager import DataManager, FeatureData
from src.models import LogisticRegressionPredictor, RandomForestPredictor
from src.strategy import StrategyEngine, TradingSignal
from src.execution import ExecutionManager
from src.risk_manager import RiskManager
from src.monitoring import MonitoringSystem


class TestKalshiAPIClient:
    """Test Kalshi API client"""
    
    @pytest.fixture
    def client(self):
        return KalshiAPIClient()
    
    def test_signature_generation(self, client):
        """Test HMAC signature generation"""
        signature = client._generate_signature("GET", "/markets", "")
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex length
    
    def test_probability_calculation(self, client):
        """Test probability calculation"""
        prob = client.calculate_probability(0.6, 0.4)
        assert prob == 0.6
    
    def test_kelly_fraction_calculation(self, client):
        """Test Kelly fraction calculation"""
        kelly = client.calculate_kelly_fraction(0.7, 0.5)
        assert 0 <= kelly <= 1


class TestDataManager:
    """Test data manager"""
    
    @pytest.fixture
    def data_manager(self):
        return DataManager()
    
    def test_database_initialization(self, data_manager):
        """Test database initialization"""
        assert data_manager.db_manager.db_path == "data/kalshi_data.db"
    
    def test_feature_engineering(self, data_manager):
        """Test feature engineering"""
        # Mock historical data
        import pandas as pd
        df = pd.DataFrame({
            'yes_price': [0.6, 0.65, 0.7],
            'no_price': [0.4, 0.35, 0.3],
            'volume': [1000, 1200, 1100],
            'open_interest': [5000, 5500, 5200],
            'timestamp': [datetime.now() - timedelta(hours=i) for i in range(3)]
        })
        df['implied_probability'] = df['yes_price'] / (df['yes_price'] + df['no_price'])
        
        features = data_manager.feature_engineer.calculate_technical_indicators(df)
        assert 'current_yes_price' in features
        assert 'current_no_price' in features
        assert 'current_implied_prob' in features


class TestModels:
    """Test ML models"""
    
    @pytest.fixture
    def logistic_model(self):
        return LogisticRegressionPredictor()
    
    @pytest.fixture
    def random_forest_model(self):
        return RandomForestPredictor()
    
    def test_model_initialization(self, logistic_model, random_forest_model):
        """Test model initialization"""
        assert logistic_model.model_name == "logistic_regression"
        assert random_forest_model.model_name == "random_forest"
        assert not logistic_model.is_trained
        assert not random_forest_model.is_trained
    
    def test_feature_preparation(self, logistic_model):
        """Test feature preparation"""
        import pandas as pd
        
        features_df = pd.DataFrame({
            'features': [
                {'feature1': 1.0, 'feature2': 2.0},
                {'feature1': 1.5, 'feature2': 2.5}
            ]
        })
        
        X, feature_names = logistic_model.prepare_features(features_df)
        assert len(feature_names) == 2
        assert X.shape[1] == 2
    
    def test_prediction_without_training(self, logistic_model):
        """Test prediction without training"""
        prob, conf = logistic_model.predict({'feature1': 1.0, 'feature2': 2.0})
        assert prob == 0.5  # Default prediction
        assert conf == 0.0


class TestStrategy:
    """Test strategy engine"""
    
    @pytest.fixture
    def strategy_engine(self):
        data_manager = Mock()
        model_manager = Mock()
        return StrategyEngine(data_manager, model_manager)
    
    def test_signal_generation(self, strategy_engine):
        """Test signal generation"""
        # Mock market data
        market_data = MarketData(
            ticker="TEST",
            yes_price=0.6,
            no_price=0.4,
            volume=1000,
            open_interest=5000,
            last_price=0.6,
            timestamp=datetime.now()
        )
        
        # Mock prediction
        from src.models import ModelPrediction
        prediction = ModelPrediction(
            ticker="TEST",
            model_probability=0.7,
            implied_probability=0.6,
            probability_delta=0.1,
            confidence=0.8,
            features_used=['feature1'],
            timestamp=datetime.now()
        )
        
        signal = strategy_engine.signal_generator.generate_signal(
            market_data, prediction, [], 10000
        )
        
        assert signal is not None
        assert signal.ticker == "TEST"
        assert signal.side == "yes"  # Model prob > implied prob
        assert signal.quantity > 0


class TestRiskManager:
    """Test risk manager"""
    
    @pytest.fixture
    def risk_manager(self):
        return RiskManager()
    
    def test_position_size_validation(self, risk_manager):
        """Test position size validation"""
        from src.strategy import TradingSignal
        
        signal = TradingSignal(
            ticker="TEST",
            side="yes",
            quantity=100,
            price=0.6,
            model_probability=0.7,
            implied_probability=0.6,
            probability_delta=0.1,
            confidence=0.8,
            kelly_fraction=0.1,
            expected_value=10.0,
            timestamp=datetime.now(),
            reason="Test signal"
        )
        
        is_valid, reason = risk_manager.position_risk_manager.validate_position_size(
            signal, 10000
        )
        
        assert is_valid
        assert reason == "Position size valid"
    
    def test_portfolio_risk_validation(self, risk_manager):
        """Test portfolio risk validation"""
        from src.kalshi_client import Position
        
        positions = {
            "TEST1": Position(
                ticker="TEST1",
                side="yes",
                quantity=100,
                average_price=0.6,
                unrealized_pnl=10.0,
                realized_pnl=0.0
            )
        }
        
        violations = risk_manager.portfolio_risk_manager.validate_portfolio_risk(
            positions, 10000
        )
        
        assert isinstance(violations, list)


class TestExecutionManager:
    """Test execution manager"""
    
    @pytest.fixture
    def execution_manager(self):
        client = Mock()
        return ExecutionManager(client)
    
    def test_execution_manager_initialization(self, execution_manager):
        """Test execution manager initialization"""
        assert execution_manager.order_manager is not None
        assert execution_manager.position_manager is not None
        assert not execution_manager.is_running


class TestMonitoringSystem:
    """Test monitoring system"""
    
    @pytest.fixture
    def monitoring_system(self):
        return MonitoringSystem()
    
    def test_monitoring_initialization(self, monitoring_system):
        """Test monitoring system initialization"""
        assert monitoring_system.monitoring_db is not None
        assert monitoring_system.logging_manager is not None
        assert monitoring_system.alert_manager is not None
        assert monitoring_system.performance_monitor is not None
    
    def test_alert_creation(self, monitoring_system):
        """Test alert creation"""
        from src.monitoring import AlertType, LogLevel
        
        alert = monitoring_system.alert_manager.create_alert(
            AlertType.TRADE_EXECUTED,
            LogLevel.INFO,
            "Test Alert",
            "This is a test alert",
            {"test": True}
        )
        
        assert alert.alert_type == AlertType.TRADE_EXECUTED
        assert alert.severity == LogLevel.INFO
        assert alert.title == "Test Alert"


# Integration tests
class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self):
        """Test bot initialization"""
        from src.main import KalshiTradingBot
        
        bot = KalshiTradingBot()
        
        # Mock the API client to avoid actual API calls
        with patch('src.main.KalshiAPIClient') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock()
            mock_client.return_value.__aexit__ = AsyncMock()
            
            await bot.initialize()
            
            assert bot.client is not None
            assert bot.data_manager is not None
            assert bot.model_manager is not None
            assert bot.strategy_engine is not None
            assert bot.execution_manager is not None
            assert bot.risk_manager is not None
            assert bot.monitoring_system is not None
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test with invalid config
        with patch('src.config.config.api.api_key', 'your_api_key_here'):
            assert not config.validate_config()
        
        # Test with valid config
        with patch('src.config.config.api.api_key', 'valid_key'):
            with patch('src.config.config.api.private_key', 'valid_private_key'):
                assert config.validate_config()


# Performance tests
class TestPerformance:
    """Performance tests"""
    
    def test_feature_engineering_performance(self):
        """Test feature engineering performance"""
        import pandas as pd
        import time
        
        # Create large dataset
        n_rows = 1000
        df = pd.DataFrame({
            'yes_price': [0.6] * n_rows,
            'no_price': [0.4] * n_rows,
            'volume': [1000] * n_rows,
            'open_interest': [5000] * n_rows,
            'timestamp': [datetime.now()] * n_rows
        })
        df['implied_probability'] = df['yes_price'] / (df['yes_price'] + df['no_price'])
        
        data_manager = DataManager()
        
        start_time = time.time()
        features = data_manager.feature_engineer.calculate_technical_indicators(df)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 1.0  # Less than 1 second
        assert len(features) > 0


if __name__ == "__main__":
    pytest.main([__file__])
