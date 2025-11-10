"""
Tests for Daily Capital Manager

This module tests the daily capital allocation logic including:
- Profit tracking and transfer calculation
- Firebase state persistence
- PayPal transfer integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.realistic_growth import DailyCapitalManager
from src.config import config


class TestDailyCapitalManager:
    """Test cases for DailyCapitalManager"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock KalshiAPIClient"""
        client = Mock()
        client.get_portfolio = AsyncMock(return_value={'balance': 2000})  # $20 in cents
        return client
    
    @pytest.fixture
    def mock_firebase_manager(self):
        """Mock FirebaseManager"""
        manager = Mock()
        manager.get_bankroll_benchmark.return_value = 20.0
        manager.set_bankroll_benchmark = Mock()
        manager.initialize = Mock()
        return manager
    
    @pytest.fixture
    def mock_paypal_manager(self):
        """Mock PayPalTransferManager"""
        manager = Mock()
        manager.initialize = AsyncMock()
        manager.transfer_daily_income = AsyncMock()
        return manager
    
    @pytest.fixture
    async def capital_manager(self, mock_client, mock_firebase_manager, mock_paypal_manager):
        """Create DailyCapitalManager with mocked dependencies"""
        with patch('src.realistic_growth.FirebaseManager', return_value=mock_firebase_manager), \
             patch('src.realistic_growth.PayPalTransferManager', return_value=mock_paypal_manager):
            
            manager = DailyCapitalManager(mock_client)
            await manager.initialize()
            return manager
    
    def test_profit_tracking(self, capital_manager):
        """Test realized profit tracking"""
        # Initial state
        assert capital_manager._realized_profit_accumulator == 0.0
        
        # Add profits
        capital_manager.update_realized_profit(150.0)
        assert capital_manager._realized_profit_accumulator == 150.0
        
        capital_manager.update_realized_profit(250.0)
        assert capital_manager._realized_profit_accumulator == 400.0
        
        # Add loss
        capital_manager.update_realized_profit(-50.0)
        assert capital_manager._realized_profit_accumulator == 350.0
    
    def test_transfer_calculation_sufficient_profit(self, capital_manager):
        """Test transfer calculation when profit >= $400"""
        # Set up sufficient profit
        capital_manager._realized_profit_accumulator = 500.0
        
        transfer_amount, retained_profit = capital_manager.calculate_transfer_and_bankroll()
        
        assert transfer_amount == 400.0  # Should transfer exactly $400
        assert retained_profit == 100.0  # Should retain $100
    
    def test_transfer_calculation_insufficient_profit(self, capital_manager):
        """Test transfer calculation when profit < $400"""
        # Set up insufficient profit
        capital_manager._realized_profit_accumulator = 150.0
        
        transfer_amount, retained_profit = capital_manager.calculate_transfer_and_bankroll()
        
        assert transfer_amount == 150.0  # Should transfer whatever profit was made
        assert retained_profit == 0.0    # Should retain nothing
    
    def test_transfer_calculation_no_profit(self, capital_manager):
        """Test transfer calculation when no profit"""
        # No profit
        capital_manager._realized_profit_accumulator = 0.0
        
        transfer_amount, retained_profit = capital_manager.calculate_transfer_and_bankroll()
        
        assert transfer_amount == 0.0
        assert retained_profit == 0.0
    
    @pytest.mark.asyncio
    async def test_daily_cycle_successful_transfer(self, capital_manager, mock_paypal_manager):
        """Test successful daily cycle execution"""
        # Set up profit and successful transfer
        capital_manager._realized_profit_accumulator = 500.0
        mock_paypal_manager.transfer_daily_income.return_value = Mock(success=True)
        
        await capital_manager.manage_daily_cycle()
        
        # Verify PayPal transfer was called with correct amount
        mock_paypal_manager.transfer_daily_income.assert_called_once_with(400.0)
        
        # Verify Firebase benchmark was updated
        capital_manager.firebase_manager.set_bankroll_benchmark.assert_called_once_with(120.0, 400.0)
        
        # Verify profit accumulator was reset
        assert capital_manager._realized_profit_accumulator == 0.0
        assert capital_manager.bankroll_benchmark == 120.0
    
    @pytest.mark.asyncio
    async def test_daily_cycle_failed_transfer(self, capital_manager, mock_paypal_manager):
        """Test daily cycle when PayPal transfer fails"""
        # Set up profit and failed transfer
        capital_manager._realized_profit_accumulator = 500.0
        mock_paypal_manager.transfer_daily_income.return_value = Mock(
            success=False, 
            error_message="Insufficient funds"
        )
        
        await capital_manager.manage_daily_cycle()
        
        # Verify PayPal transfer was attempted
        mock_paypal_manager.transfer_daily_income.assert_called_once_with(400.0)
        
        # Verify Firebase benchmark was NOT updated
        capital_manager.firebase_manager.set_bankroll_benchmark.assert_not_called()
        
        # Verify profit accumulator was NOT reset
        assert capital_manager._realized_profit_accumulator == 500.0
        assert capital_manager.bankroll_benchmark == 20.0  # Original benchmark
    
    @pytest.mark.asyncio
    async def test_daily_cycle_insufficient_cash(self, capital_manager, mock_client):
        """Test daily cycle when insufficient cash available"""
        # Set up profit but insufficient cash
        capital_manager._realized_profit_accumulator = 500.0
        mock_client.get_portfolio.return_value = {'balance': 30000}  # $300 in cents, need $400
        
        await capital_manager.manage_daily_cycle()
        
        # Verify PayPal transfer was NOT attempted
        capital_manager.paypal_manager.transfer_daily_income.assert_not_called()
        
        # Verify Firebase benchmark was NOT updated
        capital_manager.firebase_manager.set_bankroll_benchmark.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_current_available_cash(self, capital_manager, mock_client):
        """Test getting current available cash"""
        mock_client.get_portfolio.return_value = {'balance': 2500}  # $25 in cents
        
        cash = await capital_manager.get_current_available_cash()
        
        assert cash == 25.0
        mock_client.get_portfolio.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_current_available_cash_error(self, capital_manager, mock_client):
        """Test getting current available cash when API fails"""
        mock_client.get_portfolio.side_effect = Exception("API Error")
        
        cash = await capital_manager.get_current_available_cash()
        
        assert cash == 0.0


class TestFirebaseIntegration:
    """Test Firebase state persistence"""
    
    def test_bankroll_benchmark_retrieval(self):
        """Test retrieving bankroll benchmark from Firebase"""
        from src.firebase_manager import FirebaseManager
        
        # Mock Firebase document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {'bankroll_benchmark': 25.50}
        
        # Mock Firebase client
        mock_db = Mock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock FirebaseManager
        manager = FirebaseManager()
        manager.db = mock_db
        manager._initialized = True
        
        benchmark = manager.get_bankroll_benchmark()
        
        assert benchmark == 25.50
    
    def test_bankroll_benchmark_not_found(self):
        """Test retrieving bankroll benchmark when document doesn't exist"""
        from src.firebase_manager import FirebaseManager
        
        # Mock Firebase document that doesn't exist
        mock_doc = Mock()
        mock_doc.exists = False
        
        # Mock Firebase client
        mock_db = Mock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock FirebaseManager
        manager = FirebaseManager()
        manager.db = mock_db
        manager._initialized = True
        
        benchmark = manager.get_bankroll_benchmark()
        
        assert benchmark == 0.0
    
    def test_bankroll_benchmark_update(self):
        """Test updating bankroll benchmark in Firebase"""
        from src.firebase_manager import FirebaseManager
        
        # Mock Firebase client
        mock_db = Mock()
        mock_doc_ref = Mock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_doc_ref
        
        # Mock FirebaseManager
        manager = FirebaseManager()
        manager.db = mock_db
        manager._initialized = True
        
        manager.set_bankroll_benchmark(30.75, 400.0)
        
        # Verify set was called with correct data
        mock_doc_ref.set.assert_called_once()
        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args['bankroll_benchmark'] == 30.75
        assert call_args['last_transfer_amount'] == 400.0


if __name__ == "__main__":
    pytest.main([__file__])
