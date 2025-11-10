"""Unit tests for account database management."""

from src.account_manager import AccountDatabase, AccountProfile


class TestAccountDatabase:
    """Test suite for AccountDatabase."""

    def test_init(self, temp_db):
        """Test database initialization."""
        db = AccountDatabase(db_path=temp_db)
        assert db.db_path == temp_db

    def test_create_account(self, account_db):
        """Test creating an account."""
        profile = AccountProfile(
            bookmaker_name="TestBookmaker",
            account_username="test_user",
            stealth_score=0.9,
            account_status="Healthy",
        )

        account_id = account_db.create_account(profile)
        assert account_id is not None
        assert isinstance(account_id, int)

    def test_get_account(self, account_db, sample_account_profile):
        """Test retrieving an account."""
        retrieved = account_db.get_account(sample_account_profile.bookmaker_name)
        assert retrieved is not None
        assert retrieved.bookmaker_name == sample_account_profile.bookmaker_name

    def test_get_account_nonexistent(self, account_db):
        """Test retrieving non-existent account."""
        retrieved = account_db.get_account("Nonexistent")
        assert retrieved is None

    def test_update_account(self, account_db, sample_account_profile):
        """Test updating an account."""
        # Update stealth score
        sample_account_profile.stealth_score = 0.5
        account_db.update_account(sample_account_profile)

        updated = account_db.get_account(sample_account_profile.bookmaker_name)
        assert updated is not None
        assert updated.stealth_score == 0.5

    def test_delete_account(self, account_db, sample_account_profile):
        """Test deleting an account."""
        account_db.delete_account(sample_account_profile.bookmaker_name)

        deleted = account_db.get_account(sample_account_profile.bookmaker_name)
        assert deleted is None

    def test_get_all_accounts(
        self, account_db, sample_account_profile, low_stealth_account_profile
    ):
        """Test getting all accounts."""
        all_accounts = account_db.get_all_accounts()
        assert isinstance(all_accounts, list)
        assert len(all_accounts) >= 2  # At least our test accounts

    def test_log_bet(self, account_db, sample_account_profile):
        """Test logging a bet."""
        bet_id = account_db.log_bet(
            account_id=sample_account_profile.id,
            bet_type="arb",
            stake_amount=100.0,
            outcome="Home",
            odds=2.0,
            profit_loss=5.0,
            bookmaker_name=sample_account_profile.bookmaker_name,
            event_name="Test Event",
        )
        assert bet_id is not None

    def test_get_bet_history(self, account_db, sample_account_profile):
        """Test retrieving bet history."""
        # Log a bet first
        account_db.log_bet(
            account_id=sample_account_profile.id,
            bet_type="arb",
            stake_amount=100.0,
            outcome="Home",
            odds=2.0,
            profit_loss=5.0,
            bookmaker_name=sample_account_profile.bookmaker_name,
            event_name="Test Event",
        )

        history = account_db.get_bet_history(sample_account_profile.id)
        assert isinstance(history, list)
        assert len(history) > 0


class TestAccountProfile:
    """Test suite for AccountProfile dataclass."""

    def test_init_default(self):
        """Test default initialization."""
        profile = AccountProfile()
        assert profile.bookmaker_name == ""
        assert profile.stealth_score == 1.0
        assert profile.account_status == "Healthy"
        assert profile.total_bets_placed == 0

    def test_init_custom(self):
        """Test custom initialization."""
        profile = AccountProfile(
            bookmaker_name="TestBookmaker",
            account_username="test_user",
            stealth_score=0.8,
            account_status="Under Review",
        )
        assert profile.bookmaker_name == "TestBookmaker"
        assert profile.account_username == "test_user"
        assert profile.stealth_score == 0.8
        assert profile.account_status == "Under Review"
