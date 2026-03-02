"""Tests for email migration v3.

Tests the database migration that adds email configuration tables.
"""

import sqlite3
import tempfile
import os
from pathlib import Path


class TestEmailMigrationV3:
    """Test email database migration v3."""

    def setup_method(self):
        """Set up test database."""
        # Create temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')

        # Initialize basic schema (mimic v2 state)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                require_password_change BOOLEAN DEFAULT FALSE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                login_attempts INTEGER DEFAULT 0,
                locked_until DATETIME,
                session_timeout_minutes INTEGER DEFAULT 15 NOT NULL
            )
        """)

        # Create schema_version table and set to v2
        cursor.execute("""
            CREATE TABLE schema_version (
                version INTEGER PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("INSERT INTO schema_version (version) VALUES (2)")

        conn.commit()
        conn.close()

    def teardown_method(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_migration_v3_creates_email_configs_table(self):
        """Test that migration v3 creates user_email_configs table."""
        # Arrange: Get migration function
        from migrate_database import migrate_to_v3

        # Act: Run migration
        migrate_to_v3(self.db_path)

        # Assert: Check table exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_email_configs'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "user_email_configs table should be created"

    def test_migration_v3_email_configs_has_correct_columns(self):
        """Test that user_email_configs table has all required columns."""
        from migrate_database import migrate_to_v3

        migrate_to_v3(self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(user_email_configs)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        conn.close()

        # Check required columns
        required_columns = {
            'id': 'INTEGER',
            'user_id': 'INTEGER',
            'email_address': 'VARCHAR(255)',
            'password_encrypted': 'VARCHAR(500)',
            'imap_server': 'VARCHAR(255)',
            'imap_port': 'INTEGER',
            'use_ssl': 'BOOLEAN',
            'provider': 'VARCHAR(50)',
            'config_name': 'VARCHAR(100)',
            'is_active': 'BOOLEAN',
            'is_verified': 'BOOLEAN',
            'last_check_at': 'DATETIME',
            'last_check_status': 'VARCHAR(20)',
            'check_frequency': 'VARCHAR(20)',
            'next_check_at': 'DATETIME',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME',
        }

        for col_name, col_type in required_columns.items():
            assert col_name in columns, f"Column {col_name} should exist"
            assert col_type in columns[col_name] or col_name == 'id', \
                f"Column {col_name} should have type {col_type}"

    def test_migration_v3_creates_email_processing_history_table(self):
        """Test that migration v3 creates email_processing_history table."""
        from migrate_database import migrate_to_v3

        migrate_to_v3(self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='email_processing_history'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "email_processing_history table should be created"

    def test_migration_v3_processing_history_has_correct_columns(self):
        """Test that email_processing_history table has all required columns."""
        from migrate_database import migrate_to_v3

        migrate_to_v3(self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(email_processing_history)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        conn.close()

        # Check required columns
        required_columns = {
            'id': 'INTEGER',
            'email_config_id': 'INTEGER',
            'user_id': 'INTEGER',
            'message_id': 'VARCHAR(500)',
            'message_date': 'DATETIME',
            'platform': 'VARCHAR(20)',
            'attachment_name': 'VARCHAR(255)',
            'status': 'VARCHAR(20)',
            'error_message': 'TEXT',
            'import_history_id': 'INTEGER',
            'processed_at': 'DATETIME',
        }

        for col_name, col_type in required_columns.items():
            assert col_name in columns, f"Column {col_name} should exist"

    def test_migration_v3_creates_indexes(self):
        """Test that migration v3 creates required indexes."""
        from migrate_database import migrate_to_v3

        migrate_to_v3(self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check indexes on user_email_configs
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='user_email_configs'
        """)
        email_config_indexes = [row[0] for row in cursor.fetchall()]

        # Check indexes on email_processing_history
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='email_processing_history'
        """)
        history_indexes = [row[0] for row in cursor.fetchall()]

        conn.close()

        # Verify key indexes exist
        assert any('user_id' in idx for idx in email_config_indexes), \
            "user_email_configs should have user_id index"
        assert any('is_active' in idx for idx in email_config_indexes), \
            "user_email_configs should have is_active index"

    def test_migration_v3_adds_user_relationship(self):
        """Test that migration v3 adds email_configs relationship to User model."""
        from migrate_database import migrate_to_v3

        migrate_to_v3(self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check foreign key constraint
        cursor.execute("PRAGMA foreign_key_list(user_email_configs)")
        fk_list = cursor.fetchall()
        conn.close()

        assert len(fk_list) > 0, "user_email_configs should have foreign key to users"
        assert fk_list[0][2] == 'users', "Foreign key should reference users table"

    def test_migration_v3_idempotent(self):
        """Test that migration v3 can be run multiple times safely."""
        from migrate_database import migrate_to_v3

        # Run migration twice
        migrate_to_v3(self.db_path)
        migrate_to_v3(self.db_path)

        # Should not raise an error
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_email_configs'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "Migration should be idempotent"

    def test_migration_v3_sets_default_values(self):
        """Test that migration v3 sets appropriate default values."""
        from migrate_database import migrate_to_v3

        migrate_to_v3(self.db_path)

        # Insert a test email config
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # First insert a test user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES ('testuser', 'test@example.com', 'hash')
        """)
        user_id = cursor.lastrowid

        # Insert email config with minimal fields
        cursor.execute("""
            INSERT INTO user_email_configs (user_id, email_address, password_encrypted, imap_server)
            VALUES (?, 'test@test.com', 'encrypted', 'imap.example.com')
        """, (user_id,))

        # Verify defaults
        cursor.execute(f"""
            SELECT imap_port, use_ssl, is_active, is_verified, config_name, check_frequency
            FROM user_email_configs
            WHERE user_id = {user_id}
        """)
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 993, "Default imap_port should be 993"
        assert result[1] == 1, "Default use_ssl should be TRUE (1)"
        assert result[2] == 1, "Default is_active should be TRUE (1)"
        assert result[3] == 0, "Default is_verified should be FALSE (0)"
        assert result[4] == '默认邮箱', "Default config_name should be '默认邮箱'"
        assert result[5] == 'hourly', "Default check_frequency should be 'hourly'"
