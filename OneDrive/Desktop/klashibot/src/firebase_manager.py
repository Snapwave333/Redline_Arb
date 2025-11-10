"""
Firebase Manager for Kalshi Trading Bot

This module handles all Firebase Firestore operations for real-time data synchronization
between the Python bot and the React dashboard.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import os
import json
from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger(__name__)


class FirebaseManager:
    """Manages Firebase Firestore operations for the trading bot"""
    
    def __init__(self, app_id: str = "kalshi-trading-bot", user_id: str = "user-123", region: str = "us-central1"):
        self.app_id = app_id
        self.user_id = user_id
        self.region = region
        self.db = None
        self._initialized = False
        
        logger.info("Firebase manager initialized", app_id=app_id, user_id=user_id, region=region)
    
    def initialize(self, credentials_path: str = "config/firebase_service_account.json", database_id: str = "kalshi-trading"):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            try:
                app = firebase_admin.get_app()
                logger.info("Firebase already initialized, reusing existing app")
                self.db = firestore.client(database_id=database_id)
                self._initialized = True
                return
            except ValueError:
                # App doesn't exist yet, proceed with initialization
                pass
            
            if not os.path.exists(credentials_path):
                logger.warning("Firebase credentials not found, using default credentials")
                # Use default credentials (for development)
                cred = credentials.ApplicationDefault()
            else:
                cred = credentials.Certificate(credentials_path)
            
            # Initialize Firebase Admin
            firebase_admin.initialize_app(cred)
            self.db = firestore.client(database_id=database_id)
            self._initialized = True
            
            logger.info("Firebase initialized successfully", database_id=database_id, region=self.region)
            
        except Exception as e:
            logger.warning("Firebase initialization failed, running in offline mode", error=str(e))
            self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if Firebase is initialized"""
        return self._initialized
    
    def _ensure_initialized(self):
        """Ensure Firebase is initialized"""
        if not self._initialized:
            logger.warning("Firebase not initialized, skipping operation")
            return False
        return True
    
    def update_bot_state(self, state_data: Dict[str, Any]):
        """Update bot state in Firestore"""
        if not self._ensure_initialized():
            return
        
        try:
            doc_ref = (self.db.collection('artifacts')
                      .document(self.app_id)
                      .collection('users')
                      .document(self.user_id)
                      .collection('bot_status')
                      .document('main_state'))
            
            # Add timestamp
            state_data['lastUpdated'] = firestore.SERVER_TIMESTAMP
            
            doc_ref.set(state_data, merge=True)
            logger.debug("Bot state updated", state_data=state_data)
            
        except Exception as e:
            logger.error("Failed to update bot state", error=str(e))
    
    def update_position(self, position_id: str, position_data: Dict[str, Any]):
        """Update or create a position in Firestore"""
        if not self._ensure_initialized():
            return
        
        try:
            doc_ref = (self.db.collection('artifacts')
                      .document(self.app_id)
                      .collection('users')
                      .document(self.user_id)
                      .collection('positions')
                      .document(position_id))
            
            # Add timestamp
            position_data['lastUpdated'] = firestore.SERVER_TIMESTAMP
            
            doc_ref.set(position_data, merge=True)
            logger.debug("Position updated", position_id=position_id, position_data=position_data)
            
        except Exception as e:
            logger.error("Failed to update position", position_id=position_id, error=str(e))
    
    def add_performance_record(self, date: str, daily_pnl: float, cumulative_pnl: float):
        """Add daily performance record to Firestore"""
        if not self._ensure_initialized():
            return
        
        try:
            doc_ref = (self.db.collection('artifacts')
                      .document(self.app_id)
                      .collection('users')
                      .document(self.user_id)
                      .collection('performance_history')
                      .document(date))
            
            doc_ref.set({
                'date': date,
                'dailyPnl': daily_pnl,
                'cumulativePnl': cumulative_pnl,
                'lastUpdated': firestore.SERVER_TIMESTAMP
            })
            
            logger.debug("Performance record added", date=date, daily_pnl=daily_pnl, cumulative_pnl=cumulative_pnl)
            
        except Exception as e:
            logger.error("Failed to add performance record", date=date, error=str(e))
    
    def get_performance_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get performance history for the last N days"""
        if not self._ensure_initialized():
            return []
        
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            # Query performance history
            collection_ref = (self.db.collection('artifacts')
                            .document(self.app_id)
                            .collection('users')
                            .document(self.user_id)
                            .collection('performance_history'))
            
            # Get documents for the date range
            docs = collection_ref.where('date', '>=', start_date.strftime('%Y-%m-%d')).stream()
            
            performance_data = []
            for doc in docs:
                data = doc.to_dict()
                performance_data.append(data)
            
            # Sort by date
            performance_data.sort(key=lambda x: x.get('date', ''))
            
            logger.debug("Performance history retrieved", days=days, records=len(performance_data))
            return performance_data
            
        except Exception as e:
            logger.error("Failed to get performance history", error=str(e))
            return []
    
    def update_configuration(self, config_data: Dict[str, Any]) -> bool:
        """Update bot configuration using transaction"""
        if not self._ensure_initialized():
            return False
        
        try:
            doc_ref = (self.db.collection('artifacts')
                      .document(self.app_id)
                      .collection('users')
                      .document(self.user_id)
                      .collection('bot_status')
                      .document('main_state'))
            
            # Use transaction for atomic update
            @firestore.transactional
            def update_in_transaction(transaction):
                doc = doc_ref.get(transaction=transaction)
                if doc.exists:
                    current_data = doc.to_dict()
                    current_data.update(config_data)
                    current_data['lastUpdated'] = firestore.SERVER_TIMESTAMP
                    transaction.update(doc_ref, current_data)
                    return True
                return False
            
            transaction = self.db.transaction()
            success = update_in_transaction(transaction)
            
            if success:
                logger.info("Configuration updated successfully", config_data=config_data)
            else:
                logger.warning("Configuration update failed - document not found")
            
            return success
            
        except Exception as e:
            logger.error("Failed to update configuration", error=str(e))
            return False
    
    def get_bot_state(self) -> Optional[Dict[str, Any]]:
        """Get current bot state from Firestore"""
        if not self._ensure_initialized():
            return None
        
        try:
            doc_ref = (self.db.collection('artifacts')
                      .document(self.app_id)
                      .collection('users')
                      .document(self.user_id)
                      .collection('bot_status')
                      .document('main_state'))
            
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            logger.error("Failed to get bot state", error=str(e))
            return None
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions from Firestore"""
        if not self._ensure_initialized():
            return []
        
        try:
            collection_ref = (self.db.collection('artifacts')
                            .document(self.app_id)
                            .collection('users')
                            .document(self.user_id)
                            .collection('positions'))
            
            docs = collection_ref.stream()
            positions = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                positions.append(data)
            
            logger.debug("Positions retrieved", count=len(positions))
            return positions
            
        except Exception as e:
            logger.error("Failed to get positions", error=str(e))
            return []
    
    def delete_position(self, position_id: str) -> bool:
        """Delete a position from Firestore"""
        if not self._ensure_initialized():
            return False
        
        try:
            doc_ref = (self.db.collection('artifacts')
                      .document(self.app_id)
                      .collection('users')
                      .document(self.user_id)
                      .collection('positions')
                      .document(position_id))
            
            doc_ref.delete()
            logger.info("Position deleted", position_id=position_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete position", position_id=position_id, error=str(e))
            return False
    
    def get_bankroll_benchmark(self) -> float:
        """Retrieves the Bankroll Benchmark (start-of-day portfolio value)"""
        if not self._ensure_initialized():
            return 0.0
        
        try:
            doc_ref = (self.db.collection('artifacts')
                      .document(self.app_id)
                      .collection('users')
                      .document(self.user_id)
                      .collection('bot_metrics')
                      .document('trading_state'))
            
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                # Return the stored value, defaulting to 0.0 if field is missing
                return data.get('bankroll_benchmark', 0.0)
            
            logger.warning("No trading state document found in Firestore. Initializing benchmark to 0.0.")
            return 0.0
            
        except Exception as e:
            logger.error("Error retrieving bankroll benchmark from Firebase", error=str(e))
            return 0.0

    def set_bankroll_benchmark(self, new_value: float, transfer_amount: float):
        """Updates the Bankroll Benchmark after a daily transfer"""
        if not self._ensure_initialized():
            return
        
        try:
            doc_ref = (self.db.collection('artifacts')
                      .document(self.app_id)
                      .collection('users')
                      .document(self.user_id)
                      .collection('bot_metrics')
                      .document('trading_state'))
            
            data = {
                'bankroll_benchmark': new_value,
                'last_transfer_date': firestore.SERVER_TIMESTAMP,
                'last_transfer_amount': transfer_amount
            }
            # Set with merge=True to ensure we don't overwrite other metrics
            doc_ref.set(data, merge=True)
            logger.info("Bankroll benchmark updated", 
                        new_value=new_value, 
                        transfer_amount=transfer_amount)
                        
        except Exception as e:
            logger.error("Error setting bankroll benchmark in Firebase", error=str(e))

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old performance data"""
        if not self._ensure_initialized():
            return
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date()
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            collection_ref = (self.db.collection('artifacts')
                            .document(self.app_id)
                            .collection('users')
                            .document(self.user_id)
                            .collection('performance_history'))
            
            # Get old documents
            old_docs = collection_ref.where('date', '<', cutoff_str).stream()
            
            deleted_count = 0
            for doc in old_docs:
                doc.reference.delete()
                deleted_count += 1
            
            logger.info("Old data cleaned up", deleted_count=deleted_count, cutoff_date=cutoff_str)
            
        except Exception as e:
            logger.error("Failed to cleanup old data", error=str(e))
    
    def create_sample_data(self):
        """Create sample data for testing the dashboard"""
        if not self._ensure_initialized():
            logger.warning("Firebase not initialized, cannot create sample data")
            return
        
        try:
            # Create sample bot state
            sample_state = {
                'portfolioValue': 25.50,
                'dailyPnl': 2.30,
                'isRunning': True,
                'maxDailyLoss': 2.0,
                'maxPortfolioRisk': 0.1,
                'kellyFactor': 0.05,
                'currentExposure': 5.20
            }
            self.update_bot_state(sample_state)
            
            # Create sample positions
            sample_positions = [
                {
                    'marketId': 'TRUMP2024',
                    'status': 'Active',
                    'shares': 10,
                    'entryPrice': 0.45,
                    'currentPrice': 0.52,
                    'pnl': 0.70,
                    'entryTime': firestore.SERVER_TIMESTAMP,
                    'marketStatus': 'OPEN'
                },
                {
                    'marketId': 'BIDEN2024',
                    'status': 'Closed',
                    'shares': 5,
                    'entryPrice': 0.38,
                    'currentPrice': 0.42,
                    'pnl': 0.20,
                    'entryTime': firestore.SERVER_TIMESTAMP,
                    'closeTime': firestore.SERVER_TIMESTAMP,
                    'marketStatus': 'SETTLED'
                }
            ]
            
            for i, pos in enumerate(sample_positions):
                self.update_position(f"position_{i}", pos)
            
            # Create sample performance history
            base_date = datetime.now().date()
            cumulative_pnl = 0
            
            for i in range(7):
                date = base_date - timedelta(days=i)
                daily_pnl = 1.5 + (i * 0.2)  # Sample increasing PnL
                cumulative_pnl += daily_pnl
                
                self.add_performance_record(
                    date.strftime('%Y-%m-%d'),
                    daily_pnl,
                    cumulative_pnl
                )
            
            logger.info("Sample data created successfully")
            
        except Exception as e:
            logger.error("Failed to create sample data", error=str(e))
