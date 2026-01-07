import pandas as pd
from .base_parser import BaseBillParser

class UnionPayParser(BaseBillParser):
    """UnionPay bill parser"""
    
    def get_platform(self):
        return "银联"
    
    def parse(self):
        """Parse UnionPay bill CSV file"""
        # UnionPay bill has a simple format
        df = pd.read_csv(
            self.file_path, 
            encoding='gbk',
            header=0
        )
        
        # Rename columns to standard names
        column_mapping = {
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
        
        # Keep only the columns we need
        # 确保每个标准列只被映射一次，避免重复
        unique_mapped_columns = {}
        for original_col, standard_col in column_mapping.items():
            if standard_col not in unique_mapped_columns.values():
                unique_mapped_columns[original_col] = standard_col
        
        df = df.rename(columns=unique_mapped_columns)
        
        # 只保留存在的标准列，确保每个列名只出现一次
        existing_standard_columns = []
        seen_columns = set()
        for col in unique_mapped_columns.values():
            if col not in seen_columns:
                existing_standard_columns.append(col)
                seen_columns.add(col)
        
        df = df[existing_standard_columns]
        
        # Combine date and time columns
        df['transaction_time'] = df.apply(lambda x: f"{x['transaction_time']} {x['transaction_hour']}", axis=1)
        df = df.drop(columns=['transaction_hour'])
        
        # Convert amount to float and ensure it's positive
        df['amount'] = df['amount'].astype(float)
        df['amount'] = df['amount'].abs()
        
        # Normalize transaction time
        df['transaction_time'] = df['transaction_time'].apply(lambda x: self.normalize_date(x, '%Y/%m/%d %H:%M:%S'))
        
        self.data = df
        return df
    
    def _convert_to_notion(self, record):
        """Convert UnionPay record to Notion format"""
        return {
            # 商品名称 (Name) - 使用交易类型作为商品名称
            'Name': {
                'title': [{
                    'text': {
                        'content': record['transaction_type']
                    }
                }]
            },
            # 价格 (Price)
            'Price': {
                'number': record['amount']
            },
            # 交易分类 (Category)
            'Category': {
                'select': {
                    'name': record['transaction_type']
                }
            },
            # 交易时间 (Date)
            'Date': {
                'date': {
                    'start': record['transaction_time'],
                    'time_zone': 'Asia/Shanghai'
                }
            },
            # 交易对方 (Counterparty)
            'Counterparty': {
                'rich_text': [{
                    'text': {
                        'content': record['counterparty']
                    }
                }]
            },
            # 备注 (Remarks)
            'Remarks': {
                'rich_text': [{
                    'text': {
                        'content': record['remark'] if pd.notna(record['remark']) else ''
                    }
                }]
            },
            # 收/支 (Income Expense)
            'Income Expense': {
                'select': {
                    'name': str(record.get('income_expense', '')).strip() if 'income_expense' in record and record['income_expense'] else ''
                }
            }, 
            # 支付平台 (Payment Platform)
            'From': {
                'select': {
                    'name': self.get_platform()
                }
            }
        }
