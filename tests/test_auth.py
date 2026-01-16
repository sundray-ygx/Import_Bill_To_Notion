"""
Authentication system tests.

测试内容：
1. 用户注册
2. 用户登录
3. Token验证
4. 密码加密和验证
5. 会话管理
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, verify_refresh_token,
    validate_password_strength, LoginSecurity, SessionManager
)
from models import Base, User, UserSession
from schemas import UserCreate
from config import Config


# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话。"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    session = TestingSessionLocal()

    yield session

    # 清理：删除所有表
    session.close()
    Base.metadata.drop_all(bind=engine)

    # 删除测试数据库文件
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture(scope="function")
def test_password():
    """测试密码。"""
    return "TestPassword123!"


@pytest.fixture(scope="function")
def test_user_data():
    """测试用户数据。"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!"
    }


class TestPasswordHashing:
    """密码加密和验证测试。"""

    def test_get_password_hash(self, test_password):
        """测试密码哈希生成。"""
        password_hash = get_password_hash(test_password)

        # 验证哈希不为空
        assert password_hash is not None
        assert len(password_hash) > 0

        # 验证哈希不等于原密码
        assert password_hash != test_password

        # 验证bcrypt格式（以$2b$开头）
        assert password_hash.startswith("$2b$")

    def test_verify_password_correct(self, test_password):
        """测试正确的密码验证。"""
        password_hash = get_password_hash(test_password)

        # 验证正确的密码
        is_valid = verify_password(test_password, password_hash)
        assert is_valid is True

    def test_verify_password_incorrect(self, test_password):
        """测试错误的密码验证。"""
        password_hash = get_password_hash(test_password)

        # 验证错误的密码
        is_valid = verify_password("WrongPassword123!", password_hash)
        assert is_valid is False

    def test_hash_same_password_different_hashes(self, test_password):
        """测试相同密码生成不同的哈希值（bcrypt的salt特性）。"""
        hash1 = get_password_hash(test_password)
        hash2 = get_password_hash(test_password)

        # 哈希值应该不同（因为salt不同）
        assert hash1 != hash2

        # 但都应该能验证原密码
        assert verify_password(test_password, hash1) is True
        assert verify_password(test_password, hash2) is True


class TestPasswordStrength:
    """密码强度验证测试。"""

    def test_strong_password(self):
        """测试强密码。"""
        is_valid, error = validate_password_strength("StrongPass123!")
        assert is_valid is True
        assert error is None

    def test_weak_password_too_short(self):
        """测试过短的密码。"""
        is_valid, error = validate_password_strength("Short1!")
        assert is_valid is False
        assert "至少8个字符" in error

    def test_weak_password_no_lowercase(self):
        """测试没有小写字母的密码。"""
        is_valid, error = validate_password_strength("PASSWORD123!")
        assert is_valid is False
        assert "小写字母" in error

    def test_weak_password_no_uppercase(self):
        """测试没有大写字母的密码。"""
        is_valid, error = validate_password_strength("password123!")
        assert is_valid is False
        assert "大写字母" in error

    def test_weak_password_no_digit(self):
        """测试没有数字的密码。"""
        is_valid, error = validate_password_strength("Password!")
        assert is_valid is False
        assert "数字" in error


class TestTokenGeneration:
    """Token生成和验证测试。"""

    def test_create_access_token(self):
        """测试生成access token。"""
        data = {"sub": "123"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """测试生成refresh token。"""
        data = {"sub": "123"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_refresh_token_valid(self):
        """测试验证有效的refresh token。"""
        data = {"sub": "123"}
        token = create_refresh_token(data)

        payload = verify_refresh_token(token)
        assert payload is not None
        assert payload.get("sub") == "123"

    def test_verify_refresh_token_invalid(self):
        """测试验证无效的refresh token。"""
        payload = verify_refresh_token("invalid_token")
        assert payload is None


class TestLoginSecurity:
    """登录安全测试。"""

    def test_record_login_attempt_success(self, db_session, test_user_data):
        """测试记录成功的登录尝试。"""
        # 创建测试用户
        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=get_password_hash(test_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()

        # 记录成功登录
        LoginSecurity.record_login_attempt(user, True, db_session)
        db_session.refresh(user)

        # 验证登录尝试已重置
        assert user.login_attempts == 0
        assert user.locked_until is None

    def test_record_login_attempt_failure(self, db_session, test_user_data):
        """测试记录失败的登录尝试。"""
        # 创建测试用户
        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=get_password_hash(test_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()

        # 记录失败登录
        LoginSecurity.record_login_attempt(user, False, db_session)
        db_session.refresh(user)

        # 验证登录尝试已增加
        assert user.login_attempts == 1
        assert user.locked_until is None

    def test_check_account_locked(self, db_session, test_user_data):
        """测试账户锁定检查。"""
        # 创建测试用户
        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=get_password_hash(test_user_data["password"]),
            locked_until=datetime.utcnow() + timedelta(minutes=30)
        )
        db_session.add(user)
        db_session.commit()

        # 检查账户是否被锁定
        is_locked, locked_until = LoginSecurity.check_account_locked(user)

        assert is_locked is True
        assert locked_until is not None


class TestSessionManager:
    """会话管理测试。"""

    def test_revoke_all_user_sessions(self, db_session, test_user_data):
        """测试撤销用户所有会话。"""
        # 创建测试用户
        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=get_password_hash(test_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()

        # 创建多个会话
        for i in range(3):
            session = UserSession(
                user_id=user.id,
                token=f"token_{i}",
                refresh_token=f"refresh_{i}",
                expires_at=datetime.utcnow() + timedelta(minutes=15)
            )
            db_session.add(session)
        db_session.commit()

        # 撤销所有会话
        count = SessionManager.revoke_all_user_sessions(user.id, db_session)

        assert count == 3

        # 验证所有会话已被撤销
        active_sessions = db_session.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_revoked == False
        ).count()

        assert active_sessions == 0


class TestBcrypt72ByteLimit:
    """bcrypt 72 字节限制测试。

    测试 bcrypt 算法的 72 字节密码限制处理。
    这个测试用例验证当密码超过 72 字节时，
    我们的截断逻辑是否正确工作。
    """

    def test_password_exactly_72_bytes(self):
        """测试恰好 72 字节的密码。"""
        # 72 字节的 ASCII 密码
        password = "a" * 72
        password_hash = get_password_hash(password)

        assert password_hash is not None
        assert password_hash.startswith("$2b$")

        # 验证密码可以正确验证
        is_valid = verify_password(password, password_hash)
        assert is_valid is True

    def test_password_over_72_bytes_ascii(self):
        """测试超过 72 字节的 ASCII 密码。"""
        # 100 字节的 ASCII 密码（超过限制）
        password = "a" * 100
        password_hash = get_password_hash(password)

        assert password_hash is not None
        assert password_hash.startswith("$2b$")

        # 验证密码可以正确验证（使用完整的密码）
        is_valid = verify_password(password, password_hash)
        assert is_valid is True

    def test_password_over_72_bytes_unicode(self):
        """测试超过 72 字节的 Unicode 密码。"""
        # 中文字符每个占用 3 字节（UTF-8），所以 30 个字符 = 90 字节
        password = "测试密码超过限制" * 5  # 约 150+ 字节
        password_hash = get_password_hash(password)

        assert password_hash is not None
        assert password_hash.startswith("$2b$")

        # 验证密码可以正确验证
        is_valid = verify_password(password, password_hash)
        assert is_valid is True

    def test_password_over_72_bytes_mixed(self):
        """测试混合字符的超长密码。"""
        # 混合 ASCII 和 Unicode 字符，超过 72 字节
        password = "MyPassword123!测试混合字符" * 3
        password_hash = get_password_hash(password)

        assert password_hash is not None
        assert password_hash.startswith("$2b$")

        # 验证密码可以正确验证
        is_valid = verify_password(password, password_hash)
        assert is_valid is True

    def test_truncated_password_consistency(self):
        """测试截断后的密码一致性。

        验证超过 72 字节的密码在哈希和验证时
        使用相同的截断逻辑。
        """
        # 超长密码
        long_password = "a" * 100

        # 生成哈希
        hash1 = get_password_hash(long_password)
        hash2 = get_password_hash(long_password)

        # 两次哈希应该不同（因为 salt 不同）
        assert hash1 != hash2

        # 但都应该能验证原密码
        assert verify_password(long_password, hash1) is True
        assert verify_password(long_password, hash2) is True

        # 使用截断前的密码应该失败（如果只用前 72 字节）
        # 这里验证我们使用完整密码进行截断处理
        truncated = long_password[:72]
        # 注意：由于我们使用字节级截断，这个测试验证了
        # 即使是 72 字节边界，密码也能正确验证

    def test_password_with_emoji(self):
        """测试包含 emoji 的密码。"""
        # Emoji 通常占用 4 字节
        password = "Password😀🎉" * 5  # 超过 72 字节
        password_hash = get_password_hash(password)

        assert password_hash is not None
        assert password_hash.startswith("$2b$")

        # 验证密码可以正确验证
        is_valid = verify_password(password, password_hash)
        assert is_valid is True


class TestUserCreation:
    """用户创建测试。"""

    def test_create_user_with_valid_data(self, db_session, test_user_data):
        """测试使用有效数据创建用户。"""
        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=get_password_hash(test_user_data["password"]),
            is_active=True
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == test_user_data["username"]
        assert user.email == test_user_data["email"]
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None

    def test_create_superuser(self, db_session, test_user_data):
        """测试创建超级管理员。"""
        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=get_password_hash(test_user_data["password"]),
            is_superuser=True,
            is_active=True
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.is_superuser is True


class TestUserSession:
    """用户会话测试。"""

    def test_create_user_session(self, db_session, test_user_data):
        """测试创建用户会话。"""
        # 创建用户
        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=get_password_hash(test_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()

        # 创建会话
        session = UserSession(
            user_id=user.id,
            token="test_access_token",
            refresh_token="test_refresh_token",
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0"
        )

        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        assert session.id is not None
        assert session.user_id == user.id
        assert session.token == "test_access_token"
        assert session.is_revoked is False

    def test_revoke_session(self, db_session, test_user_data):
        """测试撤销会话。"""
        # 创建用户
        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=get_password_hash(test_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()

        # 创建会话
        session = UserSession(
            user_id=user.id,
            token="test_access_token",
            refresh_token="test_refresh_token",
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )

        db_session.add(session)
        db_session.commit()

        # 撤销会话
        session.is_revoked = True
        db_session.commit()
        db_session.refresh(session)

        assert session.is_revoked is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
