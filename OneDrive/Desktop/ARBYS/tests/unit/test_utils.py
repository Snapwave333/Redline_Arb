"""Unit tests for utility functions."""

from datetime import datetime, timedelta

from src.utils import (
    calculate_time_until_event,
    format_currency,
    format_percentage,
    get_env_variable,
)


class TestFormatCurrency:
    """Test suite for format_currency function."""

    def test_format_usd_default(self):
        """Test USD formatting."""
        assert format_currency(100.50) == "$100.50"
        assert format_currency(0.99) == "$0.99"
        assert format_currency(1000.0) == "$1000.00"

    def test_format_currency_custom(self):
        """Test custom currency formatting."""
        result = format_currency(100.50, currency="EUR")
        assert "100.50" in result
        assert "EUR" in result


class TestFormatPercentage:
    """Test suite for format_percentage function."""

    def test_format_percentage_default(self):
        """Test default percentage formatting."""
        assert format_percentage(5.0) == "5.00%"
        assert format_percentage(0.5) == "0.50%"
        assert format_percentage(100.0) == "100.00%"

    def test_format_percentage_custom_decimals(self):
        """Test custom decimal places."""
        assert format_percentage(5.123, decimals=1) == "5.1%"
        assert format_percentage(5.789, decimals=0) == "6%"

    def test_format_percentage_decimal_input(self):
        """Test formatting decimal values (e.g., 0.05 for 5%)."""
        # Note: function expects percentage value, not decimal
        assert format_percentage(5.0) == "5.00%"  # 5%


class TestCalculateTimeUntilEvent:
    """Test suite for calculate_time_until_event function."""

    def test_future_event(self):
        """Test calculation for future event."""
        future_time = (datetime.now() + timedelta(hours=2, minutes=30)).isoformat()
        result = calculate_time_until_event(future_time)

        assert result is not None
        assert isinstance(result, str)
        assert "h" in result or "m" in result

    def test_past_event(self):
        """Test calculation for past event."""
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        result = calculate_time_until_event(past_time)

        # Should return "Event started" or None
        assert result is None or result == "Event started"

    def test_invalid_format(self):
        """Test handling of invalid datetime format."""
        result = calculate_time_until_event("invalid-date")
        assert result is None


class TestGetEnvVariable:
    """Test suite for get_env_variable function."""

    def test_get_existing_variable(self, monkeypatch):
        """Test getting existing environment variable."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        assert get_env_variable("TEST_VAR") == "test_value"

    def test_get_nonexistent_with_default(self):
        """Test getting non-existent variable with default."""
        result = get_env_variable("NONEXISTENT_VAR", default="default_value")
        assert result == "default_value"

    def test_get_nonexistent_without_default(self):
        """Test getting non-existent variable without default."""
        result = get_env_variable("ANOTHER_NONEXISTENT_VAR")
        assert result is None
