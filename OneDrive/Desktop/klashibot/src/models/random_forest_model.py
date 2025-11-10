"""
Advanced Random Forest Model for Kalshi Trading Bot

This module provides a sophisticated Random Forest implementation with
hyperparameter tuning, feature importance tracking, and performance monitoring.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import structlog
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
import joblib
import json

logger = structlog.get_logger(__name__)


@dataclass
class RandomForestConfig:
    """Configuration for Random Forest model"""
    n_estimators: int = 100
    max_depth: int = 10
    min_samples_split: int = 20
    min_samples_leaf: int = 10
    max_features: str = 'sqrt'
    bootstrap: bool = True
    class_weight: str = 'balanced'
    random_state: int = 42
    n_jobs: int = -1


@dataclass
class HyperparameterSearchResult:
    """Result of hyperparameter search"""
    best_params: Dict[str, Any]
    best_score: float
    cv_results: Dict[str, Any]
    search_time: float


class AdvancedRandomForestPredictor:
    """
    Advanced Random Forest model with hyperparameter tuning and feature importance tracking
    """
    
    def __init__(self, config: Optional[RandomForestConfig] = None):
        self.config = config or RandomForestConfig()
        self.model = None
        self.calibrated_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.feature_importance = {}
        self.is_trained = False
        self.last_trained = None
        self.training_history = []
        self.hyperparameter_results = None
        
        # Initialize base model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Random Forest model with default parameters"""
        self.model = RandomForestClassifier(
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            min_samples_split=self.config.min_samples_split,
            min_samples_leaf=self.config.min_samples_leaf,
            max_features=self.config.max_features,
            bootstrap=self.config.bootstrap,
            class_weight=self.config.class_weight,
            random_state=self.config.random_state,
            n_jobs=self.config.n_jobs
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
    
    def perform_hyperparameter_search(self, X: np.ndarray, y: np.ndarray, 
                                    search_type: str = 'random') -> HyperparameterSearchResult:
        """
        Perform hyperparameter search using GridSearchCV or RandomizedSearchCV
        
        Args:
            X: Feature matrix
            y: Target values
            search_type: Type of search ('grid' or 'random')
            
        Returns:
            HyperparameterSearchResult with best parameters and scores
        """
        logger.info("Starting hyperparameter search", search_type=search_type)
        
        # Define parameter grid
        param_grid = {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [5, 10, 15, 20, None],
            'min_samples_split': [2, 5, 10, 20],
            'min_samples_leaf': [1, 2, 5, 10],
            'max_features': ['sqrt', 'log2', None],
            'bootstrap': [True, False],
            'class_weight': ['balanced', 'balanced_subsample', None]
        }
        
        # Use TimeSeriesSplit for time series data
        tscv = TimeSeriesSplit(n_splits=5)
        
        start_time = datetime.now()
        
        if search_type == 'grid':
            # Grid search (more thorough but slower)
            search = GridSearchCV(
                RandomForestClassifier(random_state=self.config.random_state),
                param_grid,
                cv=tscv,
                scoring='neg_log_loss',
                n_jobs=self.config.n_jobs,
                verbose=1
            )
        else:
            # Random search (faster, good for initial exploration)
            search = RandomizedSearchCV(
                RandomForestClassifier(random_state=self.config.random_state),
                param_grid,
                n_iter=50,  # Number of parameter combinations to try
                cv=tscv,
                scoring='neg_log_loss',
                n_jobs=self.config.n_jobs,
                verbose=1,
                random_state=self.config.random_state
            )
        
        # Perform search
        search.fit(X, y)
        
        search_time = (datetime.now() - start_time).total_seconds()
        
        result = HyperparameterSearchResult(
            best_params=search.best_params_,
            best_score=abs(search.best_score_),  # Convert negative log loss to positive
            cv_results={
                'mean_test_score': search.cv_results_['mean_test_score'].tolist(),
                'std_test_score': search.cv_results_['std_test_score'].tolist(),
                'params': search.cv_results_['params']
            },
            search_time=search_time
        )
        
        logger.info("Hyperparameter search completed", 
                   best_score=result.best_score,
                   search_time=search_time,
                   best_params=result.best_params)
        
        return result
    
    def train(self, features_df: pd.DataFrame, outcomes_df: pd.DataFrame, 
              perform_hyperparameter_search: bool = False) -> Dict[str, Any]:
        """
        Train the Random Forest model with optional hyperparameter tuning
        
        Args:
            features_df: DataFrame containing feature data
            outcomes_df: DataFrame containing outcome data
            perform_hyperparameter_search: Whether to perform hyperparameter search
            
        Returns:
            Dictionary containing training results and performance metrics
        """
        logger.info("Training Random Forest model")
        
        # Prepare data
        X, feature_names = self.prepare_features(features_df)
        y = self.prepare_targets(outcomes_df)
        
        if len(X) == 0 or len(y) == 0:
            logger.warning("No training data available")
            return {'error': 'No training data available'}
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Perform hyperparameter search if requested
        if perform_hyperparameter_search and len(X) >= 100:  # Need sufficient data
            self.hyperparameter_results = self.perform_hyperparameter_search(X_scaled, y)
            
            # Update model with best parameters
            self.model = RandomForestClassifier(
                **self.hyperparameter_results.best_params,
                random_state=self.config.random_state,
                n_jobs=self.config.n_jobs
            )
        else:
            logger.info("Skipping hyperparameter search", 
                       reason="Not requested or insufficient data" if len(X) < 100 else "Not requested")
        
        # Train model
        start_time = datetime.now()
        self.model.fit(X_scaled, y)
        training_time = (datetime.now() - start_time).total_seconds()
        
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
            'n_features': len(feature_names),
            'n_samples': len(X)
        }
        
        # Store training history
        training_record = {
            'timestamp': self.last_trained,
            'performance': performance_metrics,
            'hyperparameter_results': self.hyperparameter_results.best_params if self.hyperparameter_results else None
        }
        self.training_history.append(training_record)
        
        logger.info("Random Forest training completed", 
                   accuracy=performance_metrics['accuracy'],
                   roc_auc=performance_metrics['roc_auc'],
                   brier_score=performance_metrics['brier_score'],
                   n_features=len(feature_names),
                   training_time=training_time)
        
        return {
            'performance_metrics': performance_metrics,
            'feature_importance': self.feature_importance,
            'hyperparameter_results': self.hyperparameter_results,
            'training_history': training_record
        }
    
    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Make prediction using trained Random Forest model
        
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
        
        # Calculate confidence based on prediction certainty
        confidence = abs(model_prob - 0.5) * 2
        
        # Additional confidence based on feature importance alignment
        feature_confidence = self._calculate_feature_confidence(features)
        combined_confidence = (confidence + feature_confidence) / 2
        
        return model_prob, combined_confidence
    
    def _calculate_feature_confidence(self, features: Dict[str, float]) -> float:
        """
        Calculate confidence based on how well features align with importance
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Confidence score between 0 and 1
        """
        if not self.feature_importance:
            return 0.5
        
        # Calculate weighted feature alignment
        total_weight = 0
        weighted_alignment = 0
        
        for feature_name, importance in self.feature_importance.items():
            if feature_name in features:
                # Features with higher importance should have more influence
                weight = importance
                # Simple alignment: features closer to their mean are more confident
                # This is a simplified approach - in practice, you'd use historical means
                alignment = 1.0 - abs(features[feature_name]) / 10.0  # Normalize to 0-1
                weighted_alignment += weight * alignment
                total_weight += weight
        
        return weighted_alignment / total_weight if total_weight > 0 else 0.5
    
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
        
        # Categorize features
        feature_categories = {
            'momentum': [],
            'volume': [],
            'microstructure': [],
            'temporal': [],
            'technical': [],
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
            elif any(x in feature_name.lower() for x in ['rsi', 'bollinger', 'ma', 'vwap']):
                feature_categories['technical'].append((feature_name, importance))
            else:
                feature_categories['other'].append((feature_name, importance))
        
        # Calculate category importance
        category_importance = {}
        for category, features in feature_categories.items():
            if features:
                category_importance[category] = sum(importance for _, importance in features)
        
        return {
            'top_features': sorted_features[:10],
            'feature_categories': feature_categories,
            'category_importance': category_importance,
            'total_features': len(self.feature_importance),
            'importance_stats': {
                'mean': np.mean(list(self.feature_importance.values())),
                'std': np.std(list(self.feature_importance.values())),
                'max': max(self.feature_importance.values()),
                'min': min(self.feature_importance.values())
            }
        }
    
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
            'hyperparameter_results': self.hyperparameter_results,
            'config': self.config
        }
        joblib.dump(model_data, filepath)
        logger.info("Random Forest model saved", filepath=filepath)
    
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
        self.hyperparameter_results = model_data.get('hyperparameter_results')
        self.config = model_data.get('config', RandomForestConfig())
        logger.info("Random Forest model loaded", filepath=filepath)
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive model summary
        
        Returns:
            Dictionary containing model summary information
        """
        if not self.is_trained:
            return {'error': 'Model not trained'}
        
        return {
            'model_type': 'Random Forest',
            'is_trained': self.is_trained,
            'last_trained': self.last_trained,
            'n_features': len(self.feature_names),
            'n_training_samples': len(self.training_history[-1]['performance']) if self.training_history else 0,
            'feature_importance_analysis': self.get_feature_importance_analysis(),
            'hyperparameter_results': self.hyperparameter_results,
            'training_history': self.training_history,
            'config': self.config
        }
