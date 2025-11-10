"""
Vulture whitelist for ARBYS project.

This file contains symbols that vulture incorrectly flags as unused due to:
- Dynamic method calls (PyQt signals/slots, string-based lookups)
- Test-only usage (not detected by static analysis)
- Framework integration (Qt properties, paintEvent, etc.)
- Abstract interface methods required by base classes
- Staged/future features kept intentionally

Usage: vulture . .vulture_whitelist.py --min-confidence 80
"""

# Whitelist set exported for vulture tool
whitelist = {
    # GUI methods called dynamically via PyQt signals
    "open_setup_wizard",  # Called via signal in onboarding/wiring_example.py
    # Qt framework methods (called automatically by framework)
    "paintEvent",  # Called by PyQt6 when widget needs repainting
    "displayValue",  # Qt property used by QPropertyAnimation
    # Classes used in tests (not detected by static analysis)
    "SportradarAPIProvider",  # Used in tests/conftest.py, disabled in prod
    "TheOddsAPIProvider",  # Used in tests/conftest.py, disabled in prod
    "AsyncMultiAPIOrchestrator",  # Used in test_performance.py, test_concurrency.py
    "EnhancedMultiAPIOrchestrator",  # Used in tests and documentation
    "OptimizedArbitrageDetector",  # Used in tests/conftest.py, test_regression.py
    "HistoricalDataStorage",  # Used in tests and documentation
    # Utility functions used in tests
    "get_env_variable",  # Used in tests/unit/test_utils.py
    "format_percentage",  # Used in tests/unit/test_utils.py
    "calculate_time_until_event",  # Used in tests/unit/test_utils.py
    # Stake calculator methods used in tests
    "vary_stakes",  # Used in tests/unit/test_stake_calculator.py
    "optimize_stakes_for_bankroll",  # Used in tests/unit/test_stake_calculator.py
    # Test connection methods (public API, used in examples)
    "test_connection",  # Used in examples/scraper_usage_example.py
    # Abstract base class methods (interface requirements)
    "scrape_odds",  # Abstract method in base_scraper.py
    "_normalize_odds_format",  # Protected method, may be used by subclasses
    "get_team_metadata",  # Abstract method in metadata_providers/base.py
    "get_upcoming_matches",  # Abstract method in metadata_providers/base.py
    # Alternative orchestrator methods (future features)
    "find_best_arbitrages_batch",  # Public API method in OptimizedArbitrageDetector
    "fetch_odds_with_analysis",  # Enhanced orchestrator method
    "get_latency_arbitrage_opportunity",  # Enhanced orchestrator method
    # Account manager attributes (row_factory pattern)
    "row_factory",  # Used in database row factory pattern
    # Injury signal attribute
    "injury_cache_ttl",  # Configuration attribute in injury_signal.py
}
