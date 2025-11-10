"""
Machine Learning Model Framework for Kalshi Trading Bot

This module provides ML models for predicting market outcomes and calculating
probability deltas for trading decisions.
"""

import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

from .config import config
from .data_manager import DataManager, FeatureData

logger = structlog.get_logger(__name__)


@dataclass
class ModelPrediction:
    """Model prediction result"""
    ticker: str
    model_probability: float
    implied_probability: float
    probability_delta: float
    confidence: float
    features_used: List[str]
    timestamp: datetime


@dataclass
class ModelPerformance:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    cross_val_score: float
    feature_importance: Dict[str, float]


class ProbabilityPredictor:
    """Base class for probability prediction models"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.last_trained = None
    
    def prepare_features(self, features_df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Prepare features for model training/prediction"""
        if features_df.empty:
            return np.array([]), []
        
        # Extract features from JSON column
        feature_data = []
        feature_names = []
        
        for _, row in features_df.iterrows():
            if isinstance(row['features'], dict):
                feature_dict = row['features']
            else:
                feature_dict = eval(row['features']) if isinstance(row['features'], str) else {}
            
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
        """Prepare target values for training"""
        if outcomes_df.empty:
            return np.array([])
        
        return outcomes_df['outcome'].values
    
    def train(self, features_df: pd.DataFrame, outcomes_df: pd.DataFrame) -> ModelPerformance:
        """Train the model"""
        raise NotImplementedError("Subclasses must implement train method")
    
    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Make prediction for given features"""
        raise NotImplementedError("Subclasses must implement predict method")
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'last_trained': self.last_trained,
            'model_name': self.model_name
        }
        joblib.dump(model_data, filepath)
        logger.info("Model saved", model_name=self.model_name, filepath=filepath)
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
        self.last_trained = model_data['last_trained']
        logger.info("Model loaded", model_name=self.model_name, filepath=filepath)


class LogisticRegressionPredictor(ProbabilityPredictor):
    """Logistic Regression model for probability prediction"""
    
    def __init__(self):
        super().__init__("logistic_regression")
        self.model = LogisticRegression(random_state=42, max_iter=1000)
    
    def train(self, features_df: pd.DataFrame, outcomes_df: pd.DataFrame) -> ModelPerformance:
        """Train logistic regression model"""
        logger.info("Training logistic regression model")
        
        # Prepare data
        X, feature_names = self.prepare_features(features_df)
        y = self.prepare_targets(outcomes_df)
        
        if len(X) == 0 or len(y) == 0:
            logger.warning("No training data available")
            return ModelPerformance(0, 0, 0, 0, 0, {})
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.feature_names = feature_names
        self.is_trained = True
        self.last_trained = datetime.now()
        
        # Evaluate model
        y_pred = self.model.predict(X_scaled)
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, average='weighted')
        recall = recall_score(y, y_pred, average='weighted')
        f1 = f1_score(y, y_pred, average='weighted')
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
        cv_score = cv_scores.mean()
        
        # Feature importance
        feature_importance = dict(zip(feature_names, self.model.coef_[0]))
        
        performance = ModelPerformance(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            cross_val_score=cv_score,
            feature_importance=feature_importance
        )
        
        logger.info("Model training completed", 
                   accuracy=accuracy, 
                   cv_score=cv_score,
                   n_features=len(feature_names))
        
        return performance
    
    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Make prediction using logistic regression"""
        if not self.is_trained:
            logger.warning("Model not trained, returning default prediction")
            return 0.5, 0.0
        
        # Prepare feature vector
        feature_vector = []
        for name in self.feature_names:
            feature_vector.append(features.get(name, 0.0))
        
        X = np.array(feature_vector).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # Get probability prediction
        probabilities = self.model.predict_proba(X_scaled)[0]
        model_prob = probabilities[1] if len(probabilities) > 1 else probabilities[0]
        
        # Calculate confidence (distance from 0.5)
        confidence = abs(model_prob - 0.5) * 2
        
        return model_prob, confidence


class RandomForestPredictor(ProbabilityPredictor):
    """Random Forest model for probability prediction"""
    
    def __init__(self):
        super().__init__("random_forest")
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10,
            min_samples_split=5
        )
    
    def train(self, features_df: pd.DataFrame, outcomes_df: pd.DataFrame) -> ModelPerformance:
        """Train random forest model"""
        logger.info("Training random forest model")
        
        # Prepare data
        X, feature_names = self.prepare_features(features_df)
        y = self.prepare_targets(outcomes_df)
        
        if len(X) == 0 or len(y) == 0:
            logger.warning("No training data available")
            return ModelPerformance(0, 0, 0, 0, 0, {})
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.feature_names = feature_names
        self.is_trained = True
        self.last_trained = datetime.now()
        
        # Evaluate model
        y_pred = self.model.predict(X_scaled)
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, average='weighted')
        recall = recall_score(y, y_pred, average='weighted')
        f1 = f1_score(y, y_pred, average='weighted')
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
        cv_score = cv_scores.mean()
        
        # Feature importance
        feature_importance = dict(zip(feature_names, self.model.feature_importances_))
        
        performance = ModelPerformance(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            cross_val_score=cv_score,
            feature_importance=feature_importance
        )
        
        logger.info("Model training completed", 
                   accuracy=accuracy, 
                   cv_score=cv_score,
                   n_features=len(feature_names))
        
        return performance
    
    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Make prediction using random forest"""
        if not self.is_trained:
            logger.warning("Model not trained, returning default prediction")
            return 0.5, 0.0
        
        # Prepare feature vector
        feature_vector = []
        for name in self.feature_names:
            feature_vector.append(features.get(name, 0.0))
        
        X = np.array(feature_vector).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # Get probability prediction
        probabilities = self.model.predict_proba(X_scaled)[0]
        model_prob = probabilities[1] if len(probabilities) > 1 else probabilities[0]
        
        # Calculate confidence (distance from 0.5)
        confidence = abs(model_prob - 0.5) * 2
        
        return model_prob, confidence


class GradientBoostingPredictor(ProbabilityPredictor):
    """Gradient Boosting model for probability prediction"""
    
    def __init__(self):
        super().__init__("gradient_boosting")
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=6,
            learning_rate=0.1
        )
    
    def train(self, features_df: pd.DataFrame, outcomes_df: pd.DataFrame) -> ModelPerformance:
        """Train gradient boosting model"""
        logger.info("Training gradient boosting model")
        
        # Prepare data
        X, feature_names = self.prepare_features(features_df)
        y = self.prepare_targets(outcomes_df)
        
        if len(X) == 0 or len(y) == 0:
            logger.warning("No training data available")
            return ModelPerformance(0, 0, 0, 0, 0, {})
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.feature_names = feature_names
        self.is_trained = True
        self.last_trained = datetime.now()
        
        # Evaluate model
        y_pred = self.model.predict(X_scaled)
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, average='weighted')
        recall = recall_score(y, y_pred, average='weighted')
        f1 = f1_score(y, y_pred, average='weighted')
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
        cv_score = cv_scores.mean()
        
        # Feature importance
        feature_importance = dict(zip(feature_names, self.model.feature_importances_))
        
        performance = ModelPerformance(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            cross_val_score=cv_score,
            feature_importance=feature_importance
        )
        
        logger.info("Model training completed", 
                   accuracy=accuracy, 
                   cv_score=cv_score,
                   n_features=len(feature_names))
        
        return performance
    
    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Make prediction using gradient boosting"""
        if not self.is_trained:
            logger.warning("Model not trained, returning default prediction")
            return 0.5, 0.0
        
        # Prepare feature vector
        feature_vector = []
        for name in self.feature_names:
            feature_vector.append(features.get(name, 0.0))
        
        X = np.array(feature_vector).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # Get probability prediction
        probabilities = self.model.predict_proba(X_scaled)[0]
        model_prob = probabilities[1] if len(probabilities) > 1 else probabilities[0]
        
        # Calculate confidence (distance from 0.5)
        confidence = abs(model_prob - 0.5) * 2
        
        return model_prob, confidence


class EnsemblePredictor:
    """Ensemble predictor that combines multiple models"""
    
    def __init__(self):
        self.models = {
            'logistic': LogisticRegressionPredictor(),
            'random_forest': RandomForestPredictor(),
            'gradient_boosting': GradientBoostingPredictor()
        }
        self.model_weights = {
            'logistic': 0.3,
            'random_forest': 0.4,
            'gradient_boosting': 0.3
        }
    
    def train_all_models(self, data_manager: DataManager, ticker: str) -> Dict[str, ModelPerformance]:
        """Train all models for a specific ticker"""
        logger.info("Training ensemble models", ticker=ticker)
        
        # Get training data
        features_df, outcomes_df = data_manager.get_training_data(ticker)
        
        if features_df.empty or outcomes_df.empty:
            logger.warning("No training data available", ticker=ticker)
            return {}
        
        performances = {}
        
        for model_name, model in self.models.items():
            try:
                performance = model.train(features_df, outcomes_df)
                performances[model_name] = performance
                
                # Save model
                model.save_model(f"models/{ticker}_{model_name}.joblib")
                
            except Exception as e:
                logger.error("Failed to train model", 
                           model_name=model_name, 
                           ticker=ticker, 
                           error=str(e))
        
        return performances
    
    def load_models(self, ticker: str):
        """Load all trained models for a ticker"""
        for model_name, model in self.models.items():
            try:
                model.load_model(f"models/{ticker}_{model_name}.joblib")
            except FileNotFoundError:
                logger.warning("Model file not found", 
                             model_name=model_name, 
                             ticker=ticker)
    
    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Make ensemble prediction"""
        predictions = []
        confidences = []
        
        for model_name, model in self.models.items():
            if model.is_trained:
                prob, conf = model.predict(features)
                predictions.append(prob)
                confidences.append(conf)
        
        if not predictions:
            logger.warning("No trained models available for prediction")
            return 0.5, 0.0
        
        # Weighted average of predictions
        weighted_prob = np.average(predictions, weights=self.model_weights.values())
        weighted_conf = np.average(confidences, weights=self.model_weights.values())
        
        return weighted_prob, weighted_conf
    
    def should_retrain(self, ticker: str) -> bool:
        """Check if models should be retrained"""
        for model in self.models.values():
            if model.last_trained is None:
                return True
            
            time_since_training = datetime.now() - model.last_trained
            if time_since_training.total_seconds() > config.model.model_retrain_interval:
                return True
        
        return False


class ModelManager:
    """Manages ML models for all tickers"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.ensemble_predictors: Dict[str, EnsemblePredictor] = {}
        self.model_performances: Dict[str, Dict[str, ModelPerformance]] = {}
    
    def initialize_ticker(self, ticker: str):
        """Initialize models for a ticker"""
        if ticker not in self.ensemble_predictors:
            self.ensemble_predictors[ticker] = EnsemblePredictor()
            self.ensemble_predictors[ticker].load_models(ticker)
    
    def train_models(self, ticker: str) -> Dict[str, ModelPerformance]:
        """Train models for a ticker"""
        self.initialize_ticker(ticker)
        
        performances = self.ensemble_predictors[ticker].train_all_models(
            self.data_manager, ticker
        )
        
        self.model_performances[ticker] = performances
        return performances
    
    def predict_probability(self, ticker: str, features: Dict[str, float], 
                           implied_prob: float) -> ModelPrediction:
        """Make probability prediction for a ticker"""
        self.initialize_ticker(ticker)
        
        model_prob, confidence = self.ensemble_predictors[ticker].predict(features)
        probability_delta = model_prob - implied_prob
        
        return ModelPrediction(
            ticker=ticker,
            model_probability=model_prob,
            implied_probability=implied_prob,
            probability_delta=probability_delta,
            confidence=confidence,
            features_used=list(features.keys()),
            timestamp=datetime.now()
        )
    
    def should_retrain(self, ticker: str) -> bool:
        """Check if models should be retrained"""
        if ticker not in self.ensemble_predictors:
            return True
        
        return self.ensemble_predictors[ticker].should_retrain(ticker)
    
    def get_model_performance(self, ticker: str) -> Dict[str, ModelPerformance]:
        """Get model performance metrics"""
        return self.model_performances.get(ticker, {})
    
    def get_best_model(self, ticker: str) -> str:
        """Get the best performing model for a ticker"""
        performances = self.model_performances.get(ticker, {})
        
        if not performances:
            return "logistic"  # Default
        
        # Find model with highest cross-validation score
        best_model = max(performances.keys(), 
                        key=lambda x: performances[x].cross_val_score)
        
        return best_model
