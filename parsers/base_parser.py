from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime

class BaseBillParser(ABC):
    """Base class for bill parsers"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
    
    @abstractmethod
    def parse(self):
        """Parse the bill file and return structured data"""
        pass
    
    @abstractmethod
    def get_platform(self):
        """Return the platform name"""
        pass
    
    def read_csv(self, **kwargs):
        """Read CSV file with default encoding settings"""
        return pd.read_csv(self.file_path, **kwargs)
    
    def normalize_date(self, date_str, format_str):
        """Normalize date string to ISO format"""
        try:
            # 尝试使用指定的格式解析
            dt = datetime.strptime(date_str, format_str)
            return dt.isoformat()
        except ValueError:
            # 尝试其他常见的日期格式
            try_formats = [
                '%Y/%m/%d %H:%M',
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y %H:%M',
                '%m/%d/%Y %H:%M:%S',
                '%Y/%m/%d',
                '%Y-%m-%d',
                '%m/%d/%Y'
            ]
            
            for fmt in try_formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            # 如果所有格式都失败，返回原始字符串
            return date_str
    
    def get_parsed_data(self):
        """Get parsed data"""
        if self.data is None:
            self.parse()
        return self.data
    
    def to_notion_format(self):
        """Convert parsed data to Notion database format"""
        parsed_data = self.get_parsed_data()
        notion_records = []
        
        for _, record in parsed_data.iterrows():
            notion_record = self._convert_to_notion(record)
            notion_records.append(notion_record)
        
        return notion_records
    
    @abstractmethod
    def _convert_to_notion(self, record):
        """Convert a single record to Notion format"""
        pass
