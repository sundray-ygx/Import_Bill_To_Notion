"""
测试账单复盘服务
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, MagicMock, patch

from review_service import ReviewService


class TestReviewService:
    """测试ReviewService类"""

    @pytest.fixture
    def mock_notion_client(self):
        """模拟Notion客户端"""
        client = Mock()
        client.client = Mock()
        client.income_db = "income_db_id"
        client.expense_db = "expense_db_id"
        return client

    @pytest.fixture
    def service(self, mock_notion_client):
        """创建ReviewService实例"""
        with patch('review_service.NotionClient', return_value=mock_notion_client):
            return ReviewService(user_id=1)

    def test_init(self, mock_notion_client):
        """测试ReviewService初始化"""
        with patch('review_service.NotionClient', return_value=mock_notion_client):
            service = ReviewService(user_id=1)
            assert service.user_id == 1
            assert service.notion_client is not None

    def test_calculate_summary(self, service):
        """测试计算汇总数据"""
        transactions = [
            {"properties": {"Price": {"number": 100}}, "type": "income"},
            {"properties": {"Price": {"number": 50}}, "type": "expense"},
            {"properties": {"Price": {"number": 200}}, "type": "income"},
            {"properties": {"Price": {"number": 30}}, "type": "expense"},
        ]

        summary = service.calculate_summary(transactions)

        assert summary["total_income"] == 300.0
        assert summary["total_expense"] == 80.0
        assert summary["net_balance"] == 220.0
        assert summary["transaction_count"] == 4

    def test_aggregate_by_category(self, service):
        """测试按分类聚合数据"""
        transactions = [
            {
                "properties": {
                    "Category": {"select": {"name": "餐饮"}},
                    "Price": {"number": 100}
                },
                "type": "expense"
            },
            {
                "properties": {
                    "Category": {"select": {"name": "餐饮"}},
                    "Price": {"number": 50}
                },
                "type": "expense"
            },
            {
                "properties": {
                    "Category": {"select": {"name": "交通"}},
                    "Price": {"number": 30}
                },
                "type": "expense"
            },
            {
                "properties": {
                    "Category": {"select": {"name": "工资"}},
                    "Price": {"number": 5000}
                },
                "type": "income"
            },
        ]

        categories = service.aggregate_by_category(transactions)

        assert categories["餐饮"]["expense"] == 150.0
        assert categories["餐饮"]["income"] == 0.0
        assert categories["交通"]["expense"] == 30.0
        assert categories["工资"]["income"] == 5000.0

    def test_get_review_database_id_from_env(self, service):
        """测试从环境变量获取复盘数据库ID"""
        with patch.dict('os.environ', {
            'NOTION_MONTHLY_REVIEW_DB': 'monthly_db_id',
            'NOTION_QUARTERLY_REVIEW_DB': 'quarterly_db_id',
            'NOTION_YEARLY_REVIEW_DB': 'yearly_db_id'
        }):
            assert service.get_review_database_id('monthly') == 'monthly_db_id'
            assert service.get_review_database_id('quarterly') == 'quarterly_db_id'
            assert service.get_review_database_id('yearly') == 'yearly_db_id'

    def test_get_review_database_id_not_configured(self, service):
        """测试复盘数据库未配置"""
        with patch.dict('os.environ', {}, clear=True):
            # 模拟单租户模式但环境变量未配置
            with patch('config.Config.is_multi_tenant_mode', return_value=False):
                db_id = service.get_review_database_id('monthly')
                assert db_id is None

    def test_build_review_properties(self, service):
        """测试构建复盘页面属性"""
        review_type = "monthly"
        period = "2024-01"
        data = {
            "total_income": 10000.0,
            "total_expense": 5000.0,
            "net_balance": 5000.0,
            "transaction_count": 100,
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }

        properties = service._build_review_properties(review_type, period, data)

        assert properties["Name"]["title"][0]["text"]["content"] == "2024-01 账单复盘"
        assert properties["Period"]["rich_text"][0]["text"]["content"] == "2024-01"
        assert properties["Total Income"]["number"] == 10000.0
        assert properties["Total Expense"]["number"] == 5000.0
        assert properties["Net Balance"]["number"] == 5000.0
        assert properties["Transaction Count"]["number"] == 100
        assert properties["Start Date"]["date"]["start"] == "2024-01-01"
        assert properties["End Date"]["date"]["start"] == "2024-01-31"

    @patch('review_service.date')
    def test_generate_monthly_review(self, mock_date, service):
        """测试生成月度复盘"""
        mock_date.today.return_value = date(2024, 1, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        # 模拟Notion API响应
        service.notion_client.client.request.return_value = {
            "results": [],
            "has_more": False
        }
        service.notion_client.client.pages.create.return_value = {
            "id": "page_id_123"
        }

        # 模拟环境变量
        with patch.dict('os.environ', {'NOTION_MONTHLY_REVIEW_DB': 'monthly_db_id'}):
            result = service.generate_monthly_review(2024, 1)

            assert result["success"] is True
            assert result["period"] == "2024-01"
            assert result["page_id"] == "page_id_123"
            assert "data" in result

    def test_create_review_page_no_database(self, service):
        """测试复盘数据库未配置时创建页面"""
        with patch.dict('os.environ', {}, clear=True):
            with patch('config.Config.is_multi_tenant_mode', return_value=False):
                result = service.create_review_page(
                    "monthly",
                    "2024-01",
                    {"total_income": 1000}
                )
                assert result is None
