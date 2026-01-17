"""Alipay bill parser."""

import pandas as pd
from .base_parser import BaseBillParser, STANDARD_COLUMNS
import logging


logger = logging.getLogger(__name__)


class AlipayParser(BaseBillParser):
    """Alipay bill parser."""

    # Column mapping: CSV column names -> standard names
    COLUMN_MAP = {
        '交易时间': 'transaction_time',
        '交易分类': 'transaction_type',
        '交易对方': 'counterparty',
        '商品说明': 'item_name',
        '金额': 'amount',
        '收/支': 'income_expense',
        '收/付款方式': 'payment_method',
        '交易状态': 'status',
        '交易订单号': 'transaction_id',
        '商家订单号': 'merchant_id',
        '备注': 'remark',
    }

    def get_platform(self) -> str:
        return "Alipay"

    def parse(self) -> pd.DataFrame:
        """Parse Alipay bill file (CSV, TXT, XLS, XLSX)."""
        logger.info(f"Parsing Alipay bill: {self.file_path}")

        # Determine file type
        file_ext = self.file_path.lower().split('.')[-1]

        # For CSV/TXT files, find header and encoding
        if file_ext in ['csv', 'txt']:
            header_line, encoding = self.find_header_and_encoding(['交易时间', '交易分类'])
            if header_line is None:
                header_line, encoding = self.find_header_and_encoding(['金额', '收/支', '收支'])

            if header_line is None:
                raise ValueError("Could not find header line with expected keywords")

            # Read file
            self.data = self.read_file(skiprows=header_line, header=0)
        else:
            # For Excel files, read directly and find header
            self.data = self.read_file()

            # Find header row in Excel data
            header_found = False
            for idx, row in self.data.iterrows():
                row_str = ' '.join([str(v) for v in row.values if pd.notna(v)])
                if any(kw in row_str for kw in ['交易时间', '交易分类']):
                    self.data = pd.read_excel(
                        self.file_path,
                        skiprows=idx,
                        header=0,
                        engine='openpyxl' if file_ext == 'xlsx' else 'xlrd'
                    )
                    header_found = True
                    break

            if not header_found:
                # Try to use first row as header
                self.data = pd.read_excel(
                    self.file_path,
                    header=0,
                    engine='openpyxl' if file_ext == 'xlsx' else 'xlrd'
                )

        # Remove summary line if present
        try:
            if '汇总' in str(self.data.iloc[-1, 0]):
                self.data = self.data[:-1]
        except Exception:
            pass

        # Apply column mapping
        self.data = self.apply_column_mapping(self.COLUMN_MAP, STANDARD_COLUMNS)

        # Clean amount
        self.clean_amount_column()

        # Normalize dates
        if 'transaction_time' in self.data.columns:
            self.data['transaction_time'] = self.data['transaction_time'].apply(
                lambda x: self.normalize_date(str(x), '%Y-%m-%d %H:%M:%S') if pd.notna(x) else x
            )

        logger.info(f"Parsed {len(self.data)} records")
        return self.data

    def _convert_to_notion(self, record) -> dict:
        """Convert Alipay record to Notion format."""
        return {
            'Name': {'title': [{'text': {'content': str(record.get('item_name', record.get('transaction_type', '')))}}]},
            'Price': {'number': record.get('amount', 0)},
            'Category': {'select': {'name': str(record.get('transaction_type', ''))}},
            'Date': {'date': {'start': str(record.get('transaction_time', '')), 'time_zone': 'Asia/Shanghai'}},
            'Counterparty': {'rich_text': [{'text': {'content': str(record.get('counterparty', ''))}}]},
            'Remarks': {'rich_text': [{'text': {'content': str(record.get('remark', '')) if pd.notna(record.get('remark')) else ''}}]},
            'Income Expense': {'select': {'name': str(record.get('income_expense', '')).strip() if record.get('income_expense') else ''}},
            'Merchant Tracking Number': {'rich_text': [{'text': {'content': str(record.get('merchant_id', ''))}}]},
            'Transaction Number': {'rich_text': [{'text': {'content': str(record.get('transaction_id', ''))}}]},
            'Payment Method': {'select': {'name': str(record.get('payment_method', ''))}},
            'From': {'select': {'name': self.get_platform()}}
        }
