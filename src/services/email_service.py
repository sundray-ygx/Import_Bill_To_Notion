"""Email service for IMAP connection management.

This module provides the EmailService class for connecting to email servers
via IMAP, fetching emails, and managing email connections.
"""

import logging
from typing import List, Optional, Any
from contextlib import contextmanager

from imap_tools import MailBox
MailboxType = MailBox

from src.models import EmailConfig
from src.utils.crypto import PasswordEncryption


logger = logging.getLogger(__name__)


class EmailService:
    """Service for managing IMAP email connections.

    This service provides methods to connect to IMAP servers, verify
    connections, fetch emails, and properly manage connection lifecycle.

    Usage:
        service = EmailService()
        mailbox = service.connect(config)
        emails = list(mailbox.fetch(limit=10))
        service.disconnect(mailbox)
    """

    def __init__(self):
        """Initialize the email service."""
        self._crypto = None

    @property
    def _crypto_service(self) -> PasswordEncryption:
        """Lazy initialization of crypto service.

        Returns:
            PasswordEncryption instance
        """
        if self._crypto is None:
            self._crypto = PasswordEncryption()
        return self._crypto

    def connect(self, config: EmailConfig) -> MailboxType:
        """Connect to an IMAP email server.

        Args:
            config: EmailConfig containing connection details

        Returns:
            Mailbox instance from imap_tools

        Raises:
            ConnectionError: If connection fails
            ValueError: If credentials are invalid

        Example:
            >>> service = EmailService()
            >>> mailbox = service.connect(email_config)
            >>> for msg in mailbox.fetch(limit=10):
            ...     print(msg.subject)
        """
        # Decrypt password
        try:
            password = self._crypto_service.decrypt(config.password_encrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt password for {self._mask_email(config.email_address)}")
            raise ValueError(f"Failed to decrypt password: {e}")

        # Connect to IMAP server
        logger.info(f"Connecting to IMAP server: {config.imap_server}:{config.imap_port}")

        try:
            mailbox = MailBox(
                config.imap_server,
                config.imap_port,
                ssl=config.use_ssl
            )

            # Login
            mailbox.login(config.email_address, password)
            logger.info(f"Successfully connected as {self._mask_email(config.email_address)}")

            return mailbox

        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            raise ConnectionError(f"Failed to connect to email server: {e}")

    def verify_connection(self, config: EmailConfig) -> bool:
        """Verify email server connection without keeping connection open.

        Args:
            config: EmailConfig containing connection details

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self._connect_context(config) as mailbox:
                # Connection successful if we get here
                return True

        except (ConnectionError, ValueError, Exception) as e:
            logger.warning(f"Connection verification failed for {self._mask_email(config.email_address)}: {e}")
            return False

    def fetch_emails(
        self,
        config: EmailConfig,
        folder: str = 'INBOX',
        limit: int = 50,
        criteria: Optional[str] = None
    ) -> List[Any]:
        """Fetch emails from the server.

        Args:
            config: EmailConfig containing connection details
            folder: IMAP folder to fetch from (default: INBOX)
            limit: Maximum number of emails to fetch
            criteria: IMAP search criteria (optional)

        Returns:
            List of email message objects

        Raises:
            ConnectionError: If connection or fetch fails
        """
        try:
            with self._connect_context(config) as mailbox:
                # Set folder
                mailbox.folder.set(folder)

                # Build fetch criteria
                fetch_kwargs = {'limit': limit}
                if criteria:
                    fetch_kwargs['criteria'] = criteria

                # Fetch emails
                logger.info(f"Fetching up to {limit} emails from {folder}")
                emails = list(mailbox.fetch(**fetch_kwargs))

                logger.info(f"Fetched {len(emails)} emails")
                return emails

        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            raise ConnectionError(f"Failed to fetch emails: {e}")

    def disconnect(self, mailbox: MailboxType) -> None:
        """Properly disconnect from IMAP server.

        Args:
            mailbox: Mailbox instance to disconnect
        """
        try:
            if mailbox:
                mailbox.logout()
                logger.debug("Disconnected from IMAP server")
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")

    @contextmanager
    def _connect_context(self, config: EmailConfig):
        """Context manager for email connections.

        Args:
            config: EmailConfig containing connection details

        Yields:
            Mailbox instance

        Raises:
            ConnectionError: If connection fails
        """
        mailbox = None
        try:
            mailbox = self.connect(config)
            yield mailbox
        finally:
            if mailbox:
                self.disconnect(mailbox)

    def _mask_email(self, email: str) -> str:
        """Mask email address for logging.

        Args:
            email: Email address to mask

        Returns:
            Masked email address (e.g., "u***@example.com")
        """
        try:
            local, domain = email.split('@', 1)
            if len(local) > 0:
                masked_local = local[0] + '***'
            else:
                masked_local = '***'
            return f"{masked_local}@{domain}"
        except Exception:
            return "***@***.***"

    def _decrypt_password(self, encrypted: str) -> str:
        """Decrypt encrypted password.

        Args:
            encrypted: Encrypted password string

        Returns:
            Decrypted password

        Raises:
            ValueError: If decryption fails
        """
        return self._crypto_service.decrypt(encrypted)


class EmailConnectionError(Exception):
    """Exception raised for email connection errors."""

    pass


class EmailAuthenticationError(Exception):
    """Exception raised for email authentication errors."""

    pass
