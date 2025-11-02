"""
Quick verification script for API-Sports provider.

Usage:
    python scripts/verify_api_sports.py --api-key YOUR_KEY

Prints remaining requests and attempts to fetch soccer odds, showing a small sample.
"""

from __future__ import annotations

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Verify API-Sports provider")
    parser.add_argument("--api-key", required=False, help="API-Sports API key (optional, falls back to env)")
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("API_SPORTS_API_KEY", "")
    if not api_key:
        print("ERROR: No API key provided. Use --api-key or set API_SPORTS_API_KEY in environment.")
        sys.exit(1)

    # Ensure project root is on path
    root = os.getcwd()
    if root not in sys.path:
        sys.path.insert(0, root)

    try:
        from src.api_providers.api_sports import APISportsProvider
    except Exception as e:
        print(f"ERROR: Failed to import APISportsProvider: {e}")
        sys.exit(1)

    provider = APISportsProvider(api_key=api_key, enabled=True, priority=5)
    try:
        remaining = provider.get_remaining_requests()
    except Exception:
        remaining = -1
    print(f"Remaining requests today: {remaining}")

    try:
        events = provider.fetch_odds("soccer")
        print(f"Fetched events: {len(events)}")
        if events:
            # Print one sample event summary
            sample = events[0]
            print("Sample event:")
            print(f"  Event: {sample.get('event_name')}")
            print(f"  Outcomes: {len(sample.get('outcomes', []))}")
            print(f"  Bookmakers: {sorted(set(o.get('bookmaker') for o in sample.get('outcomes', [])))[:3]}")
        else:
            print("No events returned (this may happen depending on date/availability).")
    except Exception as e:
        print(f"ERROR during fetch: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()