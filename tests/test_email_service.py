"""Tests for EmailService.

Tests the IMAP connection management and email operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestEmailService:
    """Test EmailService class."""

    def test_email_service_initialization(self):
        """Test EmailService initialization."""
        from src.services.email_service import EmailService

        service = EmailService()
        assert service is not None

    def test_connect_to_email_server(self):
        """Test connecting to email server."""
        from src.services.email_service import EmailService
        from src.models import EmailConfig

        config = EmailConfig(
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com",
            imap_port=993,
            use_ssl=True
        )

        with patch('src.services.email_service.MailBox') as mock_mailbox_class, \
             patch('src.services.email_service.PasswordEncryption') as mock_crypto_class:
            mock_mailbox = MagicMock()
            mock_mailbox_class.return_value = mock_mailbox
            mock_crypto = MagicMock()
            mock_crypto.decrypt.return_value = 'decrypted_password'
            mock_crypto_class.return_value = mock_crypto

            service = EmailService()
            mailbox = service.connect(config)

            # Verify MailBox was called with correct parameters
            mock_mailbox_class.assert_called_once_with('imap.example.com', 993, ssl=True)
            # Verify login was called
            mock_mailbox.login.assert_called_once_with('test@example.com', 'decrypted_password')

    def test_verify_connection_success(self):
        """Test successful connection verification."""
        from src.services.email_service import EmailService
        from src.models import EmailConfig

        config = EmailConfig(
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )

        with patch('src.services.email_service.MailBox') as mock_mailbox_class, \
             patch('src.services.email_service.PasswordEncryption') as mock_crypto_class:
            mock_mailbox = MagicMock()
            mock_mailbox_class.return_value = mock_mailbox
            mock_crypto = MagicMock()
            mock_crypto.decrypt.return_value = 'decrypted_password'
            mock_crypto_class.return_value = mock_crypto

            service = EmailService()
            result = service.verify_connection(config)

            assert result is True
            mock_mailbox.login.assert_called_once()
            mock_mailbox.logout.assert_called_once()

    def test_verify_connection_failure(self):
        """Test failed connection verification."""
        from src.services.email_service import EmailService
        from src.models import EmailConfig

        config = EmailConfig(
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )

        with patch('src.services.email_service.MailBox') as mock_mailbox_class, \
             patch('src.services.email_service.PasswordEncryption') as mock_crypto_class:
            mock_mailbox = MagicMock()
            mock_mailbox.login.side_effect = Exception("Authentication failed")
            mock_mailbox_class.return_value = mock_mailbox
            mock_crypto = MagicMock()
            mock_crypto.decrypt.return_value = 'decrypted_password'
            mock_crypto_class.return_value = mock_crypto

            service = EmailService()
            result = service.verify_connection(config)

            assert result is False

    def test_fetch_recent_emails(self):
        """Test fetching recent emails."""
        from src.services.email_service import EmailService
        from src.models import EmailConfig

        config = EmailConfig(
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )

        with patch('src.services.email_service.MailBox') as mock_mailbox_class, \
             patch('src.services.email_service.PasswordEncryption') as mock_crypto_class:
            mock_mailbox = MagicMock()
            mock_mailbox_class.return_value = mock_mailbox
            mock_emails = [
                MagicMock(uid='msg1', subject='Test 1', from_='sender1@example.com'),
                MagicMock(uid='msg2', subject='Test 2', from_='sender2@example.com'),
            ]
            mock_mailbox.fetch.return_value = iter(mock_emails)
            mock_crypto = MagicMock()
            mock_crypto.decrypt.return_value = 'decrypted_password'
            mock_crypto_class.return_value = mock_crypto

            service = EmailService()
            emails = service.fetch_emails(config, limit=10)

            assert len(emails) == 2
            assert emails[0].uid == 'msg1'
            assert emails[1].uid == 'msg2'

    def test_disconnect(self):
        """Test disconnecting from email server."""
        from src.services.email_service import EmailService

        service = EmailService()
        mock_mailbox = MagicMock()
        service.disconnect(mock_mailbox)
        mock_mailbox.logout.assert_called_once()

    def test_mask_email_address_in_logs(self):
        """Test that email addresses are masked in logs."""
        from src.services.email_service import EmailService

        service = EmailService()
        email = "user@example.com"
        masked = service._mask_email(email)

        # Should mask the local part
        assert "user" not in masked
        assert "@" in masked
        assert "example.com" in masked

    def test_connection_timeout_handling(self):
        """Test handling of connection timeout."""
        from src.services.email_service import EmailService
        from src.models import EmailConfig

        config = EmailConfig(
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )

        with patch('src.services.email_service.MailBox') as mock_mailbox_class, \
             patch('src.services.email_service.PasswordEncryption') as mock_crypto_class:
            mock_mailbox = MagicMock()
            mock_mailbox.login.side_effect = TimeoutError("Connection timed out")
            mock_mailbox_class.return_value = mock_mailbox
            mock_crypto = MagicMock()
            mock_crypto.decrypt.return_value = 'decrypted_password'
            mock_crypto_class.return_value = mock_crypto

            service = EmailService()
            result = service.verify_connection(config)

            assert result is False

    def test_fetch_emails_with_folder(self):
        """Test fetching emails from specific folder."""
        from src.services.email_service import EmailService
        from src.models import EmailConfig

        config = EmailConfig(
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted_password",
            imap_server="imap.example.com"
        )

        with patch('src.services.email_service.MailBox') as mock_mailbox_class, \
             patch('src.services.email_service.PasswordEncryption') as mock_crypto_class:
            mock_mailbox = MagicMock()
            mock_mailbox.fetch.return_value = iter([])
            mock_mailbox_class.return_value = mock_mailbox
            mock_crypto = MagicMock()
            mock_crypto.decrypt.return_value = 'decrypted_password'
            mock_crypto_class.return_value = mock_crypto

            service = EmailService()
            service.fetch_emails(config, folder='INBOX', limit=10)

            # Verify folder was set
            mock_mailbox.folder.set.assert_called_once_with('INBOX')

    def test_decrypt_password(self):
        """Test password decryption."""
        from src.services.email_service import EmailService

        with patch('src.services.email_service.PasswordEncryption') as mock_crypto_class:
            mock_crypto = MagicMock()
            mock_crypto.decrypt.return_value = 'decrypted_password'
            mock_crypto_class.return_value = mock_crypto

            service = EmailService()
            result = service._decrypt_password('encrypted')

            assert result == 'decrypted_password'
            mock_crypto.decrypt.assert_called_once_with('encrypted')
