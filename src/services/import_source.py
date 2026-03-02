"""Import source abstraction module.

This module provides the ImportSource abstract base class and concrete
implementations for different bill import sources (file upload, email, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.models import UserUpload, ImportHistory


class ImportSource(ABC):
    """Abstract base class for bill import sources.

    This class defines the interface that all import sources must implement.
    It provides a template method `import_bills()` that orchestrates the
    import process.

    Subclasses must implement:
    - fetch_bills(): Retrieve bill files from the source
    - get_source_type(): Return a string identifying the source type
    """

    def __init__(self, user_id: int, db: Session):
        """Initialize the import source.

        Args:
            user_id: The ID of the user importing bills
            db: SQLAlchemy database session
        """
        self.user_id = user_id
        self.db = db

    @abstractmethod
    def fetch_bills(self) -> List[Dict[str, Any]]:
        """Fetch bill files from the import source.

        Returns:
            A list of bill dictionaries, each containing:
            - file_path: Path to the bill file
            - platform: Platform identifier (alipay/wechat/unionpay)
            - metadata: Additional metadata about the source

        Raises:
            Exception: If fetching fails for any reason
        """
        pass

    @abstractmethod
    def get_source_type(self) -> str:
        """Return the source type identifier.

        Returns:
            A string identifying the source type (e.g., "file_upload", "email")
        """
        pass

    def import_bills(self) -> Dict[str, Any]:
        """Import all bills from this source.

        This template method orchestrates the import process:
        1. Fetch bills from the source
        2. Import each bill using the importer
        3. Record import history

        Returns:
            A dictionary containing import statistics:
            - total: Total number of bills processed
            - imported: Total number of records imported
            - failed: Total number of records that failed
            - history_ids: List of import history IDs created

        Raises:
            Exception: If import fails critically
        """
        # Fetch bills from the source
        bills = self.fetch_bills()

        if not bills:
            return {
                'total': 0,
                'imported': 0,
                'failed': 0,
                'history_ids': []
            }

        # Import each bill and track results
        total_imported = 0
        total_failed = 0
        history_ids = []

        # Lazy import to avoid circular dependency
        from importer import import_bill

        for bill in bills:
            try:
                file_path = bill['file_path']
                platform = bill.get('platform')
                metadata = bill.get('metadata', {})

                # Import the bill
                result = import_bill(
                    file_path=file_path,
                    platform=platform,
                    user_id=self.user_id,
                    db=self.db
                )

                total_imported += result.get('success', 0)
                total_failed += result.get('failed', 0)

                # Create import history record
                history = ImportHistory(
                    user_id=self.user_id,
                    upload_id=metadata.get('upload_id'),
                    total_records=result.get('total', 0),
                    imported_records=result.get('success', 0),
                    failed_records=result.get('failed', 0),
                    status='success' if result.get('failed', 0) == 0 else 'partial'
                )
                self.db.add(history)
                self.db.commit()
                self.db.refresh(history)

                history_ids.append(history.id)

            except Exception as e:
                # Record failure and continue with next bill
                total_failed += 1

                history = ImportHistory(
                    user_id=self.user_id,
                    upload_id=metadata.get('upload_id'),
                    total_records=0,
                    imported_records=0,
                    failed_records=1,
                    status='failed',
                    error_message=str(e)
                )
                self.db.add(history)
                self.db.commit()
                self.db.refresh(history)

                history_ids.append(history.id)

        return {
            'total': len(bills),
            'imported': total_imported,
            'failed': total_failed,
            'history_ids': history_ids
        }


class FileUploadSource(ImportSource):
    """File upload import source.

    This source retrieves bills that were uploaded by users through the web interface.
    """

    def __init__(self, user_id: int, db: Session, upload_id: Optional[int] = None):
        """Initialize the file upload source.

        Args:
            user_id: The ID of the user importing bills
            db: SQLAlchemy database session
            upload_id: Specific upload ID to import (if None, imports all pending)
        """
        super().__init__(user_id, db)
        self.upload_id = upload_id

    def fetch_bills(self) -> List[Dict[str, Any]]:
        """Fetch bills from user uploads.

        Returns:
            A list of bill dictionaries from user uploads

        Raises:
            ValueError: If the specified upload is not found
        """
        if self.upload_id:
            # Fetch specific upload
            upload = self.db.query(UserUpload).filter(
                UserUpload.id == self.upload_id,
                UserUpload.user_id == self.user_id
            ).first()

            if not upload:
                raise ValueError(f"Upload not found: {self.upload_id}")

            return [{
                'file_path': upload.file_path,
                'platform': upload.platform if upload.platform else None,
                'metadata': {
                    'upload_id': upload.upload_id,
                    'filename': upload.original_file_name,
                    'uploaded_at': upload.created_at.isoformat() if upload.created_at else None
                }
            }]
        else:
            # Fetch all pending uploads for this user
            uploads = self.db.query(UserUpload).filter(
                UserUpload.user_id == self.user_id,
                UserUpload.status == 'pending'
            ).all()

            return [
                {
                    'file_path': upload.file_path,
                    'platform': upload.platform if upload.platform else None,
                    'metadata': {
                        'upload_id': upload.upload_id,
                        'filename': upload.original_file_name,
                        'uploaded_at': upload.created_at.isoformat() if upload.created_at else None
                    }
                }
                for upload in uploads
            ]

    def get_source_type(self) -> str:
        """Return the source type identifier."""
        return "file_upload"
