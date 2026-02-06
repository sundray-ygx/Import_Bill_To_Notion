"""Configuration management using environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class."""

    # ==================== 原有配置（单用户模式） ====================

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

    # ==================== 账单复盘配置 ====================
    # 复盘数据库 ID
    NOTION_MONTHLY_REVIEW_DB = os.getenv("NOTION_MONTHLY_REVIEW_DB", "")
    NOTION_QUARTERLY_REVIEW_DB = os.getenv("NOTION_QUARTERLY_REVIEW_DB", "")
    NOTION_YEARLY_REVIEW_DB = os.getenv("NOTION_YEARLY_REVIEW_DB", "")

    # 复盘模板 ID
    NOTION_MONTHLY_TEMPLATE_ID = os.getenv("NOTION_MONTHLY_TEMPLATE_ID", "")
    NOTION_QUARTERLY_TEMPLATE_ID = os.getenv("NOTION_QUARTERLY_TEMPLATE_ID", "")
    NOTION_YEARLY_TEMPLATE_ID = os.getenv("NOTION_YEARLY_TEMPLATE_ID", "")

    # ==================== 多租户配置 ====================

    # 多租户模式开关 (true/false/auto)
    # - true: 强制启用多租户模式
    # - false: 强制单用户模式
    # - auto: 自动检测（存在数据库则多用户，否则单用户）
    MULTI_TENANT_ENABLED = os.getenv("MULTI_TENANT_ENABLED", "auto").lower()

    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/database.sqlite")

    # JWT配置
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # 文件上传配置
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(50 * 1024 * 1024)))  # 默认50MB
    ALLOWED_FILE_EXTENSIONS = os.getenv("ALLOWED_FILE_EXTENSIONS", ".csv,.txt,.xls,.xlsx").split(",")

    # 注册配置
    REGISTRATION_ENABLED = os.getenv("REGISTRATION_ENABLED", "true").lower() == "true"

    # ==================== 方法 ====================

    @classmethod
    def is_single_user_mode(cls) -> bool:
        """检测是否为单用户模式。

        Returns:
            True表示单用户模式，False表示多租户模式
        """
        # 如果明确设置为false，使用多租户模式
        if cls.MULTI_TENANT_ENABLED == "false":
            return True

        # 如果明确设置为true，使用多租户模式
        if cls.MULTI_TENANT_ENABLED == "true":
            return False

        # auto模式：检测数据库文件是否存在
        # 如果存在数据库，使用多租户模式；否则使用单用户模式
        db_exists = os.path.exists("data/database.sqlite")
        return not db_exists

    @classmethod
    def is_multi_tenant_mode(cls) -> bool:
        """检测是否为多租户模式。

        Returns:
            True表示多租户模式，False表示单用户模式
        """
        return not cls.is_single_user_mode()

    @classmethod
    def validate(cls):
        """验证必需的配置。

        在多租户模式下，验证SECRET_KEY。
        在单用户模式下，验证Notion配置。
        """
        if cls.is_multi_tenant_mode():
            # 多租户模式需要SECRET_KEY
            if not cls.SECRET_KEY:
                raise ValueError("SECRET_KEY is required in multi-tenant mode. "
                                 "Please set SECRET_KEY in your .env file.")
        else:
            # 单用户模式需要Notion配置
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
        """动态更新配置。

        Args:
            key: 配置键
            value: 配置值

        Returns:
            是否更新成功
        """
        if hasattr(cls, key):
            setattr(cls, key, value)
            return True
        return False

    @classmethod
    def get_mode_display(cls) -> str:
        """获取运行模式的显示名称。

        Returns:
            模式显示名称
        """
        if cls.is_single_user_mode():
            return "Single User Mode"
        return "Multi-Tenant Mode"

    @classmethod
    def ensure_secret_key(cls) -> str:
        """确保SECRET_KEY存在。

        如果没有配置SECRET_KEY，生成一个临时密钥并警告。

        Returns:
            SECRET_KEY
        """
        if not cls.SECRET_KEY:
            import secrets
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("SECRET_KEY not configured! Using a temporary key.")
            logger.warning("Please set SECRET_KEY in your .env file for production use.")
            temp_key = secrets.token_urlsafe(48)
            cls.SECRET_KEY = temp_key
            return temp_key
        return cls.SECRET_KEY
