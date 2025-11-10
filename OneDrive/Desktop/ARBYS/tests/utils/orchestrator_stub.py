"""
Orchestrator stub for testing without real API providers.
"""


class OrchestratorStub:
    """Stub orchestrator for testing."""

    def fetch_and_merge(self, league: str) -> dict:
        """Return empty results for testing."""
        return {"events": [], "provider": "stub", "latency_ms": 0}

    def fetch_odds(self, sport: str, **kwargs) -> tuple[list[dict], list[dict], dict]:
        """Return empty results matching orchestrator signature."""
        return [], [], {}
