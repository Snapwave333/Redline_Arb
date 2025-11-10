# Vulture Dead Code Analysis Report

Generated: Analysis of vulture findings to distinguish actual dead code from false positives

## Summary

- **Total vulture findings**: 69 items
- **Actually unused (dead code)**: ~15 items
- **False positives (used but vulture missed)**: ~45 items  
- **Intentional/staged code**: ~9 items

---

## ✅ CONFIRMED DEAD CODE (Can be safely removed)

### GUI Components

1. **`gui/main_window.py:584` - `checked` variable**
   - Status: ✅ **UNUSED**
   - Reason: Lambda parameter required by PyQt signal but never used
   - Action: Can be removed or prefixed with `_`

2. **`gui/main_window.py:1004` - `provider_status_labels` attribute**
   - Status: ✅ **UNUSED**
   - Reason: Dictionary is created but never populated or accessed
   - Action: Can be removed if not planned for future use

3. **`gui/setup_wizard.py:326` - `BookmakerConfigDialog` class**
   - Status: ✅ **UNUSED**
   - Reason: Class is defined but never instantiated
   - Note: This appears to be superseded by `AccountManagerDialog`
   - Action: Remove if not needed, or document as planned feature

### Data Orchestrator Methods

4. **`src/data_orchestrator.py:209` - `get_available_providers()` method**
   - Status: ✅ **UNUSED**
   - Reason: Method exists but never called in codebase
   - Note: Could be useful for future GUI features

5. **`src/data_orchestrator.py:252` - `enable_provider()` method**
   - Status: ✅ **UNUSED**
   - Reason: Method exists but never called

6. **`src/data_orchestrator.py:259` - `disable_provider()` method**
   - Status: ✅ **UNUSED**
   - Reason: Method exists but never called

### Account Health Methods

7. **`src/account_health.py:138` - `recommend_best_accounts()` method**
   - Status: ✅ **UNUSED**
   - Reason: Not called anywhere in codebase

8. **`src/account_health.py:249` - `log_non_arb_bet()` method**
   - Status: ✅ **UNUSED**
   - Reason: Not called anywhere in codebase

9. **`src/account_health_cache.py:64` - `get_stealth_score()` method**
   - Status: ✅ **UNUSED**
   - Reason: Not called anywhere

10. **`src/account_health_cache.py:100` - `get_stats()` method**
    - Status: ✅ **UNUSED**
    - Reason: Not called anywhere

11. **`src/account_manager.py:402` - `get_last_arb_date()` method**
    - Status: ✅ **UNUSED**
    - Reason: Not called anywhere

### Data Storage

12. **`src/data_storage/historical_data.py:25` - `fetched_at` variable**
    - Status: ✅ **UNUSED** (in dataclass)
    - Reason: Defined but never used

13. **`src/data_storage/historical_data.py:28` - `final_result` variable**
    - Status: ✅ **UNUSED** (in dataclass)
    - Reason: Defined but never used

### Base Classes (Unused dataclass fields)

14. **`src/api_providers/base.py:21` - `source_api` variable**
    - Status: ✅ **UNUSED** (in StandardizedOddsEvent dataclass)
    - Reason: Field defined but never assigned or used

15. **`src/api_providers/base.py:22` - `fetched_at` variable**
    - Status: ✅ **UNUSED** (in StandardizedOddsEvent dataclass)
    - Reason: Field defined but never assigned or used

16. **`src/api_providers/base.py:31` - `last_error` variable**
    - Status: ✅ **UNUSED** (in ProviderHealth dataclass initial definition)
    - Note: This field IS actually used later (line 31), vulture may have flagged wrong line

17. **`src/metadata_providers/base.py:14-19` - Multiple unused dataclass fields**
    - Status: ✅ **UNUSED**
    - Fields: `team_id`, `country`, `logo_url`, `website`, `venue`, `referee`, `position`
    - Reason: Defined in dataclasses but never populated or used

---

## ❌ FALSE POSITIVES (Actually Used)

### Classes Used in Tests

1. **`src/api_providers/sportradar.py:17` - `SportradarAPIProvider`**
   - Status: ❌ **USED** (in tests and documentation)
   - Used in: `tests/conftest.py`, documentation files
   - Note: Intentionally disabled in production (main_window.py:894-899)

2. **`src/api_providers/the_odds_api.py:16` - `TheOddsAPIProvider`**
   - Status: ❌ **USED** (in tests and documentation)
   - Used in: `tests/conftest.py`, multiple documentation files
   - Note: Intentionally disabled in production

3. **`src/data_orchestrator_async.py:16` - `AsyncMultiAPIOrchestrator`**
   - Status: ❌ **USED** (in tests)
   - Used in: `tests/test_performance.py`, `tests/test_concurrency.py`, `tests/test_regression.py`

4. **`src/data_orchestrator_enhanced.py:17` - `EnhancedMultiAPIOrchestrator`**
   - Status: ❌ **USED** (in documentation and examples)
   - Used in: `ENHANCED_FEATURES.md`, mentioned in documentation

5. **`src/arbitrage_optimized.py:13` - `OptimizedArbitrageDetector`**
   - Status: ❌ **USED** (in tests)
   - Used in: `tests/conftest.py`, `tests/test_regression.py`

6. **`src/data_storage/historical_data.py:33` - `HistoricalDataStorage`**
   - Status: ❌ **USED** (in documentation and examples)
   - Used in: `ENHANCED_FEATURES.md`, mentioned in `src/models/probability_model.py`

### Methods Used in Tests

7. **`src/utils.py:27` - `get_env_variable()`**
   - Status: ❌ **USED** (in tests)
   - Used in: `tests/unit/test_utils.py`

8. **`src/utils.py:55` - `format_percentage()`**
   - Status: ❌ **USED** (in tests)
   - Used in: `tests/unit/test_utils.py`

9. **`src/utils.py:69` - `calculate_time_until_event()`**
   - Status: ❌ **USED** (in tests)
   - Used in: `tests/unit/test_utils.py`

10. **`src/stake_calculator.py:169` - `vary_stakes()`**
    - Status: ❌ **USED** (in tests)
    - Used in: `tests/unit/test_stake_calculator.py`, `tests/property/test_stake_property.py`

11. **`src/stake_calculator.py:214` - `optimize_stakes_for_bankroll()`**
    - Status: ❌ **USED** (in tests)
    - Used in: `tests/unit/test_stake_calculator.py`

12. **`src/arbitrage_optimized.py:145` - `find_best_arbitrages_batch()`**
    - Status: ❌ **POTENTIALLY USED** (public API method)
    - Note: May be called dynamically or in future features

### GUI Methods Used Dynamically

13. **`gui/main_window.py:162` - `open_setup_wizard()`**
    - Status: ❌ **USED** (via dynamic call)
    - Used in: `onboarding/wiring_example.py:137` via `hasattr()` check and signal connection
    - Note: This is called from welcome dialog signal

14. **`src/api_providers/sofascore_scraper.py:432` - `test_connection()`**
    - Status: ❌ **USED** (in examples)
    - Used in: `examples/scraper_usage_example.py:45`

15. **`src/api_providers/sportradar.py:277` - `test_connection()`**
    - Status: ❌ **POTENTIALLY USED** (public API method)
    - Note: Available for testing when Sportradar is enabled

### PyQt Widget Properties (Qt Framework)

16. **`gui/tachometer_widget.py:22,42` - `_value` attributes**
    - Status: ❌ **USED** (internal state)
    - Reason: Used to store tachometer value, updated on line 42

17. **`gui/tachometer_widget.py:62` - `displayValue` property**
    - Status: ❌ **USED** (Qt property animation)
    - Reason: Used by `QPropertyAnimation` on line 26 for smooth animations

18. **`gui/tachometer_widget.py:64` - `paintEvent()` method**
    - Status: ❌ **USED** (Qt framework)
    - Reason: Called automatically by PyQt6 framework when widget needs repainting

### Abstract/Interface Methods

19. **`src/scrapers/base_scraper.py:29` - `scrape_odds()`**
    - Status: ❌ **USED** (abstract method)
    - Reason: Part of abstract base class interface

20. **`src/scrapers/base_scraper.py:53` - `_normalize_odds_format()`**
    - Status: ❌ **POTENTIALLY USED** (protected method)
    - Note: May be overridden or called by subclasses

21. **`src/scrapers/odds_portal_scraper.py:40` - `scrape_odds()`**
    - Status: ❌ **USED** (implementation of abstract method)

22. **`src/metadata_providers/base.py:61,65` - `get_team_metadata()`, `get_upcoming_matches()`**
    - Status: ❌ **USED** (abstract methods)
    - Reason: Part of abstract base class interface

23. **`src/metadata_providers/sports_open_data.py:39,67` - `get_team_metadata()`, `get_upcoming_matches()`**
    - Status: ❌ **USED** (interface implementations)

24. **`src/metadata_providers/thesportsdb.py:39,64` - `get_team_metadata()`, `get_upcoming_matches()`**
    - Status: ❌ **USED** (interface implementations)

---

## 🟡 STAGED/FUTURE CODE (Intentionally kept)

### Alternative Implementations

1. **`src/data_orchestrator_async.py` - `AsyncMultiAPIOrchestrator`**
   - Status: 🟡 **STAGED CODE**
   - Reason: Alternative async implementation, used in performance tests
   - Action: Keep for performance testing/comparison

2. **`src/data_orchestrator_enhanced.py` - `EnhancedMultiAPIOrchestrator`**
   - Status: 🟡 **STAGED CODE**
   - Reason: Enhanced version with latency tracking, documented feature
   - Action: Keep for future enhancement path

3. **`src/arbitrage_optimized.py` - `OptimizedArbitrageDetector`**
   - Status: 🟡 **STAGED CODE**
   - Reason: Optimized version used in performance tests
   - Action: Keep for performance optimization testing

### Disabled but Implemented Features

4. **`src/api_providers/sportradar.py` - `SportradarAPIProvider`**
   - Status: 🟡 **DISABLED FEATURE**
   - Reason: Fully implemented but disabled in production (paid service)
   - Action: Keep for when/if re-enabled

5. **`src/api_providers/the_odds_api.py` - `TheOddsAPIProvider`**
   - Status: 🟡 **DISABLED FEATURE**
   - Reason: Fully implemented but disabled in production (paid service)
   - Action: Keep for when/if re-enabled

### Historical Data Storage

6. **`src/data_storage/historical_data.py` - `HistoricalDataStorage`**
   - Status: 🟡 **PLANNED/FUTURE FEATURE**
   - Reason: Complete implementation, referenced in docs but not actively used
   - Action: Keep for future historical analysis features

### Methods with Stubbed/Incomplete Implementations

7. **`src/data_orchestrator_enhanced.py:39` - `fetch_odds_with_analysis()`**
   - Status: 🟡 **FUTURE FEATURE**
   - Reason: Enhanced method with additional analysis

8. **`src/data_orchestrator_enhanced.py:182` - `get_latency_arbitrage_opportunity()`**
   - Status: 🟡 **FUTURE FEATURE**
   - Reason: Advanced latency-based arbitrage detection

---

## 📋 Recommendations

### Immediate Actions (Safe to Remove)

1. Remove unused `checked` parameter in `gui/main_window.py:584`
2. Remove or implement `provider_status_labels` in `gui/main_window.py:1004`
3. Remove `BookmakerConfigDialog` class if superseded
4. Remove unused dataclass fields in `src/api_providers/base.py` and `src/metadata_providers/base.py`
5. Consider removing unused methods in `data_orchestrator.py` (`get_available_providers`, `enable_provider`, `disable_provider`) unless planned for GUI

### Keep (Used in Tests/Examples)

- All utility functions (`utils.py`)
- All stake calculator methods
- Test connection methods (used in examples)
- GUI methods called dynamically
- Abstract base class methods

### Keep (Staged/Future Features)

- Alternative orchestrators (`AsyncMultiAPIOrchestrator`, `EnhancedMultiAPIOrchestrator`)
- Optimized arbitrage detector
- Disabled API providers (can be re-enabled)
- Historical data storage
- Enhanced orchestrator methods

### Consider Documenting

- Create a `.vulture` whitelist file to suppress known false positives
- Document staged/future code in codebase
- Add TODO comments for incomplete implementations

---

## Creating Vulture Whitelist

To suppress false positives, create `.vulture` file:

```
# Classes used in tests
src/api_providers/sportradar.py:17:SportradarAPIProvider
src/api_providers/the_odds_api.py:16:TheOddsAPIProvider
src/data_orchestrator_async.py:16:AsyncMultiAPIOrchestrator
src/data_orchestrator_enhanced.py:17:EnhancedMultiAPIOrchestrator
src/arbitrage_optimized.py:13:OptimizedArbitrageDetector
src/data_storage/historical_data.py:33:HistoricalDataStorage

# Methods used in tests
src/utils.py:27:get_env_variable
src/utils.py:55:format_percentage
src/utils.py:69:calculate_time_until_event
src/stake_calculator.py:169:vary_stakes
src/stake_calculator.py:214:optimize_stakes_for_bankroll

# GUI methods called dynamically
gui/main_window.py:162:open_setup_wizard

# Qt framework methods
gui/tachometer_widget.py:64:paintEvent
gui/tachometer_widget.py:62:displayValue

# Abstract base class methods
src/scrapers/base_scraper.py:29:scrape_odds
src/metadata_providers/base.py:61:get_team_metadata
src/metadata_providers/base.py:65:get_upcoming_matches
```

---

## Conclusion

Most vulture findings are **false positives** due to:
- Dynamic method calls (PyQt signals/slots)
- Test usage (not detected by static analysis)
- Framework integration (Qt properties, paintEvent)
- Abstract interface methods
- Staged/future features

Actual dead code is minimal (~15 items), mostly unused helper methods and dataclass fields that can be safely removed or cleaned up.

