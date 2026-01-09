"""WeChat Pay bill parser."""

import pandas as pd
from .base_parser import BaseBillParser, STANDARD_COLUMNS
import logging


logger = logging.getLogger(__name__)


class WeChatParser(BaseBillParser):
    """WeChat Pay bill parser."""

    # Extended column mapping for WeChat
    COLUMN_MAP = {
        '交易时间': 'transaction_time',
        '交易日期': 'transaction_time',
        '时间': 'transaction_time',
        'Date': 'transaction_time',
        'DateTime': 'transaction_time',
        '交易类型': 'transaction_type',
        '类型': 'transaction_type',
        'Type': 'transaction_type',
        '交易对方': 'counterparty',
        '对方': 'counterparty',
        'Counterparty': 'counterparty',
        '商品': 'item_name',
        '商品名称': 'item_name',
        'Item': 'item_name',
        'Goods': 'item_name',
        '金额(元)': 'amount',
        '金额': 'amount',
        '金额（元）': 'amount',
        'Amount': 'amount',
        'AMOUNT': 'amount',
        'Amount(CNY)': 'amount',
        '金额(人民币)': 'amount',
        '金额(CNY)': 'amount',
        '收/支': 'income_expense',
        '收支': 'income_expense',
        'Income/Expense': 'income_expense',
        'Direction': 'income_expense',
        '支付方式': 'payment_method',
        '支付渠道': 'payment_method',
        'PaymentMethod': 'payment_method',
        '当前状态': 'status',
        '状态': 'status',
        'Status': 'status',
        '交易单号': 'transaction_id',
        '交易编号': 'transaction_id',
        'TransactionID': 'transaction_id',
        '商户单号': 'merchant_id',
        '商户编号': 'merchant_id',
        'MerchantID': 'merchant_id',
        '备注': 'remark',
        '说明': 'remark',
        'Note': 'remark',
        'Remark': 'remark'
    }

    def get_platform(self) -> str:
        return "WeChatPay"

    def parse(self) -> pd.DataFrame:
        """Parse WeChat Pay bill CSV file."""
        logger.info(f"Parsing WeChat Pay bill: {self.file_path}")

        # Find header and encoding
        header_line, encoding = self.find_header_and_encoding(['交易时间'])
        if header_line is None:
            raise ValueError("Could not find header line with '交易时间'")

        # Read CSV
        self.data = pd.read_csv(
            self.file_path,
            encoding=encoding,
            skiprows=header_line,
            header=0
        )

        # Remove summary lines (contains '统计时间')
        for i in range(len(self.data) - 1, max(0, len(self.data) - 20), -1):
            try:
                if '统计时间' in str(self.data.iloc[i, 0]):
                    self.data = self.data[:i]
                    break
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
        """Convert WeChat record to Notion format."""
        return {
            'Name': {'title': [{'text': {'content': str(record.get('item_name', ''))}}]},
            'Price': {'number': record.get('amount', 0)},
            'Category': {'select': {'name': str(record.get('transaction_type', ''))}},
            'Date': {'date': {'start': record.get('transaction_time', ''), 'time_zone': 'Asia/Shanghai'}},
            'Counterparty': {'rich_text': [{'text': {'content': str(record.get('counterparty', ''))}}]},
            'Remarks': {'rich_text': [{'text': {'content': str(record.get('remark', ''))}}]},
            'Income Expense': {'select': {'name': str(record.get('income_expense', '')).strip() if record.get('income_expense') else ''}},
            'Transaction Number': {'rich_text': [{'text': {'content': str(record.get('transaction_id', ''))}}]},
            'Merchant Tracking Number': {'rich_text': [{'text': {'content': str(record.get('merchant_id', ''))}}]},
            'Payment Method': {'select': {'name': str(record.get('payment_method', ''))}},
            'From': {'select': {'name': self.get_platform()}}
        }
