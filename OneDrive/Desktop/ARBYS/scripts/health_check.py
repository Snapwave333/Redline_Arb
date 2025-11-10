#!/usr/bin/env python3
"""
Health check script for ARBYS bot.
Run this periodically to verify bot health.
"""

import os
import shutil
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from src.account_manager import AccountDatabase


def check_api_key():
    """Check if API key is configured."""
    if not Config.ODDS_API_KEY:
        return False, "API key not configured"
    return True, "API key configured"


def check_database():
    """Check database connectivity and integrity."""
    try:
        db = AccountDatabase()
        accounts = db.get_all_accounts()
        if not accounts:
            return False, "No accounts configured"

        # Check database integrity
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()

        if result[0] != "ok":
            return False, f"Database integrity check failed: {result[0]}"

        return True, f"Database OK ({len(accounts)} accounts)"
    except Exception as e:
        return False, f"Database error: {str(e)}"


def check_disk_space():
    """Check available disk space."""
    total, used, free = shutil.disk_usage(".")
    free_mb = free / (1024 * 1024)

    if free_mb < 100:
        return False, f"Low disk space: {free_mb:.1f}MB free"
    return True, f"Disk space OK: {free_mb:.1f}MB free"


def check_config_files():
    """Check if configuration files exist."""
    issues = []

    config_files = ["config/bookmakers.json", "config/settings.py"]

    for file in config_files:
        if not os.path.exists(file):
            issues.append(f"Missing: {file}")

    if issues:
        return False, "; ".join(issues)
    return True, "Configuration files OK"


def check_logs():
    """Check if log directory exists and is writable."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception as e:
            return False, f"Cannot create log directory: {str(e)}"

    if not os.access(log_dir, os.W_OK):
        return False, "Log directory not writable"

    return True, "Logs OK"


def main():
    """Run all health checks."""
    checks = [
        ("API Key", check_api_key),
        ("Database", check_database),
        ("Disk Space", check_disk_space),
        ("Config Files", check_config_files),
        ("Logs", check_logs),
    ]

    all_passed = True
    results = []

    for name, check_func in checks:
        passed, message = check_func()
        status = "✓" if passed else "✗"
        results.append(f"{status} {name}: {message}")
        if not passed:
            all_passed = False

    print("\n".join(results))

    if all_passed:
        print("\n✓ All health checks passed")
        sys.exit(0)
    else:
        print("\n✗ Health check failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
