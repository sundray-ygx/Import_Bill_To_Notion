"""User management routes for profile and Notion configuration."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from database import get_db
from models import User, UserNotionConfig, UserUpload, ImportHistory
from schemas import (
    UserUpdate, UserProfileResponse, NotionConfigCreate, NotionConfigUpdate,
    NotionConfigResponse, MessageResponse,
    NotionVerifyStepResponse, NotionVerifyProgressResponse
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
    注意：如果更新时 notion_api_key 为空，将保留原有的API密钥。
    """
    require_multi_tenant()

    # 检查是否已有配置
    existing_config = db.query(UserNotionConfig).filter(
        UserNotionConfig.user_id == current_user.id
    ).first()

    if existing_config:
        # 更新现有配置
        # 如果提供了新的API密钥则更新，否则保留原有密钥
        if config_data.notion_api_key:
            existing_config.notion_api_key = config_data.notion_api_key
            api_key_changed = True
        else:
            api_key_changed = False

        existing_config.notion_income_database_id = config_data.notion_income_database_id
        existing_config.notion_expense_database_id = config_data.notion_expense_database_id
        existing_config.config_name = config_data.config_name

        # 只有API密钥变化时才需要重新验证
        if api_key_changed:
            existing_config.is_verified = False

        existing_config.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing_config)

        # 记录审计日志
        _create_audit_log(
            db=db,
            user_id=current_user.id,
            action="notion_config_updated",
            request=request,
            details={"api_key_changed": api_key_changed}
        )

        logger.info(f"Notion config updated for user: {current_user.username} (ID: {current_user.id}), api_key_changed={api_key_changed}")
        return existing_config
    else:
        # 创建新配置时，API密钥是必需的
        if not config_data.notion_api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key is required for new configuration"
            )

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


@router.get("/notion-config/verify-step", response_model=NotionVerifyProgressResponse, tags=["User"])
async def verify_notion_config_step(
    step: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """分步验证Notion配置。

    支持的步骤:
    - api_key: 验证API密钥
    - income_db: 验证收入数据库
    - expense_db: 验证支出数据库

    返回当前步骤和所有步骤的状态。
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

    # 初始化步骤状态
    steps = [
        NotionVerifyStepResponse(step="api_key", status="pending", message="验证API密钥"),
        NotionVerifyStepResponse(step="income_db", status="pending", message="验证收入数据库"),
        NotionVerifyStepResponse(step="expense_db", status="pending", message="验证支出数据库")
    ]

    current_step_index = {"api_key": 0, "income_db": 1, "expense_db": 2}.get(step, 0)

    try:
        client = NotionClient(user_id=current_user.id)
        all_success = True

        # 执行请求的步骤
        if step == "api_key":
            steps[0].status = "in_progress"
            steps[0].message = "正在验证API密钥..."

            try:
                user_info = client.client.users.me()
                user_name = user_info.get('name', 'unknown')
                steps[0].status = "success"
                steps[0].message = f"API密钥验证成功 (用户: {user_name})"
                steps[0].details = {"user_name": user_name}
            except Exception as e:
                steps[0].status = "error"
                steps[0].message = "API密钥验证失败"
                steps[0].error = str(e)
                all_success = False

        elif step == "income_db":
            # 前面的步骤标记为成功（假设已验证）
            steps[0].status = "success"
            steps[0].message = "API密钥已验证"

            steps[1].status = "in_progress"
            steps[1].message = "正在验证收入数据库..."

            try:
                income_db_info = client.client.databases.retrieve(database_id=client.income_db)
                db_title = income_db_info.get('title', [{}])[0].get('text', {}).get('content', 'unknown')
                steps[1].status = "success"
                steps[1].message = f"收入数据库验证成功"
                steps[1].details = {"db_title": db_title, "db_id": client.income_db[:8] + "***"}
            except Exception as e:
                steps[1].status = "error"
                steps[1].message = "收入数据库验证失败"
                steps[1].error = str(e)
                all_success = False

        elif step == "expense_db":
            # 前面的步骤标记为成功
            steps[0].status = "success"
            steps[0].message = "API密钥已验证"
            steps[1].status = "success"
            steps[1].message = "收入数据库已验证"

            steps[2].status = "in_progress"
            steps[2].message = "正在验证支出数据库..."

            try:
                expense_db_info = client.client.databases.retrieve(database_id=client.expense_db)
                db_title = expense_db_info.get('title', [{}])[0].get('text', {}).get('content', 'unknown')
                steps[2].status = "success"
                steps[2].message = f"支出数据库验证成功"
                steps[2].details = {"db_title": db_title, "db_id": client.expense_db[:8] + "***"}

                # 如果全部成功，更新配置状态
                if all_success:
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

                    logger.info(f"Notion config fully verified for user: {current_user.username} (ID: {current_user.id})")

            except Exception as e:
                steps[2].status = "error"
                steps[2].message = "支出数据库验证失败"
                steps[2].error = str(e)
                all_success = False

        return NotionVerifyProgressResponse(
            current_step=current_step_index + 1,
            total_steps=3,
            steps=steps,
            is_complete=(step == "expense_db"),
            all_success=all_success
        )

    except Exception as e:
        logger.error(f"Notion step verification error for user {current_user.id}, step {step}: {e}")
        # 标记当前步骤为错误
        steps[current_step_index].status = "error"
        steps[current_step_index].message = f"验证出错"
        steps[current_step_index].error = str(e)

        return NotionVerifyProgressResponse(
            current_step=current_step_index + 1,
            total_steps=3,
            steps=steps,
            is_complete=False,
            all_success=False
        )


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


# ==================== 用户注销 ====================

class AccountDeletionRequest(BaseModel):
    """用户注销请求模型"""
    password: str


@router.post("/delete-account", response_model=MessageResponse, tags=["User"])
async def delete_account(
    request_data: AccountDeletionRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """注销用户账户并删除所有相关数据。

    需要验证当前密码。超级管理员账户无法注销。

    删除内容包括：
    - 用户基本信息（User表）
    - 上传的账单文件（UserUpload表 + 物理文件）
    - 导入历史记录（ImportHistory表）
    - Notion配置（UserNotionConfig表）
    - 会话信息（UserSession表）
    - 审计日志（AuditLog表）
    """
    # 超级管理员不允许注销
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser accounts cannot be deleted"
        )

    # 验证密码
    if not verify_password(request_data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    try:
        user_id = current_user.id
        username = current_user.username

        # 1. 删除物理文件（上传的账单文件）
        from web_service.services.user_file_service import UserFileService
        file_service = UserFileService()

        uploads = db.query(UserUpload).filter(UserUpload.user_id == user_id).all()
        for upload in uploads:
            try:
                file_service.delete_file(user_id, upload.id, upload.file_name)
            except Exception as e:
                logger.warning(f"Failed to delete file {upload.file_name}: {e}")

        # 2. 删除上传记录（UserUpload表）
        db.query(UserUpload).filter(UserUpload.user_id == user_id).delete()

        # 3. 删除导入历史（ImportHistory表）
        db.query(ImportHistory).filter(ImportHistory.user_id == user_id).delete()

        # 4. 删除Notion配置（UserNotionConfig表）
        db.query(UserNotionConfig).filter(UserNotionConfig.user_id == user_id).delete()

        # 5. 删除会话信息（UserSession表）
        from models import UserSession
        db.query(UserSession).filter(UserSession.user_id == user_id).delete()

        # 6. 删除审计日志（AuditLog表）
        db.query(AuditLog).filter(AuditLog.user_id == user_id).delete()

        # 7. 最后删除用户记录（User表）
        db.delete(current_user)
        db.commit()

        logger.info(f"User account deleted: {username} (ID: {user_id})")
        return {
            "success": True,
            "message": "Account deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete user account {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


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
