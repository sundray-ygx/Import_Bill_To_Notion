"""Notion API client for bill management."""

from notion_client import Client as NotionApiClient
from config import Config
import logging


logger = logging.getLogger(__name__)


class NotionClient:
    """Notion API client wrapper."""

    def __init__(self):
        logger.info(f"Initializing Notion client (API key: {'***' if Config.NOTION_API_KEY else 'not configured'})")
        self.client = NotionApiClient(auth=Config.NOTION_API_KEY)
        self.income_db = Config.NOTION_INCOME_DATABASE_ID
        self.expense_db = Config.NOTION_EXPENSE_DATABASE_ID

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
        """Verify Notion API connection."""
        logger.info("Verifying Notion connection...")
        try:
            user = self.client.users.me()
            logger.info(f"API key valid, user: {user.get('name', 'unknown')}")

            income_db = self.client.databases.retrieve(database_id=self.income_db)
            logger.info(f"Income DB accessible: {income_db.get('title', [{}])[0].get('text', {}).get('content', 'unknown')}")

            expense_db = self.client.databases.retrieve(database_id=self.expense_db)
            logger.info(f"Expense DB accessible: {expense_db.get('title', [{}])[0].get('text', {}).get('content', 'unknown')}")

            logger.info("Connection verified")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
