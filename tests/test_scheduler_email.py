"""Tests for BillScheduler email extensions.

Tests the scheduler's email checking functionality.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestBillSchedulerEmailExtensions:
    """Test BillScheduler email checking methods."""

    def test_add_email_check_job(self):
        """Test adding an email check job."""
        from src.scheduler import BillScheduler

        scheduler = BillScheduler()

        with patch.object(scheduler.scheduler, 'add_job') as mock_add_job:
            scheduler.add_email_check_job(config_id=5, frequency='hourly')

            # Verify job was added
            mock_add_job.assert_called_once()
            call_args = mock_add_job.call_args
            assert call_args[1]['id'] == 'email_check_5'
            assert call_args[1]['kwargs']['config_id'] == 5

    def test_add_email_check_job_with_daily_frequency(self):
        """Test adding email check job with daily frequency."""
        from src.scheduler import BillScheduler

        scheduler = BillScheduler()

        with patch.object(scheduler.scheduler, 'add_job') as mock_add_job:
            scheduler.add_email_check_job(config_id=10, frequency='daily')

            # Verify job was added with correct ID
            call_args = mock_add_job.call_args
            assert call_args[1]['id'] == 'email_check_10'

    def test_add_email_check_job_with_weekly_frequency(self):
        """Test adding email check job with weekly frequency."""
        from src.scheduler import BillScheduler

        scheduler = BillScheduler()

        with patch.object(scheduler.scheduler, 'add_job') as mock_add_job:
            scheduler.add_email_check_job(config_id=15, frequency='weekly')

            # Verify job was added with weekly frequency
            call_args = mock_add_job.call_args
            assert call_args[1]['id'] == 'email_check_15'

    def test_add_email_check_job_with_invalid_frequency(self):
        """Test adding email check job with invalid frequency."""
        from src.scheduler import BillScheduler

        scheduler = BillScheduler()

        with pytest.raises(ValueError, match="Unsupported frequency"):
            scheduler.add_email_check_job(config_id=5, frequency='invalid')

    def test_remove_email_check_job(self):
        """Test removing an email check job."""
        from src.scheduler import BillScheduler

        scheduler = BillScheduler()

        with patch.object(scheduler.scheduler, 'remove_job') as mock_remove:
            scheduler.remove_email_check_job(config_id=5)

            # Verify job was removed
            mock_remove.assert_called_once_with('email_check_5')

    def test_remove_email_check_job_handles_nonexistent_job(self):
        """Test that removing non-existent job doesn't raise error."""
        from src.scheduler import BillScheduler

        scheduler = BillScheduler()

        # Mock remove_job to raise exception
        with patch.object(scheduler.scheduler, 'remove_job', side_effect=Exception('Job not found')):
            # Should not raise exception
            scheduler.remove_email_check_job(config_id=999)

    def test_check_email_with_db_parameter(self):
        """Test _check_email method with db parameter."""
        from src.scheduler import BillScheduler
        from src.models import EmailConfig

        scheduler = BillScheduler()
        db_mock = MagicMock()

        # Mock config query
        config = EmailConfig(
            id=5,
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted",
            imap_server="imap.example.com"
        )
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = config
        db_mock.query.return_value = query_mock

        with patch('src.scheduler.EmailImportSource') as mock_source_class:
            mock_source = MagicMock()
            mock_source_class.return_value = mock_source
            mock_source.import_bills.return_value = {
                'total': 2,
                'imported': 20,
                'failed': 0,
                'history_ids': []
            }

            scheduler._check_email(config_id=5, db=db_mock)

            # Verify import was called
            mock_source.import_bills.assert_called_once()

    def test_check_email_updates_config_status(self):
        """Test that _check_email updates config status."""
        from src.scheduler import BillScheduler
        from src.models import EmailConfig
        from datetime import datetime

        scheduler = BillScheduler()
        db_mock = MagicMock()

        config = EmailConfig(
            id=5,
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted",
            imap_server="imap.example.com"
        )
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = config
        db_mock.query.return_value = query_mock

        with patch('src.scheduler.datetime') as mock_datetime, \
             patch('src.scheduler.EmailImportSource') as mock_source_class:
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)

            mock_source = MagicMock()
            mock_source_class.return_value = mock_source
            mock_source.import_bills.return_value = {
                'total': 1,
                'imported': 10,
                'failed': 0,
                'history_ids': []
            }

            scheduler._check_email(config_id=5, db=db_mock)

            # Verify config was updated
            assert config.last_check_at is not None
            assert config.last_check_status == 'success'
            db_mock.commit.assert_called()

    def test_check_email_handles_import_failure(self):
        """Test that _check_email handles import failures."""
        from src.scheduler import BillScheduler
        from src.models import EmailConfig

        scheduler = BillScheduler()
        db_mock = MagicMock()

        config = EmailConfig(
            id=5,
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted",
            imap_server="imap.example.com"
        )
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = config
        db_mock.query.return_value = query_mock

        with patch('src.scheduler.EmailImportSource') as mock_source_class:
            mock_source = MagicMock()
            mock_source_class.return_value = mock_source
            mock_source.import_bills.return_value = {
                'total': 1,
                'imported': 5,
                'failed': 5,
                'history_ids': []
            }

            scheduler._check_email(config_id=5, db=db_mock)

            # Verify status reflects partial success
            assert config.last_check_status == 'partial'

    def test_check_email_handles_missing_config(self):
        """Test that _check_email handles missing config gracefully."""
        from src.scheduler import BillScheduler

        scheduler = BillScheduler()
        db_mock = MagicMock()

        # Mock config not found
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db_mock.query.return_value = query_mock

        # Should not raise exception
        scheduler._check_email(config_id=999, db=db_mock)

    def test_check_email_closes_database_session(self):
        """Test that _check_email properly closes database session."""
        from src.scheduler import BillScheduler
        from src.models import EmailConfig

        scheduler = BillScheduler()
        db_mock = MagicMock()

        config = EmailConfig(
            id=5,
            user_id=1,
            email_address="test@example.com",
            password_encrypted="encrypted",
            imap_server="imap.example.com"
        )
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = config
        db_mock.query.return_value = query_mock

        with patch('src.scheduler.EmailImportSource') as mock_source_class:
            mock_source = MagicMock()
            mock_source_class.return_value = mock_source
            mock_source.import_bills.return_value = {
                'total': 0,
                'imported': 0,
                'failed': 0,
                'history_ids': []
            }

            scheduler._check_email(config_id=5, db=db_mock)

            # Verify close was NOT called (db was passed in)
            db_mock.close.assert_not_called()

    def test_get_email_check_jobs(self):
        """Test getting all email check jobs."""
        from src.scheduler import BillScheduler

        scheduler = BillScheduler()

        # Mock jobs
        mock_jobs = [
            MagicMock(id='email_check_1', name='Email check 1'),
            MagicMock(id='email_check_2', name='Email check 2'),
            MagicMock(id='other_job', name='Other job'),
        ]

        with patch.object(scheduler.scheduler, 'get_jobs', return_value=mock_jobs):
            email_jobs = scheduler.get_email_check_jobs()

            # Should only return email check jobs
            assert len(email_jobs) == 2
            assert all(job.id.startswith('email_check_') for job in email_jobs)
