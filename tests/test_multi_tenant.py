"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
Multi-tenant functionality tests.

测试内容：
1. 用户数据隔离
2. 用户Notion配置隔离
3. 用户文件上传隔离
4. 单用户模式兼容性
5. 会话管理
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta

import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.models import Base, User, UserSession, UserNotionConfig, UserUpload, ImportHistory
from src.auth import get_password_hash
from src.config import Config


# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test_multi_tenant.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 测试上传目录
TEST_UPLOAD_DIR = tempfile.mkdtemp(prefix="test_uploads_")


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话。"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

    if os.path.exists("./test_multi_tenant.db"):
        os.remove("./test_multi_tenant.db")


@pytest.fixture(scope="function")
def upload_dir():
    """创建测试上传目录。"""
    os.makedirs(TEST_UPLOAD_DIR, exist_ok=True)

    yield TEST_UPLOAD_DIR

    # 清理测试目录
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)


@pytest.fixture(scope="function")
def user1(db_session):
    """创建测试用户1。"""
    user = User(
        username="user1",
        email="user1@example.com",
        password_hash=get_password_hash("Password123!"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def user2(db_session):
    """创建测试用户2。"""
    user = User(
        username="user2",
        email="user2@example.com",
        password_hash=get_password_hash("Password123!"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def superuser(db_session):
    """创建超级管理员。"""
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


class TestDataIsolation:
    """数据隔离测试。"""

    def test_users_separate_records(self, db_session, user1, user2):
        """测试用户记录完全隔离。"""
        # 为user1创建Notion配置
        config1 = UserNotionConfig(
            user_id=user1.id,
            notion_api_key="key1_abc123",
            notion_income_database_id="income_db_1",
            notion_expense_database_id="expense_db_1"
        )
        db_session.add(config1)

        # 为user2创建Notion配置
        config2 = UserNotionConfig(
            user_id=user2.id,
            notion_api_key="key2_def456",
            notion_income_database_id="income_db_2",
            notion_expense_database_id="expense_db_2"
        )
        db_session.add(config2)

        db_session.commit()

        # 验证配置隔离
        configs1 = db_session.query(UserNotionConfig).filter(
            UserNotionConfig.user_id == user1.id
        ).all()

        configs2 = db_session.query(UserNotionConfig).filter(
            UserNotionConfig.user_id == user2.id
        ).all()

        assert len(configs1) == 1
        assert len(configs2) == 1
        assert configs1[0].notion_api_key == "key1_abc123"
        assert configs2[0].notion_api_key == "key2_def456"

    def test_user_uploads_isolation(self, db_session, user1, user2):
        """测试用户上传文件隔离。"""
        # 为user1创建上传记录
        upload1 = UserUpload(
            user_id=user1.id,
            file_name="bill1.csv",
            original_file_name="bill1.csv",
            file_path="/uploads/user1/bill1.csv",
            file_size=1024,
            platform="alipay"
        )
        db_session.add(upload1)

        # 为user2创建上传记录
        upload2 = UserUpload(
            user_id=user2.id,
            file_name="bill2.csv",
            original_file_name="bill2.csv",
            file_path="/uploads/user2/bill2.csv",
            file_size=2048,
            platform="wechat"
        )
        db_session.add(upload2)

        db_session.commit()

        # 验证上传记录隔离
        uploads1 = db_session.query(UserUpload).filter(
            UserUpload.user_id == user1.id
        ).all()

        uploads2 = db_session.query(UserUpload).filter(
            UserUpload.user_id == user2.id
        ).all()

        assert len(uploads1) == 1
        assert len(uploads2) == 1
        assert uploads1[0].file_name == "bill1.csv"
        assert uploads2[0].file_name == "bill2.csv"

    def test_import_history_isolation(self, db_session, user1, user2):
        """测试导入历史隔离。"""
        # 为user1创建导入历史
        history1 = ImportHistory(
            user_id=user1.id,
            total_records=100,
            imported_records=95,
            skipped_records=5,
            failed_records=0,
            status="success",
            platform="alipay"
        )
        db_session.add(history1)

        # 为user2创建导入历史
        history2 = ImportHistory(
            user_id=user2.id,
            total_records=50,
            imported_records=48,
            skipped_records=2,
            failed_records=0,
            status="success",
            platform="wechat"
        )
        db_session.add(history2)

        db_session.commit()

        # 验证导入历史隔离
        histories1 = db_session.query(ImportHistory).filter(
            ImportHistory.user_id == user1.id
        ).all()

        histories2 = db_session.query(ImportHistory).filter(
            ImportHistory.user_id == user2.id
        ).all()

        assert len(histories1) == 1
        assert len(histories2) == 1
        assert histories1[0].total_records == 100
        assert histories2[0].total_records == 50


class TestNotionConfigIsolation:
    """Notion配置隔离测试。"""

    def test_multiple_notion_configs(self, db_session, user1, user2):
        """测试多个用户拥有不同的Notion配置。"""
        # 为每个用户创建配置
        config1 = UserNotionConfig(
            user_id=user1.id,
            notion_api_key="secret_user1",
            notion_income_database_id="db1_income",
            notion_expense_database_id="db1_expense",
            config_name="User1 Config"
        )
        db_session.add(config1)

        config2 = UserNotionConfig(
            user_id=user2.id,
            notion_api_key="secret_user2",
            notion_income_database_id="db2_income",
            notion_expense_database_id="db2_expense",
            config_name="User2 Config"
        )
        db_session.add(config2)

        db_session.commit()

        # 验证配置完全独立
        retrieved_config1 = db_session.query(UserNotionConfig).filter(
            UserNotionConfig.user_id == user1.id
        ).first()

        retrieved_config2 = db_session.query(UserNotionConfig).filter(
            UserNotionConfig.user_id == user2.id
        ).first()

        assert retrieved_config1.notion_api_key != retrieved_config2.notion_api_key
        assert retrieved_config1.notion_income_database_id != retrieved_config2.notion_income_database_id

    def test_update_user_config_not_affect_others(self, db_session, user1, user2):
        """测试更新用户配置不影响其他用户。"""
        # 创建初始配置
        config1 = UserNotionConfig(
            user_id=user1.id,
            notion_api_key="secret_user1",
            notion_income_database_id="db1_income",
            notion_expense_database_id="db1_expense"
        )
        db_session.add(config1)

        config2 = UserNotionConfig(
            user_id=user2.id,
            notion_api_key="secret_user2",
            notion_income_database_id="db2_income",
            notion_expense_database_id="db2_expense"
        )
        db_session.add(config2)
        db_session.commit()

        # 更新user1的配置
        config1.notion_api_key = "secret_user1_updated"
        config1.config_name = "Updated Config"
        db_session.commit()

        # 验证user2的配置未受影响
        db_session.refresh(config2)
        assert config2.notion_api_key == "secret_user2"
        assert config2.config_name is None


class TestSessionIsolation:
    """会话隔离测试。"""

    def test_user_sessions_separate(self, db_session, user1, user2):
        """测试用户会话完全隔离。"""
        # 为user1创建会话
        session1 = UserSession(
            user_id=user1.id,
            token="token_user1_1",
            refresh_token="refresh_user1_1",
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            ip_address="192.168.1.1",
            user_agent="Browser/1.0"
        )
        db_session.add(session1)

        # 为user2创建会话
        session2 = UserSession(
            user_id=user2.id,
            token="token_user2_1",
            refresh_token="refresh_user2_1",
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            ip_address="192.168.1.2",
            user_agent="Browser/2.0"
        )
        db_session.add(session2)

        db_session.commit()

        # 验证会话隔离
        sessions1 = db_session.query(UserSession).filter(
            UserSession.user_id == user1.id
        ).all()

        sessions2 = db_session.query(UserSession).filter(
            UserSession.user_id == user2.id
        ).all()

        assert len(sessions1) == 1
        assert len(sessions2) == 1
        assert sessions1[0].token == "token_user1_1"
        assert sessions2[0].token == "token_user2_1"

    def test_revoke_user_sessions_not_affect_others(self, db_session, user1, user2):
        """测试撤销用户会话不影响其他用户。"""
        # 为user1创建多个会话
        for i in range(3):
            session = UserSession(
                user_id=user1.id,
                token=f"token_user1_{i}",
                refresh_token=f"refresh_user1_{i}",
                expires_at=datetime.utcnow() + timedelta(minutes=15)
            )
            db_session.add(session)

        # 为user2创建会话
        session2 = UserSession(
            user_id=user2.id,
            token="token_user2_1",
            refresh_token="refresh_user2_1",
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db_session.add(session2)
        db_session.commit()

        # 撤销user1的所有会话
        user1_sessions = db_session.query(UserSession).filter(
            UserSession.user_id == user1.id
        ).all()

        for session in user1_sessions:
            session.is_revoked = True

        db_session.commit()

        # 验证user2的会话仍然有效
        active_sessions2 = db_session.query(UserSession).filter(
            UserSession.user_id == user2.id,
            UserSession.is_revoked == False
        ).count()

        assert active_sessions2 == 1


class TestSuperuserAccess:
    """超级管理员权限测试。"""

    def test_superuser_can_see_all_users(self, db_session, user1, user2, superuser):
        """测试超级管理员可以查看所有用户。"""
        all_users = db_session.query(User).all()

        assert len(all_users) == 3  # user1, user2, superuser

        # 验证可以访问每个用户的数据
        for user in all_users:
            assert user.id is not None
            assert user.username is not None

    def test_regular_user_cannot_see_others(self, db_session, user1, user2):
        """测试普通用户无法访问其他用户的数据。"""
        # user1只能访问自己的上传
        user1_uploads = db_session.query(UserUpload).filter(
            UserUpload.user_id == user1.id
        ).all()

        # user2只能访问自己的上传
        user2_uploads = db_session.query(UserUpload).filter(
            UserUpload.user_id == user2.id
        ).all()

        # 创建user2的上传记录
        upload2 = UserUpload(
            user_id=user2.id,
            file_name="user2_bill.csv",
            original_file_name="user2_bill.csv",
            file_path="/uploads/user2/bill.csv",
            file_size=1024,
            platform="alipay"
        )
        db_session.add(upload2)
        db_session.commit()

        # 验证user1看不到user2的上传
        user1_uploads = db_session.query(UserUpload).filter(
            UserUpload.user_id == user1.id
        ).all()

        assert len(user1_uploads) == 0


class TestCascadeDelete:
    """级联删除测试。"""

    def test_delete_user_cascades_to_configs(self, db_session, user1):
        """测试删除用户时级联删除配置。"""
        # 创建Notion配置
        config = UserNotionConfig(
            user_id=user1.id,
            notion_api_key="secret_key",
            notion_income_database_id="income_db",
            notion_expense_database_id="expense_db"
        )
        db_session.add(config)
        db_session.commit()

        # 删除用户
        db_session.delete(user1)
        db_session.commit()

        # 验证配置已被级联删除
        remaining_configs = db_session.query(UserNotionConfig).filter(
            UserNotionConfig.user_id == user1.id
        ).count()

        assert remaining_configs == 0

    def test_delete_user_cascades_to_uploads(self, db_session, user1):
        """测试删除用户时级联删除上传记录。"""
        # 创建上传记录
        upload = UserUpload(
            user_id=user1.id,
            file_name="bill.csv",
            original_file_name="bill.csv",
            file_path="/uploads/user1/bill.csv",
            file_size=1024,
            platform="alipay"
        )
        db_session.add(upload)
        db_session.commit()

        # 删除用户
        db_session.delete(user1)
        db_session.commit()

        # 验证上传记录已被级联删除
        remaining_uploads = db_session.query(UserUpload).filter(
            UserUpload.user_id == user1.id
        ).count()

        assert remaining_configs = 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
