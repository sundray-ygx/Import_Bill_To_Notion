"""UnionPay bill parser."""

import pandas as pd
from .base_parser import BaseBillParser, STANDARD_COLUMNS


class UnionPayParser(BaseBillParser):
    """UnionPay bill parser."""

    # Column mapping for UnionPay
    COLUMN_MAP = {
        '交易日期': 'transaction_time',
        '交易时间': 'transaction_hour',
        '交易类型': 'transaction_type',
        '交易商户': 'counterparty',
        '交易金额': 'amount',
        '入账金额': 'posted_amount',
        '卡类型': 'card_type',
        '交易状态': 'status',
        '备注': 'remark'
    }

    def get_platform(self) -> str:
        return "UnionPay"

    def parse(self) -> pd.DataFrame:
        """Parse UnionPay bill CSV file."""
        self.data = pd.read_csv(self.file_path, encoding='gbk', header=0)

        # Apply column mapping
        self.data = self.apply_column_mapping(self.COLUMN_MAP, STANDARD_COLUMNS)

        # Combine date and time columns
        if 'transaction_time' in self.data.columns and 'transaction_hour' in self.data.columns:
            self.data['transaction_time'] = self.data.apply(
                lambda x: f"{x['transaction_time']} {x['transaction_hour']}", axis=1
            )
            self.data = self.data.drop(columns=['transaction_hour'])

        # Clean amount
        self.clean_amount_column()

        # Normalize dates
        if 'transaction_time' in self.data.columns:
            self.data['transaction_time'] = self.data['transaction_time'].apply(
                lambda x: self.normalize_date(str(x), '%Y/%m/%d %H:%M:%S')
            )

        return self.data

    def _convert_to_notion(self, record) -> dict:
        """Convert UnionPay record to Notion format."""
        return {
            'Name': {'title': [{'text': {'content': record['transaction_type']}}]},
            'Price': {'number': record['amount']},
            'Category': {'select': {'name': record['transaction_type']}},
            'Date': {'date': {'start': record['transaction_time'], 'time_zone': 'Asia/Shanghai'}},
            'Counterparty': {'rich_text': [{'text': {'content': record['counterparty']}}]},
            'Remarks': {'rich_text': [{'text': {'content': str(record.get('remark', ''))}}]},
            'Income Expense': {'select': {'name': ''}},
            'From': {'select': {'name': self.get_platform()}}
        }
