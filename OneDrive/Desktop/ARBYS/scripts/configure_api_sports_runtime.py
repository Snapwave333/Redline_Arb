"""
Runtime utility to add or update the API-Sports provider configuration without importing project modules.

Usage (PowerShell from project root):
    python scripts/configure_api_sports_runtime.py --api-key YOUR_KEY [--priority 5] [--enable true]

This will create or update config/bot_config.json with an "api_sports" provider entry,
preserving existing providers and ensuring SofaScore Scraper remains enabled as a free fallback.

It also updates .env with API_SPORTS_API_KEY=YOUR_KEY.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List


def get_project_root() -> str:
    """Return the current project root (assumes script is executed from project root)."""
    return os.getcwd()


def detect_portable_mode(root: str) -> bool:
    """Detect portable mode by checking for portable.flag in project root."""
    return os.path.exists(os.path.join(root, "portable.flag"))


def get_config_paths() -> tuple[str, str]:
    """Return (config_dir, config_file_path) based on portable mode."""
    root = get_project_root()
    if detect_portable_mode(root):
        config_dir = os.path.join(root, "portable_data", "config")
    else:
        config_dir = os.path.join(root, "config")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir, os.path.join(config_dir, "bot_config.json")


def ensure_sofascore_default(providers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure SofaScore Scraper is present and enabled as highest-priority free source."""
    sofascore_entry = {
        "name": "sofascore_scraper",
        "type": "sofascore_scraper",
        "api_key": "",
        "priority": 1,
        "enabled": True,
    }
    # Find existing index (if any)
    idx = next((i for i, p in enumerate(providers) if p.get("type") == "sofascore_scraper"), None)
    if idx is None:
        providers.insert(0, sofascore_entry)
    else:
        providers[idx].update(sofascore_entry)
    return providers


def upsert_api_sports(providers: List[Dict[str, Any]], api_key: str, priority: int, enable: bool) -> List[Dict[str, Any]]:
    """Add or update the API-Sports provider entry."""
    updated = False
    for p in providers:
        if p.get("type") == "api_sports":
            p["name"] = "api_sports"
            p["api_key"] = api_key
            p["priority"] = priority
            p["enabled"] = enable
            updated = True
            break

    if not updated:
        providers.append(
            {
                "name": "api_sports",
                "type": "api_sports",
                "api_key": api_key,
                "priority": priority,
                "enabled": enable,
            }
        )
    return providers


def load_config(config_file: str) -> Dict[str, Any]:
    """Load existing bot_config.json or create a default structure."""
    config: Dict[str, Any] = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}
    if "api_providers" not in config or not isinstance(config.get("api_providers"), list):
        config["api_providers"] = []
    return config


def save_config(config_file: str, config: Dict[str, Any]) -> None:
    """Persist bot_config.json."""
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def update_env(root: str, api_key: str) -> None:
    """Add or update API_SPORTS_API_KEY in .env."""
    env_file = os.path.join(root, ".env")
    lines: List[str] = []
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            lines = []
    found = False
    for i, line in enumerate(lines):
        if line.startswith("API_SPORTS_API_KEY="):
            lines[i] = f"API_SPORTS_API_KEY={api_key}\n"
            found = True
            break
    if not found:
        lines.append(f"API_SPORTS_API_KEY={api_key}\n")
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    parser = argparse.ArgumentParser(description="Configure API-Sports provider (runtime)")
    parser.add_argument("--api-key", required=True, help="API-Sports API key")
    parser.add_argument("--priority", type=int, default=5, help="Provider priority (higher = more preferred)")
    parser.add_argument("--enable", type=str, default="true", help="Enable provider (true/false)")
    args = parser.parse_args()

    enable = str(args.enable).lower() in {"1", "true", "yes", "on"}

    root = get_project_root()
    config_dir, config_file = get_config_paths()

    config = load_config(config_file)
    providers = config.get("api_providers", [])
    providers = ensure_sofascore_default(providers)
    providers = upsert_api_sports(providers, api_key=args.api_key, priority=args.priority, enable=enable)
    config["api_providers"] = providers
    save_config(config_file, config)

    update_env(root, args.api_key)

    print("✅ API-Sports provider configured.")
    print(f" - Enabled: {enable}")
    print(f" - Priority: {args.priority}")
    print(f" - Config file: {config_file}")
    print("You can now restart the desktop app to use API-Sports as a backup provider.")


if __name__ == "__main__":
    main()