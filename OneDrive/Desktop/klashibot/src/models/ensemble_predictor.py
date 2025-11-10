"""
Advanced Ensemble Predictor for Kalshi Trading Bot

This module provides a sophisticated ensemble system that combines multiple ML models
with dynamic weight adjustment based on recent performance and market conditions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
from collections import deque
import json
import joblib

# Import LogisticRegressionPredictor directly to avoid circular imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from models import LogisticRegressionPredictor
from .random_forest_model import AdvancedRandomForestPredictor
from .xgboost_model import AdvancedXGBoostPredictor
from ..data_manager import DataManager, FeatureData
from ..config import config

logger = structlog.get_logger(__name__)


@dataclass
class EnsembleConfig:
    """Configuration for ensemble predictor"""
    # Initial model weights
    initial_weights: Dict[str, float] = None
    
    # Dynamic weight adjustment parameters
    performance_window: int = 50  # Number of predictions to consider for weight adjustment
    min_weight: float = 0.1  # Minimum weight for any model
    max_weight: float = 0.6  # Maximum weight for any model
    weight_adjustment_rate: float = 0.1  # How quickly weights adjust
    
    # Ensemble methods
    use_dynamic_weights: bool = True
    use_confidence_weighting: bool = True
    use_market_regime_weighting: bool = True
    
    # Performance tracking
    track_individual_performance: bool = True
    retrain_threshold: float = 0.05  # Retrain if performance drops by this amount
    
    def __post_init__(self):
        if self.initial_weights is None:
            self.initial_weights = {
                'logistic': 0.25,
                'random_forest': 0.35,
                'xgboost': 0.40
            }


@dataclass
class PredictionRecord:
    """Record of a prediction and its outcome"""
    timestamp: datetime
    ticker: str
    model_predictions: Dict[str, Tuple[float, float]]  # model_name -> (prob, confidence)
    ensemble_prediction: Tuple[float, float]
    actual_outcome: Optional[int] = None
    market_regime: str = "normal"


@dataclass
class ModelPerformance:
    """Performance metrics for a single model"""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    brier_score: float
    recent_accuracy: float
    prediction_count: int
    last_updated: datetime


class AdvancedEnsemblePredictor:
    """
    Advanced ensemble predictor with dynamic weight adjustment and performance tracking
    """
    
    def __init__(self, config: Optional[EnsembleConfig] = None):
        self.config = config or EnsembleConfig()
        
        # Initialize individual models
        self.models = {
            'logistic': LogisticRegressionPredictor(),
            'random_forest': AdvancedRandomForestPredictor(),
            'xgboost': AdvancedXGBoostPredictor()
        }
        
        # Ensemble state
        self.model_weights = self.config.initial_weights.copy()
        self.prediction_history = deque(maxlen=self.config.performance_window * 2)
        self.model_performances: Dict[str, ModelPerformance] = {}
        self.market_regime = "normal"
        self.is_trained = False
        self.last_trained = None
        
        # Performance tracking
        self.ensemble_performance_history = []
        self.weight_adjustment_history = []
        
        logger.info("Advanced ensemble predictor initialized", 
                   initial_weights=self.model_weights)
    
    def train_all_models(self, data_manager: DataManager, ticker: str, 
                        perform_hyperparameter_search: bool = False) -> Dict[str, Any]:
        """
        Train all models in the ensemble
        
        Args:
            data_manager: Data manager for accessing training data
            ticker: Market ticker to train models for
            perform_hyperparameter_search: Whether to perform hyperparameter search
            
        Returns:
            Dictionary containing training results for all models
        """
        logger.info("Training ensemble models", ticker=ticker)
        
        # Get training data
        features_df, outcomes_df = data_manager.get_training_data(ticker)
        
        if features_df.empty or outcomes_df.empty:
            logger.warning("No training data available", ticker=ticker)
            return {'error': 'No training data available'}
        
        training_results = {}
        
        # Train each model
        for model_name, model in self.models.items():
            try:
                logger.info("Training model", model_name=model_name, ticker=ticker)
                
                if model_name == 'logistic':
                    # Logistic regression doesn't need hyperparameter search
                    result = model.train(features_df, outcomes_df)
                else:
                    # Advanced models can use hyperparameter search
                    result = model.train(features_df, outcomes_df, perform_hyperparameter_search)
                
                training_results[model_name] = result
                
                # Save individual model
                model.save_model(f"models/{ticker}_{model_name}.joblib")
                
                logger.info("Model training completed", 
                           model_name=model_name, 
                           ticker=ticker,
                           accuracy=result.get('performance_metrics', {}).get('accuracy', 0))
                
            except Exception as e:
                logger.error("Failed to train model", 
                           model_name=model_name, 
                           ticker=ticker, 
                           error=str(e))
                training_results[model_name] = {'error': str(e)}
        
        # Initialize model performances
        self._initialize_model_performances(training_results)
        
        # Mark ensemble as trained
        self.is_trained = all(model.is_trained for model in self.models.values())
        self.last_trained = datetime.now()
        
        logger.info("Ensemble training completed", 
                   ticker=ticker,
                   models_trained=sum(1 for r in training_results.values() if 'error' not in r),
                   ensemble_trained=self.is_trained)
        
        return training_results
    
    def _initialize_model_performances(self, training_results: Dict[str, Any]):
        """Initialize model performance tracking"""
        for model_name, result in training_results.items():
            if 'error' not in result and 'performance_metrics' in result:
                metrics = result['performance_metrics']
                self.model_performances[model_name] = ModelPerformance(
                    model_name=model_name,
                    accuracy=metrics.get('accuracy', 0),
                    precision=metrics.get('precision', 0),
                    recall=metrics.get('recall', 0),
                    f1_score=metrics.get('f1_score', 0),
                    roc_auc=metrics.get('roc_auc', 0),
                    brier_score=metrics.get('brier_score', 0),
                    recent_accuracy=metrics.get('accuracy', 0),
                    prediction_count=0,
                    last_updated=datetime.now()
                )
    
    def load_models(self, ticker: str):
        """Load all trained models for a ticker"""
        for model_name, model in self.models.items():
            try:
                model.load_model(f"models/{ticker}_{model_name}.joblib")
                logger.info("Model loaded", model_name=model_name, ticker=ticker)
            except FileNotFoundError:
                logger.warning("Model file not found", 
                             model_name=model_name, 
                             ticker=ticker)
    
    def predict_ensemble(self, features: Dict[str, float], ticker: str) -> Tuple[float, float]:
        """
        Generate ensemble prediction using dynamic weighting
        
        Args:
            features: Dictionary of feature values
            ticker: Market ticker
            
        Returns:
            Tuple of (ensemble_probability, ensemble_confidence)
        """
        if not self.is_trained:
            logger.warning("Ensemble not trained, returning default prediction")
            return 0.5, 0.0
        
        # Get predictions from all models
        model_predictions = {}
        model_confidences = {}
        
        for model_name, model in self.models.items():
            if model.is_trained:
                try:
                    prob, conf = model.predict(features)
                    model_predictions[model_name] = prob
                    model_confidences[model_name] = conf
                except Exception as e:
                    logger.error("Model prediction failed", 
                               model_name=model_name, 
                               error=str(e))
                    # Use default prediction for failed models
                    model_predictions[model_name] = 0.5
                    model_confidences[model_name] = 0.0
        
        if not model_predictions:
            logger.warning("No model predictions available")
            return 0.5, 0.0
        
        # Calculate ensemble weights
        ensemble_weights = self._calculate_ensemble_weights(model_confidences)
        
        # Generate ensemble prediction
        ensemble_prob = np.average(
            list(model_predictions.values()), 
            weights=list(ensemble_weights.values())
        )
        
        # Calculate ensemble confidence
        ensemble_conf = self._calculate_ensemble_confidence(
            model_predictions, model_confidences, ensemble_weights
        )
        
        # Record prediction for performance tracking
        prediction_record = PredictionRecord(
            timestamp=datetime.now(),
            ticker=ticker,
            model_predictions={name: (model_predictions[name], model_confidences[name]) 
                             for name in model_predictions.keys()},
            ensemble_prediction=(ensemble_prob, ensemble_conf),
            market_regime=self.market_regime
        )
        self.prediction_history.append(prediction_record)
        
        logger.debug("Ensemble prediction generated", 
                    ticker=ticker,
                    ensemble_prob=ensemble_prob,
                    ensemble_conf=ensemble_conf,
                    weights=ensemble_weights)
        
        return ensemble_prob, ensemble_conf
    
    def _calculate_ensemble_weights(self, model_confidences: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate dynamic ensemble weights based on recent performance and confidence
        
        Args:
            model_confidences: Dictionary of model confidence scores
            
        Returns:
            Dictionary of ensemble weights
        """
        if not self.config.use_dynamic_weights:
            return self.model_weights.copy()
        
        # Start with base weights
        weights = self.model_weights.copy()
        
        # Adjust weights based on recent performance
        if self.config.track_individual_performance:
            weights = self._adjust_weights_by_performance(weights)
        
        # Adjust weights based on confidence
        if self.config.use_confidence_weighting:
            weights = self._adjust_weights_by_confidence(weights, model_confidences)
        
        # Adjust weights based on market regime
        if self.config.use_market_regime_weighting:
            weights = self._adjust_weights_by_market_regime(weights)
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {name: weight / total_weight for name, weight in weights.items()}
        
        # Apply min/max constraints
        weights = self._apply_weight_constraints(weights)
        
        # Record weight adjustment
        self.weight_adjustment_history.append({
            'timestamp': datetime.now(),
            'weights': weights.copy(),
            'reason': 'dynamic_adjustment'
        })
        
        return weights
    
    def _adjust_weights_by_performance(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Adjust weights based on recent model performance"""
        if len(self.prediction_history) < 10:  # Need minimum history
            return weights
        
        # Calculate recent performance for each model
        recent_performance = {}
        for model_name in weights.keys():
            recent_correct = 0
            recent_total = 0
            
            for record in list(self.prediction_history)[-self.config.performance_window:]:
                if record.actual_outcome is not None and model_name in record.model_predictions:
                    model_prob, _ = record.model_predictions[model_name]
                    predicted_outcome = 1 if model_prob > 0.5 else 0
                    if predicted_outcome == record.actual_outcome:
                        recent_correct += 1
                    recent_total += 1
            
            if recent_total > 0:
                recent_performance[model_name] = recent_correct / recent_total
            else:
                recent_performance[model_name] = 0.5
        
        # Adjust weights based on performance
        for model_name in weights.keys():
            performance = recent_performance.get(model_name, 0.5)
            # Models with better performance get higher weights
            performance_factor = 1 + (performance - 0.5) * self.config.weight_adjustment_rate
            weights[model_name] *= performance_factor
        
        return weights
    
    def _adjust_weights_by_confidence(self, weights: Dict[str, float], 
                                    model_confidences: Dict[str, float]) -> Dict[str, float]:
        """Adjust weights based on model confidence"""
        for model_name in weights.keys():
            if model_name in model_confidences:
                confidence = model_confidences[model_name]
                # Higher confidence models get slightly higher weights
                confidence_factor = 1 + (confidence - 0.5) * 0.1
                weights[model_name] *= confidence_factor
        
        return weights
    
    def _adjust_weights_by_market_regime(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Adjust weights based on current market regime"""
        # Different models may perform better in different market conditions
        if self.market_regime == "volatile":
            # XGBoost typically handles volatility better
            weights['xgboost'] *= 1.1
            weights['logistic'] *= 0.9
        elif self.market_regime == "trending":
            # Random Forest handles trends well
            weights['random_forest'] *= 1.1
        elif self.market_regime == "sideways":
            # Logistic regression handles mean reversion
            weights['logistic'] *= 1.1
        
        return weights
    
    def _apply_weight_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Apply minimum and maximum weight constraints"""
        for model_name in weights.keys():
            weights[model_name] = max(self.config.min_weight, 
                                    min(self.config.max_weight, weights[model_name]))
        return weights
    
    def _calculate_ensemble_confidence(self, model_predictions: Dict[str, float],
                                     model_confidences: Dict[str, float],
                                     ensemble_weights: Dict[str, float]) -> float:
        """
        Calculate ensemble confidence based on agreement and individual confidences
        
        Args:
            model_predictions: Dictionary of model predictions
            model_confidences: Dictionary of model confidences
            ensemble_weights: Dictionary of ensemble weights
            
        Returns:
            Ensemble confidence score
        """
        if not model_predictions:
            return 0.0
        
        # Weighted average of individual confidences
        weighted_confidence = np.average(
            list(model_confidences.values()),
            weights=list(ensemble_weights.values())
        )
        
        # Agreement factor (how much models agree)
        predictions = list(model_predictions.values())
        if len(predictions) > 1:
            prediction_std = np.std(predictions)
            agreement_factor = max(0, 1 - prediction_std * 2)  # Higher agreement = higher confidence
        else:
            agreement_factor = 1.0
        
        # Combine weighted confidence with agreement
        ensemble_confidence = weighted_confidence * agreement_factor
        
        return min(1.0, max(0.0, ensemble_confidence))
    
    def update_prediction_outcome(self, ticker: str, actual_outcome: int):
        """
        Update the most recent prediction with actual outcome for performance tracking
        
        Args:
            ticker: Market ticker
            actual_outcome: Actual market outcome (0 or 1)
        """
        if not self.prediction_history:
            return
        
        # Find the most recent prediction for this ticker
        for record in reversed(self.prediction_history):
            if record.ticker == ticker and record.actual_outcome is None:
                record.actual_outcome = actual_outcome
                break
        
        # Update model performances
        self._update_model_performances()
        
        # Check if retraining is needed
        if self._should_retrain():
            logger.warning("Model performance degradation detected, retraining recommended")
    
    def _update_model_performances(self):
        """Update individual model performance metrics"""
        if len(self.prediction_history) < 5:
            return
        
        # Calculate recent performance for each model
        for model_name in self.model_performances.keys():
            correct = 0
            total = 0
            
            for record in list(self.prediction_history)[-self.config.performance_window:]:
                if (record.actual_outcome is not None and 
                    model_name in record.model_predictions):
                    
                    model_prob, _ = record.model_predictions[model_name]
                    predicted_outcome = 1 if model_prob > 0.5 else 0
                    
                    if predicted_outcome == record.actual_outcome:
                        correct += 1
                    total += 1
            
            if total > 0:
                recent_accuracy = correct / total
                self.model_performances[model_name].recent_accuracy = recent_accuracy
                self.model_performances[model_name].prediction_count = total
                self.model_performances[model_name].last_updated = datetime.now()
    
    def _should_retrain(self) -> bool:
        """Check if models should be retrained based on performance degradation"""
        for model_name, performance in self.model_performances.items():
            if performance.prediction_count >= 20:  # Need sufficient recent data
                performance_drop = performance.accuracy - performance.recent_accuracy
                if performance_drop > self.config.retrain_threshold:
                    return True
        return False
    
    def get_ensemble_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive ensemble summary
        
        Returns:
            Dictionary containing ensemble summary information
        """
        return {
            'ensemble_trained': self.is_trained,
            'last_trained': self.last_trained,
            'current_weights': self.model_weights,
            'model_performances': {
                name: {
                    'accuracy': perf.accuracy,
                    'recent_accuracy': perf.recent_accuracy,
                    'prediction_count': perf.prediction_count,
                    'last_updated': perf.last_updated
                }
                for name, perf in self.model_performances.items()
            },
            'prediction_history_count': len(self.prediction_history),
            'market_regime': self.market_regime,
            'weight_adjustment_count': len(self.weight_adjustment_history),
            'should_retrain': self._should_retrain()
        }
    
    def save_ensemble(self, filepath: str):
        """
        Save ensemble state to file
        
        Args:
            filepath: Path to save the ensemble
        """
        ensemble_data = {
            'model_weights': self.model_weights,
            'prediction_history': list(self.prediction_history),
            'model_performances': self.model_performances,
            'market_regime': self.market_regime,
            'is_trained': self.is_trained,
            'last_trained': self.last_trained,
            'weight_adjustment_history': self.weight_adjustment_history,
            'config': self.config
        }
        joblib.dump(ensemble_data, filepath)
        logger.info("Ensemble saved", filepath=filepath)
    
    def load_ensemble(self, filepath: str):
        """
        Load ensemble state from file
        
        Args:
            filepath: Path to load the ensemble from
        """
        ensemble_data = joblib.load(filepath)
        self.model_weights = ensemble_data['model_weights']
        self.prediction_history = deque(ensemble_data['prediction_history'], 
                                      maxlen=self.config.performance_window * 2)
        self.model_performances = ensemble_data['model_performances']
        self.market_regime = ensemble_data['market_regime']
        self.is_trained = ensemble_data['is_trained']
        self.last_trained = ensemble_data['last_trained']
        self.weight_adjustment_history = ensemble_data['weight_adjustment_history']
        self.config = ensemble_data['config']
        logger.info("Ensemble loaded", filepath=filepath)
