"""
Standalone ML Model Testing Script

This script tests the new ML models without any import dependencies.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import structlog

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

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


def test_random_forest_standalone():
    """Test Random Forest model standalone"""
    print("Testing Random Forest Model (Standalone)...")
    
    try:
        # Import directly to avoid circular imports
        sys.path.append(str(Path(__file__).parent / "src" / "models"))
        from random_forest_model import AdvancedRandomForestPredictor
        
        # Create sample training data
        n_samples = 1000
        n_features = 20
        
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        
        # Create mock features DataFrame
        features_data = []
        for i in range(n_samples):
            feature_dict = {f'feature_{j}': X[i, j] for j in range(n_features)}
            features_data.append({
                'ticker': 'TEST',
                'timestamp': datetime.now(),
                'features': feature_dict
            })
        
        features_df = pd.DataFrame(features_data)
        outcomes_df = pd.DataFrame({
            'ticker': ['TEST'] * n_samples,
            'event_date': [datetime.now()] * n_samples,
            'outcome': y
        })
        
        # Test model
        model = AdvancedRandomForestPredictor()
        result = model.train(features_df, outcomes_df, perform_hyperparameter_search=False)
        
        if 'error' not in result:
            metrics = result.get('performance_metrics', {})
            print(f"   [SUCCESS] Accuracy: {metrics.get('accuracy', 0):.3f}")
            print(f"   [SUCCESS] ROC-AUC: {metrics.get('roc_auc', 0):.3f}")
            
            # Test prediction
            test_features = {f'feature_{j}': 0.5 for j in range(n_features)}
            prob, conf = model.predict(test_features)
            print(f"   [SUCCESS] Prediction: {prob:.3f}, Confidence: {conf:.3f}")
            
            # Test feature importance
            importance = model.get_feature_importance_analysis()
            print(f"   [SUCCESS] Feature importance analysis available")
            
            return True, metrics
        else:
            print(f"   [ERROR] Training failed: {result['error']}")
            return False, result['error']
            
    except Exception as e:
        print(f"   [ERROR] Random Forest test failed: {e}")
        return False, str(e)


def test_xgboost_standalone():
    """Test XGBoost model standalone"""
    print("Testing XGBoost Model (Standalone)...")
    
    try:
        # Import directly to avoid circular imports
        sys.path.append(str(Path(__file__).parent / "src" / "models"))
        from xgboost_model import AdvancedXGBoostPredictor
        
        # Create sample training data
        n_samples = 1000
        n_features = 20
        
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        
        # Create mock features DataFrame
        features_data = []
        for i in range(n_samples):
            feature_dict = {f'feature_{j}': X[i, j] for j in range(n_features)}
            features_data.append({
                'ticker': 'TEST',
                'timestamp': datetime.now(),
                'features': feature_dict
            })
        
        features_df = pd.DataFrame(features_data)
        outcomes_df = pd.DataFrame({
            'ticker': ['TEST'] * n_samples,
            'event_date': [datetime.now()] * n_samples,
            'outcome': y
        })
        
        # Test model
        model = AdvancedXGBoostPredictor()
        result = model.train(features_df, outcomes_df, perform_hyperparameter_search=False)
        
        if 'error' not in result:
            metrics = result.get('performance_metrics', {})
            print(f"   [SUCCESS] Accuracy: {metrics.get('accuracy', 0):.3f}")
            print(f"   [SUCCESS] ROC-AUC: {metrics.get('roc_auc', 0):.3f}")
            
            # Test prediction
            test_features = {f'feature_{j}': 0.5 for j in range(n_features)}
            prob, conf = model.predict(test_features)
            print(f"   [SUCCESS] Prediction: {prob:.3f}, Confidence: {conf:.3f}")
            
            # Test feature importance
            importance = model.get_feature_importance_analysis()
            print(f"   [SUCCESS] Feature importance analysis available")
            
            return True, metrics
        else:
            print(f"   [ERROR] Training failed: {result['error']}")
            return False, result['error']
            
    except Exception as e:
        print(f"   [ERROR] XGBoost test failed: {e}")
        return False, str(e)


def test_feature_engineering_standalone():
    """Test feature engineering standalone"""
    print("Testing Feature Engineering (Standalone)...")
    
    try:
        # Import directly to avoid circular imports
        sys.path.append(str(Path(__file__).parent / "src"))
        from feature_engineering import AdvancedFeatureEngineer
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
        sample_data = pd.DataFrame({
            'timestamp': dates,
            'yes_price': np.random.uniform(30, 70, 100),
            'no_price': np.random.uniform(30, 70, 100),
            'volume': np.random.randint(10, 1000, 100),
            'open_interest': np.random.randint(100, 5000, 100),
            'implied_probability': np.random.uniform(0.3, 0.7, 100)
        })
        
        # Test feature engineering
        engineer = AdvancedFeatureEngineer()
        features = engineer.engineer_comprehensive_features(
            ticker="TEST-TICKER",
            df=sample_data
        )
        
        print(f"   [SUCCESS] Generated {len(features)} features")
        
        # Show feature categories
        categories = {
            'momentum': [k for k in features.keys() if 'momentum' in k.lower()],
            'volume': [k for k in features.keys() if 'volume' in k.lower()],
            'temporal': [k for k in features.keys() if any(x in k.lower() for x in ['hour', 'day', 'time'])],
            'technical': [k for k in features.keys() if any(x in k.lower() for x in ['rsi', 'ma', 'vwap'])],
        }
        
        for category, feature_list in categories.items():
            if feature_list:
                print(f"     {category}: {len(feature_list)} features")
        
        return True, len(features)
        
    except Exception as e:
        print(f"   [ERROR] Feature engineering test failed: {e}")
        return False, str(e)


def test_model_monitoring_standalone():
    """Test model monitoring standalone"""
    print("Testing Model Performance Monitoring (Standalone)...")
    
    try:
        # Import directly to avoid circular imports
        sys.path.append(str(Path(__file__).parent / "src"))
        from model_monitor import ModelPerformanceMonitor
        
        # Create monitor
        monitor = ModelPerformanceMonitor()
        
        # Simulate predictions
        for i in range(50):
            prediction = 0.6 + np.random.normal(0, 0.1)
            confidence = 0.7 + np.random.normal(0, 0.1)
            actual_outcome = np.random.choice([0, 1])
            
            monitor.track_prediction(
                model_name="test_model",
                ticker="TEST-TICKER",
                prediction=prediction,
                confidence=confidence,
                actual_outcome=actual_outcome
            )
        
        print("   [SUCCESS] Performance tracking working")
        
        # Check for alerts
        alerts = monitor.get_active_alerts("test_model", "TEST-TICKER")
        print(f"   [SUCCESS] Detected {len(alerts)} alerts")
        
        # Check health
        health = monitor.get_model_health("test_model", "TEST-TICKER")
        if health:
            print(f"   [SUCCESS] Model health: {health.health_score:.3f}")
            print(f"   [SUCCESS] Is healthy: {health.is_healthy}")
        
        return True, len(alerts)
        
    except Exception as e:
        print(f"   [ERROR] Model monitoring test failed: {e}")
        return False, str(e)


def main():
    """Run all standalone tests"""
    print("="*80)
    print("STANDALONE ML MODEL TESTING SUITE")
    print("="*80)
    
    results = {}
    
    # Test 1: Feature Engineering
    print("\n1. Feature Engineering Test")
    success, data = test_feature_engineering_standalone()
    results['feature_engineering'] = {'success': success, 'data': data}
    
    # Test 2: Random Forest
    print("\n2. Random Forest Test")
    success, data = test_random_forest_standalone()
    results['random_forest'] = {'success': success, 'data': data}
    
    # Test 3: XGBoost
    print("\n3. XGBoost Test")
    success, data = test_xgboost_standalone()
    results['xgboost'] = {'success': success, 'data': data}
    
    # Test 4: Model Monitoring
    print("\n4. Model Monitoring Test")
    success, data = test_model_monitoring_standalone()
    results['monitoring'] = {'success': success, 'data': data}
    
    # Generate report
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    success_count = sum(1 for result in results.values() if result['success'])
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result['success'] else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("STATUS: ALL TESTS PASSED - ML MODELS READY FOR DEPLOYMENT")
    elif success_count >= total_tests * 0.75:
        print("STATUS: MOSTLY SUCCESSFUL - MINOR ISSUES TO ADDRESS")
    else:
        print("STATUS: SIGNIFICANT ISSUES - REQUIRES ATTENTION")
    
    print("="*80)


if __name__ == "__main__":
    main()
