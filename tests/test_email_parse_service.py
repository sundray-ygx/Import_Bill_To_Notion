"""Tests for EmailParseService.

Tests the email parsing and attachment extraction functionality.
"""

import pytest
from unittest.mock import MagicMock
from typing import List, Dict, Optional


class TestEmailParseService:
    """Test EmailParseService class."""

    def test_is_bill_email_identifies_alipay(self):
        """Test identifying Alipay bill emails."""
        from src.services.email_parse_service import EmailParseService

        # Create mock email message
        msg = MagicMock()
        msg.from_ = 'alipay@alipay.com'

        result = EmailParseService.is_bill_email(msg)

        assert result is not None
        assert result['platform'] == 'alipay'

    def test_is_bill_email_identifies_wechat(self):
        """Test identifying WeChat bill emails."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        msg.from_ = 'weixinpay@wechat.com'

        result = EmailParseService.is_bill_email(msg)

        assert result is not None
        assert result['platform'] == 'wechat'

    def test_is_bill_email_identifies_unionpay(self):
        """Test identifying UnionPay bill emails."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        msg.from_ = 'unionpay@95516.com'

        result = EmailParseService.is_bill_email(msg)

        assert result is not None
        assert result['platform'] == 'unionpay'

    def test_is_bill_email_returns_none_for_unknown_sender(self):
        """Test that unknown senders return None."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        msg.from_ = 'unknown@example.com'

        result = EmailParseService.is_bill_email(msg)

        assert result is None

    def test_is_bill_email_returns_none_for_no_sender(self):
        """Test that emails without sender return None."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        msg.from_ = None

        result = EmailParseService.is_bill_email(msg)

        assert result is None

    def test_is_bill_email_case_insensitive(self):
        """Test that sender matching is case insensitive."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        msg.from_ = 'Alipay@Alipay.com'

        result = EmailParseService.is_bill_email(msg)

        assert result is not None
        assert result['platform'] == 'alipay'

    def test_extract_password_finds_chinese_pattern(self):
        """Test extracting password with Chinese pattern."""
        from src.services.email_parse_service import EmailParseService

        body = "您的账单文件已生成，密码：abc123，请查收。"

        result = EmailParseService.extract_password(body)

        assert result == 'abc123'

    def test_extract_password_finds_english_pattern(self):
        """Test extracting password with English pattern."""
        from src.services.email_parse_service import EmailParseService

        body = "Your bill is ready, password: xyz789, please check."

        result = EmailParseService.extract_password(body)

        assert result == 'xyz789'

    def test_extract_password_finds_unzip_pattern(self):
        """Test extracting unzip password."""
        from src.services.email_parse_service import EmailParseService

        body = "文件已压缩，解压密码：pass1234"

        result = EmailParseService.extract_password(body)

        assert result == 'pass1234'

    def test_extract_password_returns_none_if_not_found(self):
        """Test that None is returned when no password found."""
        from src.services.email_parse_service import EmailParseService

        body = "Your bill is ready, please check."

        result = EmailParseService.extract_password(body)

        assert result is None

    def test_extract_attachments_filters_csv_files(self):
        """Test that CSV files are extracted."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        att1 = MagicMock()
        att1.filename = 'bill.csv'
        att1.payload = b'csv data'
        att1.content_type = 'text/csv'

        msg.attachments = [att1]

        result = EmailParseService.extract_attachments(msg)

        assert len(result) == 1
        assert result[0]['filename'] == 'bill.csv'

    def test_extract_attachments_filters_zip_files(self):
        """Test that ZIP files are extracted."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        att1 = MagicMock()
        att1.filename = 'bill.zip'
        att1.payload = b'zip data'
        att1.content_type = 'application/zip'

        msg.attachments = [att1]

        result = EmailParseService.extract_attachments(msg)

        assert len(result) == 1
        assert result[0]['filename'] == 'bill.zip'

    def test_extract_attachments_rejects_other_files(self):
        """Test that non-CSV/ZIP files are rejected."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        att1 = MagicMock()
        att1.filename = 'image.jpg'
        att1.payload = b'jpg data'
        att1.content_type = 'image/jpeg'

        msg.attachments = [att1]

        result = EmailParseService.extract_attachments(msg)

        assert len(result) == 0

    def test_extract_attachments_handles_multiple_attachments(self):
        """Test handling multiple attachments."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        att1 = MagicMock()
        att1.filename = 'bill.csv'
        att1.payload = b'csv data'
        att1.content_type = 'text/csv'

        att2 = MagicMock()
        att2.filename = 'readme.txt'
        att2.payload = b'text data'
        att2.content_type = 'text/plain'

        att3 = MagicMock()
        att3.filename = 'data.zip'
        att3.payload = b'zip data'
        att3.content_type = 'application/zip'

        msg.attachments = [att1, att2, att3]

        result = EmailParseService.extract_attachments(msg)

        assert len(result) == 2
        filenames = [att['filename'] for att in result]
        assert 'bill.csv' in filenames
        assert 'data.zip' in filenames
        assert 'readme.txt' not in filenames

    def test_extract_attachments_handles_no_filename(self):
        """Test handling attachments without filename."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        att1 = MagicMock()
        att1.filename = None
        att1.payload = b'data'
        att1.content_type = 'text/csv'

        msg.attachments = [att1]

        result = EmailParseService.extract_attachments(msg)

        assert len(result) == 0

    def test_extract_attachments_returns_empty_list_for_no_attachments(self):
        """Test that empty list is returned when no attachments."""
        from src.services.email_parse_service import EmailParseService

        msg = MagicMock()
        msg.attachments = []

        result = EmailParseService.extract_attachments(msg)

        assert result == []

    def test_senders_whitelist_is_complete(self):
        """Test that senders whitelist contains all platforms."""
        from src.services.email_parse_service import EmailParseService

        assert 'alipay' in EmailParseService.SENDERS_WHITELIST
        assert 'wechat' in EmailParseService.SENDERS_WHITELIST
        assert 'unionpay' in EmailParseService.SENDERS_WHITELIST

    def test_password_patterns_are_defined(self):
        """Test that password patterns are defined."""
        from src.services.email_parse_service import EmailParseService

        assert len(EmailParseService.PASSWORD_PATTERNS) > 0
        # Check that patterns contain common password/verification code keywords
        keywords = ['密码', 'password', '提取码', '验证码']
        has_keyword = any(any(keyword in pattern.lower() for keyword in keywords)
                         for pattern in EmailParseService.PASSWORD_PATTERNS)
        assert has_keyword, "Password patterns should contain password-related keywords"
