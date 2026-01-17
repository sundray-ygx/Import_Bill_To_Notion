"""FastAPI dependency injection for authentication and authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Tuple
from database import get_db
from models import User, UserSession
from auth import verify_access_token, LoginSecurity
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)


# ==================== 认证依赖 ====================

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选）。

    如果没有提供token或token无效，返回None而不是抛出异常。

    Args:
        credentials: HTTP认证凭证
        db: 数据库session

    Returns:
        当前用户对象，未认证返回None
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_access_token(token)

    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户（必需）。

    如果没有提供token或token无效，抛出401异常。

    Args:
        credentials: HTTP认证凭证
        db: 数据库session

    Returns:
        当前用户对象

    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # 检查账户是否被锁定
    is_locked, locked_until = LoginSecurity.check_account_locked(user)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is temporarily locked. Try again after {locked_until}"
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户。

    确保用户账户处于活跃状态。

    Args:
        current_user: 当前用户

    Returns:
        当前活跃用户

    Raises:
        HTTPException: 用户未激活时抛出400错误
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# ==================== 授权依赖 ====================

def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前超级管理员用户。

    确保用户具有超级管理员权限。

    Args:
        current_user: 当前用户

    Returns:
        当前超级管理员用户

    Raises:
        HTTPException: 用户不是超级管理员时抛出403错误
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Superuser access required."
        )
    return current_user


def require_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """要求超级管理员权限的依赖。

    这是get_current_superuser的别名，提供更语义化的名称。

    Args:
        current_user: 当前用户

    Returns:
        当前超级管理员用户
    """
    return get_current_superuser(current_user)


# ==================== 会话验证 ====================

def get_valid_session(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserSession:
    """获取有效的用户会话。

    验证token对应的会话记录是否存在且有效。

    Args:
        current_user: 当前用户
        credentials: HTTP认证凭证
        db: 数据库session

    Returns:
        有效的会话对象

    Raises:
        HTTPException: 会话无效时抛出401错误
    """
    token = credentials.credentials

    session = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.token == token,
        UserSession.is_revoked == False
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or revoked"
        )

    # 检查是否过期
    from auth import SessionManager
    if not SessionManager.is_session_valid(session.expires_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired"
        )

    return session


# ==================== 条件依赖 ====================

def require_multi_tenant():
    """要求多租户模式的依赖。

    检查系统是否处于多租户模式。

    Raises:
        HTTPException: 单用户模式下抛出403错误
    """
    from config import Config

    if Config.is_single_user_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature is only available in multi-tenant mode"
        )


def require_notion_configured(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """要求用户已配置Notion的依赖。

    检查用户是否已完成Notion配置。

    Args:
        current_user: 当前用户
        db: 数据库session

    Returns:
        当前用户

    Raises:
        HTTPException: 未配置Notion时抛出400错误
    """
    from models import UserNotionConfig

    config = db.query(UserNotionConfig).filter(
        UserNotionConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notion configuration required. Please configure your Notion integration first."
        )

    return current_user


# ==================== 可选的认证依赖 ====================

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（异步版本，可选）。

    用于不需要强制认证的端点。

    Args:
        credentials: HTTP认证凭证
        db: 数据库session

    Returns:
        当前用户对象，未认证返回None
    """
    return get_current_user_optional(credentials, db)


# ==================== IP地址和User-Agent ====================

def get_client_ip(request) -> str:
    """获取客户端IP地址。

    Args:
        request: FastAPI请求对象

    Returns:
        客户端IP地址
    """
    # 检查代理头
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # 取第一个IP（客户端IP）
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 回退到直接连接的IP
    if hasattr(request.client, "host"):
        return request.client.host

    return "unknown"


def get_user_agent(request) -> str:
    """获取用户代理字符串。

    Args:
        request: FastAPI请求对象

    Returns:
        User-Agent字符串
    """
    return request.headers.get("User-Agent", "unknown")


# ==================== 分页依赖 ====================

from typing_extensions import Annotated
from fastapi import Query


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20
) -> Tuple[int, int]:
    """获取分页参数。

    Args:
        page: 页码
        page_size: 每页数量

    Returns:
        (page, page_size) 元组
    """
    return page, page_size


def get_search_params(
    search: Annotated[Optional[str], Query(description="搜索关键词")] = None,
) -> Optional[str]:
    """获取搜索参数。

    Args:
        search: 搜索关键词

    Returns:
        搜索关键词或None
    """
    return search


# ==================== 导出常用依赖 ====================

# 为了方便使用，导出常用的依赖
__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    "get_current_superuser",
    "require_superuser",
    "require_multi_tenant",
    "require_notion_configured",
    "get_valid_session",
    "get_client_ip",
    "get_user_agent",
    "get_pagination_params",
    "get_search_params",
]
