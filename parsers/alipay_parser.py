import pandas as pd
from .base_parser import BaseBillParser
import logging

logger = logging.getLogger(__name__)

class AlipayParser(BaseBillParser):
    """Alipay bill parser"""
    
    def get_platform(self):
        return "支付宝"
    
    def parse(self):
        """Parse Alipay bill CSV file"""
        logger.info(f"开始解析支付宝账单文件: {self.file_path}")
        
        # Alipay bill has some header lines before the actual data
        # Try multiple encodings and find the correct header line
        encodings = ['gbk', 'utf-8', 'gb2312']
        df = None
        success_encoding = None
        success_skiprows = None
        
        # First, find the correct encoding and header line
        for encoding in encodings:
            logger.info(f"尝试编码: {encoding}")
            try:
                # Read the entire file content to find the header line
                with open(self.file_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                
                logger.info(f"成功读取文件，共 {len(lines)} 行")
                
                # Find the line that contains '交易时间' as the header
                header_line = None
                for i, line in enumerate(lines):
                    # 更宽松的检测逻辑，只要包含交易时间关键词即可
                    if any(keyword in line for keyword in ['交易时间', '交易分类']):
                        header_line = i
                        logger.info(f"找到表头行，位于第 {i+1} 行，内容：{line.strip()}")
                        break
                
                # 如果没有找到，尝试查找包含金额关键词的行
                if header_line is None:
                    for i, line in enumerate(lines):
                        if any(keyword in line for keyword in ['金额', '收/支', '收支']):
                            header_line = i
                            logger.info(f"找到表头行（通过金额关键词），位于第 {i+1} 行，内容：{line.strip()}")
                            break
                
                if header_line is None:
                    logger.error(f"没有找到包含'交易时间'和'交易类型'的表头行")
                    continue
                
                # Now read the file with pandas, using the found header line
                logger.info(f"使用表头行 {header_line} 读取文件")
                df = pd.read_csv(
                    self.file_path, 
                    encoding=encoding,
                    skiprows=header_line, 
                    header=0
                )
                
                # Check if the dataframe has at least one row and some columns
                if len(df) > 0 and len(df.columns) > 0:
                    success_encoding = encoding
                    success_skiprows = header_line
                    logger.info(f"成功读取文件，编码: {encoding}, 表头行: {header_line+1}")
                    logger.info(f"数据列名: {df.columns.tolist()}")
                    logger.info(f"数据行数: {len(df)}")
                    break
            except Exception as e:
                logger.debug(f"读取文件失败: {e}")
                continue
        
        if df is None:
            logger.error(f"无法读取文件，尝试了以下编码: {', '.join(encodings)}")
            raise ValueError(f"Failed to read file with encodings: {', '.join(encodings)}")
        
        # Remove the last summary line if exists
        logger.info(f"检查并移除尾部汇总行")
        try:
            if '汇总' in str(df.iloc[-1, 0]):
                df = df[:-1]
                logger.info(f"移除了尾部汇总行")
        except Exception as e:
            logger.debug(f"检查尾部汇总行时出错: {e}")
        
        # 简化的列名映射表：CSV列名 -> 标准列名
        csv_to_standard_map = {
            # 交易时间相关
            '交易时间': 'transaction_time',
            
            # 交易类型相关
            '交易分类': 'transaction_type',
            
            # 交易对方相关
            '交易对方': 'counterparty',
            
            # 商品相关
            '商品说明': 'item_name',
            
            # 金额相关（最重要，支持多种格式）
            '金额': 'amount',
            
            # 收支相关
            '收/支': 'income_expense',

            # 支付方式相关
            '收/付款方式': 'payment_method',
            
            # 状态相关
            '交易状态': 'status',

            # 交易单号相关
            '交易订单号': 'transaction_id',

            # 商户单号相关
            '商家订单号': 'merchant_id',

            # 备注相关
            '备注': 'remark',
        }
        
        # 清理列名（移除空格和特殊字符）并进行映射
        logger.info(f"开始列名映射")
        mapped_columns = {}
        for col in df.columns:
            # 清理列名
            cleaned_col = col.strip()
            cleaned_col = ''.join(c for c in cleaned_col if ord(c) > 31 or c in '\t\n')
            
            # 查找映射关系
            if cleaned_col in csv_to_standard_map:
                mapped_columns[col] = csv_to_standard_map[cleaned_col]
                logger.info(f"映射列名: '{col}' -> '{csv_to_standard_map[cleaned_col]}'")
            else:
                # 智能映射：通过关键词匹配
                matched = False
                for csv_col, standard_col in csv_to_standard_map.items():
                    if csv_col in cleaned_col:
                        mapped_columns[col] = standard_col
                        logger.info(f"智能映射列名: '{col}' -> '{standard_col}' (关键词匹配: '{csv_col}')")
                        matched = True
                        break
                
                # 金额字段特殊处理：包含金额关键词的列都映射为amount
                if not matched and any(keyword in cleaned_col for keyword in ['金额', 'amount', 'AMOUNT', 'Amount']):
                    mapped_columns[col] = 'amount'
                    logger.info(f"智能映射列名: '{col}' -> 'amount' (金额关键词匹配)")
                    matched = True
        
        # 应用列名映射
        if mapped_columns:
            # 确保每个标准列只被映射一次，避免重复
            unique_mapped_columns = {}
            for original_col, standard_col in mapped_columns.items():
                if standard_col not in unique_mapped_columns.values():
                    unique_mapped_columns[original_col] = standard_col
                    logger.info(f"映射列名: '{original_col}' -> '{standard_col}'")
            
            df = df.rename(columns=unique_mapped_columns)
            logger.info(f"映射后列名: {df.columns.tolist()}")
        
        # 定义需要保留的标准列
        standard_columns = ['transaction_time', 'transaction_type', 'counterparty', 'item_name', 'amount', 
                           'income_expense', 'payment_method', 'status', 'transaction_id', 'merchant_id', 'remark']
        
        # 只保留存在的标准列，确保每个列名只出现一次
        existing_standard_columns = []
        seen_columns = set()
        for col in df.columns:
            if col in standard_columns and col not in seen_columns:
                existing_standard_columns.append(col)
                seen_columns.add(col)
        if existing_standard_columns:
            df = df[existing_standard_columns]
            logger.info(f"保留标准列: {existing_standard_columns}")
        else:
            logger.warning(f"没有匹配到任何标准列，保留所有列")
        
        # Convert amount to float and ensure it's positive
        if 'amount' in df.columns:
            logger.info(f"转换金额列类型为数值型")
            
            # First, remove any currency symbols and special characters from amount column
            logger.info(f"清理金额列，移除货币符号等特殊字符")
            df['amount'] = df['amount'].astype(str).str.replace('￥', '', regex=False)
            df['amount'] = df['amount'].str.replace(',', '', regex=False)  # Remove commas if any
            
            # Convert to numeric
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
            # Ensure amount is positive
            df['amount'] = df['amount'].abs()
        
        # Normalize transaction time if the column exists
        if 'transaction_time' in df.columns:
            logger.info(f"标准化交易时间列")
            df['transaction_time'] = df['transaction_time'].apply(lambda x: self.normalize_date(str(x), '%Y-%m-%d %H:%M:%S') if pd.notna(x) else x)
        
        logger.info(f"解析完成，数据行数: {len(df)}")
        logger.info(f"最终数据列名: {df.columns.tolist()}")
        
        self.data = df
        return df
    
    def _convert_to_notion(self, record):
        """Convert Alipay record to Notion format"""
        return {
            # 商品名称 (Name)
            'Name': {
                'title': [{
                    'text': {
                        'content': str(record.get('item_name', record.get('transaction_type', '')))
                    }
                }]
            },
            # 价格 (Price)
            'Price': {
                'number': record.get('amount', 0)
            },
            # 交易分类 (Category)
            'Category': {
                'select': {
                    'name': str(record.get('transaction_type', ''))
                }
            },
            # 交易时间 (Date)
            'Date': {
                'date': {
                    'start': str(record.get('transaction_time', '')),
                    'time_zone': 'Asia/Shanghai'
                }
            },
            # 交易对方 (Counterparty)
            'Counterparty': {
                'rich_text': [{
                    'text': {
                        'content': str(record.get('counterparty', ''))
                    }
                }]
            },
            # 备注 (Remarks)
            'Remarks': {
                'rich_text': [{
                    'text': {
                        'content': str(record.get('remark', '')) if pd.notna(record.get('remark')) else ''
                    }
                }]
            },
            # 收/支 (Income Expense)
            'Income Expense': {
                'select': {
                    'name': str(record.get('income_expense', '')).strip() if record.get('income_expense') else ''
                }
            },
            # 商家订单号 (Merchant Tracking Number)
            'Merchant Tracking Number': {
                'rich_text': [{
                    'text': {
                        'content': str(record.get('merchant_id', ''))
                    }
                }]
            },
            # 交易订单号 (Transaction Number)
            'Transaction Number': {
                'rich_text': [{
                    'text': {
                        'content': str(record.get('transaction_id', ''))
                    }
                }]
            },
            # 支付方式 (Payment Method)
            'Payment Method': {
                'select': {
                    'name': str(record.get('payment_method', ''))
                }
            },
            # 支付平台 (Payment Platform)
            'Payment Platform': {
                'select': {
                    'name': self.get_platform()
                }
            }
        }
