"""Tests for ImportSource abstract base class.

Tests the ImportSource abstraction and concrete implementations.
"""

import pytest
from abc import ABC
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock, patch


class TestImportSourceAbstract:
    """Test ImportSource abstract base class."""

    def test_import_source_is_abstract(self):
        """Test that ImportSource cannot be instantiated directly."""
        from src.services.import_source import ImportSource

        # ImportSource should be an abstract class
        assert issubclass(ImportSource, ABC)

        # Attempting to instantiate should raise TypeError
        with pytest.raises(TypeError):
            ImportSource(user_id=1, db=Mock())

    def test_import_source_requires_fetch_bills(self):
        """Test that ImportSource requires fetch_bills implementation."""
        from src.services.import_source import ImportSource

        # Concrete class without fetch_bills should fail
        class IncompleteSource(ImportSource):
            pass

        with pytest.raises(TypeError):
            IncompleteSource(user_id=1, db=Mock())

    def test_import_source_requires_get_source_type(self):
        """Test that ImportSource requires get_source_type implementation."""
        from src.services.import_source import ImportSource

        # Concrete class without get_source_type should fail
        class IncompleteSource(ImportSource):
            def fetch_bills(self) -> List[Dict[str, Any]]:
                return []

        with pytest.raises(TypeError):
            IncompleteSource(user_id=1, db=Mock())

    def test_complete_import_source_can_be_instantiated(self):
        """Test that a complete ImportSource implementation can be instantiated."""
        from src.services.import_source import ImportSource

        # Complete concrete implementation
        class CompleteSource(ImportSource):
            def fetch_bills(self) -> List[Dict[str, Any]]:
                return []

            def get_source_type(self) -> str:
                return "test_source"

        # Should be able to instantiate
        db_mock = Mock()
        source = CompleteSource(user_id=1, db=db_mock)

        assert source.user_id == 1
        assert source.db == db_mock
        assert source.get_source_type() == "test_source"
        assert source.fetch_bills() == []


class TestImportSourceImportBills:
    """Test ImportSource.import_bills template method."""

    def test_import_bills_calls_fetch_and_import(self):
        """Test that import_bills calls fetch_bills and then imports."""
        from src.services.import_source import ImportSource

        class TestSource(ImportSource):
            def fetch_bills(self) -> List[Dict[str, Any]]:
                return [
                    {
                        'file_path': '/path/to/bill.csv',
                        'platform': 'alipay',
                        'metadata': {'source': 'test'}
                    }
                ]

            def get_source_type(self) -> str:
                return "test_source"

        db_mock = Mock()
        source = TestSource(user_id=1, db=db_mock)

        # Mock the importer
        with patch('importer.import_bill') as mock_import:
            mock_import.return_value = {
                'success': 5,
                'failed': 0,
                'total': 5
            }

            result = source.import_bills()

            # Verify import_bill was called
            mock_import.assert_called_once()
            assert result['total'] == 1
            assert result['imported'] == 5

    def test_import_bills_handles_multiple_bills(self):
        """Test that import_bills processes multiple bills."""
        from src.services.import_source import ImportSource

        class TestSource(ImportSource):
            def fetch_bills(self) -> List[Dict[str, Any]]:
                return [
                    {'file_path': '/path/to/bill1.csv', 'platform': 'alipay', 'metadata': {}},
                    {'file_path': '/path/to/bill2.csv', 'platform': 'wechat', 'metadata': {}},
                    {'file_path': '/path/to/bill3.csv', 'platform': 'unionpay', 'metadata': {}},
                ]

            def get_source_type(self) -> str:
                return "test_source"

        db_mock = Mock()
        source = TestSource(user_id=1, db=db_mock)

        with patch('importer.import_bill') as mock_import:
            mock_import.return_value = {
                'success': 10,
                'failed': 0,
                'total': 10
            }

            result = source.import_bills()

            # Verify import_bill was called 3 times
            assert mock_import.call_count == 3
            assert result['total'] == 3
            assert result['imported'] == 30
            assert result['failed'] == 0

    def test_import_bills_handles_import_failures(self):
        """Test that import_bills tracks failures."""
        from src.services.import_source import ImportSource

        class TestSource(ImportSource):
            def fetch_bills(self) -> List[Dict[str, Any]]:
                return [
                    {'file_path': '/path/to/good.csv', 'platform': 'alipay', 'metadata': {}},
                    {'file_path': '/path/to/bad.csv', 'platform': 'wechat', 'metadata': {}},
                ]

            def get_source_type(self) -> str:
                return "test_source"

        db_mock = Mock()
        source = TestSource(user_id=1, db=db_mock)

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {'success': 10, 'failed': 0, 'total': 10}
            else:
                return {'success': 0, 'failed': 10, 'total': 10}

        with patch('importer.import_bill') as mock_import:
            mock_import.side_effect = side_effect

            result = source.import_bills()

            assert result['total'] == 2
            assert result['imported'] == 10
            assert result['failed'] == 10

    def test_import_bills_records_import_history(self):
        """Test that import_bills creates import history records."""
        from src.services.import_source import ImportSource

        class TestSource(ImportSource):
            def fetch_bills(self) -> List[Dict[str, Any]]:
                return [
                    {'file_path': '/path/to/bill.csv', 'platform': 'alipay', 'metadata': {}},
                ]

            def get_source_type(self) -> str:
                return "test_source"

        # Create mock db session
        db_mock = MagicMock()
        db_mock.add = MagicMock()
        db_mock.commit = MagicMock()
        db_mock.refresh = MagicMock()

        source = TestSource(user_id=1, db=db_mock)

        with patch('importer.import_bill') as mock_import:
            mock_import.return_value = {
                'success': 10,
                'failed': 0,
                'total': 10
            }

            result = source.import_bills()

            # Verify database operations
            db_mock.add.assert_called()
            db_mock.commit.assert_called()


class TestFileUploadSource:
    """Test FileUploadSource implementation."""

    def test_file_upload_source_fetches_by_upload_id(self):
        """Test that FileUploadSource fetches by upload_id."""
        from src.services.import_source import FileUploadSource
        from src.models import User, UserUpload

        # Create mock db
        db_mock = MagicMock()
        upload_mock = MagicMock()
        upload_mock.file_path = "/path/to/file.csv"
        upload_mock.platform = "alipay"
        upload_mock.upload_id = "upload-123"

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = upload_mock
        db_mock.query.return_value = query_mock

        source = FileUploadSource(user_id=1, db=db_mock, upload_id="upload-123")

        bills = source.fetch_bills()

        assert len(bills) == 1
        assert bills[0]['file_path'] == "/path/to/file.csv"
        assert bills[0]['platform'] == "alipay"
        assert bills[0]['metadata']['upload_id'] == "upload-123"

    def test_file_upload_source_get_source_type(self):
        """Test that FileUploadSource returns correct source type."""
        from src.services.import_source import FileUploadSource

        source = FileUploadSource(user_id=1, db=Mock())
        assert source.get_source_type() == "file_upload"

    def test_file_upload_source_raises_error_if_not_found(self):
        """Test that FileUploadSource raises error if upload not found."""
        from src.services.import_source import FileUploadSource

        db_mock = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db_mock.query.return_value = query_mock

        source = FileUploadSource(user_id=1, db=db_mock, upload_id="nonexistent")

        with pytest.raises(ValueError, match="Upload not found"):
            source.fetch_bills()
