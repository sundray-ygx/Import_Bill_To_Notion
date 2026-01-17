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
        '金额(元)': 'amount',  # Important: Excel format uses this exact name
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
        """Parse WeChat Pay bill file (CSV, TXT, XLS, XLSX)."""
        logger.info(f"Parsing WeChat Pay bill: {self.file_path}")

        # Determine file type
        file_ext = self.file_path.lower().split('.')[-1]

        # For CSV/TXT files, find header and encoding
        if file_ext in ['csv', 'txt']:
            header_line, encoding = self.find_header_and_encoding(['交易时间'])
            if header_line is None:
                raise ValueError("Could not find header line with '交易时间'")

            # Read file
            self.data = self.read_file(skiprows=header_line, header=0)
        else:
            # For Excel files, read and find header
            # First, read without header to find the actual data header row
            temp_df = pd.read_excel(
                self.file_path,
                header=None,
                nrows=50,
                engine='openpyxl' if file_ext == 'xlsx' else 'xlrd'
            )

            # Find the row with actual column headers
            header_row_idx = None
            for idx in range(len(temp_df)):
                row_str = ' '.join([str(v) for v in temp_df.iloc[idx].values if pd.notna(v)])
                # Look for the header row that contains "交易时间" and column separator pattern
                if '交易时间' in row_str and '交易类型' in row_str:
                    header_row_idx = idx
                    logger.info(f"Found header row at index {idx}: {row_str[:100]}")
                    break

            if header_row_idx is None:
                raise ValueError("Could not find header row with '交易时间' in Excel file")

            # Now read the actual data starting from the header row
            self.data = pd.read_excel(
                self.file_path,
                skiprows=header_row_idx,
                header=0,
                engine='openpyxl' if file_ext == 'xlsx' else 'xlrd'
            )

            # Clean column names (remove extra spaces and special characters)
            self.data.columns = self.data.columns.str.strip()

        # Remove summary lines at the end
        # Look for rows that contain summary keywords or are empty
        rows_to_keep = []
        for idx, row in self.data.iterrows():
            first_col_value = str(row.iloc[0]) if len(row) > 0 else ''

            # Skip summary rows and empty rows
            if any(kw in first_col_value for kw in ['统计时间', '汇总', '共计', 'Note:']):
                logger.info(f"Stopping at summary row {idx}: {first_col_value}")
                break

            # Skip rows where first column is empty or just a number
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() != '':
                rows_to_keep.append(idx)

        if rows_to_keep:
            # Keep only data rows before summary
            max_idx = max(rows_to_keep) + 1
            self.data = self.data.loc[:max_idx]

        # Remove rows where first column is just a row number
        if len(self.data) > 0:
            first_col = self.data.columns[0]
            # Try to convert first column to numeric to detect row numbers
            try:
                is_row_number = pd.to_numeric(self.data[first_col], errors='coerce')
                # If more than 50% of first column values are numeric, it might be row index
                if is_row_number.notna().sum() / len(self.data) > 0.5:
                    # Check if values are sequential integers
                    unique_vals = is_row_number.dropna().nunique()
                    if unique_vals == len(self.data):
                        # This looks like row numbers, drop the column
                        self.data = self.data.drop(columns=[first_col])
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
