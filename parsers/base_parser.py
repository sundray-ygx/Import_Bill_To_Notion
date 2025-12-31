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
            dt = datetime.strptime(date_str, format_str)
            return dt.isoformat()
        except ValueError:
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
