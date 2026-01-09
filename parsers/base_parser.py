"""Base parser for bill files."""

from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


# Standard column names
STANDARD_COLUMNS = [
    'transaction_time', 'transaction_type', 'counterparty', 'item_name',
    'amount', 'income_expense', 'payment_method', 'status',
    'transaction_id', 'merchant_id', 'remark'
]


class BaseBillParser(ABC):
    """Base class for bill parsers."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = None

    @abstractmethod
    def parse(self) -> pd.DataFrame:
        """Parse the bill file and return structured data."""
        pass

    @abstractmethod
    def get_platform(self) -> str:
        """Return the platform name."""
        pass

    def read_csv(self, **kwargs) -> pd.DataFrame:
        """Read CSV file with default encoding settings."""
        return pd.read_csv(self.file_path, **kwargs)

    def normalize_date(self, date_str: str, format_str: str) -> str:
        """Normalize date string to ISO format."""
        try:
            dt = datetime.strptime(date_str, format_str)
            return dt.isoformat()
        except ValueError:
            # Try common formats
            formats = [
                '%Y/%m/%d %H:%M', '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y %H:%M', '%m/%d/%Y %H:%M:%S',
                '%Y/%m/%d', '%Y-%m-%d', '%m/%d/%Y'
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).isoformat()
                except ValueError:
                    continue
            return date_str

    def find_header_and_encoding(
        self,
        header_keywords: list,
        encodings: list = None
    ) -> tuple:
        """Find header line and encoding.

        Returns:
            Tuple of (header_line_index, encoding) or (None, None) if not found
        """
        if encodings is None:
            encodings = ['gbk', 'utf-8', 'gb2312']

        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()

                for i, line in enumerate(lines):
                    if any(kw in line for kw in header_keywords):
                        logger.info(f"Found header at line {i+1}: {line.strip()}")
                        return i, encoding
            except (UnicodeDecodeError, Exception):
                continue

        return None, None

    def apply_column_mapping(
        self,
        mapping: dict,
        standard_columns: list = None
    ) -> pd.DataFrame:
        """Apply column mapping and filter to standard columns."""
        if standard_columns is None:
            standard_columns = STANDARD_COLUMNS

        df = self.data
        mapped_columns = {}

        for col in df.columns:
            cleaned_col = col.strip()
            cleaned_col = ''.join(c for c in cleaned_col if ord(c) > 31 or c in '\t\n')

            if cleaned_col in mapping:
                mapped_columns[col] = mapping[cleaned_col]
            else:
                for csv_col, standard_col in mapping.items():
                    if csv_col in cleaned_col:
                        mapped_columns[col] = standard_col
                        break

        # Apply unique mapping
        unique_mapped = {}
        for orig, std in mapped_columns.items():
            if std not in unique_mapped.values():
                unique_mapped[orig] = std

        if unique_mapped:
            df = df.rename(columns=unique_mapped)

        # Keep only existing standard columns
        existing = [col for col in df.columns if col in standard_columns]
        if existing:
            df = df[existing]

        return df

    def clean_amount_column(self, amount_col: str = 'amount'):
        """Clean amount column: remove symbols, convert to float, make positive."""
        if amount_col not in self.data.columns:
            return

        logger.info(f"Cleaning amount column")
        self.data[amount_col] = self.data[amount_col].astype(str).str.replace('￥', '', regex=False)
        self.data[amount_col] = self.data[amount_col].str.replace(',', '', regex=False)
        self.data[amount_col] = pd.to_numeric(self.data[amount_col], errors='coerce')
        self.data[amount_col] = self.data[amount_col].abs()

    def get_parsed_data(self) -> pd.DataFrame:
        """Get parsed data."""
        if self.data is None:
            self.parse()
        return self.data

    def to_notion_format(self) -> list:
        """Convert parsed data to Notion database format."""
        parsed_data = self.get_parsed_data()
        notion_records = []

        for _, record in parsed_data.iterrows():
            # Skip non-income/expense records
            if hasattr(record, 'income_expense') and record['income_expense'] == '不计收支':
                continue
            notion_record = self._convert_to_notion(record)
            notion_records.append(notion_record)

        return notion_records

    @abstractmethod
    def _convert_to_notion(self, record) -> dict:
        """Convert a single record to Notion format."""
        pass
