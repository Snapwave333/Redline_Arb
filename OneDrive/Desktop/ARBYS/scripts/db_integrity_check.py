#!/usr/bin/env python3
"""
Database Integrity Check Script for ARBYS Bot.
Performs comprehensive checks on the SQLite Account Health Database.

This script should be run periodically (e.g., daily via cron/Task Scheduler)
to ensure database integrity before the bot starts.
"""

import os
import shutil
import sqlite3
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import CONFIG_DIR


class DatabaseIntegrityChecker:
    """Performs integrity checks on the SQLite database."""

    def __init__(self, db_path: str = None):
        """
        Initialize integrity checker.

        Args:
            db_path: Path to database file (defaults to config/accounts.db)
        """
        if db_path is None:
            db_path = os.path.join(CONFIG_DIR, "accounts.db")

        self.db_path = db_path
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_failed = 0

    def check_file_exists(self) -> bool:
        """Check if database file exists and is accessible."""
        try:
            if not os.path.exists(self.db_path):
                self.errors.append(f"Database file does not exist: {self.db_path}")
                return False

            if not os.path.isfile(self.db_path):
                self.errors.append(f"Path exists but is not a file: {self.db_path}")
                return False

            # Check if file is readable
            if not os.access(self.db_path, os.R_OK):
                self.errors.append(f"Database file is not readable: {self.db_path}")
                return False

            # Check if file is writable
            if not os.access(self.db_path, os.W_OK):
                self.warnings.append(f"Database file is not writable: {self.db_path}")

            # Check file size
            file_size = os.path.getsize(self.db_path)
            if file_size == 0:
                self.errors.append("Database file is empty (0 bytes)")
                return False

            if file_size < 1024:  # Less than 1KB
                self.warnings.append(f"Database file is very small ({file_size} bytes)")

            self.checks_passed += 1
            return True

        except Exception as e:
            self.errors.append(f"Error checking file: {str(e)}")
            return False

    def check_connection(self) -> sqlite3.Connection | None:
        """Check if database connection can be established."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            conn.execute("SELECT 1")
            self.checks_passed += 1
            return conn

        except sqlite3.OperationalError as e:
            self.errors.append(f"Cannot connect to database: {str(e)}")
            return None
        except Exception as e:
            self.errors.append(f"Error connecting to database: {str(e)}")
            return None

    def check_schema(self, conn: sqlite3.Connection) -> bool:
        """Verify database schema matches expected structure."""
        try:
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # Expected tables
            expected_tables = ["accounts", "bet_log"]

            for table in expected_tables:
                if table not in tables:
                    self.errors.append(f"Required table '{table}' is missing")
                    self.checks_failed += 1
                    continue

                # Get table schema
                cursor.execute(f"PRAGMA table_info({table})")
                columns = {row[1]: row[2] for row in cursor.fetchall()}

                # Verify accounts table schema
                if table == "accounts":
                    required_columns = {
                        "bookmaker_name": "TEXT",
                        "account_username": "TEXT",
                        "stealth_score": "REAL",
                        "account_status": "TEXT",
                        "last_arb_date": "TEXT",
                        "last_non_arb_date": "TEXT",
                    }

                    for col_name, col_type in required_columns.items():
                        if col_name not in columns:
                            self.errors.append(
                                f"Required column '{col_name}' missing in 'accounts' table"
                            )
                            self.checks_failed += 1
                        elif not columns[col_name].upper().startswith(col_type):
                            self.warnings.append(
                                f"Column '{col_name}' has unexpected type: "
                                f"expected {col_type}, got {columns[col_name]}"
                            )

                # Verify bet_log table schema
                elif table == "bet_log":
                    required_columns = {
                        "bookmaker_name": "TEXT",
                        "bet_type": "TEXT",
                        "stake": "REAL",
                    }

                    for col_name, _col_type in required_columns.items():
                        if col_name not in columns:
                            self.errors.append(
                                f"Required column '{col_name}' missing in 'arb_log' table"
                            )
                            self.checks_failed += 1

            if self.checks_failed == 0:
                self.checks_passed += 1

            return self.checks_failed == 0

        except Exception as e:
            self.errors.append(f"Error checking schema: {str(e)}")
            self.checks_failed += 1
            return False

    def check_integrity(self, conn: sqlite3.Connection) -> bool:
        """Run SQLite integrity check."""
        try:
            cursor = conn.cursor()

            # Quick check first (faster)
            cursor.execute("PRAGMA quick_check")
            quick_result = cursor.fetchone()

            if quick_result[0] != "ok":
                self.errors.append(f"Quick integrity check failed: {quick_result[0]}")
                self.checks_failed += 1

                # Try full integrity check for more details
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchall()

                error_details = "\n".join(
                    [row[0] for row in integrity_result[:10]]
                )  # Limit to 10 errors
                self.errors.append(f"Integrity check details:\n{error_details}")

                return False

            self.checks_passed += 1
            return True

        except Exception as e:
            self.errors.append(f"Error running integrity check: {str(e)}")
            self.checks_failed += 1
            return False

    def check_foreign_keys(self, conn: sqlite3.Connection) -> bool:
        """Check foreign key constraints if enabled."""
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_key_check")
            violations = cursor.fetchall()

            if violations:
                self.warnings.append(f"Found {len(violations)} foreign key constraint violations")
                return False

            self.checks_passed += 1
            return True

        except Exception:
            # Foreign keys may not be enabled, this is okay
            pass

        return True

    def check_data_consistency(self, conn: sqlite3.Connection) -> bool:
        """Check for data consistency issues."""
        try:
            cursor = conn.cursor()

            # Check stealth_score range (should be 0.0-1.0)
            cursor.execute(
                """
                SELECT COUNT(*) FROM accounts 
                WHERE stealth_score < 0.0 OR stealth_score > 1.0
            """
            )
            invalid_scores = cursor.fetchone()[0]

            if invalid_scores > 0:
                self.warnings.append(
                    f"Found {invalid_scores} accounts with stealth_score outside 0.0-1.0 range"
                )

            # Check for NULL stealth_scores
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE stealth_score IS NULL")
            null_scores = cursor.fetchone()[0]

            if null_scores > 0:
                self.warnings.append(f"Found {null_scores} accounts with NULL stealth_score")

            # Check for accounts with invalid status
            valid_statuses = ["Healthy", "Under Review", "Limited", "Closed"]
            cursor.execute(
                """
                SELECT COUNT(*) FROM accounts 
                WHERE account_status NOT IN (?, ?, ?, ?)
            """,
                valid_statuses,
            )
            invalid_statuses = cursor.fetchone()[0]

            if invalid_statuses > 0:
                self.warnings.append(
                    f"Found {invalid_statuses} accounts with invalid account_status"
                )

            self.checks_passed += 1
            return True

        except Exception as e:
            self.errors.append(f"Error checking data consistency: {str(e)}")
            self.checks_failed += 1
            return False

    def backup_database(self) -> str | None:
        """Create backup of database file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)

            backup_path = os.path.join(backup_dir, f"accounts_backup_{timestamp}.db")

            shutil.copy2(self.db_path, backup_path)
            return backup_path

        except Exception as e:
            self.errors.append(f"Error creating backup: {str(e)}")
            return None

    def repair_database(self) -> bool:
        """Attempt to repair database using SQLite VACUUM."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()

            # Try VACUUM to repair
            cursor.execute("VACUUM")
            conn.commit()

            # Re-analyze
            cursor.execute("ANALYZE")
            conn.commit()

            conn.close()

            self.warnings.append("Database repair (VACUUM) completed")
            return True

        except Exception as e:
            self.errors.append(f"Error repairing database: {str(e)}")
            return False

    def run_all_checks(self, auto_repair: bool = False) -> tuple[bool, dict]:
        """
        Run all integrity checks.

        Args:
            auto_repair: If True, attempt repair on errors

        Returns:
            Tuple of (success, summary_dict)
        """
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_failed = 0

        # Check 1: File exists
        if not self.check_file_exists():
            return False, self.get_summary()

        # Check 2: Connection
        conn = self.check_connection()
        if not conn:
            return False, self.get_summary()

        try:
            # Check 3: Schema
            self.check_schema(conn)

            # Check 4: Integrity
            integrity_ok = self.check_integrity(conn)

            # Check 5: Foreign keys
            self.check_foreign_keys(conn)

            # Check 6: Data consistency
            self.check_data_consistency(conn)

            # If integrity check failed, attempt repair
            if not integrity_ok and auto_repair:
                self.warnings.append("Attempting automatic repair...")
                conn.close()

                # Create backup before repair
                backup_path = self.backup_database()
                if backup_path:
                    self.warnings.append(f"Backup created: {backup_path}")

                # Attempt repair
                if self.repair_database():
                    # Re-check integrity after repair
                    conn = self.check_connection()
                    if conn:
                        integrity_ok = self.check_integrity(conn)
                        if integrity_ok:
                            self.warnings.append("Repair successful - integrity check now passes")
                        else:
                            self.errors.append("Repair attempted but integrity check still fails")

        finally:
            conn.close()

        success = len(self.errors) == 0
        return success, self.get_summary()

    def get_summary(self) -> dict:
        """Get summary of checks."""
        return {
            "passed": self.checks_passed,
            "failed": self.checks_failed,
            "errors": self.errors,
            "warnings": self.warnings,
            "db_path": self.db_path,
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ARBYS Bot Database Integrity Check")
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to database file (default: config/accounts.db)",
    )
    parser.add_argument(
        "--auto-repair", action="store_true", help="Attempt automatic repair on errors"
    )
    parser.add_argument(
        "--backup-on-error", action="store_true", help="Create backup if errors found"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress output (for cron)")

    args = parser.parse_args()

    checker = DatabaseIntegrityChecker(db_path=args.db_path)
    success, summary = checker.run_all_checks(auto_repair=args.auto_repair)

    # Create backup if errors found and requested
    if not success and args.backup_on_error:
        backup_path = checker.backup_database()
        if backup_path:
            summary["backup_path"] = backup_path

    # Print results
    if not args.quiet:
        print("=" * 60)
        print("ARBYS Bot - Database Integrity Check")
        print("=" * 60)
        print(f"Database: {summary['db_path']}")
        print(f"Checks Passed: {summary['passed']}")
        print(f"Checks Failed: {summary['failed']}")
        print()

        if summary["warnings"]:
            print("Warnings:")
            for warning in summary["warnings"]:
                print(f"  ⚠ {warning}")
            print()

        if summary["errors"]:
            print("Errors:")
            for error in summary["errors"]:
                print(f"  ✗ {error}")
            print()

        if summary.get("backup_path"):
            print(f"Backup Created: {summary['backup_path']}")
            print()

        if success:
            print("✓ Database integrity check PASSED")
            print("=" * 60)
        else:
            print("✗ Database integrity check FAILED")
            print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
