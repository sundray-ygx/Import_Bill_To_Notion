"""Tests for CryptoService (password encryption).

Tests the password encryption and decryption functionality.
"""

import pytest
import os
from unittest.mock import patch


class TestPasswordEncryption:
    """Test PasswordEncryption class."""

    def test_encrypt_decrypt_password(self):
        """Test that password can be encrypted and decrypted."""
        from src.utils.crypto import PasswordEncryption

        # Create encryption service with test key
        with patch.dict(os.environ, {'PASSWORD_ENCRYPTION_KEY': 'test-master-key-32-bytes-long'}):
            crypto = PasswordEncryption()

            # Test password
            password = "my_email_password_123"

            # Encrypt
            encrypted = crypto.encrypt(password)

            # Verify encrypted is different from original
            assert encrypted != password
            assert len(encrypted) > 0

            # Decrypt
            decrypted = crypto.decrypt(encrypted)

            # Verify decrypted matches original
            assert decrypted == password

    def test_encrypt_produces_different_results(self):
        """Test that encrypting the same password twice produces different results."""
        from src.utils.crypto import PasswordEncryption

        with patch.dict(os.environ, {'PASSWORD_ENCRYPTION_KEY': 'test-master-key-32-bytes-long'}):
            crypto = PasswordEncryption()

            password = "test_password"

            encrypted1 = crypto.encrypt(password)
            encrypted2 = crypto.encrypt(password)

            # Fernet uses a random IV, so encrypted results should differ
            assert encrypted1 != encrypted2

            # But both should decrypt to the same password
            assert crypto.decrypt(encrypted1) == password
            assert crypto.decrypt(encrypted2) == password

    def test_decrypt_with_invalid_data_raises_error(self):
        """Test that decrypting invalid data raises an error."""
        from src.utils.crypto import PasswordEncryption

        with patch.dict(os.environ, {'PASSWORD_ENCRYPTION_KEY': 'test-master-key-32-bytes-long'}):
            crypto = PasswordEncryption()

            with pytest.raises(Exception):  # InvalidToken or similar
                crypto.decrypt("invalid_encrypted_data")

    def test_encryption_requires_master_key(self):
        """Test that PasswordEncryption requires a master key."""
        from src.utils.crypto import PasswordEncryption

        # Remove the key from environment
        with patch.dict(os.environ, {}, clear=False):
            # Remove if exists
            if 'PASSWORD_ENCRYPTION_KEY' in os.environ:
                del os.environ['PASSWORD_ENCRYPTION_KEY']

            # Should raise ValueError
            with pytest.raises(ValueError, match="PASSWORD_ENCRYPTION_KEY not set"):
                PasswordEncryption()

    def test_encrypt_empty_password(self):
        """Test that empty password can be encrypted and decrypted."""
        from src.utils.crypto import PasswordEncryption

        with patch.dict(os.environ, {'PASSWORD_ENCRYPTION_KEY': 'test-master-key-32-bytes-long'}):
            crypto = PasswordEncryption()

            encrypted = crypto.encrypt("")
            decrypted = crypto.decrypt(encrypted)

            assert decrypted == ""

    def test_encrypt_special_characters(self):
        """Test that password with special characters can be encrypted."""
        from src.utils.crypto import PasswordEncryption

        with patch.dict(os.environ, {'PASSWORD_ENCRYPTION_KEY': 'test-master-key-32-bytes-long'}):
            crypto = PasswordEncryption()

            password = "p@ssw0rd!#$%^&*()_+-=[]{}|;':\",./<>?"

            encrypted = crypto.encrypt(password)
            decrypted = crypto.decrypt(encrypted)

            assert decrypted == password

    def test_encrypt_unicode_characters(self):
        """Test that password with unicode characters can be encrypted."""
        from src.utils.crypto import PasswordEncryption

        with patch.dict(os.environ, {'PASSWORD_ENCRYPTION_KEY': 'test-master-key-32-bytes-long'}):
            crypto = PasswordEncryption()

            password = "密码123测试test"

            encrypted = crypto.encrypt(password)
            decrypted = crypto.decrypt(encrypted)

            assert decrypted == password

    def test_different_keys_produce_different_results(self):
        """Test that different keys produce different encrypted results."""
        from src.utils.crypto import PasswordEncryption

        password = "test_password"

        with patch.dict(os.environ, {'PASSWORD_ENCRYPTION_KEY': 'key-one-32-bytes-long-key-one'}):
            crypto1 = PasswordEncryption()
            encrypted1 = crypto1.encrypt(password)

        with patch.dict(os.environ, {'PASSWORD_ENCRYPTION_KEY': 'key-two-32-bytes-long-key-two'}):
            crypto2 = PasswordEncryption()
            encrypted2 = crypto2.encrypt(password)

        # Encrypted results should be different
        assert encrypted1 != encrypted2

        # Each should decrypt with its own key
        with patch.dict(os.environ, {'PASSWORD_ENCRYPTION_KEY': 'key-one-32-bytes-long-key-one'}):
            crypto1 = PasswordEncryption()
            assert crypto1.decrypt(encrypted1) == password

        with patch.dict(os.environ, {'PASSWORD_ENCRYPTION_KEY': 'key-two-32-bytes-long-key-two'}):
            crypto2 = PasswordEncryption()
            assert crypto2.decrypt(encrypted2) == password
