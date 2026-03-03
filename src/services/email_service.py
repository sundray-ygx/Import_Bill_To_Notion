"""Email service for IMAP connection management.

This module provides the EmailService class for connecting to email servers
via IMAP, fetching emails, and managing email connections.
"""

import logging
import imaplib
import sys
from typing import List, Optional, Any, Union
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

        For 163.com and other email providers that require IMAP ID (RFC 2971),
        this method sends client identification before login.

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
            # Create native imaplib connection for IMAP ID support
            # This is required for 163.com and other providers enforcing RFC 2971
            if config.imap_port == 993:
                client = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
            else:
                client = imaplib.IMAP4(config.imap_server, config.imap_port)
                # Try STARTTLS for non-SSL connections
                try:
                    client.starttls()
                except Exception as e:
                    logger.debug(f"STARTTLS not available: {e}")

            # Send IMAP ID command BEFORE login (required by 163.com)
            self._send_imap_id(client)

            # Login using native imaplib
            try:
                client.login(config.email_address, password)
                logger.info(f"Successfully logged in as {self._mask_email(config.email_address)}")
            except Exception as e:
                logger.error(f"Login failed: {e}")
                client.logout()
                raise ValueError(f"Authentication failed: {e}")

            # Wrap native client in imap-tools MailBox for compatibility
            # We need to manually set the client since we already connected
            mailbox = MailBox(config.imap_server, config.imap_port)
            mailbox.client = client
            # Mark as already connected to prevent reconnection
            mailbox.login = lambda *args, **kwargs: None  # No-op: already logged in

            logger.info(f"Successfully connected as {self._mask_email(config.email_address)}")

            return mailbox

        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            raise ConnectionError(f"Failed to connect to email server: {e}")

    def _send_imap_id(self, client: imaplib.IMAP4) -> None:
        """Send IMAP ID command to identify client (RFC 2971).

        This is required by some email providers like 163.com to prevent
        "Unsafe Login" errors. The ID command must be sent BEFORE login.

        Args:
            client: imaplib IMAP4 client instance
        """
        try:
            # IMAP ID parameters per RFC 2971
            id_params = {
                "name": "NotionBillImporter",
                "version": "2.2.0",
                "vendor": "CustomClient",
                "support-email": "noreply@notionbillimporter.local",
                "os": "Python",
                "os-version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            }

            # Build ID command string
            # Format: ID ("name" "value" "name2" "value2" ...)
            id_args = []
            for key, value in id_params.items():
                # Escape quotes in values
                safe_value = value.replace('\\', '\\\\').replace('"', '\\"')
                id_args.append(f'"{key}"')
                id_args.append(f'"{safe_value}"')

            id_command_str = '(' + ' '.join(id_args) + ')'

            logger.debug(f"Sending IMAP ID: ID {id_command_str}")

            # Try ID() method first (Python 3.5+)
            try:
                result, data = client.ID(id_command_str)
                if result == 'OK':
                    logger.info("IMAP ID sent successfully")
                else:
                    logger.warning(f"IMAP ID command returned: {result} {data}")
            except AttributeError:
                # Fallback to xatom for older Python versions
                result, data = client.xatom('ID', id_command_str)
                if result == 'OK':
                    logger.info("IMAP ID sent successfully via xatom")
                else:
                    logger.warning(f"IMAP ID via xatom returned: {result} {data}")

        except Exception as e:
            # Don't fail the connection if ID fails, just log it
            # Some servers don't support ID or may reject it
            logger.debug(f"IMAP ID command failed (non-critical): {e}")

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
