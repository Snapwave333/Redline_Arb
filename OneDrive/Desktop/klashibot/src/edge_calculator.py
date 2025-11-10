"""
Edge Calculator Module

This module handles the calculation of trading edge (probability delta) and
optimal position sizing using the Kelly criterion with confidence adjustments.
"""

import structlog
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class EdgeResult:
    """Result of edge calculation"""
    edge: float
    implied_probability: float
    model_probability: float
    meets_threshold: bool
    recommended_position: int
    confidence_score: float
    market_quality_score: float


class EdgeCalculator:
    """Calculates trading edge and optimal position sizing"""
    
    def __init__(self, threshold_config):
        self.config = threshold_config
    
    def calculate_implied_probability(self, yes_price: float, no_price: float) -> float:
        """
        Calculate implied probability from market prices
        
        Args:
            yes_price: Best yes bid price (0-100)
            no_price: Best no bid price (0-100)
            
        Returns:
            Implied probability (0.0 to 1.0)
        """
        try:
            # Handle edge cases
            if yes_price <= 0 and no_price <= 0:
                return 0.5  # No market data, assume 50/50
            
            if yes_price <= 0:
                return 0.0  # No yes bids, market thinks it's impossible
            
            if no_price <= 0:
                return 1.0  # No no bids, market thinks it's certain
            
            # Calculate implied probability using market maker formula
            # Implied prob = yes_price / (yes_price + no_price)
            total_price = yes_price + no_price
            if total_price <= 0:
                return 0.5
            
            implied_prob = yes_price / total_price
            
            # Ensure probability is within bounds
            return max(0.0, min(1.0, implied_prob))
            
        except Exception as e:
            logger.warning("Error calculating implied probability", 
                         yes_price=yes_price, no_price=no_price, error=str(e))
            return 0.5
    
    def calculate_edge(self, model_probability: float, implied_probability: float) -> float:
        """
        Calculate trading edge (probability delta)
        
        Args:
            model_probability: Model's predicted probability (0.0 to 1.0)
            implied_probability: Market's implied probability (0.0 to 1.0)
            
        Returns:
            Edge value (positive = bullish edge, negative = bearish edge)
        """
        try:
            edge = model_probability - implied_probability
            logger.debug("Edge calculated", 
                        model_prob=model_probability, 
                        implied_prob=implied_probability, 
                        edge=edge)
            return edge
            
        except Exception as e:
            logger.error("Error calculating edge", error=str(e))
            return 0.0
    
    def meets_threshold(self, edge: float, confidence: float) -> bool:
        """
        Determine if edge meets trading threshold
        
        Args:
            edge: Calculated edge value
            confidence: Model confidence score
            
        Returns:
            True if edge meets threshold for trading
        """
        try:
            # Check minimum edge threshold
            min_edge = abs(edge) >= self.config.min_edge_threshold
            
            # Check minimum confidence threshold
            min_confidence = confidence >= self.config.min_model_confidence
            
            # Check if edge is within reasonable bounds
            reasonable_edge = abs(edge) <= self.config.max_edge_threshold
            
            meets_threshold = min_edge and min_confidence and reasonable_edge
            
            logger.debug("Threshold check", 
                        edge=edge, 
                        confidence=confidence,
                        min_edge=min_edge,
                        min_confidence=min_confidence,
                        reasonable_edge=reasonable_edge,
                        meets_threshold=meets_threshold)
            
            return meets_threshold
            
        except Exception as e:
            logger.error("Error checking threshold", error=str(e))
            return False
    
    def calculate_kelly_position(self, edge: float, balance: float, confidence: float) -> int:
        """
        Calculate optimal position size using Kelly criterion
        
        Args:
            edge: Trading edge (probability delta)
            balance: Available account balance
            confidence: Model confidence score
            
        Returns:
            Recommended position size in cents
        """
        try:
            # Base Kelly fraction from config
            base_kelly = self.config.base_kelly_fraction
            
            # Scale Kelly fraction based on edge magnitude
            edge_magnitude = abs(edge)
            kelly_scaling = min(edge_magnitude * self.config.kelly_scaling_factor, 1.0)
            
            # Apply confidence scaling
            confidence_scaling = min(confidence, 1.0)
            
            # Calculate final Kelly fraction
            kelly_fraction = base_kelly * kelly_scaling * confidence_scaling
            
            # Cap at maximum Kelly fraction
            kelly_fraction = min(kelly_fraction, self.config.max_kelly_fraction)
            
            # Calculate position size
            position_cents = int(balance * kelly_fraction * 100)  # Convert to cents
            
            # Ensure minimum position size
            min_position = 50  # $0.50 minimum
            position_cents = max(position_cents, min_position)
            
            logger.debug("Kelly position calculated", 
                        edge=edge,
                        balance=balance,
                        confidence=confidence,
                        kelly_fraction=kelly_fraction,
                        position_cents=position_cents)
            
            return position_cents
            
        except Exception as e:
            logger.error("Error calculating Kelly position", error=str(e))
            return 50  # Return minimum position on error
    
    def evaluate_market_quality(self, market_data: Dict[str, Any]) -> float:
        """
        Evaluate market quality for trading
        
        Args:
            market_data: Market data including prices, volume, etc.
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        try:
            quality_score = 1.0
            
            # Check liquidity (bid/ask prices)
            yes_bid = market_data.get('yes_bid', 0)
            no_bid = market_data.get('no_bid', 0)
            
            if yes_bid <= 0 or no_bid <= 0:
                quality_score *= 0.5  # Reduce quality if no bids
            
            # Check spread
            yes_ask = market_data.get('yes_ask', 0)
            no_ask = market_data.get('no_ask', 0)
            
            if yes_ask > 0 and yes_bid > 0:
                spread = yes_ask - yes_bid
                max_spread = self.config.max_spread_percent * 100  # Convert to cents
                if spread > max_spread:
                    quality_score *= 0.7  # Reduce quality for wide spreads
            
            # Check volume
            volume = market_data.get('volume', 0)
            if volume < self.config.min_volume:
                quality_score *= 0.8  # Reduce quality for low volume
            
            # Check liquidity in cents
            total_liquidity = yes_bid + no_bid
            if total_liquidity < self.config.min_liquidity_cents:
                quality_score *= 0.6  # Reduce quality for low liquidity
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.error("Error evaluating market quality", error=str(e))
            return 0.0
    
    def calculate_comprehensive_edge(self, 
                                   market_data: Dict[str, Any], 
                                   model_probability: float,
                                   model_confidence: float,
                                   account_balance: float) -> EdgeResult:
        """
        Calculate comprehensive edge analysis
        
        Args:
            market_data: Market data including prices
            model_probability: Model's predicted probability
            model_confidence: Model's confidence score
            account_balance: Available account balance
            
        Returns:
            EdgeResult with all calculations
        """
        try:
            # Extract market prices
            yes_price = market_data.get('yes_bid', 0)
            no_price = market_data.get('no_bid', 0)
            
            # Calculate implied probability
            implied_prob = self.calculate_implied_probability(yes_price, no_price)
            
            # Calculate edge
            edge = self.calculate_edge(model_probability, implied_prob)
            
            # Check if meets threshold
            meets_threshold = self.meets_threshold(edge, model_confidence)
            
            # Calculate recommended position
            recommended_position = self.calculate_kelly_position(edge, account_balance, model_confidence)
            
            # Evaluate market quality
            market_quality = self.evaluate_market_quality(market_data)
            
            # Apply market quality adjustment to position
            if market_quality < 0.7:
                recommended_position = int(recommended_position * market_quality)
            
            result = EdgeResult(
                edge=edge,
                implied_probability=implied_prob,
                model_probability=model_probability,
                meets_threshold=meets_threshold,
                recommended_position=recommended_position,
                confidence_score=model_confidence,
                market_quality_score=market_quality
            )
            
            logger.info("Comprehensive edge calculated", 
                       ticker=market_data.get('ticker', 'unknown'),
                       edge=edge,
                       implied_prob=implied_prob,
                       model_prob=model_probability,
                       meets_threshold=meets_threshold,
                       position=recommended_position,
                       market_quality=market_quality)
            
            return result
            
        except Exception as e:
            logger.error("Error in comprehensive edge calculation", error=str(e))
            # Return default result on error
            return EdgeResult(
                edge=0.0,
                implied_probability=0.5,
                model_probability=model_probability,
                meets_threshold=False,
                recommended_position=50,
                confidence_score=model_confidence,
                market_quality_score=0.0
            )
