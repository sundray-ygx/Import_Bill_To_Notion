"""Authentication routes for user registration, login, logout, etc."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from database import get_db
from models import User, UserSession, AuditLog
from schemas import (
    UserCreate, UserResponse, TokenResponse, RefreshTokenRequest,
    PasswordChangeRequest, MessageResponse
)
from auth import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, verify_refresh_token,
    validate_password_strength, LoginSecurity, SessionManager
)
from dependencies import get_current_user, get_current_active_user, get_client_ip, get_user_agent
from config import Config
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=TokenResponse, tags=["Authentication"])
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """用户注册。

    创建新用户账户。需要检查用户名和邮箱是否已被使用。
    注册成功后自动登录用户并返回 token。
    """
    # 检查是否允许注册
    if not Config.REGISTRATION_ENABLED and Config.is_multi_tenant_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently disabled"
        )

    # 验证密码强度
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # 检查用户名是否存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # 检查邮箱是否存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # 创建用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 注册成功后自动登录：生成 tokens
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})

    # 保存 session
    session = UserSession(
        user_id=new_user.id,
        token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    db.add(session)

    # 更新最后登录时间
    new_user.last_login = datetime.utcnow()

    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=new_user.id,
        action="register",
        request=request,
        details={"username": new_user.username}
    )

    logger.info(f"New user registered: {new_user.username} (ID: {new_user.id})")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": new_user
    }


@router.post("/login", response_model=TokenResponse, tags=["Authentication"])
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录。

    使用 OAuth2 密码流进行用户登录。
    返回 access_token 和 refresh_token。
    """
    # 查找用户
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        # 记录失败的登录尝试（不暴露用户名是否存在）
        _create_audit_log(
            db=db,
            user_id=None,
            action="login_failed",
            request=request,
            details={"username": form_data.username, "reason": "user_not_found"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查账户是否被锁定
    is_locked, locked_until = LoginSecurity.check_account_locked(user)
    if is_locked:
        _create_audit_log(
            db=db,
            user_id=user.id,
            action="login_failed",
            request=request,
            details={"reason": "account_locked", "locked_until": str(locked_until)}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is temporarily locked. Try again after {locked_until}"
        )

    # 验证密码
    if not verify_password(form_data.password, user.password_hash):
        # 记录失败的登录尝试
        LoginSecurity.record_login_attempt(user, False, db)
        _create_audit_log(
            db=db,
            user_id=user.id,
            action="login_failed",
            request=request,
            details={"reason": "invalid_password"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查账户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # 生成 tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # 保存 session
    session = UserSession(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    db.add(session)

    # 更新最后登录时间和重置登录尝试
    user.last_login = datetime.utcnow()
    LoginSecurity.record_login_attempt(user, True, db)

    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=user.id,
        action="login",
        request=request
    )

    logger.info(f"User logged in: {user.username} (ID: {user.id})")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }


@router.post("/logout", response_model=MessageResponse, tags=["Authentication"])
async def logout(
    refresh_token: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """用户登出。

    撤销当前用户的所有 session。
    """
    # 撤销所有 session
    count = SessionManager.revoke_all_user_sessions(current_user.id, db)

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_user.id,
        action="logout",
        request=request,
        details={"revoked_sessions": count}
    )

    logger.info(f"User logged out: {current_user.username} (ID: {current_user.id}), revoked {count} sessions")
    return {
        "success": True,
        "message": "Logged out successfully"
    }


@router.post("/refresh", response_model=TokenResponse, tags=["Authentication"])
async def refresh_token(
    token_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """刷新 access token。

    使用 refresh_token 获取新的 access_token。
    """
    # 验证 refresh token
    payload = verify_refresh_token(token_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = int(payload.get("sub"))

    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # 查找并验证 session
    session = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.refresh_token == token_data.refresh_token,
        UserSession.is_revoked == False
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or revoked"
    )

    # 生成新的 tokens
    new_access_token = create_access_token(data={"sub": str(user_id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user_id)})

    # 更新 session
    session.token = new_access_token
    session.refresh_token = new_refresh_token
    session.expires_at = datetime.utcnow() + timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    db.commit()

    logger.info(f"Token refreshed for user: {user.username} (ID: {user_id})")
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }


@router.get("/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前登录用户的信息。

    返回当前用户的详细信息。
    """
    return current_user


@router.post("/change-password", response_model=MessageResponse, tags=["Authentication"])
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """修改当前用户的密码。

    需要提供当前密码和新密码。
    """
    # 验证当前密码
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # 验证新密码强度
    is_valid, error_msg = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.require_password_change = False
    current_user.updated_at = datetime.utcnow()
    db.commit()

    # 撤销所有现有 session（强制重新登录）
    SessionManager.revoke_all_user_sessions(current_user.id, db)

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_user.id,
        action="password_changed",
        request=request
    )

    logger.info(f"Password changed for user: {current_user.username} (ID: {current_user.id})")
    return {
        "success": True,
        "message": "Password changed successfully. Please login again."
    }


# ==================== 配置向导 ====================

class SetupCheckResponse(BaseModel):
    """配置检查响应。"""
    needs_setup: bool
    user_count: int


class SetupCreateAdminRequest(BaseModel):
    """创建管理员请求。"""
    username: str
    email: EmailStr
    password: str
    settings: Optional[dict] = None


@router.get("/setup/check", response_model=SetupCheckResponse, tags=["Setup"])
async def check_setup_needed(db: Session = Depends(get_db)):
    """检查是否需要进行初始设置。"""
    user_count = db.query(User).count()
    return {
        "needs_setup": user_count == 0,
        "user_count": user_count
    }


@router.post("/setup/check-username", tags=["Setup"])
async def check_username_available(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """检查用户名是否可用。"""
    username = request_data.get("username", "")
    existing = db.query(User).filter(User.username == username).first()
    return {
        "exists": existing is not None
    }


@router.post("/setup/create-admin", tags=["Setup"])
async def create_initial_admin(
    admin_data: SetupCreateAdminRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """创建初始管理员账户。

    只能在没有用户时调用。第一个用户自动成为超级管理员。
    """
    # 检查是否已有用户
    user_count = db.query(User).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统已初始化，无法使用此接口"
        )

    # 创建超级管理员
    admin_user = User(
        username=admin_data.username,
        email=admin_data.email,
        password_hash=get_password_hash(admin_data.password),
        is_superuser=True,
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    # 保存系统设置
    if admin_data.settings:
        from models import SystemSettings
        for key, value in admin_data.settings.items():
            setting = SystemSettings(
                setting_key=key,
                setting_value=str(value),
                updated_by=admin_user.id
            )
            db.add(setting)
        db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=admin_user.id,
        action="system_initialized",
        request=request,
        details={
            "admin_username": admin_user.username,
            "settings": admin_data.settings
        }
    )

    logger.info(f"System initialized by admin: {admin_user.username}")
    return {
        "success": True,
        "message": "Admin user created successfully",
        "username": admin_user.username
    }


# ==================== 辅助函数 ====================

def _create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    request: Request,
    details: dict = None
):
    """创建审计日志记录。

    Args:
        db: 数据库 session
        user_id: 用户 ID
        action: 操作类型
        request: FastAPI 请求对象
        details: 详细信息（字典）
    """
    try:
        import json
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details=json.dumps(details) if details else None
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        # 审计日志失败不应影响主流程
        logger.error(f"Failed to create audit log: {e}")
