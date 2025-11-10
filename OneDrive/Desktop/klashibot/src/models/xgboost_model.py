"""
Advanced XGBoost Model for Kalshi Trading Bot

This module provides a sophisticated XGBoost implementation with
early stopping, probability calibration, and advanced hyperparameter tuning.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import structlog
from dataclasses import dataclass
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
import joblib
import json

logger = structlog.get_logger(__name__)


@dataclass
class XGBoostConfig:
    """Configuration for XGBoost model"""
    n_estimators: int = 100
    learning_rate: float = 0.1
    max_depth: int = 6
    min_child_weight: int = 3
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    colsample_bylevel: float = 0.8
    reg_alpha: float = 0.0
    reg_lambda: float = 1.0
    gamma: float = 0.0
    objective: str = 'binary:logistic'
    eval_metric: str = 'logloss'
    early_stopping_rounds: int = 10
    random_state: int = 42
    n_jobs: int = -1


@dataclass
class XGBoostTrainingResult:
    """Result of XGBoost training with early stopping"""
    best_iteration: int
    best_score: float
    training_history: Dict[str, List[float]]
    feature_importance: Dict[str, float]
    training_time: float


class AdvancedXGBoostPredictor:
    """
    Advanced XGBoost model with early stopping, probability calibration, and hyperparameter tuning
    """
    
    def __init__(self, config: Optional[XGBoostConfig] = None):
        self.config = config or XGBoostConfig()
        self.model = None
        self.calibrated_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.feature_importance = {}
        self.is_trained = False
        self.last_trained = None
        self.training_history = []
        self.best_iteration = 0
        self.training_result = None
        
        # Initialize base model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the XGBoost model with default parameters"""
        self.model = xgb.XGBClassifier(
            n_estimators=self.config.n_estimators,
            learning_rate=self.config.learning_rate,
            max_depth=self.config.max_depth,
            min_child_weight=self.config.min_child_weight,
            subsample=self.config.subsample,
            colsample_bytree=self.config.colsample_bytree,
            colsample_bylevel=self.config.colsample_bylevel,
            reg_alpha=self.config.reg_alpha,
            reg_lambda=self.config.reg_lambda,
            gamma=self.config.gamma,
            objective=self.config.objective,
            eval_metric=self.config.eval_metric,
            random_state=self.config.random_state,
            n_jobs=self.config.n_jobs,
            verbosity=0  # Suppress XGBoost output
        )
    
    def prepare_features(self, features_df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare features for model training/prediction
        
        Args:
            features_df: DataFrame containing feature data
            
        Returns:
            Tuple of (feature_matrix, feature_names)
        """
        if features_df.empty:
            return np.array([]), []
        
        # Extract features from JSON column
        feature_data = []
        feature_names = []
        
        for _, row in features_df.iterrows():
            if isinstance(row['features'], dict):
                feature_dict = row['features']
            else:
                feature_dict = json.loads(row['features']) if isinstance(row['features'], str) else {}
            
            feature_data.append(feature_dict)
            
            # Collect feature names
            for key in feature_dict.keys():
                if key not in feature_names:
                    feature_names.append(key)
        
        # Create feature matrix
        feature_matrix = []
        for feature_dict in feature_data:
            row = []
            for name in feature_names:
                row.append(feature_dict.get(name, 0.0))
            feature_matrix.append(row)
        
        return np.array(feature_matrix), feature_names
    
    def prepare_targets(self, outcomes_df: pd.DataFrame) -> np.ndarray:
        """
        Prepare target values for training
        
        Args:
            outcomes_df: DataFrame containing outcome data
            
        Returns:
            Array of target values
        """
        if outcomes_df.empty:
            return np.array([])
        
        return outcomes_df['outcome'].values
    
    def perform_hyperparameter_search(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """
        Perform hyperparameter search using XGBoost's built-in CV
        
        Args:
            X: Feature matrix
            y: Target values
            
        Returns:
            Dictionary with best parameters and CV results
        """
        logger.info("Starting XGBoost hyperparameter search")
        
        # Define parameter grid for XGBoost
        param_grid = {
            'n_estimators': [50, 100, 200],
            'learning_rate': [0.01, 0.1, 0.2],
            'max_depth': [3, 6, 9],
            'min_child_weight': [1, 3, 5],
            'subsample': [0.8, 0.9, 1.0],
            'colsample_bytree': [0.8, 0.9, 1.0],
            'reg_alpha': [0, 0.1, 1],
            'reg_lambda': [1, 1.5, 2]
        }
        
        # Use XGBoost's built-in CV for hyperparameter tuning
        best_score = float('inf')
        best_params = None
        cv_results = []
        
        # Sample parameter combinations (simplified grid search)
        import itertools
        param_combinations = list(itertools.product(*param_grid.values()))
        
        # Limit to 20 combinations for efficiency
        if len(param_combinations) > 20:
            import random
            param_combinations = random.sample(param_combinations, 20)
        
        for params in param_combinations:
            param_dict = dict(zip(param_grid.keys(), params))
            
            # Create model with current parameters
            temp_model = xgb.XGBClassifier(
                **param_dict,
                objective=self.config.objective,
                eval_metric=self.config.eval_metric,
                random_state=self.config.random_state,
                verbosity=0
            )
            
            # Use TimeSeriesSplit for time series data
            tscv = TimeSeriesSplit(n_splits=3)
            scores = []
            
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                
                # Train with early stopping
                temp_model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    early_stopping_rounds=self.config.early_stopping_rounds,
                    verbose=False
                )
                
                # Get validation score
                y_pred_proba = temp_model.predict_proba(X_val)[:, 1]
                score = brier_score_loss(y_val, y_pred_proba)
                scores.append(score)
            
            avg_score = np.mean(scores)
            cv_results.append({
                'params': param_dict,
                'score': avg_score,
                'std': np.std(scores)
            })
            
            if avg_score < best_score:
                best_score = avg_score
                best_params = param_dict
        
        logger.info("Hyperparameter search completed", 
                   best_score=best_score,
                   best_params=best_params)
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'cv_results': cv_results
        }
    
    def train(self, features_df: pd.DataFrame, outcomes_df: pd.DataFrame, 
              perform_hyperparameter_search: bool = False) -> Dict[str, Any]:
        """
        Train the XGBoost model with early stopping and optional hyperparameter tuning
        
        Args:
            features_df: DataFrame containing feature data
            outcomes_df: DataFrame containing outcome data
            perform_hyperparameter_search: Whether to perform hyperparameter search
            
        Returns:
            Dictionary containing training results and performance metrics
        """
        logger.info("Training XGBoost model")
        
        # Prepare data
        X, feature_names = self.prepare_features(features_df)
        y = self.prepare_targets(outcomes_df)
        
        if len(X) == 0 or len(y) == 0:
            logger.warning("No training data available")
            return {'error': 'No training data available'}
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Perform hyperparameter search if requested
        hyperparameter_results = None
        if perform_hyperparameter_search and len(X) >= 100:  # Need sufficient data
            hyperparameter_results = self.perform_hyperparameter_search(X_scaled, y)
            
            # Update model with best parameters
            self.model = xgb.XGBClassifier(
                **hyperparameter_results['best_params'],
                objective=self.config.objective,
                eval_metric=self.config.eval_metric,
                random_state=self.config.random_state,
                n_jobs=self.config.n_jobs,
                verbosity=0
            )
        else:
            logger.info("Skipping hyperparameter search", 
                       reason="Not requested or insufficient data" if len(X) < 100 else "Not requested")
        
        # Split data for early stopping
        split_idx = int(0.8 * len(X_scaled))
        X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Train model with early stopping
        start_time = datetime.now()
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Get best iteration and training history
        self.best_iteration = getattr(self.model, 'best_iteration', self.config.n_estimators)
        training_history = {
            'train_logloss': getattr(self.model, 'evals_result_', {}).get('validation_0', {}).get('logloss', []),
            'val_logloss': getattr(self.model, 'evals_result_', {}).get('validation_0', {}).get('logloss', [])
        }
        
        # Calibrate probabilities
        self.calibrated_model = CalibratedClassifierCV(self.model, method='isotonic', cv=3)
        self.calibrated_model.fit(X_scaled, y)
        
        # Store training information
        self.feature_names = feature_names
        self.is_trained = True
        self.last_trained = datetime.now()
        
        # Calculate feature importance
        self.feature_importance = dict(zip(feature_names, self.model.feature_importances_))
        
        # Evaluate model
        y_pred = self.model.predict(X_scaled)
        y_pred_proba = self.calibrated_model.predict_proba(X_scaled)[:, 1]
        
        # Calculate performance metrics
        performance_metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y, y_pred, average='weighted', zero_division=0),
            'roc_auc': roc_auc_score(y, y_pred_proba) if len(np.unique(y)) > 1 else 0.5,
            'brier_score': brier_score_loss(y, y_pred_proba),
            'training_time': training_time,
            'best_iteration': self.best_iteration,
            'n_features': len(feature_names),
            'n_samples': len(X)
        }
        
        # Store training result
        self.training_result = XGBoostTrainingResult(
            best_iteration=self.best_iteration,
            best_score=performance_metrics['brier_score'],
            training_history=training_history,
            feature_importance=self.feature_importance,
            training_time=training_time
        )
        
        # Store training history
        training_record = {
            'timestamp': self.last_trained,
            'performance': performance_metrics,
            'hyperparameter_results': hyperparameter_results,
            'training_result': self.training_result
        }
        self.training_history.append(training_record)
        
        logger.info("XGBoost training completed", 
                   accuracy=performance_metrics['accuracy'],
                   roc_auc=performance_metrics['roc_auc'],
                   brier_score=performance_metrics['brier_score'],
                   best_iteration=self.best_iteration,
                   n_features=len(feature_names),
                   training_time=training_time)
        
        return {
            'performance_metrics': performance_metrics,
            'feature_importance': self.feature_importance,
            'hyperparameter_results': hyperparameter_results,
            'training_result': self.training_result,
            'training_history': training_record
        }
    
    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Make prediction using trained XGBoost model with calibrated probabilities
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Tuple of (probability, confidence)
        """
        if not self.is_trained:
            logger.warning("Model not trained, returning default prediction")
            return 0.5, 0.0
        
        # Prepare feature vector
        feature_vector = []
        for name in self.feature_names:
            feature_vector.append(features.get(name, 0.0))
        
        X = np.array(feature_vector).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # Get calibrated probability prediction
        probabilities = self.calibrated_model.predict_proba(X_scaled)[0]
        model_prob = probabilities[1] if len(probabilities) > 1 else probabilities[0]
        
        # Calculate confidence based on prediction certainty and feature importance
        base_confidence = abs(model_prob - 0.5) * 2
        feature_confidence = self._calculate_feature_confidence(features)
        
        # Combine confidences with emphasis on calibrated probability
        combined_confidence = (base_confidence * 0.7 + feature_confidence * 0.3)
        
        return model_prob, combined_confidence
    
    def _calculate_feature_confidence(self, features: Dict[str, float]) -> float:
        """
        Calculate confidence based on feature importance and values
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Confidence score between 0 and 1
        """
        if not self.feature_importance:
            return 0.5
        
        # Calculate weighted feature confidence
        total_weight = 0
        weighted_confidence = 0
        
        for feature_name, importance in self.feature_importance.items():
            if feature_name in features:
                weight = importance
                # Features closer to 0 (normalized) are more confident
                # This is a simplified approach - in practice, you'd use historical distributions
                feature_value = abs(features[feature_name])
                confidence = max(0, 1 - feature_value / 5.0)  # Normalize to 0-1
                weighted_confidence += weight * confidence
                total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.5
    
    def get_feature_importance_analysis(self) -> Dict[str, Any]:
        """
        Get detailed feature importance analysis
        
        Returns:
            Dictionary containing feature importance analysis
        """
        if not self.feature_importance:
            return {'error': 'Model not trained or no feature importance available'}
        
        # Sort features by importance
        sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        # Categorize features by type
        feature_categories = {
            'momentum': [],
            'volume': [],
            'microstructure': [],
            'temporal': [],
            'technical': [],
            'cross_market': [],
            'other': []
        }
        
        for feature_name, importance in sorted_features:
            if 'momentum' in feature_name.lower():
                feature_categories['momentum'].append((feature_name, importance))
            elif 'volume' in feature_name.lower():
                feature_categories['volume'].append((feature_name, importance))
            elif any(x in feature_name.lower() for x in ['spread', 'imbalance', 'depth', 'liquidity']):
                feature_categories['microstructure'].append((feature_name, importance))
            elif any(x in feature_name.lower() for x in ['hour', 'day', 'time', 'weekend']):
                feature_categories['temporal'].append((feature_name, importance))
            elif any(x in feature_name.lower() for x in ['rsi', 'bollinger', 'ma', 'vwap', 'obv']):
                feature_categories['technical'].append((feature_name, importance))
            elif any(x in feature_name.lower() for x in ['correlation', 'sector', 'cross']):
                feature_categories['cross_market'].append((feature_name, importance))
            else:
                feature_categories['other'].append((feature_name, importance))
        
        # Calculate category importance
        category_importance = {}
        for category, features in feature_categories.items():
            if features:
                category_importance[category] = sum(importance for _, importance in features)
        
        return {
            'top_features': sorted_features[:15],  # XGBoost typically has more important features
            'feature_categories': feature_categories,
            'category_importance': category_importance,
            'total_features': len(self.feature_importance),
            'importance_stats': {
                'mean': np.mean(list(self.feature_importance.values())),
                'std': np.std(list(self.feature_importance.values())),
                'max': max(self.feature_importance.values()),
                'min': min(self.feature_importance.values())
            },
            'best_iteration': self.best_iteration
        }
    
    def get_training_curves(self) -> Dict[str, List[float]]:
        """
        Get training curves for visualization
        
        Returns:
            Dictionary containing training and validation curves
        """
        if not self.training_result:
            return {'error': 'No training result available'}
        
        return self.training_result.training_history
    
    def save_model(self, filepath: str):
        """
        Save trained model to file
        
        Args:
            filepath: Path to save the model
        """
        model_data = {
            'model': self.model,
            'calibrated_model': self.calibrated_model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'is_trained': self.is_trained,
            'last_trained': self.last_trained,
            'training_history': self.training_history,
            'training_result': self.training_result,
            'best_iteration': self.best_iteration,
            'config': self.config
        }
        joblib.dump(model_data, filepath)
        logger.info("XGBoost model saved", filepath=filepath)
    
    def load_model(self, filepath: str):
        """
        Load trained model from file
        
        Args:
            filepath: Path to load the model from
        """
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.calibrated_model = model_data['calibrated_model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.feature_importance = model_data['feature_importance']
        self.is_trained = model_data['is_trained']
        self.last_trained = model_data['last_trained']
        self.training_history = model_data.get('training_history', [])
        self.training_result = model_data.get('training_result')
        self.best_iteration = model_data.get('best_iteration', 0)
        self.config = model_data.get('config', XGBoostConfig())
        logger.info("XGBoost model loaded", filepath=filepath)
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive model summary
        
        Returns:
            Dictionary containing model summary information
        """
        if not self.is_trained:
            return {'error': 'Model not trained'}
        
        return {
            'model_type': 'XGBoost',
            'is_trained': self.is_trained,
            'last_trained': self.last_trained,
            'n_features': len(self.feature_names),
            'n_training_samples': len(self.training_history[-1]['performance']) if self.training_history else 0,
            'feature_importance_analysis': self.get_feature_importance_analysis(),
            'training_result': self.training_result,
            'training_history': self.training_history,
            'config': self.config,
            'best_iteration': self.best_iteration
        }
