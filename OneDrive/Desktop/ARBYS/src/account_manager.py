"""
Account profile data model and database schema.
"""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AccountProfile:
    """Represents a bookmaker account profile."""

    id: int | None = None
    bookmaker_name: str = ""
    account_username: str = ""
    total_bets_placed: int = 0
    total_arb_bets: int = 0
    total_non_arb_bets: int = 0
    total_profit_loss: float = 0.0
    total_staked: float = 0.0
    last_bet_amount: float = 0.0
    last_bet_date: str | None = None
    last_arb_date: str | None = None  # Timestamp of last arbitrage bet
    last_non_arb_date: str | None = None  # Timestamp of last non-arb bet (mug bet)
    stealth_score: float = 1.0  # 0.0-1.0 scale, higher is better (1.0 = low risk)
    account_status: str = "Healthy"  # Healthy, Under Review, Limited, Closed
    notes: str = ""
    created_at: str | None = None
    updated_at: str | None = None


class AccountDatabase:
    """Manages SQLite database for account profiles."""

    def __init__(self, db_path: str = "config/accounts.db"):
        """
        Initialize the account database.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper timeout for concurrent access."""
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def init_database(self):
        """Initialize database schema."""
        import os

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bookmaker_name TEXT NOT NULL,
                account_username TEXT NOT NULL,
                total_bets_placed INTEGER DEFAULT 0,
                total_arb_bets INTEGER DEFAULT 0,
                total_non_arb_bets INTEGER DEFAULT 0,
                total_profit_loss REAL DEFAULT 0.0,
                total_staked REAL DEFAULT 0.0,
                last_bet_amount REAL DEFAULT 0.0,
                last_bet_date TEXT,
                last_arb_date TEXT,
                last_non_arb_date TEXT,
                stealth_score REAL DEFAULT 1.0,
                account_status TEXT DEFAULT 'Healthy',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bookmaker_name, account_username)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bet_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                bet_type TEXT NOT NULL,  -- 'arb' or 'non_arb'
                stake_amount REAL NOT NULL,
                outcome TEXT,
                odds REAL,
                profit_loss REAL,
                bookmaker_name TEXT,
                event_name TEXT,
                notes TEXT,
                placed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """
        )

        conn.commit()
        conn.close()
        logger.info("Account database initialized")

    def create_account(self, profile: AccountProfile) -> int:
        """
        Create a new account profile.

        Args:
            profile: AccountProfile object

        Returns:
            ID of created account
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO accounts (
                bookmaker_name, account_username, total_bets_placed,
                total_arb_bets, total_non_arb_bets, total_profit_loss,
                total_staked, last_bet_amount, last_bet_date,
                last_arb_date, last_non_arb_date,
                stealth_score, account_status, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                profile.bookmaker_name,
                profile.account_username,
                profile.total_bets_placed,
                profile.total_arb_bets,
                profile.total_non_arb_bets,
                profile.total_profit_loss,
                profile.total_staked,
                profile.last_bet_amount,
                profile.last_bet_date,
                profile.last_arb_date,
                profile.last_non_arb_date,
                profile.stealth_score,
                profile.account_status,
                profile.notes,
                now,
                now,
            ),
        )

        account_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(
            f"Created account profile: {profile.bookmaker_name} - {profile.account_username}"
        )
        return account_id

    def get_account(
        self, bookmaker_name: str, account_username: str = None
    ) -> AccountProfile | None:
        """
        Get account profile by bookmaker name.

        Args:
            bookmaker_name: Name of the bookmaker
            account_username: Optional username (if multiple accounts per bookmaker)

        Returns:
            AccountProfile if found, None otherwise
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if account_username:
            cursor.execute(
                "SELECT * FROM accounts WHERE bookmaker_name = ? AND account_username = ?",
                (bookmaker_name, account_username),
            )
        else:
            cursor.execute(
                "SELECT * FROM accounts WHERE bookmaker_name = ? LIMIT 1", (bookmaker_name,)
            )

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_profile(row)
        return None

    def get_all_accounts(self) -> list[AccountProfile]:
        """Get all account profiles."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts ORDER BY bookmaker_name")
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_profile(row) for row in rows]

    def update_account(self, profile: AccountProfile):
        """Update account profile."""
        if not profile.id:
            raise ValueError("Account profile must have an ID to update")

        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute(
            """
            UPDATE accounts SET
                total_bets_placed = ?,
                total_arb_bets = ?,
                total_non_arb_bets = ?,
                total_profit_loss = ?,
                total_staked = ?,
                last_bet_amount = ?,
                last_bet_date = ?,
                last_arb_date = ?,
                last_non_arb_date = ?,
                stealth_score = ?,
                account_status = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
        """,
            (
                profile.total_bets_placed,
                profile.total_arb_bets,
                profile.total_non_arb_bets,
                profile.total_profit_loss,
                profile.total_staked,
                profile.last_bet_amount,
                profile.last_bet_date,
                profile.last_arb_date,
                profile.last_non_arb_date,
                profile.stealth_score,
                profile.account_status,
                profile.notes,
                now,
                profile.id,
            ),
        )

        conn.commit()
        conn.close()
        logger.debug(f"Updated account profile ID: {profile.id}")

    def log_bet(
        self,
        account_id: int,
        bet_type: str,
        stake_amount: float,
        outcome: str = None,
        odds: float = None,
        profit_loss: float = None,
        bookmaker_name: str = None,
        event_name: str = None,
        notes: str = None,
    ):
        """
        Log a bet transaction.

        Args:
            account_id: Account ID
            bet_type: 'arb' or 'non_arb'
            stake_amount: Amount staked
            outcome: Outcome name
            odds: Odds used
            profit_loss: Profit/loss from this bet
            bookmaker_name: Bookmaker name
            event_name: Event name
            notes: Additional notes
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO bet_log (
                account_id, bet_type, stake_amount, outcome, odds,
                profit_loss, bookmaker_name, event_name, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                account_id,
                bet_type,
                stake_amount,
                outcome,
                odds,
                profit_loss,
                bookmaker_name,
                event_name,
                notes,
            ),
        )

        bet_id = cursor.lastrowid

        # Commit and close connection before calling other methods that open their own connections
        conn.commit()
        conn.close()

        # Update account profile (this will open its own connection)
        profile = self.get_account_by_id(account_id)
        if profile:
            profile.total_bets_placed += 1
            profile.total_staked += stake_amount

            now = datetime.now().isoformat()

            if bet_type == "arb":
                profile.total_arb_bets += 1
                profile.last_arb_date = now
            else:
                profile.total_non_arb_bets += 1
                profile.last_non_arb_date = now

            if profit_loss is not None:
                profile.total_profit_loss += profit_loss

            profile.last_bet_amount = stake_amount
            profile.last_bet_date = now

            # Recalculate stealth score
            profile.stealth_score = self._calculate_stealth_score(profile)

            self.update_account(profile)

        return bet_id

    def delete_account(self, bookmaker_name: str, account_username: str = None) -> bool:
        """
        Delete an account by bookmaker name.

        Args:
            bookmaker_name: Name of the bookmaker
            account_username: Optional username (if multiple accounts per bookmaker)

        Returns:
            True if account was deleted, False otherwise
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if account_username:
            cursor.execute(
                "DELETE FROM accounts WHERE bookmaker_name = ? AND account_username = ?",
                (bookmaker_name, account_username),
            )
        else:
            cursor.execute("DELETE FROM accounts WHERE bookmaker_name = ?", (bookmaker_name,))

        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()

        return deleted

    def get_bet_history(self, account_id: int, limit: int = 100) -> list[dict]:
        """
        Get bet history for an account.

        Args:
            account_id: Account ID
            limit: Maximum number of bets to return

        Returns:
            List of bet dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM bet_log 
            WHERE account_id = ? 
            ORDER BY placed_at DESC 
            LIMIT ?
        """,
            (account_id, limit),
        )

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        # Convert rows to dictionaries
        cols = [description[0] for description in cursor.description]
        return [dict(zip(cols, row, strict=False)) for row in rows]

    def update_account_after_bet(self, account_id: int, pnl_delta: float) -> None:
        """
        Update account balance after a bet (add profit/loss).

        Args:
            account_id: Account ID
            pnl_delta: Profit/loss delta to add to total_profit_loss
        """
        profile = self.get_account_by_id(account_id)
        if profile:
            profile.total_profit_loss += pnl_delta
            self.update_account(profile)

    def get_account_by_id(self, account_id: int) -> AccountProfile | None:
        """Get account profile by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_profile(row)
        return None

    def _row_to_profile(self, row: sqlite3.Row) -> AccountProfile:
        """Convert database row to AccountProfile."""
        # sqlite3.Row uses bracket notation, not .get()
        # For optional fields, use bracket notation (column should always exist in schema)
        return AccountProfile(
            id=row["id"],
            bookmaker_name=row["bookmaker_name"],
            account_username=row["account_username"],
            total_bets_placed=row["total_bets_placed"],
            total_arb_bets=row["total_arb_bets"],
            total_non_arb_bets=row["total_non_arb_bets"],
            total_profit_loss=row["total_profit_loss"],
            total_staked=row["total_staked"],
            last_bet_amount=row["last_bet_amount"],
            last_bet_date=row["last_bet_date"] if row["last_bet_date"] else None,
            last_arb_date=row["last_arb_date"] if row["last_arb_date"] else None,
            last_non_arb_date=row["last_non_arb_date"] if row["last_non_arb_date"] else None,
            stealth_score=row["stealth_score"],
            account_status=row["account_status"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _calculate_stealth_score(self, profile: AccountProfile) -> float:
        """
        Calculate stealth score based on account activity.

        Args:
            profile: AccountProfile object

        Returns:
            Stealth score (0.0-1.0, where 1.0 = low risk, 0.0 = high risk)
        """
        score = 1.0  # Start with perfect score

        # Penalize high percentage of arb bets
        if profile.total_bets_placed > 0:
            arb_percentage = (profile.total_arb_bets / profile.total_bets_placed) * 100
            if arb_percentage > 80:
                score -= 0.30  # High arb percentage is very suspicious
            elif arb_percentage > 60:
                score -= 0.15
            elif arb_percentage > 40:
                score -= 0.05
            elif arb_percentage < 30:
                score += 0.05  # Reward good mix

        # Penalize high total profit
        if profile.total_profit_loss > 1000:
            score -= 0.20
        elif profile.total_profit_loss > 500:
            score -= 0.10
        elif profile.total_profit_loss < 0:
            score += 0.05  # Small loss is actually good for stealth

        # Check time since last non-arb bet (mug bet)
        if profile.last_non_arb_date:
            try:
                from dateutil import parser

                last_non_arb = parser.parse(profile.last_non_arb_date)
                days_since_non_arb = (datetime.now() - last_non_arb.replace(tzinfo=None)).days

                if days_since_non_arb > 30:
                    score -= 0.15  # Haven't placed mug bet in over a month
                elif days_since_non_arb > 14:
                    score -= 0.10
                elif days_since_non_arb > 7:
                    score -= 0.05
            except Exception:
                pass

        # Check rapid arb betting (multiple arbs in short time)
        if profile.last_arb_date:
            try:
                from dateutil import parser

                last_arb = parser.parse(profile.last_arb_date)
                hours_since_arb = (
                    datetime.now() - last_arb.replace(tzinfo=None)
                ).total_seconds() / 3600

                if hours_since_arb < 1:
                    score -= 0.10  # Very recent arb bet
                elif hours_since_arb < 6:
                    score -= 0.05
            except Exception:
                pass

        # Penalize consistent stake sizes
        if (
            profile.total_bets_placed > 10
            and profile.last_bet_amount > 0
            and profile.last_bet_amount == round(profile.last_bet_amount)
        ):
            score -= 0.03  # Round numbers are slightly suspicious

        # Penalize account status heavily
        if profile.account_status == "Closed":
            score = 0.0
        elif profile.account_status == "Limited":
            score *= 0.4  # Reduce to 40% of current score
        elif profile.account_status == "Under Review":
            score *= 0.7  # Reduce to 70% of current score

        # Ensure score stays in valid range [0.0, 1.0]
        return max(0.0, min(1.0, score))
