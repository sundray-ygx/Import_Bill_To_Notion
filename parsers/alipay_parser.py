import pandas as pd
from .base_parser import BaseBillParser

class AlipayParser(BaseBillParser):
    """Alipay bill parser"""
    
    def get_platform(self):
        return "支付宝"
    
    def parse(self):
        """Parse Alipay bill CSV file"""
        # Alipay bill has some header lines before the actual data
        # Skip the first few lines and read the header from line 4
        df = pd.read_csv(
            self.file_path, 
            encoding='gbk',
            skiprows=4, 
            header=0
        )
        
        # Remove the last summary line if exists
        if '汇总' in str(df.iloc[-1, 0]):
            df = df[:-1]
        
        # Rename columns to standard names
        column_mapping = {
            '交易时间': 'transaction_time',
            '交易类型': 'transaction_type',
            '交易对方': 'counterparty',
            '商品名称': 'item_name',
            '金额（元）': 'amount',
            '收/支': 'income_expense',
            '交易状态': 'status',
            '备注': 'remark'
        }
        
        # Keep only the columns we need
        df = df.rename(columns=column_mapping)
        df = df[column_mapping.values()]
        
        # Convert amount to float and ensure it's positive
        df['amount'] = df['amount'].astype(float)
        df['amount'] = df['amount'].abs()
        
        # Normalize transaction time
        df['transaction_time'] = df['transaction_time'].apply(lambda x: self.normalize_date(x, '%Y-%m-%d %H:%M:%S'))
        
        self.data = df
        return df
    
    def _convert_to_notion(self, record):
        """Convert Alipay record to Notion format"""
        return {
            # 商品名称 (Name)
            'Name': {
                'title': [{
                    'text': {
                        'content': record['item_name']
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
            # 支付平台 (Payment Platform)
            'Payment Platform': {
                'select': {
                    'name': self.get_platform()
                }
            }
        }
