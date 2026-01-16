"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict
from datetime import datetime


# ==================== 用户相关 ====================

class UserBase(BaseModel):
    """用户基础schema。"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="电子邮箱")


class UserCreate(UserBase):
    """用户注册schema。"""
    password: str = Field(..., min_length=8, max_length=100, description="密码")

    @validator('password')
    def validate_password(cls, v):
        """验证密码强度。"""
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class UserUpdate(BaseModel):
    """用户更新schema。"""
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """用户响应schema。"""
    id: int
    is_superuser: bool
    is_active: bool
    require_password_change: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class UserProfileResponse(UserResponse):
    """用户资料响应schema（包含统计信息）。"""
    total_uploads: int = 0
    total_imports: int = 0
    notion_configured: bool = False


# ==================== 认证相关 ====================

class TokenResponse(BaseModel):
    """Token响应schema。"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """刷新token请求schema。"""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """修改密码请求schema。"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator('new_password')
    def validate_password(cls, v):
        """验证密码强度。"""
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class PasswordResetRequest(BaseModel):
    """重置密码请求schema（管理员）。"""
    new_password: str = Field(..., min_length=8, max_length=100)


# ==================== Notion配置相关 ====================

class NotionConfigBase(BaseModel):
    """Notion配置基础schema。"""
    notion_api_key: str = Field(..., min_length=10, description="Notion API密钥")
    notion_income_database_id: str = Field(..., min_length=1, description="收入数据库ID")
    notion_expense_database_id: str = Field(..., min_length=1, description="支出数据库ID")
    config_name: str = Field(default="默认配置", max_length=100, description="配置名称")


class NotionConfigCreate(NotionConfigBase):
    """创建Notion配置schema。"""
    pass


class NotionConfigUpdate(BaseModel):
    """更新Notion配置schema。"""
    notion_api_key: Optional[str] = Field(None, min_length=10)
    notion_income_database_id: Optional[str] = Field(None, min_length=1)
    notion_expense_database_id: Optional[str] = Field(None, min_length=1)
    config_name: Optional[str] = Field(None, max_length=100)


class NotionConfigResponse(NotionConfigBase):
    """Notion配置响应schema。"""
    id: int
    user_id: int
    is_verified: bool
    last_verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 文件上传相关 ====================

class FileUploadResponse(BaseModel):
    """文件上传响应schema。"""
    id: int
    file_name: str
    original_file_name: str
    file_size: int
    platform: str
    upload_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UploadRequest(BaseModel):
    """上传请求schema。"""
    platform: Optional[str] = Field("auto", description="支付平台")
    sync_type: str = Field("immediate", description="同步类型: immediate或scheduled")


class UploadResponse(BaseModel):
    """上传操作响应schema。"""
    success: bool
    message: str
    upload_id: int
    file: FileUploadResponse
    import_result: Optional[dict] = None


class FileListResponse(BaseModel):
    """文件列表响应schema。"""
    files: List[FileUploadResponse]
    total: int
    page: int
    page_size: int


# ==================== 导入历史相关 ====================

class ImportHistoryResponse(BaseModel):
    """导入历史响应schema。"""
    id: int
    upload_id: Optional[int]
    file_name: Optional[str] = None  # 来自关联的UserUpload表
    original_file_name: Optional[str] = None  # 来自关联的UserUpload表
    platform: Optional[str] = None  # 来自关联的UserUpload表
    total_records: int
    imported_records: int
    skipped_records: int
    failed_records: int
    status: str
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]

    class Config:
        from_attributes = True


class ImportHistoryListResponse(BaseModel):
    """导入历史列表响应schema。"""
    history: List[ImportHistoryResponse]
    total: int
    page: int
    page_size: int


# ==================== 管理员相关 ====================

class AdminUserCreate(UserCreate):
    """管理员创建用户schema。"""
    is_superuser: bool = False
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    """管理员更新用户schema。"""
    email: Optional[EmailStr] = None
    is_superuser: Optional[bool] = None
    is_active: Optional[bool] = None


class AdminUserListResponse(BaseModel):
    """管理员用户列表响应schema。"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class SystemStatsResponse(BaseModel):
    """系统统计响应schema。"""
    total_users: int
    active_users: int
    total_uploads: int
    total_imports: int
    success_rate: float
    uploads_today: int
    imports_today: int


class AuditLogResponse(BaseModel):
    """审计日志响应schema。"""
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    ip_address: Optional[str]
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """审计日志列表响应schema。"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class SystemSettingsResponse(BaseModel):
    """系统设置响应schema。"""
    registration_enabled: bool = True
    max_file_size: int = 52428800  # 50MB
    allowed_file_types: List[str] = [".csv", ".txt", ".xls", ".xlsx"]
    session_timeout_minutes: int = 15
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30


class SystemSettingsUpdate(BaseModel):
    """系统设置更新schema。"""
    registration_enabled: Optional[bool] = None
    max_file_size: Optional[int] = None
    allowed_file_types: Optional[List[str]] = None
    session_timeout_minutes: Optional[int] = None
    max_login_attempts: Optional[int] = None
    lockout_duration_minutes: Optional[int] = None


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    """通用消息响应schema。"""
    success: bool
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """错误响应schema。"""
    detail: str
    error_code: Optional[str] = None
