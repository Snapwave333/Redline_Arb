"""
Async-optimized data orchestrator for parallel provider fetching.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from src.api_providers.base import OddsAPIProvider
from src.data_orchestrator import MultiAPIOrchestrator

logger = logging.getLogger(__name__)


# TODO(redline): kept for perf alt in tests - async implementation used for performance testing
class AsyncMultiAPIOrchestrator(MultiAPIOrchestrator):
    """
    Async-optimized orchestrator that fetches from multiple providers in parallel.

    This reduces latency by fetching from all providers simultaneously
    instead of sequentially.
    """

    def __init__(
        self,
        providers: list[OddsAPIProvider],
        failover_enabled: bool = True,
        require_all_providers: bool = False,
        max_workers: int = 5,
    ):
        """
        Initialize async orchestrator.

        Args:
            providers: List of API provider instances
            failover_enabled: Enable automatic failover
            require_all_providers: Require all providers to succeed
            max_workers: Maximum parallel workers for fetching
        """
        super().__init__(providers, failover_enabled, require_all_providers)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def fetch_odds_async(self, sport: str, **kwargs) -> tuple[list[dict], list[dict], dict]:
        """
        Asynchronously fetch odds from all enabled providers in parallel.

        Args:
            sport: Sport to fetch odds for
            **kwargs: Additional parameters

        Returns:
            Tuple of (merged_results, errors, latency_stats)
        """
        import time

        enabled_providers = [p for p in self.providers if p.is_enabled()]

        if not enabled_providers:
            return [], [], {}

        # Create tasks for parallel execution with timing
        tasks = []
        start_times = {}

        for provider in enabled_providers:
            provider_name = provider.get_provider_name()
            start_times[provider_name] = time.time()
            task = self._fetch_provider_async(provider, sport, **kwargs)
            tasks.append(task)

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results with latency tracking
        provider_results = []
        errors = []
        latency_stats = {}

        for provider, result in zip(enabled_providers, results, strict=False):
            provider_name = provider.get_provider_name()
            response_time = time.time() - start_times[provider_name]

            if isinstance(result, Exception):
                error_info = {
                    "provider": provider_name,
                    "error": str(result),
                    "timestamp": datetime.now().isoformat(),
                }
                errors.append(error_info)
                latency_stats[provider_name] = {
                    "response_time": response_time,
                    "success": False,
                    "error": str(result),
                }
                logger.warning(f"Provider {provider_name} failed: {str(result)}")
            elif result:
                provider_results.append(
                    {
                        "provider": provider_name,
                        "data": result,
                        "timestamp": datetime.now().isoformat(),
                        "latency": response_time,
                    }
                )
                latency_stats[provider_name] = {
                    "response_time": response_time,
                    "success": True,
                    "result_count": len(result) if result else 0,
                }

        # Merge results
        merged_results = self._merge_results(provider_results)

        return merged_results, errors, latency_stats

    async def _fetch_provider_async(self, provider: OddsAPIProvider, sport: str, **kwargs):
        """
        Fetch odds from a single provider asynchronously.

        Args:
            provider: Provider instance
            sport: Sport to fetch
            **kwargs: Additional parameters

        Returns:
            List of event dictionaries or None
        """
        loop = asyncio.get_event_loop()

        # Run synchronous fetch in thread pool
        try:
            result = await loop.run_in_executor(self.executor, provider.fetch_odds, sport, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error fetching from {provider.get_provider_name()}: {e}")
            raise

    def fetch_odds(self, sport: str, **kwargs) -> tuple[list[dict], list[dict], dict]:
        """
        Synchronous wrapper for async fetch (maintains backward compatibility).

        Args:
            sport: Sport to fetch odds for
            **kwargs: Additional parameters

        Returns:
            Tuple of (merged_results, errors, latency_stats)
        """
        # Run async method in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new event loop in a thread
                import threading

                result_container = {}
                exception_container = {}

                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result = new_loop.run_until_complete(self.fetch_odds_async(sport, **kwargs))
                        result_container["result"] = result
                        new_loop.close()
                    except Exception as e:
                        exception_container["exception"] = e

                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()

                if exception_container:
                    raise exception_container["exception"]
                return result_container["result"]
            else:
                return loop.run_until_complete(self.fetch_odds_async(sport, **kwargs))
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self.fetch_odds_async(sport, **kwargs))

    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)
