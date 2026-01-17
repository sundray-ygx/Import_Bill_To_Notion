"""Notion API client for bill management."""

from notion_client import Client as NotionApiClient, APIResponseError
from config import Config
import logging


logger = logging.getLogger(__name__)

# Notion API 超时配置（秒）
NOTION_TIMEOUT = 30


class NotionClient:
    """Notion API client wrapper.

    支持单用户模式和多租户模式：
    - 单用户模式：使用全局配置的 Notion API key 和数据库 ID
    - 多租户模式：根据 user_id 从数据库获取用户的 Notion 配置
    """

    def __init__(self, user_id=None):
        """初始化 Notion 客户端。

        Args:
            user_id: 用户ID（多租户模式必需）
        """
        self.user_id = user_id

        if Config.is_single_user_mode():
            # 单用户模式：使用全局配置
            logger.info(f"Initializing Notion client in single-user mode (API key: {'***' if Config.NOTION_API_KEY else 'not configured'})")
            self.client = NotionApiClient(auth=Config.NOTION_API_KEY, timeout_ms=NOTION_TIMEOUT * 1000)
            self.income_db = Config.NOTION_INCOME_DATABASE_ID
            self.expense_db = Config.NOTION_EXPENSE_DATABASE_ID
        else:
            # 多用户模式：从数据库获取用户配置
            if not user_id:
                raise ValueError("user_id is required in multi-tenant mode")

            logger.info(f"Initializing Notion client for user {user_id}")
            config = self._get_user_notion_config(user_id)

            # 脱敏日志
            masked_key = f"{config['api_key'][:8]}***" if config['api_key'] else "not configured"
            logger.info(f"User {user_id} Notion API key: {masked_key}")

            self.client = NotionApiClient(auth=config['api_key'], timeout_ms=NOTION_TIMEOUT * 1000)
            self.income_db = config['income_db']
            self.expense_db = config['expense_db']

    def _get_user_notion_config(self, user_id):
        """从数据库获取用户的 Notion 配置。

        Args:
            user_id: 用户ID

        Returns:
            包含配置信息的字典，包含 api_key, income_db, expense_db

        Raises:
            ValueError: 配置不存在时
        """
        from database import get_db_context
        from models import UserNotionConfig

        with get_db_context() as db:
            config = db.query(UserNotionConfig).filter(
                UserNotionConfig.user_id == user_id
            ).first()

            if not config:
                raise ValueError(f"Notion config not found for user {user_id}")

            # 在会话关闭前提取所有需要的值
            # 这样可以避免会话关闭后访问对象属性的错误
            return {
                'api_key': config.notion_api_key,
                'income_db': config.notion_income_database_id,
                'expense_db': config.notion_expense_database_id,
                'is_verified': config.is_verified
            }

    def _clean_properties(self, properties: dict) -> tuple:
        """Clean properties and extract income/expense type.

        Returns:
            Tuple of (cleaned_properties, income_expense_type)
        """
        cleaned = {}
        income_expense_type = ""

        # Extract income/expense type first
        if 'Income Expense' in properties:
            prop = properties['Income Expense']
            if prop and 'select' in prop and prop['select']:
                name = prop['select'].get('name', '').strip()
                if name:
                    income_expense_type = name

        # Clean each property
        for name, value in properties.items():
            if value is None:
                continue
            if isinstance(value, dict) and not value:
                continue
            if name == 'Income Expense':
                continue

            cleaned_prop = self._clean_property(value)
            if cleaned_prop:
                cleaned[name] = cleaned_prop

        # Ensure at least Name exists
        if not cleaned:
            cleaned['Name'] = {'title': [{'text': {'content': 'Unknown Record'}}]}

        return cleaned, income_expense_type

    def _clean_property(self, value: dict) -> dict:
        """Clean a single property value."""
        if 'select' in value:
            select = value['select']
            if select and select.get('name'):
                return {'select': {'name': str(select['name']).strip()}}
            return {}

        if 'title' in value:
            if value['title'] and isinstance(value['title'], list):
                return {'title': value['title']}
            return {}

        if 'rich_text' in value:
            return {'rich_text': value['rich_text']}

        if 'number' in value:
            num = value['number']
            if num is not None:
                try:
                    return {'number': float(num)}
                except (ValueError, TypeError):
                    pass
            return {}

        if 'date' in value:
            date = value['date']
            if date and isinstance(date, dict) and 'start' in date:
                return {'date': date}

        return {}

    def create_page(self, properties: dict):
        """Create a page in Notion."""
        cleaned, income_expense_type = self._clean_properties(properties)

        # Route to income or expense database
        db_id = self.income_db if income_expense_type == '收入' else self.expense_db

        response = self.client.pages.create(
            parent={"database_id": db_id},
            properties=cleaned
        )
        logger.info(f"Created page: {response['id']} (DB: {'income' if income_expense_type == '收入' else 'expense'})")
        return response

    def batch_import(self, records: list, batch_size: int = 10) -> dict:
        """Import records in batches."""
        logger.info(f"Batch import: {len(records)} records, batch size: {batch_size}")

        imported, skipped = 0, 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_num = i // batch_size + 1
            total = (len(records) - 1) // batch_size + 1

            logger.info(f"Processing batch {batch_num}/{total}, {len(batch)} records")

            for record in batch:
                try:
                    if 'Date' not in record or 'Price' not in record:
                        logger.error(f"Missing required fields: {record}")
                        skipped += 1
                        continue
                    self.create_page(record)
                    imported += 1
                except Exception as e:
                    logger.error(f"Failed to import record: {e}")
                    skipped += 1

            logger.info(f"Batch {batch_num}/{total} complete")

        logger.info(f"Import complete: {imported} imported, {skipped} skipped")
        return {"imported": imported, "updated": 0, "skipped": skipped}

    def verify_connection(self) -> bool:
        """验证 Notion API 连接。

        尝试连接到 Notion API 并验证配置是否正确。

        Returns:
            bool: 连接成功返回 True，否则返回 False
        """
        logger.info("Verifying Notion connection...")
        try:
            # 验证 API 密钥
            logger.debug("Fetching user info from Notion API...")
            user = self.client.users.me()
            logger.info(f"API key valid, user: {user.get('name', 'unknown')}")

            # 验证收入数据库
            logger.debug(f"Fetching income database: {self.income_db[:8]}***")
            income_db = self.client.databases.retrieve(database_id=self.income_db)
            income_title = income_db.get('title', [{}])[0].get('text', {}).get('content', 'unknown')
            logger.info(f"Income DB accessible: {income_title}")

            # 验证支出数据库
            logger.debug(f"Fetching expense database: {self.expense_db[:8]}***")
            expense_db = self.client.databases.retrieve(database_id=self.expense_db)
            expense_title = expense_db.get('title', [{}])[0].get('text', {}).get('content', 'unknown')
            logger.info(f"Expense DB accessible: {expense_title}")

            logger.info("Connection verified successfully")
            return True

        except APIResponseError as e:
            # Notion API 返回了错误响应
            logger.error(f"Notion API error: {e}")
            if hasattr(e, 'body') and e.body:
                logger.error(f"Error details: {e.body}")
            if hasattr(e, 'status'):
                logger.error(f"Status code: {e.status}")
            return False

        except Exception as e:
            # 其他错误（网络错误、超时等）
            error_type = type(e).__name__
            logger.error(f"Connection failed ({error_type}): {e}")
            return False
