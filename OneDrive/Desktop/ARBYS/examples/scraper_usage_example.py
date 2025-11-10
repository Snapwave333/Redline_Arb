"""
Example: Using SofaScore Scraper with ARBYS

This example demonstrates how to integrate the free SofaScore scraper
with the existing ARBYS arbitrage detection system.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from src.api_providers.sofascore_scraper import SofaScoreScraperProvider
from src.arbitrage import ArbitrageDetector
from src.data_orchestrator import MultiAPIOrchestrator
from src.stake_calculator import StakeCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def example_standalone_scraper():
    """Example: Using SofaScore scraper standalone."""
    print("\n=== Example 1: Standalone SofaScore Scraper ===\n")

    # Create scraper provider
    scraper = SofaScoreScraperProvider(
        api_key="scraper",  # Not used, kept for interface compatibility
        enabled=True,
        priority=1,
        cache_ttl=300,  # Cache for 5 minutes
        max_requests_per_second=2.0,  # Respectful rate limiting
    )

    # Test connection
    print("Testing SofaScore connection...")
    test_result = scraper.test_connection()
    print(f"Connection test: {test_result}")

    # Fetch odds for soccer
    print("\nFetching soccer odds...")
    events = scraper.fetch_odds("soccer")

    print(f"\nFound {len(events)} events with odds")

    # Display first few events
    for i, event in enumerate(events[:3]):
        print(f"\nEvent {i+1}: {event['event_name']}")
        print(f"  Sport: {event['sport']}")
        print(f"  Commence Time: {event['commence_time']}")
        print(f"  Outcomes: {len(event['outcomes'])}")
        for outcome in event["outcomes"][:3]:  # Show first 3 outcomes
            print(
                f"    - {outcome['outcome_name']}: {outcome['odds']:.2f} @ {outcome['bookmaker']}"
            )


def example_with_orchestrator():
    """Example: Using scraper with MultiAPIOrchestrator (with failover)."""
    print("\n=== Example 2: Scraper with Multi-API Orchestrator ===\n")

    # Create providers
    scraper = SofaScoreScraperProvider(priority=1)  # Primary (free)

    # Optional: Add paid API as backup (if you have API key)
    # the_odds_api = TheOddsAPIProvider(
    #     api_key="your_api_key_here",
    #     priority=2  # Secondary (paid)
    # )

    # Create orchestrator with failover
    orchestrator = MultiAPIOrchestrator(
        providers=[scraper],  # Add more providers here: [scraper, the_odds_api]
        failover_enabled=True,
        require_all_providers=False,
    )

    # Fetch odds (orchestrator handles failover automatically)
    print("Fetching odds via orchestrator...")
    events, errors = orchestrator.fetch_odds("soccer")

    if errors:
        print(f"\nProvider errors: {len(errors)}")
        for error in errors:
            print(f"  - {error['provider']}: {error['error']}")

    print(
        f"\nSuccessfully fetched {len(events)} events from {len({e.get('source_apis', ['scraper'])[0] if e.get('source_apis') else ['scraper'] for e in events})} provider(s)"
    )


def example_arbitrage_detection():
    """Example: Detecting arbitrage opportunities from scraped data."""
    print("\n=== Example 3: Arbitrage Detection with Scraped Data ===\n")

    # Setup
    scraper = SofaScoreScraperProvider()
    orchestrator = MultiAPIOrchestrator(providers=[scraper])
    detector = ArbitrageDetector(min_profit_percentage=1.0)
    calculator = StakeCalculator(min_stake_threshold=10.0)

    # Fetch odds
    print("Fetching odds...")
    events, errors = orchestrator.fetch_odds("soccer")

    if not events:
        print("No events found. Try again later.")
        return

    print(f"Analyzing {len(events)} events for arbitrage opportunities...\n")

    # Detect arbitrage
    opportunities_found = 0
    for event in events:
        outcomes = event.get("outcomes", [])
        if len(outcomes) < 2:
            continue

        opportunity = detector.detect_arbitrage(outcomes)

        if opportunity:
            opportunities_found += 1
            print("🎯 ARBITRAGE FOUND!")
            print(f"   Event: {event['event_name']}")
            print(f"   Profit: {opportunity.profit_percentage:.2f}%")
            print(f"   Total Implied Probability: {opportunity.total_implied_probability:.4f}")
            print("   Outcomes:")

            for outcome in opportunity.outcomes:
                print(
                    f"     - {outcome['outcome_name']}: {outcome['odds']:.2f} @ {outcome['bookmaker']}"
                )

            # Calculate stakes
            stake_dist = calculator.calculate_stakes(opportunity, total_stake=100.0)
            print(f"\n   Stake Distribution (Total: ${stake_dist.total_stake:.2f}):")
            for stake_info in stake_dist.stakes:
                print(
                    f"     - {stake_info['outcome_name']} ({stake_info['bookmaker']}): ${stake_info['stake']:.2f}"
                )
            print(
                f"   Guaranteed Profit: ${stake_dist.guaranteed_profit:.2f} ({stake_dist.profit_percentage:.2f}%)"
            )

            if stake_dist.warnings:
                print(f"   ⚠️  Warnings: {', '.join(stake_dist.warnings)}")

            print()

    if opportunities_found == 0:
        print("No arbitrage opportunities found in current data.")
        print("This is normal - arbitrage opportunities are rare.")


def example_multiple_sports():
    """Example: Fetching odds for multiple sports."""
    print("\n=== Example 4: Multiple Sports ===\n")

    scraper = SofaScoreScraperProvider()

    sports = ["soccer", "basketball", "tennis"]

    for sport in sports:
        print(f"\nFetching {sport} odds...")
        events = scraper.fetch_odds(sport)
        print(f"  Found {len(events)} events")

        if events:
            total_outcomes = sum(len(e.get("outcomes", [])) for e in events)
            print(f"  Total outcomes: {total_outcomes}")


def example_caching():
    """Example: Demonstrating caching behavior."""
    print("\n=== Example 5: Caching Demonstration ===\n")

    scraper = SofaScoreScraperProvider(cache_ttl=60)  # 1-minute cache

    import time

    print("First request (cache miss - will fetch from API)...")
    start = time.time()
    events1 = scraper.fetch_odds("soccer")
    time1 = time.time() - start
    print(f"  Time: {time1:.2f}s, Events: {len(events1)}")

    print("\nSecond request (cache hit - will use cache)...")
    start = time.time()
    events2 = scraper.fetch_odds("soccer")
    time2 = time.time() - start
    print(f"  Time: {time2:.4f}s, Events: {len(events2)}")

    print(f"\nCache speedup: {time1/time2:.1f}x faster")


if __name__ == "__main__":
    print("=" * 60)
    print("ARBYS SofaScore Scraper Usage Examples")
    print("=" * 60)

    try:
        # Run examples
        example_standalone_scraper()
        example_with_orchestrator()
        example_arbitrage_detection()
        example_multiple_sports()
        example_caching()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("\nTip: Make sure you've installed all dependencies:")
        print("  pip install -r requirements.txt")
