"""Email import source module.

This module provides the EmailImportSource class for importing bills
from email attachments.
"""

import logging
import tempfile
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from src.services.import_source import ImportSource
from src.models import EmailConfig, ProcessedEmail
from src.services.email_service import EmailService
from src.services.email_parse_service import EmailParseService


logger = logging.getLogger(__name__)


class EmailImportSource(ImportSource):
    """Email-based bill import source.

    This source retrieves bill files from email attachments by:
    1. Connecting to configured IMAP email accounts
    2. Fetching recent emails
    3. Identifying bill emails from trusted senders
    4. Extracting bill file attachments (CSV, ZIP)
    5. Skipping already processed emails

    Usage:
        # Import from all active email configs
        source = EmailImportSource(user_id=1, db=session)
        bills = source.import_bills()

        # Import from specific config
        source = EmailImportSource(user_id=1, db=session, config_id=5)
        bills = source.import_bills()
    """

    def __init__(self, user_id: int, db: Session, config_id: Optional[int] = None):
        """Initialize the email import source.

        Args:
            user_id: The ID of the user importing bills
            db: SQLAlchemy database session
            config_id: Specific email config ID to import from (if None, imports from all active configs)
        """
        super().__init__(user_id, db)
        self.config_id = config_id

    def fetch_bills(self) -> List[Dict[str, Any]]:
        """Fetch bill files from email accounts.

        Returns:
            A list of bill dictionaries, each containing:
            - file_path: Path to temporary bill file
            - platform: Platform identifier (alipay/wechat/unionpay)
            - metadata: Email metadata (message_id, from_addr, subject, etc.)

        Raises:
            ValueError: If no active email configs found
        """
        # Get email configs to fetch from
        configs = self._get_email_configs()

        if not configs:
            logger.warning(f"No active email configs found for user {self.user_id}")
            return []

        logger.info(f"Fetching bills from {len(configs)} email config(s)")

        all_bills = []

        # Fetch bills from each config
        for config in configs:
            try:
                config_bills = self._fetch_from_config(config)
                all_bills.extend(config_bills)
                logger.info(f"Fetched {len(config_bills)} bills from config {config.id}")
            except Exception as e:
                logger.error(f"Error fetching bills from config {config.id}: {e}")
                continue

        logger.info(f"Total bills fetched: {len(all_bills)}")
        return all_bills

    def _get_email_configs(self) -> List[EmailConfig]:
        """Get email configs for this user.

        Returns:
            List of EmailConfig objects
        """
        if self.config_id:
            # Fetch specific config
            config = self.db.query(EmailConfig).filter(
                EmailConfig.id == self.config_id,
                EmailConfig.user_id == self.user_id,
                EmailConfig.is_active == True
            ).first()

            return [config] if config else []

        else:
            # Fetch all active and verified configs
            configs = self.db.query(EmailConfig).filter(
                EmailConfig.user_id == self.user_id,
                EmailConfig.is_active == True,
                EmailConfig.is_verified == True
            ).all()

            return configs

    def _fetch_from_config(self, config: EmailConfig) -> List[Dict[str, Any]]:
        """Fetch bills from a single email config.

        Args:
            config: EmailConfig object

        Returns:
            List of bill dictionaries

        Raises:
            ConnectionError: If email connection fails
        """
        bills = []
        mailbox = None

        try:
            # Connect to email server
            email_service = EmailService()
            mailbox = email_service.connect(config)

            # Fetch recent emails (limit to 50)
            logger.debug(f"Fetching emails from {self._mask_email(config.email_address)}")
            emails = list(mailbox.fetch(limit=50))

            logger.debug(f"Fetched {len(emails)} emails")

            # Process each email
            for msg in emails:
                try:
                    # Check if already processed
                    if self._is_processed(msg.uid, config.id):
                        logger.debug(f"Email {msg.uid} already processed, skipping")
                        continue

                    # Check if it's a bill email
                    bill_info = EmailParseService.is_bill_email(msg)
                    if not bill_info:
                        continue

                    # Extract attachments
                    attachments = EmailParseService.extract_attachments(msg)
                    if not attachments:
                        logger.debug(f"Email {msg.uid} has no bill attachments, skipping")
                        continue

                    # Download each attachment
                    for att in attachments:
                        try:
                            temp_file = self._download_attachment(att)

                            bills.append({
                                'file_path': temp_file,
                                'platform': bill_info['platform'],
                                'metadata': {
                                    'message_id': msg.uid,
                                    'config_id': config.id,
                                    'from_addr': str(msg.from_),
                                    'subject': msg.subject,
                                    'date': msg.date_str,
                                    'attachment_name': att['filename']
                                }
                            })

                            logger.debug(f"Downloaded attachment: {att['filename']}")

                        except Exception as e:
                            logger.error(f"Error downloading attachment: {e}")
                            continue

                except Exception as e:
                    logger.error(f"Error processing email {msg.uid}: {e}")
                    continue

        finally:
            # Always disconnect
            if mailbox:
                email_service.disconnect(mailbox)

        return bills

    def _download_attachment(self, attachment: Dict[str, Any]) -> str:
        """Download attachment to temporary file.

        Args:
            attachment: Attachment dictionary with filename and payload

        Returns:
            Path to temporary file

        Raises:
            IOError: If file write fails
        """
        filename = attachment['filename']
        payload = attachment['payload']

        # Create temp file with appropriate suffix
        suffix = self._get_file_suffix(filename)

        with tempfile.NamedTemporaryFile(
            mode='wb',
            delete=False,
            suffix=suffix
        ) as f:
            f.write(payload)
            temp_path = f.name

        logger.debug(f"Created temp file: {temp_path}")
        return temp_path

    def _is_processed(self, message_id: str, config_id: int) -> bool:
        """Check if email has already been processed.

        Args:
            message_id: Email message UID
            config_id: Email config ID

        Returns:
            True if already processed, False otherwise
        """
        processed = self.db.query(ProcessedEmail).filter(
            ProcessedEmail.message_id == message_id,
            ProcessedEmail.email_config_id == config_id
        ).first()

        return processed is not None

    def _mask_email(self, email: str) -> str:
        """Mask email address for logging.

        Args:
            email: Email address to mask

        Returns:
            Masked email address
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

    def _get_file_suffix(self, filename: str) -> str:
        """Get file suffix from filename.

        Args:
            filename: Original filename

        Returns:
            File suffix with dot (e.g., '.csv')
        """
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[-1]
        return ''

    def get_source_type(self) -> str:
        """Return the source type identifier.

        Returns:
            String 'email'
        """
        return "email"
