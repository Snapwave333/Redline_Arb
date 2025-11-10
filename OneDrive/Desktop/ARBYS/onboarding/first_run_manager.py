"""
First-run flag management for onboarding system.

Persists user onboarding state (welcome dialog seen, tutorial completed, etc.)
to JSON file with atomic writes.
"""

import contextlib
import json
import logging
import os
import tempfile
from typing import Any

logger = logging.getLogger(__name__)

CONFIG_DIR = "config"
FLAGS_FILE = os.path.join(CONFIG_DIR, "first_run_flags.json")


def load_flags() -> dict[str, Any]:
    """
    Load first-run flags from JSON file.

    Returns:
        Dictionary with keys:
            - has_seen_welcome (bool): Whether user has seen welcome dialog
            - has_completed_tutorial (bool): Whether user has completed tutorial
            - last_version_seen (str): Last version string seen
            - show_welcome_on_startup (bool): Whether to show welcome on startup
    """
    if not os.path.exists(FLAGS_FILE):
        return {
            "has_seen_welcome": False,
            "has_completed_tutorial": False,
            "last_version_seen": "",
            "show_welcome_on_startup": True,
        }

    try:
        with open(FLAGS_FILE, encoding="utf-8") as f:
            flags = json.load(f)

        # Ensure all required keys exist with defaults
        default_flags = {
            "has_seen_welcome": False,
            "has_completed_tutorial": False,
            "last_version_seen": "",
            "show_welcome_on_startup": True,
        }

        for key, default_value in default_flags.items():
            if key not in flags:
                flags[key] = default_value

        return flags
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Error loading first-run flags: {e}, using defaults")
        return {
            "has_seen_welcome": False,
            "has_completed_tutorial": False,
            "last_version_seen": "",
            "show_welcome_on_startup": True,
        }


def save_flags(flags: dict[str, Any]) -> None:
    """
    Save first-run flags to JSON file using atomic write.

    Args:
        flags: Dictionary with flag values to save

    Raises:
        IOError: If file write fails
    """
    # Ensure config directory exists
    os.makedirs(CONFIG_DIR, exist_ok=True)

    # Atomic write: write to temp file, then rename
    try:
        # Write to temporary file in same directory
        temp_fd, temp_path = tempfile.mkstemp(
            dir=CONFIG_DIR, suffix=".tmp", prefix="first_run_flags_", text=True
        )

        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(flags, f, indent=2, ensure_ascii=False)

            # Atomic rename (works on Windows too if target doesn't exist)
            # On Windows, we may need to remove target first
            if os.path.exists(FLAGS_FILE):
                os.remove(FLAGS_FILE)
            os.rename(temp_path, FLAGS_FILE)

            logger.debug(f"Saved first-run flags to {FLAGS_FILE}")
        except Exception as e:
            # Clean up temp file on error
            with contextlib.suppress(OSError):
                os.unlink(temp_path)
            raise OSError(f"Failed to save first-run flags: {e}") from e
    except Exception as e:
        logger.error(f"Error saving first-run flags: {e}")
        raise
