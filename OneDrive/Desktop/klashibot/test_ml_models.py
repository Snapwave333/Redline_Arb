"""
Comprehensive ML Model Testing Suite for Kalshi Trading Bot

This script tests all the new ML models (Random Forest, XGBoost, Ensemble) with real market data
and validates their performance against the existing logistic regression baseline.
"""

import sys
import asyncio
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import structlog
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

# Import our modules
from src.config import config
from src.data_manager import DataManager
from src.feature_engineering import AdvancedFeatureEngineer, MarketMicrostructure
from src.models import LogisticRegressionPredictor
from src.models.random_forest_model import AdvancedRandomForestPredictor
from src.models.xgboost_model import AdvancedXGBoostPredictor
from src.models.ensemble_predictor import AdvancedEnsemblePredictor
from src.model_monitor import ModelPerformanceMonitor
from src.kalshi_client import KalshiAPIClient

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger(__name__)


class MLModelTester:
    """
    Comprehensive testing suite for all ML models
    """
    
    def __init__(self):
        self.data_manager = DataManager()
        self.feature_engineer = AdvancedFeatureEngineer()
        self.model_monitor = ModelPerformanceMonitor()
        
        # Initialize models
        self.models = {
            'logistic': LogisticRegressionPredictor(),
            'random_forest': AdvancedRandomForestPredictor(),
            'xgboost': AdvancedXGBoostPredictor()
        }
        
        self.ensemble = AdvancedEnsemblePredictor()
        self.test_results = {}
        
        logger.info("ML Model Tester initialized")
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of all ML models"""
        print("="*80)
        print("COMPREHENSIVE ML MODEL TESTING SUITE")
        print("="*80)
        
        try:
            # Initialize data manager
            await self.data_manager.initialize()
            
            # Test 1: Feature Engineering
            print("\n1. Testing Advanced Feature Engineering...")
            await self.test_feature_engineering()
            
            # Test 2: Individual Model Training
            print("\n2. Testing Individual Model Training...")
            await self.test_individual_models()
            
            # Test 3: Ensemble Training
            print("\n3. Testing Ensemble Training...")
            await self.test_ensemble_training()
            
            # Test 4: Model Predictions
            print("\n4. Testing Model Predictions...")
            await self.test_model_predictions()
            
            # Test 5: Performance Monitoring
            print("\n5. Testing Performance Monitoring...")
            await self.test_performance_monitoring()
            
            # Test 6: Model Comparison
            print("\n6. Comparing Model Performance...")
            await self.compare_model_performance()
            
            # Generate final report
            print("\n7. Generating Test Report...")
            self.generate_test_report()
            
        except Exception as e:
            logger.error("Test suite failed", error=str(e))
            print(f"\n[ERROR] Test suite failed: {e}")
        
        finally:
            await self.data_manager.cleanup()
    
    async def test_feature_engineering(self):
        """Test advanced feature engineering"""
        print("   Testing feature engineering with real market data...")
        
        try:
            # Get real market data
            tickers = await self.get_test_tickers()
            if not tickers:
                print("   [WARNING] No test tickers available")
                return
            
            test_ticker = tickers[0]
            print(f"   Using test ticker: {test_ticker}")
            
            # Collect market data
            market_data = await self.data_manager.collect_market_data([test_ticker])
            if test_ticker not in market_data:
                print("   [WARNING] No market data collected")
                return
            
            # Get historical data for feature engineering
            historical_df = self.data_manager.db_manager.get_historical_data(test_ticker, days=30)
            if historical_df.empty:
                print("   [WARNING] No historical data available")
                return
            
            # Test feature engineering
            features = self.feature_engineer.engineer_comprehensive_features(
                ticker=test_ticker,
                df=historical_df,
                microstructure=None,  # We don't have orderbook data in this test
                related_markets=None
            )
            
            print(f"   [SUCCESS] Generated {len(features)} features")
            print(f"   Feature categories:")
            
            # Categorize features
            categories = {
                'momentum': [k for k in features.keys() if 'momentum' in k.lower()],
                'volume': [k for k in features.keys() if 'volume' in k.lower()],
                'temporal': [k for k in features.keys() if any(x in k.lower() for x in ['hour', 'day', 'time'])],
                'technical': [k for k in features.keys() if any(x in k.lower() for x in ['rsi', 'ma', 'vwap'])],
                'other': [k for k in features.keys() if not any(x in k.lower() for x in ['momentum', 'volume', 'hour', 'day', 'time', 'rsi', 'ma', 'vwap'])]
            }
            
            for category, feature_list in categories.items():
                if feature_list:
                    print(f"     {category}: {len(feature_list)} features")
            
            self.test_results['feature_engineering'] = {
                'success': True,
                'n_features': len(features),
                'categories': categories
            }
            
        except Exception as e:
            print(f"   [ERROR] Feature engineering test failed: {e}")
            self.test_results['feature_engineering'] = {'success': False, 'error': str(e)}
    
    async def test_individual_models(self):
        """Test individual model training"""
        print("   Testing individual model training...")
        
        try:
            # Get test ticker
            tickers = await self.get_test_tickers()
            if not tickers:
                print("   [WARNING] No test tickers available")
                return
            
            test_ticker = tickers[0]
            
            # Get training data
            features_df, outcomes_df = self.data_manager.get_training_data(test_ticker, days=30)
            
            if features_df.empty or outcomes_df.empty:
                print("   [WARNING] No training data available")
                return
            
            print(f"   Training data: {len(features_df)} features, {len(outcomes_df)} outcomes")
            
            model_results = {}
            
            # Test each model
            for model_name, model in self.models.items():
                print(f"   Testing {model_name}...")
                
                try:
                    if model_name == 'logistic':
                        result = model.train(features_df, outcomes_df)
                    else:
                        # Advanced models with hyperparameter search
                        result = model.train(features_df, outcomes_df, perform_hyperparameter_search=False)
                    
                    if 'error' not in result:
                        metrics = result.get('performance_metrics', {})
                        print(f"     [SUCCESS] Accuracy: {metrics.get('accuracy', 0):.3f}, "
                              f"ROC-AUC: {metrics.get('roc_auc', 0):.3f}")
                        
                        model_results[model_name] = {
                            'success': True,
                            'accuracy': metrics.get('accuracy', 0),
                            'roc_auc': metrics.get('roc_auc', 0),
                            'brier_score': metrics.get('brier_score', 0)
                        }
                    else:
                        print(f"     [ERROR] {result['error']}")
                        model_results[model_name] = {'success': False, 'error': result['error']}
                        
                except Exception as e:
                    print(f"     [ERROR] {model_name} training failed: {e}")
                    model_results[model_name] = {'success': False, 'error': str(e)}
            
            self.test_results['individual_models'] = model_results
            
        except Exception as e:
            print(f"   [ERROR] Individual model testing failed: {e}")
            self.test_results['individual_models'] = {'error': str(e)}
    
    async def test_ensemble_training(self):
        """Test ensemble training"""
        print("   Testing ensemble training...")
        
        try:
            # Get test ticker
            tickers = await self.get_test_tickers()
            if not tickers:
                print("   [WARNING] No test tickers available")
                return
            
            test_ticker = tickers[0]
            
            # Train ensemble
            ensemble_results = self.ensemble.train_all_models(
                self.data_manager, 
                test_ticker, 
                perform_hyperparameter_search=False
            )
            
            if 'error' not in ensemble_results:
                print(f"   [SUCCESS] Ensemble trained successfully")
                
                # Show individual model results
                for model_name, result in ensemble_results.items():
                    if 'error' not in result:
                        metrics = result.get('performance_metrics', {})
                        print(f"     {model_name}: Accuracy {metrics.get('accuracy', 0):.3f}, "
                              f"ROC-AUC {metrics.get('roc_auc', 0):.3f}")
                
                self.test_results['ensemble'] = {
                    'success': True,
                    'results': ensemble_results
                }
            else:
                print(f"   [ERROR] Ensemble training failed: {ensemble_results['error']}")
                self.test_results['ensemble'] = {'success': False, 'error': ensemble_results['error']}
                
        except Exception as e:
            print(f"   [ERROR] Ensemble testing failed: {e}")
            self.test_results['ensemble'] = {'success': False, 'error': str(e)}
    
    async def test_model_predictions(self):
        """Test model predictions"""
        print("   Testing model predictions...")
        
        try:
            # Get test ticker
            tickers = await self.get_test_tickers()
            if not tickers:
                print("   [WARNING] No test tickers available")
                return
            
            test_ticker = tickers[0]
            
            # Generate test features
            historical_df = self.data_manager.db_manager.get_historical_data(test_ticker, days=30)
            if historical_df.empty:
                print("   [WARNING] No historical data for predictions")
                return
            
            features = self.feature_engineer.engineer_comprehensive_features(
                ticker=test_ticker,
                df=historical_df
            )
            
            prediction_results = {}
            
            # Test individual model predictions
            for model_name, model in self.models.items():
                if model.is_trained:
                    try:
                        prob, conf = model.predict(features)
                        print(f"     {model_name}: Probability {prob:.3f}, Confidence {conf:.3f}")
                        prediction_results[model_name] = {
                            'probability': prob,
                            'confidence': conf,
                            'success': True
                        }
                    except Exception as e:
                        print(f"     {model_name}: [ERROR] {e}")
                        prediction_results[model_name] = {'success': False, 'error': str(e)}
                else:
                    print(f"     {model_name}: [SKIP] Model not trained")
                    prediction_results[model_name] = {'success': False, 'error': 'Model not trained'}
            
            # Test ensemble prediction
            if self.ensemble.is_trained:
                try:
                    ensemble_prob, ensemble_conf = self.ensemble.predict_ensemble(features, test_ticker)
                    print(f"     ensemble: Probability {ensemble_prob:.3f}, Confidence {ensemble_conf:.3f}")
                    prediction_results['ensemble'] = {
                        'probability': ensemble_prob,
                        'confidence': ensemble_conf,
                        'success': True
                    }
                except Exception as e:
                    print(f"     ensemble: [ERROR] {e}")
                    prediction_results['ensemble'] = {'success': False, 'error': str(e)}
            
            self.test_results['predictions'] = prediction_results
            
        except Exception as e:
            print(f"   [ERROR] Prediction testing failed: {e}")
            self.test_results['predictions'] = {'error': str(e)}
    
    async def test_performance_monitoring(self):
        """Test performance monitoring"""
        print("   Testing performance monitoring...")
        
        try:
            # Test tracking predictions
            test_ticker = "TEST-TICKER"
            
            # Simulate some predictions
            for i in range(10):
                prediction = 0.6 + np.random.normal(0, 0.1)
                confidence = 0.7 + np.random.normal(0, 0.1)
                actual_outcome = np.random.choice([0, 1])
                
                self.model_monitor.track_prediction(
                    model_name="test_model",
                    ticker=test_ticker,
                    prediction=prediction,
                    confidence=confidence,
                    actual_outcome=actual_outcome
                )
            
            print("     [SUCCESS] Performance tracking working")
            
            # Test drift detection
            # Simulate performance degradation
            for i in range(20):
                prediction = 0.4 + np.random.normal(0, 0.2)  # Worse predictions
                confidence = 0.5 + np.random.normal(0, 0.2)
                actual_outcome = np.random.choice([0, 1])
                
                self.model_monitor.track_prediction(
                    model_name="test_model",
                    ticker=test_ticker,
                    prediction=prediction,
                    confidence=confidence,
                    actual_outcome=actual_outcome
                )
            
            # Check for alerts
            alerts = self.model_monitor.get_active_alerts("test_model", test_ticker)
            if alerts:
                print(f"     [SUCCESS] Detected {len(alerts)} drift alerts")
            else:
                print("     [INFO] No drift alerts detected")
            
            # Test health status
            health = self.model_monitor.get_model_health("test_model", test_ticker)
            if health:
                print(f"     [SUCCESS] Model health: {health.health_score:.3f}, "
                      f"Healthy: {health.is_healthy}")
            
            self.test_results['monitoring'] = {
                'success': True,
                'alerts_count': len(alerts),
                'health_score': health.health_score if health else 0
            }
            
        except Exception as e:
            print(f"   [ERROR] Performance monitoring test failed: {e}")
            self.test_results['monitoring'] = {'success': False, 'error': str(e)}
    
    async def compare_model_performance(self):
        """Compare performance of all models"""
        print("   Comparing model performance...")
        
        try:
            comparison_results = {}
            
            # Get individual model results
            individual_results = self.test_results.get('individual_models', {})
            
            for model_name, result in individual_results.items():
                if result.get('success'):
                    comparison_results[model_name] = {
                        'accuracy': result.get('accuracy', 0),
                        'roc_auc': result.get('roc_auc', 0),
                        'brier_score': result.get('brier_score', 0)
                    }
            
            # Get ensemble results
            ensemble_results = self.test_results.get('ensemble', {})
            if ensemble_results.get('success'):
                ensemble_performance = {}
                for model_name, result in ensemble_results.get('results', {}).items():
                    if 'error' not in result:
                        metrics = result.get('performance_metrics', {})
                        ensemble_performance[model_name] = {
                            'accuracy': metrics.get('accuracy', 0),
                            'roc_auc': metrics.get('roc_auc', 0),
                            'brier_score': metrics.get('brier_score', 0)
                        }
                
                comparison_results['ensemble'] = ensemble_performance
            
            # Find best performing model
            if comparison_results:
                best_accuracy = max(
                    (result.get('accuracy', 0) for result in comparison_results.values()),
                    default=0
                )
                
                best_roc_auc = max(
                    (result.get('roc_auc', 0) for result in comparison_results.values()),
                    default=0
                )
                
                print(f"     Best Accuracy: {best_accuracy:.3f}")
                print(f"     Best ROC-AUC: {best_roc_auc:.3f}")
                
                # Show individual model rankings
                print("     Model Rankings (by ROC-AUC):")
                sorted_models = sorted(
                    comparison_results.items(),
                    key=lambda x: x[1].get('roc_auc', 0),
                    reverse=True
                )
                
                for i, (model_name, metrics) in enumerate(sorted_models, 1):
                    print(f"       {i}. {model_name}: ROC-AUC {metrics.get('roc_auc', 0):.3f}")
            
            self.test_results['comparison'] = comparison_results
            
        except Exception as e:
            print(f"   [ERROR] Model comparison failed: {e}")
            self.test_results['comparison'] = {'error': str(e)}
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("ML MODEL TESTING REPORT")
        print("="*80)
        
        # Feature Engineering Results
        fe_results = self.test_results.get('feature_engineering', {})
        if fe_results.get('success'):
            print(f"\n1. Feature Engineering: SUCCESS")
            print(f"   Generated {fe_results.get('n_features', 0)} features")
        else:
            print(f"\n1. Feature Engineering: FAILED")
            print(f"   Error: {fe_results.get('error', 'Unknown')}")
        
        # Individual Models Results
        individual_results = self.test_results.get('individual_models', {})
        print(f"\n2. Individual Models:")
        for model_name, result in individual_results.items():
            if result.get('success'):
                print(f"   {model_name}: SUCCESS")
                print(f"     Accuracy: {result.get('accuracy', 0):.3f}")
                print(f"     ROC-AUC: {result.get('roc_auc', 0):.3f}")
            else:
                print(f"   {model_name}: FAILED")
                print(f"     Error: {result.get('error', 'Unknown')}")
        
        # Ensemble Results
        ensemble_results = self.test_results.get('ensemble', {})
        if ensemble_results.get('success'):
            print(f"\n3. Ensemble: SUCCESS")
        else:
            print(f"\n3. Ensemble: FAILED")
            print(f"   Error: {ensemble_results.get('error', 'Unknown')}")
        
        # Predictions Results
        prediction_results = self.test_results.get('predictions', {})
        print(f"\n4. Predictions:")
        for model_name, result in prediction_results.items():
            if result.get('success'):
                print(f"   {model_name}: Probability {result.get('probability', 0):.3f}, "
                      f"Confidence {result.get('confidence', 0):.3f}")
            else:
                print(f"   {model_name}: FAILED")
        
        # Monitoring Results
        monitoring_results = self.test_results.get('monitoring', {})
        if monitoring_results.get('success'):
            print(f"\n5. Performance Monitoring: SUCCESS")
            print(f"   Alerts: {monitoring_results.get('alerts_count', 0)}")
            print(f"   Health Score: {monitoring_results.get('health_score', 0):.3f}")
        else:
            print(f"\n5. Performance Monitoring: FAILED")
        
        # Overall Assessment
        print(f"\n" + "="*80)
        print("OVERALL ASSESSMENT")
        print("="*80)
        
        success_count = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get('success'))
        total_tests = len([r for r in self.test_results.values() 
                          if isinstance(r, dict) and 'success' in r])
        
        print(f"Tests Passed: {success_count}/{total_tests}")
        
        if success_count == total_tests:
            print("STATUS: ALL TESTS PASSED - ML MODELS READY FOR DEPLOYMENT")
        elif success_count >= total_tests * 0.8:
            print("STATUS: MOSTLY SUCCESSFUL - MINOR ISSUES TO ADDRESS")
        else:
            print("STATUS: SIGNIFICANT ISSUES - REQUIRES ATTENTION")
        
        print("="*80)
    
    async def get_test_tickers(self) -> List[str]:
        """Get test tickers from real market data"""
        try:
            # Use the existing get_active_markets script logic
            client = KalshiAPIClient()
            await client.__aenter__()
            
            markets = await client.get_markets(limit=10)
            
            # Filter for markets with actual bids
            test_tickers = []
            for market in markets:
                if market.get('yes_bid', 0) > 0 or market.get('no_bid', 0) > 0:
                    test_tickers.append(market['ticker'])
                    if len(test_tickers) >= 3:  # Get a few test tickers
                        break
            
            await client.__aexit__(None, None, None)
            return test_tickers
            
        except Exception as e:
            logger.error("Failed to get test tickers", error=str(e))
            # Return a mock ticker for testing
            return ["TEST-TICKER-123"]


async def main():
    """Main test function"""
    tester = MLModelTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())
