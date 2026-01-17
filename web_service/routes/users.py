"""User management routes for profile and Notion configuration."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User, UserNotionConfig, UserUpload, ImportHistory
from schemas import (
    UserUpdate, UserProfileResponse, NotionConfigCreate, NotionConfigUpdate,
    NotionConfigResponse, MessageResponse
)
from auth import get_password_hash, verify_password, validate_password_strength
from dependencies import get_current_active_user, require_multi_tenant
from notion_api import NotionClient
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== 用户资料 ====================

@router.get("/profile", response_model=UserProfileResponse, tags=["User"])
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的详细资料。

    包含用户信息和统计数据。
    """
    # 检查是否配置了Notion
    notion_config = db.query(UserNotionConfig).filter(
        UserNotionConfig.user_id == current_user.id
    ).first()

    # 统计数据
    total_uploads = db.query(UserUpload).filter(
        UserUpload.user_id == current_user.id
    ).count()

    total_imports = db.query(ImportHistory).filter(
        ImportHistory.user_id == current_user.id
    ).count()

    # 构建响应
    response_dict = {
        **current_user.__dict__,
        "total_uploads": total_uploads,
        "total_imports": total_imports,
        "notion_configured": notion_config is not None
    }

    return UserProfileResponse(**response_dict)


@router.put("/profile", response_model=MessageResponse, tags=["User"])
async def update_user_profile(
    profile_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户的资料。

    可以更新邮箱等信息。
    """
    # 如果要更新邮箱，检查是否已被使用
    if profile_update.email and profile_update.email != current_user.email:
        existing = db.query(User).filter(User.email == profile_update.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        current_user.email = profile_update.email

    current_user.updated_at = datetime.utcnow()
    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_user.id,
        action="profile_updated",
        request=request,
        details={"updated_fields": ["email"] if profile_update.email else []}
    )

    logger.info(f"User profile updated: {current_user.username} (ID: {current_user.id})")
    return {
        "success": True,
        "message": "Profile updated successfully"
    }


# ==================== Notion配置 ====================

@router.get("/notion-config", tags=["User"])
async def get_notion_config(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的Notion配置。

    返回用户配置的Notion API密钥和数据库ID（敏感信息会脱敏）。
    如果未配置，返回 is_configured: false。
    """
    require_multi_tenant()

    config = db.query(UserNotionConfig).filter(
        UserNotionConfig.user_id == current_user.id
    ).first()

    if not config:
        return {
            "is_configured": False,
            "notion_api_key": None,
            "notion_income_database_id": None,
            "notion_expense_database_id": None,
            "config_name": None,
            "is_verified": False
        }

    # 返回配置（API密钥脱敏）
    return {
        "is_configured": True,
        "id": config.id,
        "user_id": config.user_id,
        "config_name": config.config_name,
        "notion_api_key": _mask_api_key(config.notion_api_key),
        "notion_income_database_id": config.notion_income_database_id,
        "notion_expense_database_id": config.notion_expense_database_id,
        "is_verified": config.is_verified,
        "last_verified_at": config.last_verified_at,
        "created_at": config.created_at,
        "updated_at": config.updated_at
    }


@router.post("/notion-config", response_model=NotionConfigResponse, tags=["User"])
async def create_or_update_notion_config(
    config_data: NotionConfigCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建或更新当前用户的Notion配置。

    配置Notion API密钥和数据库ID。
    """
    require_multi_tenant()

    # 检查是否已有配置
    existing_config = db.query(UserNotionConfig).filter(
        UserNotionConfig.user_id == current_user.id
    ).first()

    if existing_config:
        # 更新现有配置
        existing_config.notion_api_key = config_data.notion_api_key
        existing_config.notion_income_database_id = config_data.notion_income_database_id
        existing_config.notion_expense_database_id = config_data.notion_expense_database_id
        existing_config.config_name = config_data.config_name
        existing_config.is_verified = False  # 需要重新验证
        existing_config.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing_config)

        # 记录审计日志
        _create_audit_log(
            db=db,
            user_id=current_user.id,
            action="notion_config_updated",
            request=request
        )

        logger.info(f"Notion config updated for user: {current_user.username} (ID: {current_user.id})")
        return existing_config
    else:
        # 创建新配置
        new_config = UserNotionConfig(
            user_id=current_user.id,
            notion_api_key=config_data.notion_api_key,
            notion_income_database_id=config_data.notion_income_database_id,
            notion_expense_database_id=config_data.notion_expense_database_id,
            config_name=config_data.config_name
        )
        db.add(new_config)
        db.commit()
        db.refresh(new_config)

        # 记录审计日志
        _create_audit_log(
            db=db,
            user_id=current_user.id,
            action="notion_config_created",
            request=request
        )

        logger.info(f"Notion config created for user: {current_user.username} (ID: {current_user.id})")
        return new_config


@router.post("/notion-config/verify", response_model=MessageResponse, tags=["User"])
async def verify_notion_config(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """验证当前用户的Notion配置。

    尝试连接到Notion API并验证配置是否正确。
    """
    require_multi_tenant()

    config = db.query(UserNotionConfig).filter(
        UserNotionConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notion configuration not found"
        )

    try:
        # 创建Notion客户端并验证连接
        client = NotionClient(user_id=current_user.id)
        is_valid = client.verify_connection()

        if is_valid:
            config.is_verified = True
            config.last_verified_at = datetime.utcnow()
            db.commit()

            # 记录审计日志
            _create_audit_log(
                db=db,
                user_id=current_user.id,
                action="notion_config_verified",
                request=request
            )

            logger.info(f"Notion config verified for user: {current_user.username} (ID: {current_user.id})")
            return {
                "success": True,
                "message": "Notion configuration verified successfully"
            }
        else:
            return {
                "success": False,
                "message": "Notion configuration verification failed. Please check your API key and database IDs."
            }
    except Exception as e:
        logger.error(f"Notion verification error for user {current_user.id}: {e}")
        return {
            "success": False,
            "message": f"Verification failed: {str(e)}"
        }


@router.delete("/notion-config", response_model=MessageResponse, tags=["User"])
async def delete_notion_config(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除当前用户的Notion配置。

    删除后将无法导入账单到Notion。
    """
    require_multi_tenant()

    config = db.query(UserNotionConfig).filter(
        UserNotionConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notion configuration not found"
        )

    db.delete(config)
    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_user.id,
        action="notion_config_deleted",
        request=request
    )

    logger.info(f"Notion config deleted for user: {current_user.username} (ID: {current_user.id})")
    return {
        "success": True,
        "message": "Notion configuration deleted successfully"
    }


# ==================== 辅助函数 ====================

from datetime import datetime
from models import AuditLog
from dependencies import get_client_ip, get_user_agent


def _mask_api_key(api_key: str) -> str:
    """脱敏 API 密钥，只显示前4个和后4个字符。

    Args:
        api_key: 原始 API 密钥

    Returns:
        脱敏后的 API 密钥
    """
    if not api_key or len(api_key) <= 8:
        return "****"
    return api_key[:4] + "****" + api_key[-4:]


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
