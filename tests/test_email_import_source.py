"""Tests for EmailImportSource.

Tests the email-based bill import source functionality.
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, Mock, patch
from sqlalchemy.orm import Session


class TestEmailImportSource:
    """Test EmailImportSource class."""

    def test_initialization_with_config_id(self):
        """Test initialization with specific config ID."""
        from src.services.email_import_source import EmailImportSource

        db_mock = MagicMock()
        source = EmailImportSource(user_id=1, db=db_mock, config_id=5)

        assert source.user_id == 1
        assert source.config_id == 5

    def test_initialization_without_config_id(self):
        """Test initialization without specific config ID."""
        from src.services.email_import_source import EmailImportSource

        db_mock = MagicMock()
        source = EmailImportSource(user_id=1, db=db_mock)

        assert source.user_id == 1
        assert source.config_id is None

    def test_get_source_type(self):
        """Test get_source_type returns 'email'."""
        from src.services.email_import_source import EmailImportSource

        db_mock = MagicMock()
        source = EmailImportSource(user_id=1, db=db_mock)

        assert source.get_source_type() == "email"

    def test_fetch_bills_with_config_id(self):
        """Test fetching bills with specific config ID."""
        from src.services.email_import_source import EmailImportSource
        from src.models import EmailConfig

        # Mock database
        db_mock = MagicMock(spec=Session)
        query_mock = MagicMock()
        config = EmailConfig(
            id=5,
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted",
            imap_server="imap.example.com"
        )
        query_mock.filter.return_value.first.return_value = config
        db_mock.query.return_value = query_mock

        source = EmailImportSource(user_id=1, db=db_mock, config_id=5)

        with patch.object(source, '_fetch_from_config', return_value=[]) as mock_fetch:
            bills = source.fetch_bills()

            # Verify config was fetched
            db_mock.query.assert_called_once_with(EmailConfig)
            mock_fetch.assert_called_once()

    def test_fetch_bills_without_config_id(self):
        """Test fetching bills from all active configs."""
        from src.services.email_import_source import EmailImportSource
        from src.models import EmailConfig

        # Mock database
        db_mock = MagicMock(spec=Session)
        query_mock = MagicMock()
        configs = [
            EmailConfig(id=1, user_id=1, email_address="a@example.com", password_encrypted="x", imap_server="imap.a.com"),
            EmailConfig(id=2, user_id=1, email_address="b@example.com", password_encrypted="y", imap_server="imap.b.com"),
        ]
        query_mock.filter.return_value.all.return_value = configs
        db_mock.query.return_value = query_mock

        source = EmailImportSource(user_id=1, db=db_mock)

        with patch.object(source, '_fetch_from_config', return_value=[]) as mock_fetch:
            bills = source.fetch_bills()

            # Should call _fetch_from_config for each config
            assert mock_fetch.call_count == 2

    def test_is_processed_returns_true_for_processed_email(self):
        """Test _is_processed returns True for processed emails."""
        from src.services.email_import_source import EmailImportSource
        from src.models import ProcessedEmail

        db_mock = MagicMock(spec=Session)
        query_mock = MagicMock()
        processed = ProcessedEmail(id=1, email_config_id=5, user_id=1, message_id="msg123", status="success")
        query_mock.filter.return_value.first.return_value = processed
        db_mock.query.return_value = query_mock

        source = EmailImportSource(user_id=1, db=db_mock)
        result = source._is_processed("msg123", 5)

        assert result is True

    def test_is_processed_returns_false_for_unprocessed_email(self):
        """Test _is_processed returns False for unprocessed emails."""
        from src.services.email_import_source import EmailImportSource

        db_mock = MagicMock(spec=Session)
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db_mock.query.return_value = query_mock

        source = EmailImportSource(user_id=1, db=db_mock)
        result = source._is_processed("msg123", 5)

        assert result is False

    def test_download_attachment(self):
        """Test downloading attachment to temp file."""
        from src.services.email_import_source import EmailImportSource

        db_mock = MagicMock(spec=Session)
        source = EmailImportSource(user_id=1, db=db_mock)

        attachment = {
            'filename': 'bill.csv',
            'payload': b'csv,data,here'
        }

        temp_file = source._download_attachment(attachment)

        assert temp_file is not None
        assert os.path.exists(temp_file)

        # Verify content
        with open(temp_file, 'rb') as f:
            content = f.read()
            assert content == b'csv,data,here'

        # Cleanup
        os.unlink(temp_file)

    def test_fetch_from_config_integration(self):
        """Test _fetch_from_config with mocked email service."""
        from src.services.email_import_source import EmailImportSource
        from src.models import EmailConfig
        from src.services.email_parse_service import EmailParseService

        config = EmailConfig(
            id=5,
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted",
            imap_server="imap.example.com"
        )

        db_mock = MagicMock(spec=Session)
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db_mock.query.return_value = query_mock

        source = EmailImportSource(user_id=1, db=db_mock)

        # Mock email service
        with patch('src.services.email_import_source.EmailService') as mock_email_service_class:
            mock_mailbox = MagicMock()
            mock_email_service = MagicMock()
            mock_email_service_class.return_value = mock_email_service
            mock_email_service.connect.return_value = mock_mailbox

            # Mock emails
            mock_msg = MagicMock()
            mock_msg.uid = 'msg123'
            mock_msg.from_ = 'alipay@alipay.com'
            mock_msg.subject = 'Bill'
            mock_msg.date_str = '2024-01-01'

            # Mock attachments
            mock_att = MagicMock()
            mock_att.filename = 'bill.csv'
            mock_att.payload = b'csv,data'
            mock_att.content_type = 'text/csv'

            mock_msg.attachments = [mock_att]
            mock_mailbox.fetch.return_value = iter([mock_msg])

            # Mock attachment download
            with patch.object(source, '_download_attachment', return_value='/tmp/bill.csv'):
                bills = source._fetch_from_config(config)

                # Should have one bill
                assert len(bills) == 1
                assert bills[0]['file_path'] == '/tmp/bill.csv'
                assert bills[0]['platform'] == 'alipay'

    def test_fetch_from_config_skips_processed_emails(self):
        """Test that processed emails are skipped."""
        from src.services.email_import_source import EmailImportSource
        from src.models import EmailConfig

        config = EmailConfig(
            id=5,
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted",
            imap_server="imap.example.com"
        )

        db_mock = MagicMock(spec=Session)
        source = EmailImportSource(user_id=1, db=db_mock)

        # Mock _is_processed to return True
        with patch.object(source, '_is_processed', return_value=True):
            with patch('src.services.email_import_source.EmailService') as mock_email_service_class:
                mock_mailbox = MagicMock()
                mock_email_service = MagicMock()
                mock_email_service_class.return_value = mock_email_service
                mock_email_service.connect.return_value = mock_mailbox

                mock_msg = MagicMock()
                mock_msg.uid = 'msg123'
                mock_mailbox.fetch.return_value = iter([mock_msg])

                bills = source._fetch_from_config(config)

                # Should skip the email
                assert len(bills) == 0

    def test_fetch_from_config_skips_non_bill_emails(self):
        """Test that non-bill emails are skipped."""
        from src.services.email_import_source import EmailImportSource
        from src.models import EmailConfig

        config = EmailConfig(
            id=5,
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted",
            imap_server="imap.example.com"
        )

        db_mock = MagicMock(spec=Session)
        source = EmailImportSource(user_id=1, db=db_mock)

        with patch('src.services.email_import_source.EmailService') as mock_email_service_class:
            mock_mailbox = MagicMock()
            mock_email_service = MagicMock()
            mock_email_service_class.return_value = mock_email_service
            mock_email_service.connect.return_value = mock_mailbox

            # Mock non-bill email
            mock_msg = MagicMock()
            mock_msg.uid = 'msg123'
            mock_msg.from_ = 'unknown@example.com'
            mock_mailbox.fetch.return_value = iter([mock_msg])

            with patch('src.services.email_import_source.EmailParseService.is_bill_email', return_value=None):
                bills = source._fetch_from_config(config)

                # Should skip the email
                assert len(bills) == 0

    def test_fetch_from_config_disconnects_mailbox(self):
        """Test that mailbox is properly disconnected."""
        from src.services.email_import_source import EmailImportSource
        from src.models import EmailConfig

        config = EmailConfig(
            id=5,
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted",
            imap_server="imap.example.com"
        )

        db_mock = MagicMock(spec=Session)
        source = EmailImportSource(user_id=1, db=db_mock)

        with patch('src.services.email_import_source.EmailService') as mock_email_service_class:
            mock_mailbox = MagicMock()
            mock_email_service = MagicMock()
            mock_email_service_class.return_value = mock_email_service
            mock_email_service.connect.return_value = mock_mailbox
            mock_mailbox.fetch.return_value = iter([])

            bills = source._fetch_from_config(config)

            # Verify disconnect was called
            mock_email_service.disconnect.assert_called_once_with(mock_mailbox)
