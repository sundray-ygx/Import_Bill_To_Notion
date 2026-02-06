"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API endpoint tests.

测试内容：
1. 用户注册API
2. 用户登录API
3. Token刷新API
4. 用户信息API
5. 权限验证
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_service.main import app
from src.services.database import get_db
from src.models import Base, User, UserSession
from src.auth import get_password_hash, create_access_token, create_refresh_token
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 依赖项覆盖：使用测试数据库
def override_get_db():
    """覆盖get_db依赖项以使用测试数据库。"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 覆盖依赖项
from web_service.main import app as main_app
main_app.dependency_overrides[get_db] = override_get_db

client = TestClient(main_app)


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话。"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

    if os.path.exists("./test_api.db"):
        os.remove("./test_api.db")


@pytest.fixture(scope="function")
def test_user(db_session):
    """创建测试用户。"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("TestPassword123!"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_superuser(db_session):
    """创建测试超级管理员。"""
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("AdminPassword123!"),
        is_superuser=True,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """获取认证头。"""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def superuser_headers(test_superuser):
    """获取超级管理员认证头。"""
    token = create_access_token(data={"sub": str(test_superuser.id)})
    return {"Authorization": f"Bearer {token}"}


class TestAuthEndpoints:
    """认证端点测试。"""

    def test_register_user_success(self):
        """测试成功注册用户。"""
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPassword123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    def test_register_user_duplicate_username(self, test_user):
        """测试注册时用户名重复。"""
        response = client.post("/api/auth/register", json={
            "username": test_user.username,
            "email": "different@example.com",
            "password": "Password123!"
        })

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_register_user_weak_password(self):
        """测试注册时密码强度不足。"""
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "weak"
        })

        assert response.status_code == 400

    def test_login_success(self, test_user):
        """测试成功登录。"""
        response = client.post("/api/auth/login", data={
            "username": test_user.username,
            "password": "TestPassword123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_invalid_credentials(self):
        """测试登录时凭证无效。"""
        response = client.post("/api/auth/login", data={
            "username": "nonexistent",
            "password": "WrongPassword123!"
        })

        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_login_inactive_user(self, db_session, test_user):
        """测试登录未激活用户。"""
        test_user.is_active = False
        db_session.commit()

        response = client.post("/api/auth/login", data={
            "username": test_user.username,
            "password": "TestPassword123!"
        })

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"]


class TestUserEndpoints:
    """用户端点测试。"""

    def test_get_current_user(self, auth_headers):
        """测试获取当前用户信息。"""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data

    def test_get_current_user_unauthorized(self):
        """测试未认证访问用户信息。"""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_change_password_success(self, auth_headers):
        """测试成功修改密码。"""
        response = client.post("/api/auth/change-password", headers=auth_headers, json={
            "current_password": "TestPassword123!",
            "new_password": "NewPassword456!"
        })

        assert response.status_code == 200
        assert "success" in response.json()["message"]

    def test_change_password_wrong_current(self, auth_headers):
        """测试修改密码时当前密码错误。"""
        response = client.post("/api/auth/change-password", headers=auth_headers, json={
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword456!"
        })

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"]


class TestTokenRefresh:
    """Token刷新测试。"""

    def test_refresh_token_success(self, db_session, test_user):
        """测试成功刷新token。"""
        # 创建会话
        refresh_token = create_refresh_token(data={"sub": str(test_user.id)})
        session = UserSession(
            user_id=test_user.id,
            token="old_access_token",
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db_session.add(session)
        db_session.commit()

        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self):
        """测试刷新token时token无效。"""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_refresh_token"
        })

        assert response.status_code == 401


class TestAdminEndpoints:
    """管理员端点测试。"""

    def test_get_stats_success(self, superuser_headers):
        """测试成功获取系统统计。"""
        response = client.get("/api/admin/stats", headers=superuser_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data

    def test_get_stats_unauthorized(self, auth_headers):
        """测试未授权访问系统统计。"""
        response = client.get("/api/admin/stats", headers=auth_headers)

        assert response.status_code == 403

    def test_get_users_list_success(self, superuser_headers):
        """测试成功获取用户列表。"""
        response = client.get("/api/admin/users", headers=superuser_headers)

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data

    def test_get_users_list_unauthorized(self, auth_headers):
        """测试未授权访问用户列表。"""
        response = client.get("/api/admin/users", headers=auth_headers)

        assert response.status_code == 403

    def test_create_user_success(self, superuser_headers):
        """测试管理员创建用户。"""
        response = client.post("/api/admin/users", headers=superuser_headers, json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPassword123!",
            "is_active": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"

    def test_update_user_success(self, db_session, test_user, superuser_headers):
        """测试管理员更新用户。"""
        response = client.put(f"/api/admin/users/{test_user.id}", headers=superuser_headers, json={
            "email": "updated@example.com",
            "is_active": False
        })

        assert response.status_code == 200

    def test_delete_user_success(self, db_session, test_user, superuser_headers):
        """测试管理员删除用户。"""
        response = client.delete(f"/api/admin/users/{test_user.id}", headers=superuser_headers)

        assert response.status_code == 200

    def test_reset_user_password_success(self, db_session, test_user, superuser_headers):
        """测试管理员重置用户密码。"""
        response = client.post(f"/api/admin/users/{test_user.id}/reset-password",
                             headers=superuser_headers,
                             json={"new_password": "NewPassword123!"})

        assert response.status_code == 200


class TestBillsEndpoints:
    """账单端点测试。"""

    def test_get_history_stats_success(self, auth_headers):
        """测试成功获取导入历史统计。"""
        response = client.get("/api/bills/history/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "successful" in data

    def test_get_history_stats_unauthorized(self):
        """测试未授权访问历史统计。"""
        response = client.get("/api/bills/history/stats")

        assert response.status_code == 401


class TestSetupEndpoints:
    """配置向导端点测试。"""

    def test_check_setup_needed_no_users(self, db_session):
        """测试检查是否需要设置（没有用户）。"""
        response = client.get("/api/auth/setup/check")

        assert response.status_code == 200
        data = response.json()
        assert data["needs_setup"] is True
        assert data["user_count"] == 0

    def test_check_setup_needed_with_users(self, db_session, test_user):
        """测试检查是否需要设置（已有用户）。"""
        response = client.get("/api/auth/setup/check")

        assert response.status_code == 200
        data = response.json()
        assert data["needs_setup"] is False
        assert data["user_count"] > 0

    def test_check_username_available(self):
        """测试检查用户名是否可用。"""
        response = client.post("/api/auth/setup/check-username", json={
            "username": "newusername"
        })

        assert response.status_code == 200
        data = response.json()
        assert "exists" in data

    def test_create_admin_success(self, db_session):
        """测试成功创建管理员。"""
        response = client.post("/api/auth/setup/create-admin", json={
            "username": "admin",
            "email": "admin@example.com",
            "password": "AdminPassword123!",
            "settings": {
                "allow_registration": True
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_admin_when_users_exist(self, db_session, test_user):
        """测试已有用户时创建管理员（应该失败）。"""
        response = client.post("/api/auth/setup/create-admin", json={
            "username": "admin",
            "email": "admin@example.com",
            "password": "AdminPassword123!"
        })

        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
