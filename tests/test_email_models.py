"""Tests for email configuration models.

Tests the EmailConfig and ProcessedEmail SQLAlchemy models.
"""

import pytest
from datetime import datetime
from src.models import EmailConfig, ProcessedEmail, User
from src.services.database import get_db


class TestEmailConfigModel:
    """Test EmailConfig model."""

    def test_create_email_config(self, db_session):
        """Test creating an email configuration."""
        # Arrange: Create a test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Act: Create email config
        config = EmailConfig(
            user_id=user.id,
            email_address="user@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com",
            imap_port=993,
            use_ssl=True,
            provider="gmail",
            config_name="My Gmail"
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        # Assert: Verify config was created
        assert config.id is not None
        assert config.user_id == user.id
        assert config.email_address == "user@example.com"
        assert config.imap_server == "imap.example.com"
        assert config.imap_port == 993
        assert config.use_ssl is True
        assert config.provider == "gmail"
        assert config.config_name == "My Gmail"
        assert config.is_active is True  # Default value
        assert config.is_verified is False  # Default value
        assert config.check_frequency == "hourly"  # Default value

    def test_email_config_defaults(self, db_session):
        """Test email configuration default values."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        config = EmailConfig(
            user_id=user.id,
            email_address="user@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        assert config.imap_port == 993  # Default
        assert config.use_ssl is True  # Default
        assert config.config_name == "默认邮箱"  # Default
        assert config.is_active is True  # Default
        assert config.is_verified is False  # Default
        assert config.check_frequency == "hourly"  # Default

    def test_email_config_timestamps(self, db_session):
        """Test email configuration timestamps."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        config = EmailConfig(
            user_id=user.id,
            email_address="user@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        assert config.created_at is not None
        assert config.updated_at is not None
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)

    def test_email_config_relationship_with_user(self, db_session):
        """Test relationship between EmailConfig and User."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        config = EmailConfig(
            user_id=user.id,
            email_address="user@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )
        db_session.add(config)
        db_session.commit()

        # Query through relationship
        db_session.refresh(user)
        # Note: Relationship will be added to User model later


class TestProcessedEmailModel:
    """Test ProcessedEmail model."""

    def test_create_processed_email(self, db_session):
        """Test creating a processed email record."""
        # Create user and email config
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        config = EmailConfig(
            user_id=user.id,
            email_address="user@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        # Create processed email record
        processed = ProcessedEmail(
            email_config_id=config.id,
            user_id=user.id,
            message_id="test-message-id-123",
            message_date=datetime.utcnow(),
            platform="alipay",
            attachment_name="alipay_bill.csv",
            status="success"
        )
        db_session.add(processed)
        db_session.commit()
        db_session.refresh(processed)

        assert processed.id is not None
        assert processed.email_config_id == config.id
        assert processed.user_id == user.id
        assert processed.message_id == "test-message-id-123"
        assert processed.platform == "alipay"
        assert processed.attachment_name == "alipay_bill.csv"
        assert processed.status == "success"
        assert processed.error_message is None
        assert processed.import_history_id is None

    def test_processed_email_with_error(self, db_session):
        """Test processed email record with error."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        config = EmailConfig(
            user_id=user.id,
            email_address="user@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        processed = ProcessedEmail(
            email_config_id=config.id,
            user_id=user.id,
            message_id="error-message-id",
            status="failed",
            error_message="Failed to parse email attachment"
        )
        db_session.add(processed)
        db_session.commit()
        db_session.refresh(processed)

        assert processed.status == "failed"
        assert "Failed to parse" in processed.error_message
        assert processed.platform is None
        assert processed.attachment_name is None

    def test_processed_email_unique_message_id_per_config(self, db_session):
        """Test that message_id must be unique per email config."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        config = EmailConfig(
            user_id=user.id,
            email_address="user@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        # Create first processed email
        processed1 = ProcessedEmail(
            email_config_id=config.id,
            user_id=user.id,
            message_id="duplicate-id",
            status="success"
        )
        db_session.add(processed1)
        db_session.commit()

        # Try to create duplicate - should raise error
        processed2 = ProcessedEmail(
            email_config_id=config.id,
            user_id=user.id,
            message_id="duplicate-id",  # Same message_id
            status="success"
        )
        db_session.add(processed2)

        with pytest.raises(Exception):  # IntegrityError expected
            db_session.commit()

    def test_processed_email_timestamp(self, db_session):
        """Test processed email timestamp."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        config = EmailConfig(
            user_id=user.id,
            email_address="user@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        processed = ProcessedEmail(
            email_config_id=config.id,
            user_id=user.id,
            message_id="test-id",
            status="success"
        )
        db_session.add(processed)
        db_session.commit()
        db_session.refresh(processed)

        assert processed.processed_at is not None
        assert isinstance(processed.processed_at, datetime)


@pytest.fixture
def db_session():
    """Create a test database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.services.database import Base

    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
