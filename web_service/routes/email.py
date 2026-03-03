"""Email configuration routes.

This module provides API endpoints for managing email configurations,
including CRUD operations, connection verification, and manual email checking.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.services.database import get_db
from src.services.dependencies import get_current_user
from src.models import User, EmailConfig, ProcessedEmail
from src.schemas import (
    EmailConfigCreate,
    EmailConfigUpdate,
    EmailConfigResponse,
    EmailConfigListResponse,
    EmailConfigVerifyRequest,
    EmailConfigVerifyResponse,
    EmailCheckRequest,
    EmailCheckResponse,
    ProcessedEmailListResponse,
    EmailProviderTemplate,
    EmailProvidersResponse,
    MessageResponse
)
from src.services.email_service import EmailService
from src.services.email_import_source import EmailImportSource
from src.utils.crypto import PasswordEncryption
from src.scheduler import BillScheduler


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])

# Email provider templates
EMAIL_PROVIDERS: List[EmailProviderTemplate] = [
    {
        "provider": "gmail",
        "name": "Gmail",
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "use_ssl": True,
        "description": "Gmail需要使用应用专用密码，请前往Google账户设置生成"
    },
    {
        "provider": "qq",
        "name": "QQ邮箱",
        "imap_server": "imap.qq.com",
        "imap_port": 993,
        "use_ssl": True,
        "description": "QQ邮箱需要开启IMAP服务并使用授权码"
    },
    {
        "provider": "163",
        "name": "163邮箱",
        "imap_server": "imap.163.com",
        "imap_port": 993,
        "use_ssl": True,
        "description": "163邮箱需要开启IMAP服务并使用授权码"
    },
    {
        "provider": "outlook",
        "name": "Outlook",
        "imap_server": "outlook.office365.com",
        "imap_port": 993,
        "use_ssl": True,
        "description": "Outlook/Hotmail邮箱"
    },
    {
        "provider": "custom",
        "name": "自定义",
        "imap_server": "",
        "imap_port": 993,
        "use_ssl": True,
        "description": "手动配置IMAP服务器"
    }
]


@router.post("/config", response_model=EmailConfigResponse)
async def create_email_config(
    config_data: EmailConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建邮箱配置。"""
    # Check if email address already exists for this user
    existing = db.query(EmailConfig).filter(
        EmailConfig.user_id == current_user.id,
        EmailConfig.email_address == config_data.email_address
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱地址已存在配置"
        )

    # Encrypt password with enhanced error handling
    try:
        crypto = PasswordEncryption()
        password_encrypted = crypto.encrypt(config_data.password)
        logger.info(f"Password encrypted successfully for user {current_user.id}")
    except ValueError as e:
        logger.error(f"Password encryption failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码加密失败：{str(e)}。请检查服务器配置。"
        )
    except Exception as e:
        logger.error(f"Unexpected error during password encryption for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码加密过程中发生未知错误"
        )

    # Create config
    config = EmailConfig(
        user_id=current_user.id,
        email_address=config_data.email_address,
        password_encrypted=password_encrypted,
        imap_server=config_data.imap_server,
        imap_port=config_data.imap_port,
        use_ssl=config_data.use_ssl,
        provider=config_data.provider,
        config_name=config_data.config_name,
        check_frequency=config_data.check_frequency,
        is_active=True,
        is_verified=False
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    logger.info(f"User {current_user.id} created email config {config.id}")

    return config


@router.get("/configs", response_model=EmailConfigListResponse)
async def get_email_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的邮箱配置列表。"""
    configs = db.query(EmailConfig).filter(
        EmailConfig.user_id == current_user.id
    ).order_by(EmailConfig.created_at.desc()).all()

    total = len(configs)

    return EmailConfigListResponse(configs=configs, total=total)


@router.get("/config/{config_id}", response_model=EmailConfigResponse)
async def get_email_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定邮箱配置。"""
    config = db.query(EmailConfig).filter(
        EmailConfig.id == config_id,
        EmailConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮箱配置不存在"
        )

    return config


@router.put("/config/{config_id}", response_model=EmailConfigResponse)
async def update_email_config(
    config_id: int,
    config_data: EmailConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新邮箱配置。"""
    config = db.query(EmailConfig).filter(
        EmailConfig.id == config_id,
        EmailConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮箱配置不存在"
        )

    # Update fields
    update_data = config_data.model_dump(exclude_unset=True)

    # Encrypt new password if provided
    if 'password' in update_data and update_data['password']:
        try:
            crypto = PasswordEncryption()
            update_data['password_encrypted'] = crypto.encrypt(update_data['password'])
            logger.info(f"Password re-encrypted successfully for config {config_id}")
            del update_data['password']
        except ValueError as e:
            logger.error(f"Password encryption failed for config {config_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"密码加密失败：{str(e)}。请检查服务器配置。"
            )
        except Exception as e:
            logger.error(f"Unexpected error during password encryption for config {config_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码加密过程中发生未知错误"
            )

    # If critical fields changed, mark as unverified
    critical_fields = ['email_address', 'password_encrypted', 'imap_server', 'imap_port', 'use_ssl']
    if any(field in update_data for field in critical_fields):
        update_data['is_verified'] = False
        update_data['last_check_status'] = None

    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    logger.info(f"User {current_user.id} updated email config {config_id}")

    return config


@router.delete("/config/{config_id}", response_model=MessageResponse)
async def delete_email_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除邮箱配置。"""
    config = db.query(EmailConfig).filter(
        EmailConfig.id == config_id,
        EmailConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮箱配置不存在"
        )

    config_name = config.config_name
    db.delete(config)
    db.commit()

    # Remove scheduler job if exists
    try:
        scheduler = BillScheduler()
        scheduler.remove_email_check_job(config_id)
    except Exception as e:
        logger.warning(f"Failed to remove scheduler job for config {config_id}: {e}")

    logger.info(f"User {current_user.id} deleted email config {config_id}")

    return MessageResponse(
        success=True,
        message=f"邮箱配置 '{config_name}' 已删除"
    )


@router.post("/config/{config_id}/verify", response_model=EmailConfigVerifyResponse)
async def verify_email_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """验证邮箱配置连接。"""
    config = db.query(EmailConfig).filter(
        EmailConfig.id == config_id,
        EmailConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮箱配置不存在"
        )

    # Verify connection
    email_service = EmailService()
    is_valid = email_service.verify_connection(config)

    if is_valid:
        config.is_verified = True
        config.last_check_status = 'success'
        config.last_check_at = datetime.utcnow()
        db.commit()

        return EmailConfigVerifyResponse(
            success=True,
            message="邮箱连接验证成功"
        )
    else:
        config.is_verified = False
        config.last_check_status = 'failed'
        config.last_check_at = datetime.utcnow()
        db.commit()

        return EmailConfigVerifyResponse(
            success=False,
            message="邮箱连接验证失败，请检查配置信息"
        )


@router.post("/check", response_model=EmailCheckResponse)
async def check_email_now(
    request: EmailCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动触发邮箱检查。"""
    try:
        # Create email import source
        source = EmailImportSource(
            user_id=current_user.id,
            db=db,
            config_id=request.config_id
        )

        # Import bills
        result = source.import_bills()

        return EmailCheckResponse(
            success=True,
            message=f"邮箱检查完成，共处理 {result['total']} 个账单",
            checked_configs=1 if request.config_id else 0,
            total_imported=result['imported'],
            total_failed=result['failed'],
            details=[]
        )

    except Exception as e:
        logger.error(f"Manual email check failed for user {current_user.id}: {e}")
        return EmailCheckResponse(
            success=False,
            message=f"邮箱检查失败: {str(e)}",
            checked_configs=0,
            total_imported=0,
            total_failed=0
        )


@router.get("/providers", response_model=EmailProvidersResponse)
async def get_email_providers():
    """获取支持的邮箱服务商模板。"""
    return EmailProvidersResponse(providers=EMAIL_PROVIDERS)


@router.get("/processed", response_model=ProcessedEmailListResponse)
async def get_processed_emails(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取已处理邮件历史。"""
    offset = (page - 1) * page_size

    # Get total count
    total = db.query(ProcessedEmail).filter(
        ProcessedEmail.user_id == current_user.id
    ).count()

    # Get paginated results
    emails = db.query(ProcessedEmail).filter(
        ProcessedEmail.user_id == current_user.id
    ).order_by(ProcessedEmail.processed_at.desc()).offset(offset).limit(page_size).all()

    return ProcessedEmailListResponse(
        emails=emails,
        total=total,
        page=page,
        page_size=page_size
    )
