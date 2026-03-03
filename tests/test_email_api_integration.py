#!/usr/bin/env python3
"""
邮箱配置 API 集成测试

测试邮箱配置管理的完整 API 流程：
1. 创建邮箱配置
2. 查询配置列表
3. 获取单个配置
4. 更新配置
5. 验证连接
6. 手动检查邮件
7. 删除配置

使用方法：
pytest tests/test_email_api_integration.py -v
或
pytest tests/test_email_api_integration.py -v --cov=web_service.routes.email
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch, MagicMock

from web_service.main import app
from src.services.database import get_db
from src.models import Base, User, EmailConfig
from src.services.dependencies import get_current_user
from src.utils.crypto import PasswordEncryption


# 测试数据库
TEST_DATABASE_URL = "sqlite:///./test_email_api.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def set_test_env():
    """设置测试环境变量"""
    original_env = os.environ.copy()
    os.environ["PASSWORD_ENCRYPTION_KEY"] = "test-encryption-key-32-bytes-long!"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["ALGORITHM"] = "HS256"
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU9bK8fk.5q",  # TestPass123!
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client(db_session, test_user):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(test_user):
    """生成认证头"""
    from src.services.auth import create_access_token
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_email_service():
    """模拟 EmailService"""
    with patch('web_service.routes.email.EmailService') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.verify_connection.return_value = True
        mock_instance.connect.return_value = MagicMock()
        mock_instance.fetch_emails.return_value = []
        yield mock_instance


@pytest.fixture
def valid_email_config():
    """有效的邮箱配置数据"""
    return {
        "email_address": "test@example.com",
        "password": "TestPassword123",
        "imap_server": "imap.example.com",
        "imap_port": 993,
        "use_ssl": True,
        "provider": "custom",
        "config_name": "测试邮箱",
        "check_frequency": "hourly"
    }


# ==================== 测试用例 ====================

class TestEmailConfigCreation:
    """测试邮箱配置创建"""

    def test_create_email_config_success(self, client, valid_email_config, mock_email_service):
        """测试成功创建邮箱配置"""
        response = client.post("/api/email/config", json=valid_email_config)

        assert response.status_code == 200
        data = response.json()
        assert data["email_address"] == valid_email_config["email_address"]
        assert data["imap_server"] == valid_email_config["imap_server"]
        assert data["config_name"] == valid_email_config["config_name"]
        assert "id" in data
        assert data["is_active"] is True
        assert data["is_verified"] is False

    def test_create_email_config_duplicate(self, client, db_session, valid_email_config):
        """测试创建重复邮箱配置"""
        # 创建第一个配置
        client.post("/api/email/config", json=valid_email_config)

        # 尝试创建重复配置
        response = client.post("/api/email/config", json=valid_email_config)

        assert response.status_code == 400
        assert "已存在" in response.json()["detail"]

    def test_create_email_config_invalid_email(self, client, valid_email_config):
        """测试创建邮箱配置 - 无效邮箱"""
        valid_email_config["email_address"] = "invalid-email"
        response = client.post("/api/email/config", json=valid_email_config)

        assert response.status_code == 422  # Validation error

    def test_create_email_config_invalid_port(self, client, valid_email_config):
        """测试创建邮箱配置 - 无效端口"""
        valid_email_config["imap_port"] = 99999
        response = client.post("/api/email/config", json=valid_email_config)

        assert response.status_code == 422  # Validation error


class TestEmailConfigRetrieval:
    """测试邮箱配置查询"""

    def test_get_email_configs_empty(self, client):
        """测试获取空的配置列表"""
        response = client.get("/api/email/configs")

        assert response.status_code == 200
        data = response.json()
        assert data["configs"] == []
        assert data["total"] == 0

    def test_get_email_configs_with_data(self, client, valid_email_config):
        """测试获取配置列表"""
        # 创建两个配置
        client.post("/api/email/config", json=valid_email_config)
        valid_email_config["email_address"] = "test2@example.com"
        client.post("/api/email/config", json=valid_email_config)

        response = client.get("/api/email/configs")

        assert response.status_code == 200
        data = response.json()
        assert len(data["configs"]) == 2
        assert data["total"] == 2

    def test_get_single_email_config_success(self, client, valid_email_config):
        """测试获取单个配置"""
        create_response = client.post("/api/email/config", json=valid_email_config)
        config_id = create_response.json()["id"]

        response = client.get(f"/api/email/config/{config_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == config_id
        assert data["email_address"] == valid_email_config["email_address"]

    def test_get_single_email_config_not_found(self, client):
        """测试获取不存在的配置"""
        response = client.get("/api/email/config/99999")

        assert response.status_code == 404


class TestEmailConfigUpdate:
    """测试邮箱配置更新"""

    def test_update_email_config_success(self, client, valid_email_config):
        """测试成功更新配置"""
        create_response = client.post("/api/email/config", json=valid_email_config)
        config_id = create_response.json()["id"]

        update_data = {
            "config_name": "更新的配置名称",
            "check_frequency": "daily"
        }
        response = client.put(f"/api/email/config/{config_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["config_name"] == "更新的配置名称"
        assert data["check_frequency"] == "daily"

    def test_update_email_config_not_found(self, client):
        """测试更新不存在的配置"""
        response = client.put("/api/email/config/99999", json={"config_name": "新名称"})

        assert response.status_code == 404


class TestEmailConfigDeletion:
    """测试邮箱配置删除"""

    def test_delete_email_config_success(self, client, valid_email_config):
        """测试成功删除配置"""
        create_response = client.post("/api/email/config", json=valid_email_config)
        config_id = create_response.json()["id"]

        response = client.delete(f"/api/email/config/{config_id}")

        assert response.status_code == 200
        assert "删除" in response.json()["message"] or "deleted" in response.json()["message"].lower()

        # 验证配置已删除
        get_response = client.get(f"/api/email/config/{config_id}")
        assert get_response.status_code == 404

    def test_delete_email_config_not_found(self, client):
        """测试删除不存在的配置"""
        response = client.delete("/api/email/config/99999")

        assert response.status_code == 404


class TestEmailConfigVerification:
    """测试邮箱连接验证"""

    def test_verify_email_connection_success(self, client, valid_email_config, mock_email_service):
        """测试成功验证连接"""
        create_response = client.post("/api/email/config", json=valid_email_config)
        config_id = create_response.json()["id"]

        response = client.post(f"/api/email/config/{config_id}/verify")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "成功" in data["message"] or "success" in data["message"].lower()

    def test_verify_email_connection_failure(self, client, valid_email_config):
        """测试验证连接失败"""
        create_response = client.post("/api/email/config", json=valid_email_config)
        config_id = create_response.json()["id"]

        # Mock the EmailService.verify_connection to return False
        with patch('web_service.routes.email.EmailService') as mock_es:
            mock_instance = MagicMock()
            mock_instance.verify_connection.return_value = False
            mock_es.return_value = mock_instance

            response = client.post(f"/api/email/config/{config_id}/verify")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False


class TestEmailManualCheck:
    """测试手动邮件检查"""

    def test_manual_email_check_success(self, client, valid_email_config):
        """测试手动触发邮件检查"""
        create_response = client.post("/api/email/config", json=valid_email_config)
        config_id = create_response.json()["id"]

        with patch('web_service.routes.email.EmailImportSource') as mock_import_source:
            mock_instance = MagicMock()
            mock_import_source.return_value.import_bills.return_value = {
                "total": 1,
                "imported": 1,
                "skipped": 0,
                "failed": 0
            }

            # Provide request body with config_id
            response = client.post("/api/email/check", json={"config_id": config_id})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "checked_configs" in data


class TestEmailProviders:
    """测试邮箱服务商模板"""

    def test_get_email_providers(self, client):
        """测试获取服务商列表"""
        response = client.get("/api/email/providers")

        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert len(data["providers"]) > 0

        # 验证包含常用服务商
        provider_names = [p["provider"] for p in data["providers"]]
        assert "qq" in provider_names
        assert "163" in provider_names
        assert "gmail" in provider_names
        assert "outlook" in provider_names


class TestProcessedEmailHistory:
    """测试已处理邮件历史"""

    def test_get_processed_emails_empty(self, client, valid_email_config):
        """测试获取空的邮件历史"""
        create_response = client.post("/api/email/config", json=valid_email_config)
        config_id = create_response.json()["id"]

        response = client.get(f"/api/email/processed?config_id={config_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["emails"] == []
        assert data["total"] == 0


class TestSecurity:
    """测试安全性"""

    def test_password_encrypted_in_storage(self, client, db_session, valid_email_config):
        """测试密码加密存储"""
        response = client.post("/api/email/config", json=valid_email_config)
        config_id = response.json()["id"]

        # 直接查询数据库
        config = db_session.query(EmailConfig).filter(EmailConfig.id == config_id).first()
        assert config is not None
        assert config.password_encrypted != valid_email_config["password"]
        assert len(config.password_encrypted) > 0

    def test_password_not_in_response(self, client, valid_email_config):
        """测试响应中不包含密码"""
        response = client.post("/api/email/config", json=valid_email_config)

        assert "password" not in response.json()
        assert "password_encrypted" not in response.json()

    def test_user_data_isolation(self, client, db_session, test_user, valid_email_config):
        """测试用户数据隔离"""
        # 为测试用户创建配置
        response = client.post("/api/email/config", json=valid_email_config)
        config_id = response.json()["id"]

        # 创建另一个用户
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU9bK8fk.5q",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()

        # 切换到另一个用户
        def override_get_current_user_other():
            return other_user

        app.dependency_overrides[get_current_user] = override_get_current_user_other

        # 尝试访问第一个用户的配置
        response = client.get(f"/api/email/config/{config_id}")

        # 应该返回404（数据隔离）
        assert response.status_code == 404

        app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=web_service.routes.email", "--cov-report=term-missing"])
