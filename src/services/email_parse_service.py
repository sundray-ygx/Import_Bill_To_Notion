"""Email parsing service.

This module provides the EmailParseService class for identifying bill emails,
extracting passwords from email bodies, and extracting bill file attachments.
"""

import re
import logging
from typing import Optional, Dict, List, Any


logger = logging.getLogger(__name__)


class EmailParseService:
    """Service for parsing bill emails and extracting attachments.

    This service provides methods to:
    - Identify bill emails from trusted senders
    - Extract passwords from email bodies (for ZIP files)
    - Extract bill file attachments (CSV, ZIP)

    Usage:
        # Check if email is a bill email
        bill_info = EmailParseService.is_bill_email(message)

        # Extract password from email body
        password = EmailParseService.extract_password(email_body)

        # Extract bill file attachments
        attachments = EmailParseService.extract_attachments(message)
    """

    # Sender whitelist for bill emails
    # Format: platform -> list of trusted sender email addresses/patterns
    SENDERS_WHITELIST: Dict[str, List[str]] = {
        'alipay': [
            'alipay@alipay.com',
            'service@alipay.com',
            'notify@alipay.com',
        ],
        'wechat': [
            'weixinpay@wechat.com',
            'pay@wechat.com',
            'tenpay@wechat.com',
        ],
        'unionpay': [
            'unionpay@95516.com',
            'service@95516.com',
            'payment@95516.com',
        ],
    }

    # Regular expression patterns for extracting passwords from email bodies
    # These patterns match common password formats in Chinese and English
    PASSWORD_PATTERNS: List[str] = [
        r'密码[：:]\s*([A-Za-z0-9]{6,20})',  # Chinese: 密码: xxxxx
        r'解压密码[：:]\s*([A-Za-z0-9]{6,20})',  # Chinese: 解压密码: xxxxx
        r'password[：:]\s*([A-Za-z0-9]{6,20})',  # English: password: xxxxx
        r'提取码[：:]\s*([A-Za-z0-9]{4,10})',  # Chinese: 提取码: xxxx
        r'验证码[：:]\s*([A-Za-z0-9]{4,10})',  # Chinese: 验证码: xxxx
    ]

    @classmethod
    def is_bill_email(cls, msg: Any) -> Optional[Dict[str, str]]:
        """Check if an email is a bill email from a trusted sender.

        Args:
            msg: Email message object (from imap_tools)

        Returns:
            Dictionary with 'platform' key if bill email, None otherwise.
            Example: {'platform': 'alipay'}

        Raises:
            None: Returns None on any error or if not a bill email
        """
        try:
            # Get sender email address
            from_addr = msg.from_
            if not from_addr:
                logger.debug("Email has no sender")
                return None

            # Convert to lowercase for case-insensitive matching
            from_email = str(from_addr).lower()

            # Check against whitelist
            for platform, senders in cls.SENDERS_WHITELIST.items():
                for sender in senders:
                    if sender.lower() in from_email:
                        logger.debug(f"Identified {platform} bill email from {from_email}")
                        return {'platform': platform}

            logger.debug(f"Email from {from_email} not in whitelist")
            return None

        except Exception as e:
            logger.error(f"Error checking if email is bill email: {e}")
            return None

    @classmethod
    def extract_password(cls, email_body: str) -> Optional[str]:
        """Extract password from email body text.

        This method searches for common password patterns in the email body,
        such as "密码: abc123" or "password: xyz789".

        Args:
            email_body: Plain text or HTML content of the email

        Returns:
            Extracted password string, or None if not found

        Raises:
            None: Returns None on any error or if no password found
        """
        if not email_body:
            return None

        try:
            # Try each pattern
            for pattern in cls.PASSWORD_PATTERNS:
                match = re.search(pattern, email_body, re.IGNORECASE)
                if match:
                    password = match.group(1)
                    logger.debug(f"Found password using pattern: {pattern}")
                    return password

            logger.debug("No password found in email body")
            return None

        except Exception as e:
            logger.error(f"Error extracting password from email: {e}")
            return None

    @classmethod
    def extract_attachments(cls, msg: Any) -> List[Dict[str, Any]]:
        """Extract bill file attachments from email.

        This method filters attachments to only include CSV and ZIP files,
        which are the common formats for bill files.

        Args:
            msg: Email message object (from imap_tools)

        Returns:
            List of attachment dictionaries, each containing:
            - filename: Attachment filename
            - payload: Attachment binary data
            - content_type: MIME content type

        Raises:
            None: Returns empty list on any error
        """
        attachments = []

        try:
            if not hasattr(msg, 'attachments') or not msg.attachments:
                logger.debug("Email has no attachments")
                return []

            for att in msg.attachments:
                try:
                    # Get filename
                    filename = att.filename
                    if not filename:
                        logger.debug("Attachment has no filename, skipping")
                        continue

                    # Filter by file extension
                    filename_lower = filename.lower()
                    if not (filename_lower.endswith('.csv') or filename_lower.endswith('.zip')):
                        logger.debug(f"Skipping attachment {filename}: not CSV or ZIP")
                        continue

                    # Extract attachment data
                    attachments.append({
                        'filename': filename,
                        'payload': att.payload,
                        'content_type': att.content_type,
                    })
                    logger.debug(f"Extracted attachment: {filename}")

                except Exception as e:
                    logger.warning(f"Error processing attachment: {e}")
                    continue

            logger.info(f"Extracted {len(attachments)} bill file attachments")
            return attachments

        except Exception as e:
            logger.error(f"Error extracting attachments: {e}")
            return []

    @classmethod
    def get_platform_from_sender(cls, sender_email: str) -> Optional[str]:
        """Get payment platform from sender email address.

        Args:
            sender_email: Sender email address

        Returns:
            Platform name (alipay/wechat/unionpay) or None
        """
        if not sender_email:
            return None

        sender_lower = sender_email.lower()

        for platform, senders in cls.SENDERS_WHITELIST.items():
            for sender in senders:
                if sender.lower() in sender_lower:
                    return platform

        return None
