"""
Historical dataset storage system for model training and analysis.
Stores odds data, outcomes, and metadata for later analysis.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HistoricalOddsRecord:
    """Record of historical odds data."""

    id: int | None = None
    event_name: str = ""
    sport: str = ""
    home_team: str = ""
    away_team: str = ""
    commence_time: datetime = None
    provider: str = ""
    outcomes_json: str = ""  # JSON string of outcomes
    arbitrage_detected: bool = False
    arbitrage_profit: float | None = None


# TODO(redline): historical storage (future feature) - complete implementation for historical analysis
class HistoricalDataStorage:
    """Stores and retrieves historical odds data for analysis."""

    def __init__(self, db_path: str = "data/historical_odds.db"):
        """
        Initialize historical data storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historical_odds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                sport TEXT NOT NULL,
                home_team TEXT,
                away_team TEXT,
                commence_time TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                provider TEXT NOT NULL,
                outcomes_json TEXT NOT NULL,
                final_result TEXT,
                arbitrage_detected BOOLEAN DEFAULT 0,
                arbitrage_profit REAL,
                INDEX idx_commence_time (commence_time),
                INDEX idx_provider (provider),
                INDEX idx_sport (sport)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                odds_record_id INTEGER,
                event_name TEXT NOT NULL,
                profit_percentage REAL NOT NULL,
                total_stake REAL,
                guaranteed_profit REAL,
                detected_at TEXT NOT NULL,
                executed BOOLEAN DEFAULT 0,
                actual_profit REAL,
                FOREIGN KEY (odds_record_id) REFERENCES historical_odds(id)
            )
        """
        )

        conn.commit()
        conn.close()

    def store_odds_record(
        self, event_data: dict, provider: str, arbitrage_info: dict = None
    ) -> int:
        """
        Store an odds record.

        Args:
            event_data: Standardized event dictionary with odds
            provider: Provider name
            arbitrage_info: Optional arbitrage detection info

        Returns:
            Record ID
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            # Parse commence time
            commence_time = event_data.get("commence_time", datetime.now().isoformat())
            if isinstance(commence_time, str):
                commence_time = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))

            outcomes_json = json.dumps(event_data.get("outcomes", []))

            arbitrage_detected = 0
            arbitrage_profit = None
            if arbitrage_info:
                arbitrage_detected = 1
                arbitrage_profit = arbitrage_info.get("profit_percentage", 0)

            cursor.execute(
                """
                INSERT INTO historical_odds (
                    event_name, sport, home_team, away_team,
                    commence_time, fetched_at, provider,
                    outcomes_json, arbitrage_detected, arbitrage_profit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event_data.get("event_name", ""),
                    event_data.get("sport", ""),
                    event_data.get("home_team", ""),
                    event_data.get("away_team", ""),
                    commence_time.isoformat(),
                    datetime.now().isoformat(),
                    provider,
                    outcomes_json,
                    arbitrage_detected,
                    arbitrage_profit,
                ),
            )

            record_id = cursor.lastrowid

            # Store arbitrage opportunity if detected
            if arbitrage_info and arbitrage_detected:
                cursor.execute(
                    """
                    INSERT INTO arbitrage_opportunities (
                        odds_record_id, event_name, profit_percentage,
                        total_stake, guaranteed_profit, detected_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        record_id,
                        event_data.get("event_name", ""),
                        arbitrage_info.get("profit_percentage", 0),
                        arbitrage_info.get("total_stake", 0),
                        arbitrage_info.get("guaranteed_profit", 0),
                        datetime.now().isoformat(),
                    ),
                )

            conn.commit()
            return record_id

        except Exception as e:
            logger.error(f"Error storing historical odds: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_historical_odds(
        self,
        sport: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        provider: str = None,
    ) -> list[dict]:
        """
        Retrieve historical odds records.

        Args:
            sport: Filter by sport
            start_date: Start date filter
            end_date: End date filter
            provider: Filter by provider

        Returns:
            List of historical odds records
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM historical_odds WHERE 1=1"
        params = []

        if sport:
            query += " AND sport = ?"
            params.append(sport)

        if start_date:
            query += " AND commence_time >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND commence_time <= ?"
            params.append(end_date.isoformat())

        if provider:
            query += " AND provider = ?"
            params.append(provider)

        query += " ORDER BY commence_time DESC LIMIT 1000"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            record = dict(row)
            record["outcomes"] = json.loads(record["outcomes_json"])
            results.append(record)

        conn.close()
        return results

    def update_final_result(self, record_id: int, result: str):
        """Update final result for a completed match."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE historical_odds 
            SET final_result = ? 
            WHERE id = ?
        """,
            (result, record_id),
        )

        conn.commit()
        conn.close()

    def get_arbitrage_statistics(self, days: int = 30) -> dict:
        """
        Get statistics on detected arbitrage opportunities.

        Args:
            days: Number of days to analyze

        Returns:
            Statistics dictionary
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Total opportunities
        cursor.execute(
            """
            SELECT COUNT(*), AVG(profit_percentage), 
                   SUM(guaranteed_profit), COUNT(CASE WHEN executed = 1 THEN 1 END)
            FROM arbitrage_opportunities
            WHERE detected_at >= ?
        """,
            (start_date,),
        )

        row = cursor.fetchone()
        stats = {
            "total_opportunities": row[0] or 0,
            "avg_profit_percentage": row[1] or 0.0,
            "total_potential_profit": row[2] or 0.0,
            "executed_count": row[3] or 0,
        }

        conn.close()
        return stats
