"""Unit tests for The Odds API provider."""

from src.api_providers.the_odds_api import TheOddsAPIProvider


class TestTheOddsAPIProvider:
    """Unit tests for TheOddsAPIProvider."""

    def test_init(self):
        """Test provider initialization."""
        provider = TheOddsAPIProvider(api_key="test_key", enabled=True, priority=1)
        assert provider.api_key == "test_key"
        assert provider.enabled is True
        assert provider.priority == 1
        assert provider.get_provider_name() == "the_odds_api"

    def test_get_provider_name(self):
        """Test provider name."""
        provider = TheOddsAPIProvider(api_key="test")
        assert provider.get_provider_name() == "the_odds_api"

    def test_normalize_response_happy_path(self):
        """Test normalize_response with valid JSON."""
        provider = TheOddsAPIProvider(api_key="test")

        raw_data = [
            {
                "sport_title": "Soccer",
                "home_team": "Team A",
                "away_team": "Team B",
                "commence_time": "2024-01-01T12:00:00Z",
                "bookmakers": [
                    {
                        "title": "Bookmaker A",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Team A", "price": 2.1},
                                    {"name": "Team B", "price": 2.2},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]

        events = provider.normalize_response(raw_data)

        assert isinstance(events, list)
        assert len(events) == 1
        event = events[0]
        assert event["sport"] == "Soccer"
        assert event["home_team"] == "Team A"
        assert event["away_team"] == "Team B"
        assert len(event["outcomes"]) == 2
        assert event["outcomes"][0]["outcome_name"] == "Team A"
        assert event["outcomes"][0]["odds"] == 2.1

    def test_normalize_response_empty(self):
        """Test normalize_response with empty data."""
        provider = TheOddsAPIProvider(api_key="test")
        events = provider.normalize_response([])
        assert isinstance(events, list)
        assert len(events) == 0

    def test_normalize_response_missing_fields(self):
        """Test normalize_response with missing optional fields."""
        provider = TheOddsAPIProvider(api_key="test")

        raw_data = [
            {
                "sport_title": "Soccer",
                "home_team": "Team A",
                "away_team": "Team B",
                "bookmakers": [
                    {
                        "title": "Bookmaker A",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Team A", "price": 2.1},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]

        events = provider.normalize_response(raw_data)
        assert len(events) == 1
        assert events[0]["commence_time"] == ""  # Default when missing

    def test_fetch_odds_disabled(self):
        """Test fetch_odds when provider is disabled."""
        provider = TheOddsAPIProvider(api_key="test", enabled=False)
        result = provider.fetch_odds("soccer")
        assert result == []

    def test_get_available_sports_error_handling(self):
        """Test get_available_sports handles errors gracefully."""
        provider = TheOddsAPIProvider(api_key="invalid_key")
        # Should not crash, returns empty list or valid list
        sports = provider.get_available_sports()
        assert isinstance(sports, list)
