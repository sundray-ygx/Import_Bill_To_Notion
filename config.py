import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration management class"""
    
    # Notion Configuration
    NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
    NOTION_INCOME_DATABASE_ID = os.getenv("NOTION_INCOME_DATABASE_ID", "")
    NOTION_EXPENSE_DATABASE_ID = os.getenv("NOTION_EXPENSE_DATABASE_ID", "")
    
    # Bill File Configuration
    DEFAULT_BILL_DIR = os.getenv("DEFAULT_BILL_DIR", "./bills")
    DEFAULT_BILL_PLATFORM = os.getenv("DEFAULT_BILL_PLATFORM", "alipay")
    
    # Scheduler Configuration
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
    SCHEDULER_CRON = os.getenv("SCHEDULER_CRON", "0 0 1 * *")  # Run on the 1st day of every month at 00:00
    
    # Log Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_fields = [
            ("NOTION_API_KEY", cls.NOTION_API_KEY),
            ("NOTION_INCOME_DATABASE_ID", cls.NOTION_INCOME_DATABASE_ID),
            ("NOTION_EXPENSE_DATABASE_ID", cls.NOTION_EXPENSE_DATABASE_ID)
        ]
        
        missing_fields = [field[0] for field in required_fields if not field[1]]
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
    
    @classmethod
    def update(cls, key, value):
        """Update configuration dynamically"""
        if hasattr(cls, key):
            setattr(cls, key, value)
            return True
        return False