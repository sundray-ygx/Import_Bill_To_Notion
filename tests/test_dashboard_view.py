"""
Dashboard视图模块测试
测试Dashboard API端点和数据格式
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models import User, ImportHistory
from auth import get_password_hash
from web_service.main import app


class TestDashboardAPI:
    """Dashboard API测试"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        """设置测试数据"""
        # 创建测试用户
        self.user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass123")
        )
        db_session.add(self.user)
        db_session.commit()

        # 创建测试导入历史记录
        now = datetime.now()

        # 本月成功的导入记录
        history1 = ImportHistory(
            user_id=self.user.id,
            file_name="alipay_202401.csv",
            platform="alipay",
            status="success",
            income_count=10,
            expense_count=20,
            total_count=30,
            income_total=5000.00,
            expense_total=2000.00,
            created_at=now
        )

        # 本月失败的导入记录
        history2 = ImportHistory(
            user_id=self.user.id,
            file_name="wechat_error.csv",
            platform="wechat",
            status="failed",
            error_message="文件格式不正确",
            created_at=now - timedelta(hours=2)
        )

        # 上月的导入记录
        last_month = now.replace(day=1) - timedelta(days=1)
        history3 = ImportHistory(
            user_id=self.user.id,
            file_name="unionpay_202312.csv",
            platform="unionpay",
            status="success",
            income_count=15,
            expense_count=25,
            total_count=40,
            income_total=8000.00,
            expense_total=3000.00,
            created_at=last_month
        )

        db_session.add_all([history1, history2, history3])
        db_session.commit()

        self.client = TestClient(app)

    def test_get_dashboard_stats_success(self, db_session: Session):
        """测试获取统计数据成功"""
        # 使用依赖覆盖设置认证用户
        def override_get_db():
            yield db_session

        def override_get_current_user():
            return self.user

        app.dependency_overrides[get_db] = override_get_db
        from dependencies import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user

        response = self.client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert data["success"] is True
        assert "data" in data

        # 验证统计数据
        stats = data["data"]
        assert "monthlyIncome" in stats
        assert "monthlyExpense" in stats
        assert "netBalance" in stats
        assert "transactionCount" in stats
        assert stats["monthlyIncome"] == 5000.00
        assert stats["monthlyExpense"] == 2000.00
        assert stats["netBalance"] == 3000.00
        assert stats["transactionCount"] == 30

        # 清理依赖覆盖
        app.dependency_overrides.clear()

    def test_get_dashboard_stats_with_trend(self, db_session: Session):
        """测试获取带趋势的统计数据"""
        def override_get_db():
            yield db_session

        def override_get_current_user():
            return self.user

        app.dependency_overrides[get_db] = override_get_db
        from dependencies import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user

        response = self.client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        stats = data["data"]

        # 验证趋势数据
        assert "incomeTrend" in stats
        assert "expenseTrend" in stats
        # 上月数据存在，应该有趋势值
        assert stats["incomeTrend"] is not None
        assert stats["expenseTrend"] is not None

        app.dependency_overrides.clear()

    def test_get_dashboard_activity_success(self, db_session: Session):
        """测试获取活动记录成功"""
        def override_get_db():
            yield db_session

        def override_get_current_user():
            return self.user

        app.dependency_overrides[get_db] = override_get_db
        from dependencies import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user

        response = self.client.get("/api/dashboard/activity?limit=5")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

        # 验证活动记录
        activities = data["data"]
        assert len(activities) == 3  # 应该有3条记录

        # 验证第一条记录（成功的导入）
        first_activity = activities[0]
        assert "type" in first_activity
        assert "title" in first_activity
        assert "description" in first_activity
        assert "time" in first_activity
        assert "status" in first_activity
        assert first_activity["type"] == "import"
        assert first_activity["status"] == "success"
        assert "支付宝" in first_activity["title"]
        assert "30 条记录" in first_activity["description"]

        app.dependency_overrides.clear()

    def test_get_dashboard_activity_limit(self, db_session: Session):
        """测试活动记录限制"""
        def override_get_db():
            yield db_session

        def override_get_current_user():
            return self.user

        app.dependency_overrides[get_db] = override_get_db
        from dependencies import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user

        response = self.client.get("/api/dashboard/activity?limit=2")

        assert response.status_code == 200
        data = response.json()
        activities = data["data"]

        # 验证限制
        assert len(activities) == 2

        app.dependency_overrides.clear()

    def test_get_dashboard_activity_empty_user(self, db_session: Session):
        """测试没有活动记录的用户"""
        # 创建一个没有导入历史的新用户
        new_user = User(
            username="newuser",
            email="new@example.com",
            hashed_password=get_password_hash("testpass123")
        )
        db_session.add(new_user)
        db_session.commit()

        def override_get_db():
            yield db_session

        def override_get_current_user():
            return new_user

        app.dependency_overrides[get_db] = override_get_db
        from dependencies import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user

        response = self.client.get("/api/dashboard/activity")

        assert response.status_code == 200
        data = response.json()
        activities = data["data"]

        # 应该返回欢迎信息
        assert len(activities) == 1
        assert activities[0]["type"] == "info"
        assert "欢迎使用" in activities[0]["title"]

        app.dependency_overrides.clear()

    def test_get_dashboard_overview_success(self, db_session: Session):
        """测试获取概览信息成功"""
        def override_get_db():
            yield db_session

        def override_get_current_user():
            return self.user

        app.dependency_overrides[get_db] = override_get_db
        from dependencies import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user

        response = self.client.get("/api/dashboard/overview")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert data["success"] is True
        assert "data" in data

        # 验证概览数据
        overview = data["data"]
        assert "totalImports" in overview
        assert "successImports" in overview
        assert "successRate" in overview
        assert "latestActivity" in overview
        assert overview["totalImports"] == 3
        assert overview["successImports"] == 2
        assert overview["successRate"] > 0

        app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
