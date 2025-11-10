"""Unit tests for Sportradar API provider."""

from src.api_providers.sportradar import SportradarAPIProvider


class TestSportradarAPIProvider:
    """Unit tests for SportradarAPIProvider."""

    def test_init(self):
        """Test provider initialization."""
        provider = SportradarAPIProvider(api_key="test_key", enabled=True, priority=1)
        assert provider.api_key == "test_key"
        assert provider.enabled is True
        assert provider.priority == 1
        assert provider.get_provider_name() == "sportradar"

    def test_get_provider_name(self):
        """Test provider name."""
        provider = SportradarAPIProvider(api_key="test")
        assert provider.get_provider_name() == "sportradar"

    def test_normalize_response_events_key(self):
        """Test normalize_response with 'events' key structure."""
        provider = SportradarAPIProvider(api_key="test")

        raw_data = {
            "events": [
                {
                    "sport": {"name": "Soccer"},
                    "competitors": [
                        {"name": "Team A"},
                        {"name": "Team B"},
                    ],
                    "scheduled": "2024-01-01T12:00:00Z",
                    "markets": [
                        {
                            "bookmaker": {"name": "Bookmaker A"},
                            "market_type": "h2h",
                            "outcomes": [
                                {"name": "Team A", "odds": 2.1},
                                {"name": "Team B", "odds": 2.2},
                            ],
                        }
                    ],
                }
            ]
        }

        events = provider.normalize_response(raw_data)

        assert isinstance(events, list)
        assert len(events) == 1
        event = events[0]
        assert event["sport"] == "Soccer"
        assert event["home_team"] == "Team A"
        assert event["away_team"] == "Team B"

    def test_normalize_response_sport_events_key(self):
        """Test normalize_response with 'sport_events' key structure."""
        provider = SportradarAPIProvider(api_key="test")

        raw_data = {
            "sport_events": [
                {
                    "sport": {"name": "Basketball"},
                    "competitors": [
                        {"name": "Team C"},
                        {"name": "Team D"},
                    ],
                    "markets": [
                        {
                            "bookmaker_name": "Bookmaker B",
                            "type": "h2h",
                            "outcomes": [
                                {"name": "Team C", "price": 1.9},
                            ],
                        }
                    ],
                }
            ]
        }

        events = provider.normalize_response(raw_data)
        assert isinstance(events, list)
        assert len(events) == 1

    def test_normalize_response_empty(self):
        """Test normalize_response with empty data."""
        provider = SportradarAPIProvider(api_key="test")
        events = provider.normalize_response({})
        assert isinstance(events, list)

    def test_normalize_response_list_format(self):
        """Test normalize_response with direct list format."""
        provider = SportradarAPIProvider(api_key="test")

        raw_data = [
            {
                "sport": {"name": "Tennis"},
                "competitors": [{"name": "Player A"}, {"name": "Player B"}],
            }
        ]

        events = provider.normalize_response(raw_data)
        assert isinstance(events, list)

    def test_fetch_odds_disabled(self):
        """Test fetch_odds when provider is disabled."""
        provider = SportradarAPIProvider(api_key="test", enabled=False)
        result = provider.fetch_odds("soccer")
        assert result == []

    def test_get_available_sports(self):
        """Test get_available_sports returns list."""
        provider = SportradarAPIProvider(api_key="test")
        sports = provider.get_available_sports()
        assert isinstance(sports, list)
        assert len(sports) > 0
