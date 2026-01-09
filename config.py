"""Configuration management using environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class."""

    # Notion Configuration
    NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
    NOTION_INCOME_DATABASE_ID = os.getenv("NOTION_INCOME_DATABASE_ID", "")
    NOTION_EXPENSE_DATABASE_ID = os.getenv("NOTION_EXPENSE_DATABASE_ID", "")

    # Bill File Configuration
    DEFAULT_BILL_DIR = os.getenv("DEFAULT_BILL_DIR", "./bills")
    DEFAULT_BILL_PLATFORM = os.getenv("DEFAULT_BILL_PLATFORM", "alipay")

    # Scheduler Configuration
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
    SCHEDULER_CRON = os.getenv("SCHEDULER_CRON", "0 0 1 * *")

    # Log Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required = [
            ("NOTION_API_KEY", cls.NOTION_API_KEY),
            ("NOTION_INCOME_DATABASE_ID", cls.NOTION_INCOME_DATABASE_ID),
            ("NOTION_EXPENSE_DATABASE_ID", cls.NOTION_EXPENSE_DATABASE_ID)
        ]
        missing = [field for field, value in required if not value]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")

    @classmethod
    def update(cls, key: str, value):
        """Update configuration dynamically."""
        if hasattr(cls, key):
            setattr(cls, key, value)
            return True
        return False
