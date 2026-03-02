"""Password encryption utilities.

This module provides password encryption and decryption functionality using
Fernet symmetric encryption (AES-128-CBC/HMAC-SHA256).
"""

import os
import base64
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class PasswordEncryption:
    """Password encryption utility using Fernet symmetric encryption.

    This class provides secure password encryption using the Fernet algorithm
    (AES-128-CBC with HMAC-SHA256 for authentication). The encryption key is
    derived from a master key using PBKDF2 with SHA256.

    Usage:
        crypto = PasswordEncryption()
        encrypted = crypto.encrypt("my_password")
        decrypted = crypto.decrypt(encrypted)
    """

    def __init__(self, master_key: Optional[str] = None):
        """Initialize the password encryption utility.

        Args:
            master_key: The master encryption key. If None, reads from the
                PASSWORD_ENCRYPTION_KEY environment variable.

        Raises:
            ValueError: If no master key is provided or found in environment.
        """
        self.master_key = master_key or os.getenv("PASSWORD_ENCRYPTION_KEY")

        if not self.master_key:
            raise ValueError("PASSWORD_ENCRYPTION_KEY not set")

        # Derive Fernet key from master key using PBKDF2
        # This provides key separation and adds computational cost to brute force
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # Fernet requires 32-byte key
            salt=b'notion_bill_importer',  # Application-specific salt
            iterations=100000,  # High iteration count for security
        )

        # Derive key and create Fernet cipher
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        self.cipher = Fernet(key)

    def encrypt(self, password: str) -> str:
        """Encrypt a password.

        Args:
            password: The plaintext password to encrypt.

        Returns:
            The encrypted password as a URL-safe base64 encoded string.

        Raises:
            Exception: If encryption fails.
        """
        try:
            # Encrypt password
            encrypted_bytes = self.cipher.encrypt(password.encode('utf-8'))

            # Return as base64 string
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')

        except Exception as e:
            raise ValueError(f"Failed to encrypt password: {e}")

    def decrypt(self, encrypted_password: str) -> str:
        """Decrypt an encrypted password.

        Args:
            encrypted_password: The encrypted password string returned by encrypt().

        Returns:
            The decrypted plaintext password.

        Raises:
            InvalidToken: If the encrypted data is invalid or tampered with.
            ValueError: If decryption fails for other reasons.
        """
        try:
            # Decode base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode('utf-8'))

            # Decrypt password
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)

            # Return as string
            return decrypted_bytes.decode('utf-8')

        except InvalidToken as e:
            raise InvalidToken("Invalid encrypted data or wrong encryption key") from e

        except Exception as e:
            raise ValueError(f"Failed to decrypt password: {e}")

    def rotate_key(self, old_encrypted: str, new_master_key: str) -> str:
        """Re-encrypt password with a new master key.

        This method decrypts the password using the current master key and
        re-encrypts it with a new master key.

        Args:
            old_encrypted: Password encrypted with the current master key.
            new_master_key: The new master key to use for encryption.

        Returns:
            The password re-encrypted with the new master key.

        Raises:
            InvalidToken: If the old encrypted data is invalid.
            ValueError: If re-encryption fails.
        """
        # Decrypt with current key
        decrypted = self.decrypt(old_encrypted)

        # Create new cipher with new key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'notion_bill_importer',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(new_master_key.encode()))
        new_cipher = Fernet(key)

        # Re-encrypt with new key
        encrypted_bytes = new_cipher.encrypt(decrypted.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
