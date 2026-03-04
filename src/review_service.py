"""
账单复盘服务
从 Notion 收支数据库读取数据，生成周期性复盘报告，写入复盘数据库
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dateutil.relativedelta import relativedelta
from src.notion_api import NotionClient


logger = logging.getLogger(__name__)


class ReviewService:
    """账单复盘服务"""

    # 复盘类型
    TYPE_MONTHLY = 'monthly'
    TYPE_QUARTERLY = 'quarterly'
    TYPE_YEARLY = 'yearly'

    # 类级别的数据库结构缓存，避免重复查询
    _database_structure_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self, user_id: Optional[int] = None):
        """初始化复盘服务

        Args:
            user_id: 用户ID（多租户模式必需）

        Raises:
            ValueError: 用户未配置 Notion API key 或数据库 ID
        """
        self.user_id = user_id
        try:
            self.notion_client = NotionClient(user_id=user_id)
        except ValueError as e:
            logger.error(f"Failed to initialize Notion client for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing Notion client: {e}")
            raise

    def fetch_transactions(
        self,
        start_date: date,
        end_date: date,
        database_type: str = 'all'
    ) -> List[Dict[str, Any]]:
        """获取指定时间范围的交易数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            database_type: 数据库类型 (income/expense/all)

        Returns:
            交易记录列表
        """
        logger.info(f"Fetching transactions from {start_date} to {end_date}")

        transactions = []

        # 计算日期范围天数
        from datetime import datetime
        delta = end_date - start_date
        days = delta.days + 1

        # 如果日期范围超过90天，分批查询以提高性能
        if days > 90:
            logger.info(f"Date range is {days} days (> 90), using batch queries")
            transactions = self._fetch_transactions_in_batches(
                self.notion_client.income_db if database_type in ['income', 'all'] else None,
                self.notion_client.expense_db if database_type in ['expense', 'all'] else None,
                start_date,
                end_date
            )
        else:
            # 查询收入数据库
            if database_type in ['income', 'all']:
                income_data = self._query_database(
                    self.notion_client.income_db,
                    start_date,
                    end_date
                )
                for item in income_data:
                    item['type'] = 'income'
                    transactions.append(item)

            # 查询支出数据库
            if database_type in ['expense', 'all']:
                expense_data = self._query_database(
                    self.notion_client.expense_db,
                    start_date,
                    end_date
                )
                for item in expense_data:
                    item['type'] = 'expense'
                    transactions.append(item)

        logger.info(f"Fetched {len(transactions)} transactions")
        return transactions

    def _fetch_transactions_in_batches(
        self,
        income_db: Optional[str],
        expense_db: Optional[str],
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """分批获取交易数据（适用于大日期范围）

        将日期范围拆分为多个小批次，每批最多30天
        这样可以避免单次查询数据量过大导致超时

        Args:
            income_db: 收入数据库ID
            expense_db: 支出数据库ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            交易记录列表
        """
        from datetime import timedelta

        transactions = []
        batch_start = start_date
        batch_size_days = 30  # 每批30天

        while batch_start <= end_date:
            batch_end = min(batch_start + timedelta(days=batch_size_days - 1), end_date)

            logger.info(f"Fetching batch: {batch_start} to {batch_end}")

            # 查询收入数据库
            if income_db:
                try:
                    income_data = self._query_database(income_db, batch_start, batch_end)
                    for item in income_data:
                        item['type'] = 'income'
                        transactions.append(item)
                except Exception as e:
                    logger.warning(f"Failed to fetch income data for batch {batch_start} to {batch_end}: {e}")

            # 查询支出数据库
            if expense_db:
                try:
                    expense_data = self._query_database(expense_db, batch_start, batch_end)
                    for item in expense_data:
                        item['type'] = 'expense'
                        transactions.append(item)
                except Exception as e:
                    logger.warning(f"Failed to fetch expense data for batch {batch_start} to {batch_end}: {e}")

            batch_start = batch_end + timedelta(days=1)

        return transactions

    def _query_database(
        self,
        database_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """查询指定数据库

        Args:
            database_id: 数据库ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            查询结果列表
        """
        # 直接使用 databases.query API，更高效
        logger.info(f"Querying database {database_id[:8]}... with date filter")
        return self._query_by_database_query(database_id, start_date, end_date)

    def _query_by_database_query(
        self,
        database_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """使用 databases.query API 查询数据库（标准方法）

        Args:
            database_id: 数据库ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            查询结果列表
        """
        import time

        results = []
        has_more = True
        next_cursor = None
        max_retries = 3  # 增加重试次数

        # 首先尝试一个简单的查询来验证数据库可访问性
        logger.info(f"Testing database {database_id[:8]}... accessibility with simple query...")
        logger.info(f"Full database ID: {database_id}")
        logger.info(f"Database ID length: {len(database_id)}")

        try:
            # 尝试使用 databases.retrieve API 来验证数据库
            logger.info("Trying databases.retrieve API first...")
            db_info = self.notion_client.client.databases.retrieve(database_id=database_id)
            logger.info(f"Database retrieve successful: {db_info.get('title', [{}])[0].get('text', {}).get('content', 'unknown')}")

            # 如果 retrieve 成功，尝试 query
            simple_response = self.notion_client.client.request(
                path=f"/databases/{database_id}/query",
                method="POST",
                body={}
            )
            logger.info(f"Simple query successful, got {len(simple_response.get('results', []))} results")
        except Exception as e:
            logger.error(f"Database access failed: {e}")
            if hasattr(e, 'body') and e.body:
                logger.error(f"Error body: {e.body}")
            if hasattr(e, 'status') and e.status:
                logger.error(f"HTTP status: {e.status}")

            # 简单查询失败，可能是数据库不存在或者权限问题
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "forbidden" in error_msg:
                raise RuntimeError(f"无权访问数据库 {database_id[:8]}...。请检查：1) API 集成是否已授予该数据库的访问权限 2) 在 Notion 中检查集成设置")
            elif "not found" in error_msg or "invalid" in error_msg:
                raise RuntimeError(f"数据库 ID {database_id[:8]}... 无效或数据库不存在。请检查：1) 数据库 ID 是否正确复制 2) 数据库是否已共享给集成")
            else:
                raise RuntimeError(f"无法访问数据库 {database_id[:8]}...。请检查：1) 数据库 ID 是否正确 2) API 密钥是否有访问权限。错误详情: {e}")

        while has_more:
            # 构建 API 请求体
            body = {
                "filter": {
                    "and": [
                        {
                            "property": "Date",
                            "date": {
                                "on_or_after": start_date.isoformat()
                            }
                        },
                        {
                            "property": "Date",
                            "date": {
                                "on_or_before": end_date.isoformat()
                            }
                        }
                    ]
                }
            }

            if next_cursor:
                body["start_cursor"] = next_cursor

            # 添加分页，避免一次查询过多数据
            if not next_cursor:
                body["page_size"] = 100  # 首次查询获取 100 条以提高性能

            for attempt in range(max_retries):
                try:
                    logger.info(f"Querying database {database_id[:8]}... from {start_date} to {end_date} (attempt {attempt + 1}/{max_retries})")
                    logger.info(f"Request body: {body}")  # 改为 INFO 级别以便查看
                    logger.info(f"Date filter: {start_date.isoformat()} to {end_date.isoformat()}")

                    # 验证 database_id 格式
                    if not database_id or len(database_id) < 32:
                        raise ValueError(f"Invalid database_id: '{database_id}'. Database ID must be 32 characters.")

                    response = self.notion_client.client.request(
                        path=f"/databases/{database_id}/query",
                        method="POST",
                        body=body
                    )

                    logger.debug("Response received, processing results...")

                    results.extend(response.get("results", []))
                    has_more = response.get("has_more", False)
                    next_cursor = response.get("next_cursor")
                    logger.info(f"Fetched {len(response.get('results', []))} records, has_more={has_more}, total so far={len(results)}")

                    break

                except Exception as e:
                    error_str = str(e).lower()
                    error_msg = str(e)
                    is_timeout = "timeout" in error_str
                    is_invalid_url = "invalid request url" in error_str

                    logger.error(f"Database query error (attempt {attempt + 1}/{max_retries}): {e}")

                    # 尝试获取更详细的错误信息
                    if hasattr(e, 'body') and e.body:
                        logger.error(f"Notion API error body: {e.body}")
                    if hasattr(e, 'status') and e.status:
                        logger.error(f"Notion API status code: {e.status}")

                    if attempt == max_retries - 1:
                        logger.error(f"All {max_retries} attempts failed")

                        # 提供更具体的错误消息
                        if is_invalid_url or (hasattr(e, 'status') and e.status == 400):
                            # HTTP 400 通常意味着请求体有问题
                            error_detail = ""
                            if hasattr(e, 'body') and e.body:
                                try:
                                    import json
                                    error_body = json.loads(e.body) if isinstance(e.body, str) else e.body
                                    if isinstance(error_body, dict):
                                        error_detail = error_body.get('message', '')
                                except (ValueError, TypeError, json.JSONDecodeError):
                                    pass

                            if "filter" in error_detail.lower() or "date" in error_detail.lower():
                                raise RuntimeError(f"数据库查询失败：Notion 数据库中可能没有 'Date' 属性，或者属性名不匹配。请检查 Notion 数据库结构。错误详情: {error_detail}")
                            else:
                                raise RuntimeError(f"数据库查询失败 (HTTP 400)。请检查：1) Notion 数据库 ID 是否正确 2) 数据库是否有 'Date' 属性。错误详情: {error_detail}")
                        elif is_timeout:
                            logger.warning("Timeout error - query took too long, try narrowing the date range")
                            raise RuntimeError(f"Query timeout after {max_retries} attempts. The date range may be too large.")
                        else:
                            raise RuntimeError(f"Failed to query database after {max_retries} attempts: {e}")

                    # 使用指数退避策略
                    wait_time = min(2 ** attempt, 10)  # 最多等待10秒
                    logger.info(f"Waiting {wait_time}s before retry (exponential backoff)...")
                    time.sleep(wait_time)

        return results

    def aggregate_by_category(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """按分类聚合数据

        Args:
            transactions: 交易记录列表

        Returns:
            分类汇总数据 {category: {income: x, expense: y}}
        """
        categories = {}

        for transaction in transactions:
            # 提取分类
            props = transaction.get("properties", {})
            category_prop = props.get("Category", {})
            category_name = "未分类"

            if category_prop.get("select"):
                category_name = category_prop["select"].get("name", "未分类")

            # 提取金额
            price_prop = props.get("Price", {})
            amount = price_prop.get("number", 0) or 0

            # 获取类型
            trans_type = transaction.get("type", "expense")

            if category_name not in categories:
                categories[category_name] = {"income": 0.0, "expense": 0.0}

            categories[category_name][trans_type] += amount

        return categories

    def calculate_summary(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算汇总数据

        Args:
            transactions: 交易记录列表

        Returns:
            汇总数据
        """
        total_income = 0.0
        total_expense = 0.0
        transaction_count = len(transactions)

        for transaction in transactions:
            props = transaction.get("properties", {})
            price_prop = props.get("Price", {})
            amount = price_prop.get("number", 0) or 0
            trans_type = transaction.get("type", "expense")

            if trans_type == "income":
                total_income += amount
            else:
                total_expense += amount

        return {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "net_balance": round(total_income - total_expense, 2),
            "transaction_count": transaction_count
        }

    def get_review_database_id(self, review_type: str) -> Optional[str]:
        """获取复盘数据库ID

        Args:
            review_type: 复盘类型 (monthly/quarterly/yearly)

        Returns:
            数据库ID，未配置返回None
        """
        from src.config import Config
        import os

        # 从环境变量获取
        env_key = f"NOTION_{review_type.upper()}_REVIEW_DB"
        db_id = os.getenv(env_key, "")

        if db_id:
            logger.debug(f"从环境变量获取 {review_type} 复盘数据库ID: {db_id[:8]}...")
            return db_id

        # 从用户配置获取（多租户模式）
        if self.user_id and Config.is_multi_tenant_mode():
            from src.services.database import get_db_context
            from src.models import UserNotionConfig

            with get_db_context() as db:
                config = db.query(UserNotionConfig).filter(
                    UserNotionConfig.user_id == self.user_id
                ).first()

                if config:
                    field_map = {
                        "monthly": "notion_monthly_review_db",
                        "quarterly": "notion_quarterly_review_db",
                        "yearly": "notion_yearly_review_db"
                    }
                    field_name = field_map.get(review_type)
                    if field_name and hasattr(config, field_name):
                        user_db_id = getattr(config, field_name)
                        if user_db_id:
                            logger.debug(f"从用户配置获取 {review_type} 复盘数据库ID: {user_db_id[:8]}...")
                            return user_db_id

        logger.warning(f"{review_type} 复盘数据库未配置")
        return None

    def create_review_page(
        self,
        review_type: str,
        period: str,
        data: Dict[str, Any]
    ) -> Optional[str]:
        """创建复盘页面

        使用模板页面创建复盘，填充真实数据

        Args:
            review_type: 复盘类型 (monthly/quarterly/yearly)
            period: 周期标识 (如 2024-01, 2024-Q1, 2024)
            data: 复盘数据

        Returns:
            创建的页面ID，失败返回None
        """
        from src.config import Config
        import os

        # 获取复盘数据库ID
        database_id = self.get_review_database_id(review_type)
        if not database_id:
            logger.error(f"Review database not configured for type: {review_type}")
            return None

        # 获取模板页面ID
        template_id_key = f"NOTION_{review_type.upper()}_TEMPLATE_ID"
        template_id = os.getenv(template_id_key, "")

        if not template_id:
            logger.warning(f"Template not configured for {review_type}, falling back to basic page")
            return self._create_basic_review_page(review_type, period, data, database_id)

        try:
            # 从模板页面复制内容
            template_page = self.notion_client.client.pages.retrieve(page_id=template_id)

            # 构建页面属性（使用模板的属性格式）
            properties = self._build_review_properties_from_template(template_page, period, data, database_id)

            # 创建新页面，使用模板的内容
            response = self.notion_client.client.pages.create(
                parent={"database_id": database_id},
                properties=properties,
                children=self._get_template_children(template_page, period, data)
            )

            page_id = response.get("id")
            logger.info(f"Review page created from template: {page_id}")
            return page_id

        except Exception as e:
            logger.error(f"Failed to create review page from template: {e}")
            # 如果模板创建失败，回退到基本页面
            return self._create_basic_review_page(review_type, period, data, database_id)

    def _create_basic_review_page(
        self,
        review_type: str,
        period: str,
        data: Dict[str, Any],
        database_id: str
    ) -> Optional[str]:
        """创建基本复盘页面（不使用模板）

        Args:
            review_type: 复盘类型
            period: 周期标识
            data: 复盘数据
            database_id: 数据库ID

        Returns:
            创建的页面ID，失败返回None
        """
        try:
            logger.info(f"开始创建基本复盘页面，周期: {period}")

            # 首先获取数据库的结构，找到标题属性
            logger.info(f"获取数据库结构: {database_id[:8]}...")
            database_info = self.notion_client.client.databases.retrieve(database_id=database_id)
            database_properties = database_info.get("properties", {})

            logger.info(f"数据库属性数量: {len(database_properties)}")
            logger.debug(f"数据库属性: {list(database_properties.keys())}")

            # 查找标题类型的属性（通常是 "Name" 或 "名称" 或 "title"）
            title_property_id = None
            title_property_name = None

            for prop_name, prop_config in database_properties.items():
                if prop_config.get("type") == "title":
                    title_property_id = prop_name
                    title_property_name = prop_name
                    break

            if not title_property_id:
                logger.error("No title property found in database")
                return None

            logger.info(f"找到标题属性: {title_property_name}")

            # 使用实际找到的标题属性名
            properties = {
                title_property_name: {
                    "title": [
                        {
                            "text": {
                                "content": f"{period} 账单复盘"
                            }
                        }
                    ]
                }
            }

            # 填充其他属性
            summary = data.get("summary", {})
            for prop_name, prop_config in database_properties.items():
                if prop_name == title_property_name:
                    continue

                prop_type = prop_config.get("type")

                if prop_type == "number":
                    # 根据属性名映射到数据字段
                    value_map = {
                        "Total Income": summary.get("total_income", 0),
                        "total_income": summary.get("total_income", 0),
                        "收入": summary.get("total_income", 0),
                        "Total Expense": summary.get("total_expense", 0),
                        "total_expense": summary.get("total_expense", 0),
                        "支出": summary.get("total_expense", 0),
                        "Net Balance": summary.get("net_balance", 0),
                        "net_balance": summary.get("net_balance", 0),
                        "结余": summary.get("net_balance", 0),
                        "Transaction Count": data.get("transaction_count", 0),
                        "transaction_count": data.get("transaction_count", 0),
                        "交易数": data.get("transaction_count", 0)
                    }
                    value = value_map.get(prop_name)
                    if value is not None:
                        properties[prop_name] = {"number": value}
                        logger.info(f"填充数值属性 {prop_name} = {value}")

                elif prop_type == "date":
                    date_value = None
                    if "Start" in prop_name or "start" in prop_name.lower() or "开始" in prop_name:
                        date_value = data.get("start_date", "")
                    elif "End" in prop_name or "end" in prop_name.lower() or "结束" in prop_name:
                        date_value = data.get("end_date", "")

                    if date_value:
                        properties[prop_name] = {"date": {"start": date_value}}
                        logger.info(f"填充日期属性 {prop_name} = {date_value}")

                elif prop_type == "rich_text":
                    properties[prop_name] = {
                        "rich_text": [
                            {
                                "text": {
                                    "content": period
                                }
                            }
                        ]
                    }
                    logger.info(f"填充文本属性 {prop_name} = {period}")

            logger.info(f"准备创建页面，属性数量: {len(properties)}")
            logger.debug(f"页面属性: {properties}")

            response = self.notion_client.client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )

            page_id = response.get("id")
            logger.info(f"页面创建成功: {page_id}")

            # 添加内容块
            logger.info("开始添加内容块...")
            self._add_review_content_blocks(page_id, period, data)

            logger.info(f"基本复盘页面创建完成: {page_id}")
            return page_id

        except Exception as e:
            logger.error(f"Failed to create basic review page: {e}")
            # 输出更详细的错误信息
            if hasattr(e, 'body') and e.body:
                logger.error(f"Error body: {e.body}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _build_review_properties_from_template(
        self,
        template_page: Dict[str, Any],
        period: str,
        data: Dict[str, Any],
        database_id: str
    ) -> Dict[str, Any]:
        """从模板页面构建属性

        Args:
            template_page: 模板页面数据
            period: 周期标识
            data: 复盘数据
            database_id: 目标数据库ID

        Returns:
            页面属性
        """
        logger.info("开始从模板构建属性")

        # 获取目标数据库的属性结构
        logger.info(f"获取目标数据库结构: {database_id[:8]}...")
        database_info = self.notion_client.client.databases.retrieve(database_id=database_id)
        database_properties = database_info.get("properties", {})

        logger.info(f"目标数据库属性数量: {len(database_properties)}")

        # 找到标题属性
        title_property_name = None
        for prop_name, prop_config in database_properties.items():
            if prop_config.get("type") == "title":
                title_property_name = prop_name
                break

        if not title_property_name:
            logger.error("No title property found in target database")
            raise ValueError("目标数据库没有标题属性")

        logger.info(f"找到标题属性: {title_property_name}")

        # 获取数据摘要
        summary = data.get("summary", {})

        # 构建新页面的属性
        properties = {
            title_property_name: {
                "title": [
                    {
                        "text": {
                            "content": f"{period} 账单复盘"
                        }
                    }
                ]
            }
        }

        # 根据目标数据库的属性类型填充数据
        for prop_name, prop_config in database_properties.items():
            if prop_name == title_property_name:
                continue

            prop_type = prop_config.get("type")

            if prop_type == "number":
                # 根据属性名映射到数据字段（修复：从 summary 中获取）
                value_map = {
                    "Total Income": summary.get("total_income", 0),
                    "total_income": summary.get("total_income", 0),
                    "收入": summary.get("total_income", 0),
                    "Total Expense": summary.get("total_expense", 0),
                    "total_expense": summary.get("total_expense", 0),
                    "支出": summary.get("total_expense", 0),
                    "Net Balance": summary.get("net_balance", 0),
                    "net_balance": summary.get("net_balance", 0),
                    "结余": summary.get("net_balance", 0),
                    "Transaction Count": data.get("transaction_count", 0),
                    "transaction_count": data.get("transaction_count", 0),
                    "交易数": data.get("transaction_count", 0)
                }
                value = value_map.get(prop_name)
                if value is not None:  # 填充所有值，包括零值
                    properties[prop_name] = {"number": value}
                    logger.info(f"填充数值属性 {prop_name} = {value}")

            elif prop_type == "date":
                date_value = None
                if ("Start" in prop_name or "start" in prop_name.lower() or "开始" in prop_name):
                    date_value = data.get("start_date", "")
                elif ("End" in prop_name or "end" in prop_name.lower() or "结束" in prop_name):
                    date_value = data.get("end_date", "")

                if date_value:
                    properties[prop_name] = {"date": {"start": date_value}}
                    logger.info(f"填充日期属性 {prop_name} = {date_value}")

            elif prop_type == "rich_text":
                properties[prop_name] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": period
                            }
                        }
                    ]
                }
                logger.info(f"填充文本属性 {prop_name} = {period}")

            elif prop_type == "select":
                # 如果有 select 类型的属性，可以设置周期类型
                properties[prop_name] = {
                    "select": {"name": period}
                }
                logger.info(f"填充选择属性 {prop_name} = {period}")

        logger.info(f"属性构建完成，共填充 {len(properties)} 个属性")
        logger.debug(f"构建的属性: {properties}")
        return properties

    def _get_template_children(
        self,
        template_page: Dict[str, Any],
        period: str,
        data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """获取模板的子块并填充数据

        Args:
            template_page: 模板页面数据
            period: 周期标识
            data: 复盘数据

        Returns:
            填充数据后的子块列表
        """
        logger.info("开始获取并处理模板子块")

        # 获取模板的子块
        template_blocks = self.notion_client.client.blocks.children.list(
            block_id=template_page["id"]
        )

        logger.info(f"获取到 {len(template_blocks.get('results', []))} 个模板块")

        children = []
        summary = data.get("summary", {})
        categories = data.get("categories", {})

        for block in template_blocks.get("results", []):
            block_copy = block.copy()
            block_type = block_copy.get("type")

            # 处理不同类型的块
            if block_type == "paragraph":
                # 段落块，替换占位符
                text_content = self._replace_placeholders_in_text(
                    block_copy["paragraph"],
                    period,
                    data
                )
                block_copy["paragraph"] = text_content

            elif block_type in ["heading_1", "heading_2", "heading_3"]:
                # 标题块，替换占位符
                heading_key = block_type
                text_content = self._replace_placeholders_in_text(
                    block_copy[heading_key],
                    period,
                    data
                )
                block_copy[heading_key] = text_content

            elif block_type == "bulleted_list_item":
                # 项目符号列表，替换占位符
                text_content = self._replace_placeholders_in_text(
                    block_copy["bulleted_list_item"],
                    period,
                    data
                )
                block_copy["bulleted_list_item"] = text_content

            elif block_type == "numbered_list_item":
                # 编号列表，替换占位符
                text_content = self._replace_placeholders_in_text(
                    block_copy["numbered_list_item"],
                    period,
                    data
                )
                block_copy["numbered_list_item"] = text_content

            elif block_type == "to_do":
                # 待办事项，替换占位符
                text_content = self._replace_placeholders_in_text(
                    block_copy["to_do"],
                    period,
                    data
                )
                block_copy["to_do"] = text_content

            # 处理特殊占位符：{{categories_table}}
            if block_type == "paragraph":
                text_content = block_copy.get("paragraph", {})
                if "rich_text" in text_content:
                    for text_obj in text_content["rich_text"]:
                        if "text" in text_obj and "content" in text_obj["text"]:
                            content = text_obj["text"]["content"]
                            # 如果包含分类表格占位符，生成分类表格
                            if "{{categories_table}}" in content:
                                # 替换为分类表格
                                table_blocks = self._generate_category_table_block(categories, summary)
                                if table_blocks:
                                    children.extend(table_blocks)
                                continue  # 跳过原段落

            children.append(block_copy)

        logger.info(f"处理后的子块数量: {len(children)}")
        return children

    def _replace_placeholders_in_text(
        self,
        text_block: Dict[str, Any],
        period: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """替换文本块中的占位符

        Args:
            text_block: 文本块（paragraph、heading等）
            period: 周期标识
            data: 复盘数据

        Returns:
            替换后的文本块
        """
        summary = data.get("summary", {})
        categories = data.get("categories", {})

        # 构建替换数据
        replacements = {
            "{{period}}": period,
            "{{start_date}}": data.get("start_date", ""),
            "{{end_date}}": data.get("end_date", ""),
            "{{total_income}}": f"{summary.get('total_income', 0):.2f}",
            "{{total_expense}}": f"{summary.get('total_expense', 0):.2f}",
            "{{net_balance}}": f"{summary.get('net_balance', 0):.2f}",
            "{{transaction_count}}": str(data.get("transaction_count", 0))
        }

        # 添加分类数据替换（收入TOP5和支出TOP5）
        expense_categories = sorted(
            [(cat, amounts.get('expense', 0)) for cat, amounts in categories.items() if amounts.get('expense', 0) > 0],
            key=lambda x: x[1],
            reverse=True
        )[:5]

        income_categories = sorted(
            [(cat, amounts.get('income', 0)) for cat, amounts in categories.items() if amounts.get('income', 0) > 0],
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # 添加收入TOP5替换
        for i, (cat, amount) in enumerate(income_categories, 1):
            replacements[f"{{{{income_top{i}_category}}}}"] = cat
            replacements[f"{{{{income_top{i}_amount}}}}"] = f"{amount:.2f}"

        # 添加支出TOP5替换
        for i, (cat, amount) in enumerate(expense_categories, 1):
            replacements[f"{{{{expense_top{i}_category}}}}"] = cat
            replacements[f"{{{{expense_top{i}_amount}}}}"] = f"{amount:.2f}"

        # 替换文本内容
        if "rich_text" in text_block:
            for text in text_block["rich_text"]:
                if "text" in text and "content" in text["text"]:
                    content = text["text"]["content"]
                    for placeholder, value in replacements.items():
                        content = content.replace(placeholder, str(value))
                    text["text"]["content"] = content

        return text_block

    def _generate_category_table_block(self, categories: Dict[str, Dict[str, float]], summary: Dict[str, float]) -> List[Dict[str, Any]]:
        """生成分类的表格块

        Args:
            categories: 分类数据 {"category_name": {"income": 0, "expense": 100}}
            summary: 摘要数据

        Returns:
            表格块列表
        """
        logger.info("开始生成分类表格块")

        blocks = []

        # 添加表格标题
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "📊 分类统计"}
                    }
                ]
            }
        })

        # 生成支出分类列表
        expense_categories = sorted(
            [(cat, amounts.get('expense', 0)) for cat, amounts in categories.items() if amounts.get('expense', 0) > 0],
            key=lambda x: x[1],
            reverse=True
        )

        if expense_categories:
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "支出分类"}
                        }
                    ]
                }
            })

            for cat, amount in expense_categories:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"{cat}: ¥{amount:.2f}"}
                            }
                        ]
                    }
                })

        # 生成收入分类列表
        income_categories = sorted(
            [(cat, amounts.get('income', 0)) for cat, amounts in categories.items() if amounts.get('income', 0) > 0],
            key=lambda x: x[1],
            reverse=True
        )

        if income_categories:
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "收入分类"}
                        }
                    ]
                }
            })

            for cat, amount in income_categories:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"{cat}: ¥{amount:.2f}"}
                            }
                        ]
                    }
                })

        logger.info(f"生成了 {len(blocks)} 个分类表格块")
        return blocks

    def _add_review_content_blocks(
        self,
        page_id: str,
        period: str,
        data: Dict[str, Any]
    ) -> None:
        """添加复盘内容块（按照人工复盘的格式）

        Args:
            page_id: 页面ID
            period: 周期标识
            data: 复盘数据
        """
        logger.info(f"开始添加复盘内容块到页面 {page_id[:8]}...")

        summary = data.get("summary", {})
        categories = data.get("categories", {})
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")

        # 格式化日期
        try:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            start_date_str = start_dt.strftime("%Y年%m月%d日")
            end_date_str = end_dt.strftime("%Y年%m月%d日")
        except (ValueError, AttributeError):
            start_date_str = start_date
            end_date_str = end_date

        # 计算收支金额（以万为单位）
        balance_wan = summary.get("net_balance", 0) / 10000

        # 获取TOP分类
        expense_sorted = sorted(
            [(cat, amounts.get('expense', 0)) for cat, amounts in categories.items() if amounts.get('expense', 0) > 0],
            key=lambda x: x[1],
            reverse=True
        )
        income_sorted = sorted(
            [(cat, amounts.get('income', 0)) for cat, amounts in categories.items() if amounts.get('income', 0) > 0],
            key=lambda x: x[1],
            reverse=True
        )

        # 构建复盘摘要
        summary_text = f"1、本月收入 {summary.get('total_income', 0):.2f}，支出 {summary.get('total_expense', 0):.2f}，收益 {summary.get('net_balance', 0):.2f}，共 {balance_wan:.2f}w 左右\n"

        # 构建支出TOP分析
        expense_analysis = "2、本月支出数据中，TOP N 支出分别为："
        expense_top_parts = []
        for i, (cat, amount) in enumerate(expense_sorted[:5], 1):
            amount_wan = amount / 10000
            if amount_wan >= 1:
                expense_top_parts.append(f"{amount_wan:.1f}W为{cat}")
            else:
                expense_top_parts.append(f"{amount:.0f}为{cat}")
        expense_analysis += "，".join(expense_top_parts) + "费用"

        # 构建收入TOP分析
        income_analysis = "\n3、本月收入数据中，TOP N 收入分别为："
        income_top_parts = []
        for i, (cat, amount) in enumerate(income_sorted[:5], 1):
            amount_wan = amount / 10000
            if amount_wan >= 1:
                income_top_parts.append(f"{amount_wan:.1f}W为{cat}")
            else:
                income_top_parts.append(f"{amount:.0f}为{cat}")
        income_analysis += "，".join(income_top_parts) + "收入" if income_top_parts else "暂无收入"

        # 构建内容块
        blocks = [
            # 月度复盘概述
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "月度复盘"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": summary_text + expense_analysis + income_analysis
                            }
                        }
                    ]
                }
            },
            # 收支源数据
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "收支源数据"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"统计周期：{start_date_str} 至 {end_date_str}"
                            }
                        }
                    ],
                    "color": "gray"
                }
            },
            # 月度收支情况
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "月度收支情况"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "月度收支情况"
                            }
                        }
                    ]
                }
            },
            # 汇总
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "数据分析"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "汇总"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"本月收入 {summary.get('total_income', 0):.2f}，支出 {summary.get('total_expense', 0):.2f}，收益 {summary.get('net_balance', 0):.2f}，共 {balance_wan:.2f}w 左右"
                            }
                        }
                    ]
                }
            },
            # 支出数据分析
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "支出数据分析"
                            }
                        }
                    ]
                }
            },
        ]

        # 添加支出TOP分析
        if expense_sorted:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "1、本月支出数据中，TOP N 支出分别为：" + "，".join(expense_top_parts) + "费用"
                            }
                        }
                    ]
                }
            })

            # 详细分析
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "2、详细分析如下"
                            }
                        }
                    ]
                }
            })

            for i, (cat, amount) in enumerate(expense_sorted[:5], 1):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"{cat}：¥{amount:.2f}"
                                }
                            }
                        ]
                    }
                })

        # 收入数据分析
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "收入数据分析"
                        }
                    }
                ]
            }
        })

        if income_sorted:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "1、本月收入数据中，TOP N 收入分别为：" + "，".join(income_top_parts) + "收入"
                            }
                        }
                    ]
                }
            })

            # 详细分析
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "2、收入详细分析"
                            }
                        }
                    ]
                }
            })

            for i, (cat, amount) in enumerate(income_sorted[:5], 1):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"{cat}：¥{amount:.2f}"
                                }
                            }
                        ]
                    }
                })

        # 月度复盘总结
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "月度复盘总结"
                        }
                    }
                ]
            }
        })

        # 批量添加块
        logger.info(f"准备添加 {len(blocks)} 个内容块")
        for i, block in enumerate(blocks):
            try:
                self.notion_client.client.blocks.children.append(
                    block_id=page_id,
                    children=[block]
                )
                if (i + 1) % 10 == 0:
                    logger.info(f"已添加 {i + 1}/{len(blocks)} 个内容块")
            except Exception as e:
                logger.error(f"添加第 {i + 1} 个内容块失败: {e}")

        logger.info(f"成功添加 {len(blocks)} 个内容块到页面 {page_id[:8]}...")

    def generate_monthly_review(self, year: int, month: int) -> Dict[str, Any]:
        """生成月度复盘

        Args:
            year: 年份
            month: 月份 (1-12)

        Returns:
            复盘结果
        """
        logger.info("=" * 50)
        logger.info(f"开始生成月度复盘: {year}-{month:02d}")
        logger.info("=" * 50)

        # 阶段1: 获取账单数据
        logger.info("[阶段 1/4] 获取账单数据...")

        # 检查复盘数据库是否配置
        database_id = self.get_review_database_id(self.TYPE_MONTHLY)
        if not database_id:
            logger.warning("Monthly review database not configured")
            return {
                "success": False,
                "period": f"{year}-{month:02d}",
                "error": "月度复盘数据库未配置。请在设置中配置复盘数据库 ID，或在环境变量中设置 NOTION_MONTHLY_REVIEW_DB。"
            }

        # 计算日期范围
        start_date = date(year, month, 1)
        end_date = start_date + relativedelta(months=1, days=-1)
        logger.info(f"复盘周期: {start_date} 至 {end_date}")

        # 获取交易数据
        logger.info("正在获取交易数据...")
        transactions = self.fetch_transactions(start_date, end_date)
        logger.info(f"获取到 {len(transactions)} 条交易记录")

        # 计算汇总
        logger.info("正在计算汇总数据...")
        summary = self.calculate_summary(transactions)
        logger.info(f"汇总: 收入 ¥{summary['total_income']:.2f}, 支出 ¥{summary['total_expense']:.2f}, 结余 ¥{summary['net_balance']:.2f}")

        # 按分类聚合
        logger.info("正在按分类聚合...")
        categories = self.aggregate_by_category(transactions)
        logger.info(f"聚合了 {len(categories)} 个分类")

        # 构建复盘数据
        period = f"{year}-{month:02d}"
        review_data = {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "transaction_count": len(transactions),
            "summary": summary,
            "categories": categories
        }

        # 阶段2: 获取模板
        logger.info("[阶段 2/4] 获取复盘模板...")

        # 阶段3&4: 创建复盘页面（包含填充模板数据）
        logger.info("[阶段 3/4] 填充模板数据...")
        logger.info("[阶段 4/4] 创建复盘页面...")

        page_id = self.create_review_page(
            self.TYPE_MONTHLY,
            period,
            review_data
        )

        if page_id:
            logger.info(f"✓ 月度复盘生成成功: {page_id}")
        else:
            logger.error("✗ 月度复盘生成失败")

        logger.info("=" * 50)

        return {
            "success": page_id is not None,
            "period": period,
            "page_id": page_id,
            "data": review_data,
            "error": None if page_id else "创建复盘页面失败，请检查复盘数据库配置和属性设置"
        }

    def generate_quarterly_review(self, year: int, quarter: int) -> Dict[str, Any]:
        """生成季度复盘

        Args:
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            复盘结果
        """
        logger.info(f"Generating quarterly review for {year}-Q{quarter}")

        # 检查复盘数据库是否配置
        database_id = self.get_review_database_id(self.TYPE_QUARTERLY)
        if not database_id:
            logger.warning("Quarterly review database not configured")
            return {
                "success": False,
                "period": f"{year}-Q{quarter}",
                "error": "季度复盘数据库未配置。请在设置中配置复盘数据库 ID，或在环境变量中设置 NOTION_QUARTERLY_REVIEW_DB。"
            }

        # 计算日期范围
        start_month = (quarter - 1) * 3 + 1
        start_date = date(year, start_month, 1)
        end_date = start_date + relativedelta(months=3, days=-1)

        # 获取交易数据
        transactions = self.fetch_transactions(start_date, end_date)

        # 计算汇总
        summary = self.calculate_summary(transactions)

        # 按分类聚合
        categories = self.aggregate_by_category(transactions)

        # 构建复盘数据
        period = f"{year}-Q{quarter}"
        review_data = {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            **summary,
            "categories": categories
        }

        # 创建复盘页面
        page_id = self.create_review_page(
            self.TYPE_QUARTERLY,
            period,
            review_data
        )

        return {
            "success": page_id is not None,
            "period": period,
            "page_id": page_id,
            "data": review_data,
            "error": None if page_id else "创建复盘页面失败，请检查复盘数据库配置和属性设置"
        }

    def generate_yearly_review(self, year: int) -> Dict[str, Any]:
        """生成年度复盘

        Args:
            year: 年份

        Returns:
            复盘结果
        """
        logger.info(f"Generating yearly review for {year}")

        # 检查复盘数据库是否配置
        database_id = self.get_review_database_id(self.TYPE_YEARLY)
        if not database_id:
            logger.warning("Yearly review database not configured")
            return {
                "success": False,
                "period": f"{year}",
                "error": "年度复盘数据库未配置。请在设置中配置复盘数据库 ID，或在环境变量中设置 NOTION_YEARLY_REVIEW_DB。"
            }

        # 计算日期范围
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # 获取交易数据
        transactions = self.fetch_transactions(start_date, end_date)

        # 计算汇总
        summary = self.calculate_summary(transactions)

        # 按分类聚合
        categories = self.aggregate_by_category(transactions)

        # 构建复盘数据
        period = str(year)
        review_data = {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            **summary,
            "categories": categories
        }

        # 创建复盘页面
        page_id = self.create_review_page(
            self.TYPE_YEARLY,
            period,
            review_data
        )

        return {
            "success": page_id is not None,
            "period": period,
            "page_id": page_id,
            "data": review_data,
            "error": None if page_id else "创建复盘页面失败，请检查复盘数据库配置和属性设置"
        }

    def batch_generate_reviews(
        self,
        start_date: date,
        end_date: date,
        review_type: str = TYPE_MONTHLY
    ) -> List[Dict[str, Any]]:
        """批量生成复盘

        Args:
            start_date: 开始日期
            end_date: 结束日期
            review_type: 复盘类型 (monthly/quarterly/yearly)

        Returns:
            复盘结果列表
        """
        logger.info(f"Batch generating {review_type} reviews from {start_date} to {end_date}")

        results = []
        current = start_date

        if review_type == self.TYPE_MONTHLY:
            while current <= end_date:
                result = self.generate_monthly_review(current.year, current.month)
                results.append(result)
                current = current + relativedelta(months=1)

        elif review_type == self.TYPE_QUARTERLY:
            # 按季度迭代
            year = current.year
            quarter = (current.month - 1) // 3 + 1
            while date(year, quarter * 3, 1) <= end_date:
                result = self.generate_quarterly_review(year, quarter)
                results.append(result)
                quarter += 1
                if quarter > 4:
                    quarter = 1
                    year += 1

        elif review_type == self.TYPE_YEARLY:
            while current.year <= end_date.year:
                result = self.generate_yearly_review(current.year)
                results.append(result)
                current = current + relativedelta(years=1)

        return results

    # ==================== 新增：Markdown 生成方法 ====================

    def generate_review_markdown(
        self,
        start_date: date,
        end_date: date,
        transactions: List[Dict[str, Any]],
        summary: Dict[str, Any],
        categories: Dict[str, Dict[str, float]],
        review_title: str = None
    ) -> str:
        """生成复盘 Markdown 内容

        Args:
            start_date: 开始日期
            end_date: 结束日期
            transactions: 交易记录列表
            summary: 汇总数据
            categories: 分类数据
            review_title: 复盘标题（可选）

        Returns:
            Markdown 格式的复盘内容
        """
        # 格式化日期
        start_date_str = start_date.strftime("%Y年%m月%d日")
        end_date_str = end_date.strftime("%Y年%m月%d日")
        start_date_iso = start_date.isoformat()
        end_date_iso = end_date.isoformat()

        # 计算收支金额（以万为单位）
        balance_wan = summary.get("net_balance", 0) / 10000

        # 获取 TOP 分类
        expense_categories = {k: v["expense"] for k, v in categories.items() if v["expense"] > 0}
        income_categories = {k: v["income"] for k, v in categories.items() if v["income"] > 0}

        expense_top5 = self._get_top_sorted(expense_categories, 5)
        income_top5 = self._get_top_sorted(income_categories, 5)

        # 生成摘要文本
        summary_text = self._generate_summary_text(summary, expense_top5, income_top5)

        # 生成数据库视图链接
        database_links = self._generate_database_view_links(start_date_iso, end_date_iso)

        # 标题
        title = review_title or f"{start_date.year}年{start_date.month}月复盘" if start_date.month == end_date.month else f"{start_date_str} 至 {end_date_str} 复盘"

        # 构建 Markdown
        markdown = f"""# {title}

开始日期: {start_date_str}
结束日期: {end_date_str}
状态: 计划中

月度复盘: {summary_text}

## 收支源数据

{database_links['source']}

## 月度收支情况

{database_links['monthly']}

## 数据分析

### 汇总

本月收入 {summary.get('total_income', 0):.2f} ，支出 {summary.get('total_expense', 0):.2f} ，收益 {summary.get('net_balance', 0):.2f} ，共 {balance_wan:.2f}w 左右

### 支出数据分析

{self._generate_expense_analysis(expense_top5, summary.get('total_expense', 0))}

### 收入数据分析

{self._generate_income_analysis(income_top5, summary.get('total_income', 0))}

## 月度复盘总结

（请在此处填写您的复盘总结）

---

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return markdown

    def build_review_attributes(
        self,
        start_date: date,
        end_date: date,
        summary: Dict[str, Any],
        review_title: str = None,
        status: str = "计划中"
    ) -> Dict[str, Any]:
        """构建复盘属性数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            summary: 汇总数据
            review_title: 复盘标题
            status: 状态

        Returns:
            属性数据字典
        """
        # 生成标题
        if not review_title:
            if start_date.year == end_date.year and start_date.month == end_date.month:
                review_title = f"{start_date.year}年{start_date.month}月复盘"
            else:
                review_title = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} 复盘"

        # 生成摘要文本
        balance_wan = summary.get("net_balance", 0) / 10000
        summary_text = (
            f"1、本期收入 {summary.get('total_income', 0):.2f} ，"
            f"支出 {summary.get('total_expense', 0):.2f} ，"
            f"收益 {summary.get('net_balance', 0):.2f} ，"
            f"共 {balance_wan:.2f}w 左右"
        )

        return {
            "title": review_title,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status": status,
            "summary": summary_text,
            "total_income": summary.get("total_income", 0),
            "total_expense": summary.get("total_expense", 0),
            "net_balance": summary.get("net_balance", 0),
            "transaction_count": summary.get("transaction_count", 0)
        }

    def create_review_from_content(
        self,
        review_type: str,
        attributes: Dict[str, Any],
        markdown_content: str
    ) -> Optional[str]:
        """根据内容创建复盘页面

        Args:
            review_type: 复盘类型 (monthly/quarterly/yearly)
            attributes: 属性数据
            markdown_content: Markdown 正文内容

        Returns:
            创建的页面ID，失败返回None
        """
        # 获取复盘数据库ID
        database_id = self.get_review_database_id(review_type)
        if not database_id:
            logger.error(f"Review database not configured for type: {review_type}")
            return None

        # 打印日志：使用正确的复盘类型
        logger.info(f"创建复盘页面 - 类型: {review_type}, 数据库ID: {database_id[:8]}...")

        try:
            # 构建页面属性（传入正确的 review_type）
            page_properties = self._build_properties_from_attributes(attributes, review_type)

            # 创建页面
            page_data = {
                "parent": {"database_id": database_id},
                "properties": page_properties
            }

            # 添加标题块
            title = attributes.get("title", "复盘")
            blocks = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": title}}]
                    }
                }
            ]

            # 将 Markdown 转换为 Notion 块
            content_blocks = self._markdown_to_blocks(markdown_content)
            blocks.extend(content_blocks)

            # 添加子块
            page_data["children"] = blocks

            # 创建页面
            logger.info(f"正在创建 Notion 页面，父数据库: {database_id[:8]}...")
            response = self.notion_client.client.request(
                path="/pages",
                method="POST",
                body=page_data
            )

            page_id = response.get("id")
            if page_id:
                logger.info(f"复盘页面创建成功: {page_id}")
                logger.info(f"页面URL: https://www.notion.so/{page_id.replace('-', '')}")
            else:
                logger.error(f"页面创建失败，响应: {response}")
            return page_id

        except Exception as e:
            logger.error(f"Failed to create review page: {e}", exc_info=True)
            logger.error(f"复盘类型: {review_type}")
            logger.error(f"数据库ID: {database_id if database_id else 'None'}")
            return None

    @classmethod
    def clear_database_cache(cls, database_id: Optional[str] = None):
        """清除数据库结构缓存

        Args:
            database_id: 可选，指定要清除的数据库ID。
                        如果为 None，则清除所有缓存。
        """
        if database_id:
            # 清除特定数据库的缓存
            keys_to_remove = [k for k in cls._database_structure_cache if k.startswith(database_id)]
            for key in keys_to_remove:
                del cls._database_structure_cache[key]
            logger.info(f"已清除数据库 {database_id[:8]}... 的缓存")
        else:
            # 清除所有缓存
            cls._database_structure_cache.clear()
            logger.info("已清除所有数据库结构缓存")

    def _get_top_sorted(self, categories: Dict[str, float], n: int = 5) -> List[tuple]:
        """获取排序后的 TOP N 分类

        Args:
            categories: 分类字典 {name: amount}
            n: 返回数量

        Returns:
            排序后的列表 [(name, amount), ...]
        """
        return sorted(categories.items(), key=lambda x: x[1], reverse=True)[:n]

    def _generate_summary_text(
        self,
        summary: Dict[str, Any],
        expense_top5: List[tuple],
        income_top5: List[tuple]
    ) -> str:
        """生成摘要文本"""
        total_expense = summary.get("total_expense", 0)

        # 支出描述
        expense_desc = "，".join([
            f"{amount:.0f}为{name}"
            for name, amount in expense_top5
        ]) if expense_top5 else "无"

        # 收入描述
        income_desc = "，".join([
            f"{amount:.0f}为{name}"
            for name, amount in income_top5
        ]) if income_top5 else "无"

        # 计算占比
        expense_parts = []
        for name, amount in expense_top5:
            if total_expense > 0:
                ratio = amount / total_expense
                expense_parts.append(f"{amount:.0f}为{name}（占比{ratio*100:.1f}%）")

        return (
            f"1、本期收入 {summary.get('total_income', 0):.2f} ，"
            f"支出 {summary.get('total_expense', 0):.2f} ，"
            f"收益 {summary.get('net_balance', 0):.2f} ，"
            f"共 {summary.get('net_balance', 0)/10000:.2f}w 左右\n"
            f"2、本期支出数据中，TOP N 支出分别为： {expense_desc}\n"
            f"3、本期收入数据中，TOP N 收入分别为： {income_desc}"
        )

    def _generate_expense_analysis(self, expense_top5: List[tuple], total_expense: float) -> str:
        """生成支出分析文本"""
        if not expense_top5:
            return "本期无支出数据"

        lines = [
            "1. 本期支出数据中，TOP N 支出分别为：" +
            "，".join([f"{amount:.0f}为{name}" for name, amount in expense_top5]),
            "2. 详细分析如下（异常数据分析）"
        ]

        for i, (name, amount) in enumerate(expense_top5, 1):
            ratio = (amount / total_expense * 100) if total_expense > 0 else 0
            lines.append(f"    {i}. {amount:.0f}为{name}（占比{ratio:.1f}%）")

        return "\n".join(lines)

    def _generate_income_analysis(self, income_top5: List[tuple], total_income: float) -> str:
        """生成收入分析文本"""
        if not income_top5:
            return "本期无收入数据"

        lines = [
            "1. 本期收入数据中，TOP N 收入分别为：" +
            "，".join([f"{amount:.0f}为{name}" for name, amount in income_top5]),
            "2. 收入详细分析（异常数据分析）"
        ]

        for i, (name, amount) in enumerate(income_top5, 1):
            ratio = (amount / total_income * 100) if total_income > 0 else 0
            lines.append(f"    {i}. {amount:.0f}为{name}（占比{ratio:.1f}%）")

        return "\n".join(lines)

    def _generate_database_view_links(self, start_date: str, end_date: str) -> Dict[str, str]:
        """生成数据库视图链接

        Args:
            start_date: 开始日期 (ISO format)
            end_date: 结束日期 (ISO format)

        Returns:
            包含各类视图链接的字典
        """
        income_db_id = self.notion_client.income_db
        expense_db_id = self.notion_client.expense_db

        # Notion 数据库视图链接格式
        # 注意：Notion 的视图过滤需要通过查询参数实现
        # 这里提供基础链接，用户可以在 Notion 中进一步筛选

        base_links = {
            'source': f"""### 收支源数据

- [收入数据库](https://www.notion.so/{income_db_id})
- [支出数据库](https://www.notion.so/{expense_db_id})

> 💡 提示：点击链接后，可在 Notion 中使用筛选功能查看指定日期范围的数据（筛选条件：Date >= {start_date}, Date <= {end_date}）""",
            'monthly': f"""### 月度收支情况

- [收入数据库](https://www.notion.so/{income_db_id})
- [支出数据库](https://www.notion.so/{expense_db_id})

> 💡 提示：点击链接后，可在 Notion 中使用筛选功能查看指定日期范围的数据（筛选条件：Date >= {start_date}, Date <= {end_date}）"""
        }

        return base_links

    def _build_properties_from_attributes(self, attributes: Dict[str, Any], review_type: str = "monthly") -> Dict[str, Any]:
        """从属性字典构建 Notion 属性格式

        Args:
            attributes: 属性字典
            review_type: 复盘类型 (monthly/quarterly/yearly)

        Returns:
            Notion 属性格式
        """
        # 获取数据库结构以查找标题属性
        database_id = self.get_review_database_id(review_type)

        # 打印日志：使用正确的数据库ID
        if database_id:
            logger.info(f"构建属性 - 复盘类型: {review_type}, 数据库ID: {database_id[:8]}...")

        properties = {}
        database_properties = {}  # 初始化为空字典

        # 动态检测标题属性名（使用缓存优化）
        if database_id:
            cache_key = f"{database_id}:{review_type}"
            try:
                # 检查缓存
                if cache_key in self._database_structure_cache:
                    database_properties = self._database_structure_cache[cache_key]
                    logger.info(f"使用缓存的数据库结构: {cache_key}")
                else:
                    # 使用更短的超时时间获取数据库结构（15秒快速失败）
                    import httpx
                    temp_client = self.notion_client.client
                    # 创建带短超时的临时客户端（15秒）
                    original_timeout = None
                    if hasattr(temp_client, 'timeout_ms'):
                        original_timeout = temp_client.timeout_ms
                        temp_client.timeout_ms = 15000  # 15秒超时，快速失败

                    try:
                        database_info = temp_client.databases.retrieve(database_id=database_id)
                    finally:
                        # 恢复原超时设置
                        if original_timeout is not None and hasattr(temp_client, 'timeout_ms'):
                            temp_client.timeout_ms = original_timeout

                    database_properties = database_info.get("properties", {})
                    # 缓存结果
                    self._database_structure_cache[cache_key] = database_properties
                    logger.info(f"已缓存数据库结构: {cache_key}")

                title_property_name = None
                for prop_name, prop_config in database_properties.items():
                    if prop_config.get("type") == "title":
                        title_property_name = prop_name
                        break

                if title_property_name:
                    properties[title_property_name] = {
                        "title": [{"text": {"content": attributes.get("title", "复盘")}}]
                    }
                    logger.info(f"找到标题属性: {title_property_name}")
            except Exception as e:
                logger.warning(f"Failed to retrieve database structure for {review_type}: {e}")

        # 如果没有找到标题属性，使用默认名称
        # 检查是否已存在 title 类型的属性
        has_title = any("title" in p for p in properties.values())
        if not has_title:
            properties["Name"] = {
                "title": [{"text": {"content": attributes.get("title", "复盘")}}]
            }

        # 动态映射属性名（从数据库结构中查找匹配的字段）
        if database_properties:
            db_properties = database_properties

            # 定义字段映射：属性值 -> 可能的字段名列表
            field_mappings = {
                "start_date": ["Start Date", "开始日期", "起始日期", "开始时间", "起始时间"],
                "end_date": ["End Date", "结束日期", "截止日期", "结束时间", "截止时间"],
                "status": ["Status", "状态", "进度"],
                "total_income": ["Total Income", "总收入", "收入合计", "收入总计"],
                "total_expense": ["Total Expense", "总支出", "支出合计", "支出总计"],
                "net_balance": ["Net Balance", "净余额", "收支差额", "余额", "结余"],
                "transaction_count": ["Transaction Count", "交易次数", "记录数", "笔数"]
            }

            # 动态查找并设置属性
            for attr_key, possible_names in field_mappings.items():
                if attr_key not in attributes:
                    continue

                # 在数据库中查找匹配的字段名
                matched_prop_name = None
                for possible_name in possible_names:
                    if possible_name in db_properties:
                        prop_type = db_properties[possible_name].get("type")
                        matched_prop_name = possible_name
                        break

                if matched_prop_name:
                    # 根据字段类型设置值
                    prop_type = db_properties[matched_prop_name].get("type")
                    if prop_type == "date":
                        properties[matched_prop_name] = {
                            "date": {"start": attributes[attr_key]}
                        }
                    elif prop_type == "number":
                        properties[matched_prop_name] = {
                            "number": attributes[attr_key]
                        }
                    elif prop_type == "select":
                        properties[matched_prop_name] = {
                            "select": {"name": attributes[attr_key]}
                        }
                    logger.info(f"设置属性 {matched_prop_name} = {attributes[attr_key]}")
        else:
            # 回退方案：使用英文字段名（仅当无法获取数据库结构时）
            if "start_date" in attributes:
                properties["Start Date"] = {
                    "date": {"start": attributes["start_date"]}
                }
            if "end_date" in attributes:
                properties["End Date"] = {
                    "date": {"start": attributes["end_date"]}
                }
            if "status" in attributes:
                properties["Status"] = {
                    "select": {"name": attributes["status"]}
                }
            if "total_income" in attributes:
                properties["Total Income"] = {
                    "number": attributes["total_income"]
                }
            if "total_expense" in attributes:
                properties["Total Expense"] = {
                    "number": attributes["total_expense"]
                }
            if "net_balance" in attributes:
                properties["Net Balance"] = {
                    "number": attributes["net_balance"]
                }
            if "transaction_count" in attributes:
                properties["Transaction Count"] = {
                    "number": attributes["transaction_count"]
                }

        return properties

    def _markdown_to_blocks(self, markdown: str) -> List[Dict[str, Any]]:
        """将 Markdown 转换为 Notion 块

        Args:
            markdown: Markdown 文本

        Returns:
            Notion 块列表
        """
        blocks = []
        lines = markdown.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 跳过标题行（已经在页面创建时处理）
            if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
                # 添加标题块
                level = len(line.split()[0])
                text = line.lstrip("#").strip()

                heading_type = f"heading_{min(level, 3)}"
                blocks.append({
                    "object": "block",
                    "type": heading_type,
                    heading_type: {
                        "rich_text": [{"type": "text", "text": {"content": text}}]
                    }
                })
                i += 1
                continue

            # 空行
            if not line:
                i += 1
                continue

            # 列表项
            if line.startswith("- "):
                text = line[2:].strip()
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": text}}]
                    }
                })
                i += 1
                continue

            # 编号列表
            if line[0].isdigit() and line[1:].startswith(". "):
                text = line.split(". ", 1)[1].strip()
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": text}}]
                    }
                })
                i += 1
                continue

            # 引用块
            if line.startswith("> "):
                text = line[2:].strip()
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [{"type": "text", "text": {"content": text}}]
                    }
                })
                i += 1
                continue

            # 分隔线
            if line == "---":
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
                i += 1
                continue

            # 普通段落（合并连续非空行）
            paragraph_lines = []
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("#", "-", ">", "---")) and not (lines[i][0].isdigit() and lines[i][1] == "."):
                paragraph_lines.append(lines[i].strip())
                i += 1

            if paragraph_lines:
                text = " ".join(paragraph_lines)
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": text}}]
                    }
                })
                continue

            i += 1

        return blocks
