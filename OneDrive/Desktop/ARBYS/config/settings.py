"""
Configuration management for the arbitrage bot.
"""

import json
import logging
import os
import sys

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


def _detect_portable_mode() -> bool:
    """Detect if running in portable mode by checking for portable.flag."""
    # Check if portable.flag exists in the same directory as main.py or executable
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to project root
        app_dir = os.path.dirname(os.path.dirname(app_dir))

    portable_flag = os.path.join(app_dir, "portable.flag")
    return os.path.exists(portable_flag)


def _get_config_dir() -> str:
    """Get configuration directory, using portable_data/ if in portable mode."""
    if _detect_portable_mode():
        # Running in portable mode - use portable_data/ directory
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        config_dir = os.path.join(base_dir, "portable_data", "config")
        os.makedirs(config_dir, exist_ok=True)
        return config_dir
    else:
        # Normal mode - use config/ directory
        return "config"


# Configuration file path (detects portable mode)
CONFIG_DIR = _get_config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "bot_config.json")
BOOKMAKERS_FILE = os.path.join(CONFIG_DIR, "bookmakers.json")


class Config:
    """Configuration settings for the arbitrage bot."""

    # API Configuration - Paid APIs removed, only free providers available
    # Legacy single API removed - use multi-API orchestrator with SofaScore Scraper

    # Test Mode
    TEST_MODE: bool = os.getenv("TEST_MODE", "0") == "1"

    # Legacy API Key (for backward compatibility with setup wizard)
    ODDS_API_KEY: str = os.getenv("ODDS_API_KEY", "") or ""

    # Multi-API Configuration
    USE_MULTI_API: bool = os.getenv("USE_MULTI_API", "false").lower() == "true"

    # Bot Configuration
    MIN_PROFIT_PERCENTAGE: float = float(os.getenv("MIN_PROFIT_PERCENTAGE", "1.0"))
    MAX_STAKE: float = float(os.getenv("MAX_STAKE", "1000.0"))
    DEFAULT_STAKE: float = float(os.getenv("DEFAULT_STAKE", "100.0"))

    # Alert Configuration
    ENABLE_SOUND_ALERTS: bool = os.getenv("ENABLE_SOUND_ALERTS", "true").lower() == "true"
    PROFIT_THRESHOLD_ALERT: float = float(os.getenv("PROFIT_THRESHOLD_ALERT", "5.0"))

    # Anti-Detection Settings
    ROUND_STAKES: bool = os.getenv("ROUND_STAKES", "true").lower() == "true"
    VARY_BET_SIZES: bool = os.getenv("VARY_BET_SIZES", "true").lower() == "true"
    MAX_BET_VARIATION_PERCENT: float = float(os.getenv("MAX_BET_VARIATION_PERCENT", "5.0"))
    MIN_STAKE_THRESHOLD: float = float(os.getenv("MIN_STAKE_THRESHOLD", "10.0"))
    BET_DELAY_SECONDS: int = int(os.getenv("BET_DELAY_SECONDS", "15"))

    # Update Interval (seconds)
    UPDATE_INTERVAL: int = int(os.getenv("UPDATE_INTERVAL", "30"))

    # Risk Management
    MAX_MARKET_AGE_HOURS: float = float(os.getenv("MAX_MARKET_AGE_HOURS", "24.0"))
    CRITICAL_STEALTH_THRESHOLD: float = float(os.getenv("CRITICAL_STEALTH_THRESHOLD", "0.2"))

    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration settings.

        Returns:
            True if configuration is valid
        """
        # Check if any providers are configured (only free SofaScore Scraper available)
        providers = cls.get_api_providers()
        if not providers or not any(p.get("enabled", False) for p in providers):
            logger.warning(
                "No API providers configured. Please configure SofaScore Scraper (free)."
            )
            return False
        return True

    @classmethod
    def save_api_key(cls, api_key: str, provider_name: str = "the_odds_api"):
        """Save API key to environment file."""
        env_file = ".env"
        lines = []

        if os.path.exists(env_file):
            with open(env_file) as f:
                lines = f.readlines()

        # Update or add API key
        env_key = f"{provider_name.upper()}_API_KEY"
        if provider_name == "the_odds_api":
            env_key = "ODDS_API_KEY"

        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{env_key}=") or (
                provider_name == "the_odds_api" and line.startswith("ODDS_API_KEY=")
            ):
                lines[i] = f"{env_key}={api_key}\n"
                found = True
                break

        if not found:
            lines.append(f"{env_key}={api_key}\n")

        with open(env_file, "w") as f:
            f.writelines(lines)

        if provider_name == "the_odds_api":
            cls.ODDS_API_KEY = api_key
        logger.info(f"API key saved for {provider_name}")

    @classmethod
    def get_bookmakers(cls) -> list[dict[str, str]]:
        """
        Get list of configured bookmakers.

        Returns:
            List of bookmaker dictionaries with name and optional username
        """
        if not os.path.exists(BOOKMAKERS_FILE):
            return []

        try:
            with open(BOOKMAKERS_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading bookmakers: {str(e)}")
            return []

    @classmethod
    def save_bookmakers(cls, bookmakers: list[dict[str, str]]):
        """
        Save bookmaker list to configuration file.

        Args:
            bookmakers: List of bookmaker dictionaries
        """
        os.makedirs(CONFIG_DIR, exist_ok=True)

        with open(BOOKMAKERS_FILE, "w") as f:
            json.dump(bookmakers, f, indent=2)

        logger.info(f"Saved {len(bookmakers)} bookmakers to configuration")

    @classmethod
    def add_bookmaker(cls, name: str, username: str = ""):
        """
        Add a bookmaker to the configuration.

        Args:
            name: Bookmaker name
            username: Optional account username
        """
        bookmakers = cls.get_bookmakers()

        # Check if already exists
        for bm in bookmakers:
            if bm.get("name", "").lower() == name.lower():
                # Update existing
                bm["username"] = username
                cls.save_bookmakers(bookmakers)
                return

        # Add new
        bookmakers.append({"name": name, "username": username})
        cls.save_bookmakers(bookmakers)

    @classmethod
    def remove_bookmaker(cls, name: str):
        """
        Remove a bookmaker from configuration.

        Args:
            name: Bookmaker name to remove
        """
        bookmakers = cls.get_bookmakers()
        bookmakers = [bm for bm in bookmakers if bm.get("name", "").lower() != name.lower()]
        cls.save_bookmakers(bookmakers)

    @classmethod
    def get_preferred_sports(cls) -> list[str]:
        """Get list of preferred sports."""
        if not os.path.exists(CONFIG_FILE):
            return ["soccer", "basketball", "baseball", "hockey", "tennis"]

        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
                return config.get(
                    "preferred_sports", ["soccer", "basketball", "baseball", "hockey", "tennis"]
                )
        except Exception:
            return ["soccer", "basketball", "baseball", "hockey", "tennis"]

    @classmethod
    def save_preferred_sports(cls, sports: list[str]):
        """Save preferred sports list."""
        os.makedirs(CONFIG_DIR, exist_ok=True)

        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    config = json.load(f)
            except Exception:
                pass

        config["preferred_sports"] = sports

        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

    @classmethod
    def get_api_providers(cls) -> list[dict[str, any]]:
        """
        Get list of configured API providers.

        Returns:
            List of provider configuration dictionaries
        """
        if not os.path.exists(CONFIG_FILE):
            # Default: SofaScore Scraper (free)
            return [
                {
                    "name": "sofascore_scraper",
                    "type": "sofascore_scraper",
                    "api_key": "",  # Not needed for SofaScore
                    "priority": 1,
                    "enabled": True,  # Enabled by default since it's free
                }
            ]

        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
                providers = config.get("api_providers", [])

                # If no providers configured, return default (SofaScore Scraper)
                if not providers:
                    return [
                        {
                            "name": "sofascore_scraper",
                            "type": "sofascore_scraper",
                            "api_key": "",  # Not needed for SofaScore
                            "priority": 1,
                            "enabled": True,  # Enabled by default since it's free
                        }
                    ]

                return providers
        except Exception as e:
            logger.error(f"Error loading API providers: {e}")
            # Return default SofaScore Scraper on error
            return [
                {
                    "name": "sofascore_scraper",
                    "type": "sofascore_scraper",
                    "api_key": "",  # Not needed for SofaScore
                    "priority": 1,
                    "enabled": True,  # Enabled by default since it's free
                }
            ]

    @classmethod
    def save_api_providers(cls, providers: list[dict[str, any]]):
        """
        Save API provider configuration.

        Args:
            providers: List of provider configuration dictionaries
        """
        os.makedirs(CONFIG_DIR, exist_ok=True)

        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    config = json.load(f)
            except Exception:
                pass

        config["api_providers"] = providers

        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved {len(providers)} API provider configurations")
