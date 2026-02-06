"""SQLAlchemy ORM models for multi-tenant system."""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
    Numeric, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """用户表。"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # 权限和状态
    is_superuser = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    require_password_change = Column(Boolean, default=False, nullable=False)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # 安全相关
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    session_timeout_minutes = Column(Integer, default=15, nullable=False)

    # 关系
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    notion_config = relationship("UserNotionConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    uploads = relationship("UserUpload", back_populates="user", cascade="all, delete-orphan")
    import_history = relationship("ImportHistory", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', is_superuser={self.is_superuser})>"


class UserSession(Base):
    """用户会话表。"""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_revoked = Column(Boolean, default=False, nullable=False)

    # 关系
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class UserNotionConfig(Base):
    """用户Notion配置表。"""

    __tablename__ = "user_notion_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    notion_api_key = Column(String(255), nullable=False)
    notion_income_database_id = Column(String(100), nullable=False)
    notion_expense_database_id = Column(String(100), nullable=False)
    config_name = Column(String(100), default="默认配置")

    is_verified = Column(Boolean, default=False, nullable=False)
    last_verified_at = Column(DateTime(timezone=True))

    # 复盘数据库配置
    notion_monthly_review_db = Column(String(100), nullable=True)
    notion_quarterly_review_db = Column(String(100), nullable=True)
    notion_yearly_review_db = Column(String(100), nullable=True)
    notion_monthly_template_id = Column(String(100), nullable=True)
    notion_quarterly_template_id = Column(String(100), nullable=True)
    notion_yearly_template_id = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="notion_config")

    def __repr__(self):
        return f"<UserNotionConfig(id={self.id}, user_id={self.user_id}, is_verified={self.is_verified})>"


class UserUpload(Base):
    """用户上传记录表。"""

    __tablename__ = "user_uploads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 文件相关字段：文件保存成功后才填充
    file_name = Column(String(255), nullable=True)  # 保存后的文件名
    original_file_name = Column(String(255), nullable=False)  # 原始文件名
    file_path = Column(String(500), nullable=True)  # 完整文件路径
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）

    platform = Column(String(20), nullable=False)  # alipay, wechat, unionpay, auto
    upload_type = Column(String(20), default="immediate")  # immediate, scheduled
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, processing, completed, failed

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # 关系
    user = relationship("User", back_populates="uploads")
    import_history = relationship("ImportHistory", back_populates="upload", uselist=False)

    def __repr__(self):
        return f"<UserUpload(id={self.id}, user_id={self.user_id}, file_name='{self.file_name}', status='{self.status}')>"


class ImportHistory(Base):
    """导入历史表。"""

    __tablename__ = "import_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    upload_id = Column(Integer, ForeignKey("user_uploads.id", ondelete="SET NULL"), index=True)

    total_records = Column(Integer, nullable=False)
    imported_records = Column(Integer, default=0)
    skipped_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)

    status = Column(String(20), nullable=False)  # success, partial, failed
    error_message = Column(Text)

    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # 关系
    user = relationship("User", back_populates="import_history")
    upload = relationship("UserUpload", back_populates="import_history")

    def __repr__(self):
        return f"<ImportHistory(id={self.id}, user_id={self.user_id}, status='{self.status}', imported={self.imported_records}/{self.total_records})>"


class SystemSettings(Base):
    """系统设置表。"""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(Text)
    description = Column(Text)

    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SystemSettings(key='{self.setting_key}', value='{self.setting_value}')>"


class AuditLog(Base):
    """审计日志表。"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)

    action = Column(String(100), nullable=False, index=True)  # login, logout, register, user_created, etc.
    resource_type = Column(String(50), index=True)  # user, upload, config, etc.
    resource_id = Column(Integer, index=True)

    ip_address = Column(String(45))
    user_agent = Column(Text)
    details = Column(Text)  # JSON格式的详细信息

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # 关系
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', created_at={self.created_at})>"
