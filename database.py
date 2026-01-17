"""Database management for multi-tenant system."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = "sqlite:///data/database.sqlite"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite需要
    echo=False  # 设置为True可查看SQL日志
)

# Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
Base = declarative_base()


def init_db():
    """初始化数据库，创建所有表。"""
    # 确保data目录存在
    os.makedirs("data", exist_ok=True)

    # 导入所有模型以确保表被注册
    from models import (
        User, UserSession, UserNotionConfig,
        UserUpload, ImportHistory, SystemSettings, AuditLog
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


@contextmanager
def get_db_context():
    """获取数据库session的上下文管理器。

    用于非FastAPI环境（如脚本、测试）。

    用法:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db():
    """获取数据库session的生成器。

    用于FastAPI依赖注入。

    用法:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DBManager:
    """数据库管理器，提供常用操作。"""

    @staticmethod
    def reset_database():
        """重置数据库（删除所有数据并重新创建表）。

        警告：此操作会删除所有数据！
        """
        from models import (
            User, UserSession, UserNotionConfig,
            UserUpload, ImportHistory, SystemSettings, AuditLog
        )

        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")

        # 重新创建表
        Base.metadata.create_all(bind=engine)
        logger.info("Database reset completed")

    @staticmethod
    def get_database_info() -> dict:
        """获取数据库信息。"""
        from models import (
            User, UserSession, UserNotionConfig,
            UserUpload, ImportHistory, SystemSettings, AuditLog
        )

        db = SessionLocal()
        try:
            info = {
                "database_size": _get_db_size(),
                "tables": {
                    "users": db.query(User).count(),
                    "user_sessions": db.query(UserSession).count(),
                    "user_notion_configs": db.query(UserNotionConfig).count(),
                    "user_uploads": db.query(UserUpload).count(),
                    "import_history": db.query(ImportHistory).count(),
                    "system_settings": db.query(SystemSettings).count(),
                    "audit_logs": db.query(AuditLog).count(),
                }
            }
            return info
        finally:
            db.close()

    @staticmethod
    def backup_database(backup_path: str = None):
        """备份数据库文件。

        Args:
            backup_path: 备份文件路径，默认为data/database.backup.{timestamp}.sqlite
        """
        import shutil
        from datetime import datetime

        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/database.backup.{timestamp}.sqlite"

        if os.path.exists("data/database.sqlite"):
            shutil.copy2("data/database.sqlite", backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return backup_path
        else:
            raise FileNotFoundError("Database file not found")


def _get_db_size() -> int:
    """获取数据库文件大小（字节）。"""
    db_path = "data/database.sqlite"
    if os.path.exists(db_path):
        return os.path.getsize(db_path)
    return 0


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    init_db()
    info = DBManager.get_database_info()
    print(f"Database info: {info}")
