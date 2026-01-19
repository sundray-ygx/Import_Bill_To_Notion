"""Admin routes for user management, system settings, and audit logs."""

import os
import re
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from database import get_db
from models import User, UserUpload, ImportHistory, AuditLog
from schemas import (
    AdminUserCreate, AdminUserUpdate, AdminUserListResponse, UserResponse,
    SystemStatsResponse, AuditLogResponse, AuditLogListResponse,
    SystemSettingsResponse, SystemSettingsUpdate, MessageResponse
)
from auth import get_password_hash
from dependencies import get_current_superuser, get_client_ip, get_user_agent
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

# 日志配置
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOG_LINES = 5000  # 最大保留行数
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "web_service.log")


# ==================== 用户管理 ====================

@router.get("/users", response_model=AdminUserListResponse, tags=["Admin"])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_superuser: Optional[bool] = None,
    current_admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（超级管理员）。"""
    # 构建查询
    query = db.query(User)

    if search:
        query = query.filter(
            or_(
                User.username.contains(search),
                User.email.contains(search)
            )
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if is_superuser is not None:
        query = query.filter(User.is_superuser == is_superuser)

    # 计算总数
    total = query.count()

    # 分页
    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/users", response_model=dict, tags=["Admin"])
async def create_user(
    user_data: AdminUserCreate,
    request: Request,
    current_admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """创建新用户（超级管理员）。"""
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
        is_superuser=user_data.is_superuser,
        is_active=user_data.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_admin.id,
        action="user_created",
        request=request,
        details={
            "target_user_id": new_user.id,
            "username": new_user.username,
            "is_superuser": new_user.is_superuser
        }
    )

    logger.info(f"User created by admin {current_admin.username}: {new_user.username}")
    return {
        "success": True,
        "message": "User created successfully",
        "user": UserResponse.model_validate(new_user)
    }


@router.put("/users/{user_id}", response_model=MessageResponse, tags=["Admin"])
async def update_user(
    user_id: int,
    user_data: AdminUserUpdate,
    request: Request,
    current_admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """更新用户信息（超级管理员）。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 检查是否要移除超级管理员权限
    if user_data.is_superuser is not None and user_data.is_superuser == False:
        if user.is_superuser:
            # 检查是否是最后一个超级管理员
            superuser_count = db.query(User).filter(User.is_superuser == True).count()
            if superuser_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove superuser role from the last superuser"
                )

    # 更新字段
    if user_data.email is not None:
        # 检查邮箱是否被其他用户使用
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        user.email = user_data.email

    if user_data.is_superuser is not None:
        user.is_superuser = user_data.is_superuser

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    user.updated_at = datetime.utcnow()
    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_admin.id,
        action="user_updated",
        request=request,
        details={
            "target_user_id": user.id,
            "changes": {k: v for k, v in user_data.dict(exclude_unset=True).items() if v is not None}
        }
    )

    logger.info(f"User updated by admin {current_admin.username}: user_id={user_id}")
    return {
        "success": True,
        "message": "User updated successfully"
    }


@router.delete("/users/{user_id}", response_model=MessageResponse, tags=["Admin"])
async def delete_user(
    user_id: int,
    request: Request,
    current_admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """删除用户（超级管理员）。"""
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    username = user.username
    db.delete(user)
    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_admin.id,
        action="user_deleted",
        request=request,
        details={
            "target_user_id": user_id,
            "username": username
        }
    )

    logger.info(f"User deleted by admin {current_admin.username}: {username} (ID: {user_id})")
    return {
        "success": True,
        "message": "User deleted successfully"
    }


@router.post("/users/{user_id}/reset-password", response_model=MessageResponse, tags=["Admin"])
async def reset_user_password(
    user_id: int,
    new_password: str = ...,
    request: Request = None,
    current_admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """重置用户密码（超级管理员）。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 更新密码
    user.password_hash = get_password_hash(new_password)
    user.require_password_change = True
    user.updated_at = datetime.utcnow()
    db.commit()

    # 撤销用户所有会话
    from auth import SessionManager
    SessionManager.revoke_all_user_sessions(user_id, db)

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_admin.id,
        action="password_reset",
        request=request,
        details={
            "target_user_id": user_id,
            "username": user.username
        }
    )

    logger.info(f"Password reset by admin {current_admin.username} for user: {user.username}")
    return {
        "success": True,
        "message": "Password reset successfully"
    }


@router.get("/users/{user_id}", tags=["Admin"])
async def get_user_detail(
    user_id: int,
    current_admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """获取用户详细信息。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 获取用户统计
    total_uploads = db.query(UserUpload).filter(UserUpload.user_id == user_id).count()
    total_imports = db.query(ImportHistory).filter(ImportHistory.user_id == user_id).count()

    # 获取Notion配置状态
    notion_configured = False
    from models import UserNotionConfig
    notion_config = db.query(UserNotionConfig).filter(UserNotionConfig.user_id == user_id).first()
    if notion_config:
        notion_configured = True

    return {
        "user": user,
        "stats": {
            "total_uploads": total_uploads,
            "total_imports": total_imports
        },
        "notion_configured": notion_configured
    }


# ==================== 系统统计 ====================

@router.get("/stats", response_model=SystemStatsResponse, tags=["Admin"])
async def get_system_stats(
    current_admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """获取系统统计信息（超级管理员）。"""
    # 用户统计
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()

    # 上传统计
    total_uploads = db.query(UserUpload).count()

    # 导入统计
    total_imports = db.query(ImportHistory).count()

    # 成功率计算
    successful_imports = db.query(ImportHistory).filter(ImportHistory.status == 'success').count()
    success_rate = (successful_imports / total_imports * 100) if total_imports > 0 else 0

    # 今日统计
    today = datetime.now().date()
    uploads_today = db.query(UserUpload).filter(
        func.date(UserUpload.created_at) == today
    ).count()

    imports_today = db.query(ImportHistory).filter(
        func.date(ImportHistory.started_at) == today
    ).count()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_uploads": total_uploads,
        "total_imports": total_imports,
        "success_rate": round(success_rate, 1),
        "uploads_today": uploads_today,
        "imports_today": imports_today
    }


# ==================== 审计日志 ====================

@router.get("/audit-logs", response_model=AuditLogListResponse, tags=["Admin"])
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    current_admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """获取审计日志（超级管理员）。"""
    # 构建查询
    query = db.query(AuditLog)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if action:
        query = query.filter(AuditLog.action.contains(action))

    # 计算总数
    total = query.count()

    # 分页并关联用户信息
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # 构建响应
    log_responses = []
    for log in logs:
        username = None
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            if user:
                username = user.username

        log_responses.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": username,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "details": log.details,
            "created_at": log.created_at
        })

    return {
        "logs": log_responses,
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ==================== 系统设置 ====================

@router.get("/settings", response_model=SystemSettingsResponse, tags=["Admin"])
async def get_system_settings(
    current_admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """获取系统设置（超级管理员）。"""
    from models import SystemSettings

    settings = {
        "registration_enabled": True,
        "max_file_size": 52428800,
        "allowed_file_types": [".csv", ".txt", ".xls", ".xlsx"],
        "session_timeout_minutes": 15,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 30
    }

    # 从数据库加载设置
    db_settings = db.query(SystemSettings).all()
    for setting in db_settings:
        if setting.setting_key in settings:
            value = setting.setting_value

            # 转换类型
            if isinstance(settings[setting.setting_key], bool):
                value = value.lower() == 'true'
            elif isinstance(settings[setting.setting_key], int):
                value = int(value)
            elif isinstance(settings[setting.setting_key], list):
                value = value.split(',')

            settings[setting.setting_key] = value

    return SystemSettingsResponse(**settings)


@router.put("/settings", response_model=MessageResponse, tags=["Admin"])
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    request: Request,
    current_admin: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """更新系统设置（超级管理员）。"""
    from models import SystemSettings

    # 更新设置
    for key, value in settings_update.dict(exclude_unset=True).items():
        if value is not None:
            setting = db.query(SystemSettings).filter(SystemSettings.setting_key == key).first()

            # 转换为字符串存储
            str_value = str(value)
            if isinstance(value, list):
                str_value = ','.join(value)

            if setting:
                setting.setting_value = str_value
                setting.updated_by = current_admin.id
                setting.updated_at = datetime.utcnow()
            else:
                new_setting = SystemSettings(
                    setting_key=key,
                    setting_value=str_value,
                    updated_by=current_admin.id
                )
                db.add(new_setting)

    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_admin.id,
        action="settings_updated",
        request=request,
        details={k: v for k, v in settings_update.dict(exclude_unset=True).items() if v is not None}
    )

    logger.info(f"Settings updated by admin {current_admin.username}")
    return {
        "success": True,
        "message": "Settings updated successfully"
    }


# ==================== 日志管理 ====================

class LogEntry(BaseModel):
    """日志条目模型"""
    timestamp: str
    level: str
    logger: str
    location: str
    message: str
    details: Optional[str] = None


def _parse_log_line(line: str) -> Optional[dict]:
    """解析日志行。

    实际日志格式: 2025-12-29 23:10:33,996 - module_name - LEVEL - message
    或: 2025-01-19 15:30:45 - module_name - filename.py:123 - LEVEL - message
    """
    # 首先尝试带文件位置的新格式
    pattern_with_location = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d+)?) - ([\w.]+) - ([\w./]+):(\d+) - (\w+) - (.+)$'
    match = re.match(pattern_with_location, line.strip())
    if match:
        return {
            "timestamp": match.group(1).split(',')[0],  # 移除毫秒部分
            "logger": match.group(2),
            "location": f"{match.group(3)}:{match.group(4)}",
            "level": match.group(5),
            "message": match.group(6)
        }

    # 尝试不带文件位置的简化格式
    pattern_simple = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d+)?) - ([\w.]+) - (\w+) - (.+)$'
    match = re.match(pattern_simple, line.strip())
    if match:
        return {
            "timestamp": match.group(1).split(',')[0],  # 移除毫秒部分
            "logger": match.group(2),
            "location": "",
            "level": match.group(3),
            "message": match.group(4)
        }

    return None


def _read_log_file(
    limit: int = 500,
    level: Optional[str] = None,
    search: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> List[dict]:
    """读取日志文件并解析。

    Args:
        limit: 返回的最大日志条数
        level: 日志级别筛选 (INFO, ERROR, WARNING, DEBUG)
        search: 搜索关键词
        start_time: 开始时间 (YYYY-MM-DD HH:MM:SS)
        end_time: 结束时间 (YYYY-MM-DD HH:MM:SS)

    Returns:
        日志条目列表
    """
    if not os.path.exists(LOG_FILE_PATH):
        return []

    logs = []
    lines = []

    # 尝试多种编码读取日志文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    for encoding in encodings:
        try:
            with open(LOG_FILE_PATH, 'r', encoding=encoding) as f:
                lines = f.readlines()
            break  # 成功读取，退出循环
        except UnicodeDecodeError:
            continue

    # 如果所有编码都失败，使用 errors='replace' 作为最后手段
    if not lines:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

    try:

        # 从文件末尾开始读取（最新的日志在前）
        for line in reversed(lines[-MAX_LOG_LINES:]):
            parsed = _parse_log_line(line)
            if parsed:
                # 级别筛选
                if level and parsed["level"] != level.upper():
                    continue

                # 搜索筛选
                if search and search.lower() not in parsed["message"].lower():
                    continue

                # 时间范围筛选
                if start_time and parsed["timestamp"] < start_time:
                    continue
                if end_time and parsed["timestamp"] > end_time:
                    continue

                logs.append(parsed)
                if len(logs) >= limit:
                    break

    except Exception as e:
        logger.error(f"Failed to read log file: {e}")

    return logs


def _rotate_log_file():
    """日志文件轮转：当文件过大时清理老日志。"""
    if not os.path.exists(LOG_FILE_PATH):
        return

    try:
        file_size = os.path.getsize(LOG_FILE_PATH)
        if file_size > MAX_LOG_FILE_SIZE:
            # 尝试多种编码读取日志文件
            lines = []
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            for encoding in encodings:
                try:
                    with open(LOG_FILE_PATH, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    break  # 成功读取，退出循环
                except UnicodeDecodeError:
                    continue

            # 如果所有编码都失败，使用 errors='replace' 作为最后手段
            if not lines:
                with open(LOG_FILE_PATH, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()

            # 保留最后N行
            keep_lines = lines[-MAX_LOG_LINES:] if len(lines) > MAX_LOG_LINES else lines

            # 写回文件
            with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                f.writelines(keep_lines)

            logger.info(f"Log file rotated: kept {len(keep_lines)} lines")
    except Exception as e:
        logger.error(f"Failed to rotate log file: {e}")


@router.get("/logs", tags=["Admin"])
async def get_logs(
    limit: int = Query(500, ge=1, le=2000),
    level: Optional[str] = Query(None, regex="^(INFO|ERROR|WARNING|DEBUG|all)$"),
    search: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_superuser)
):
    """获取系统日志（超级管理员）。

    支持按级别、关键词和时间范围筛选。
    """
    # 自动轮转日志（如果文件过大）
    _rotate_log_file()

    # 处理级别筛选
    filter_level = None if level == "all" else level

    logs = _read_log_file(
        limit=limit,
        level=filter_level,
        search=search,
        start_time=start_time,
        end_time=end_time
    )

    return {
        "logs": logs,
        "total": len(logs),
        "log_file": LOG_FILE_PATH
    }


@router.delete("/logs", tags=["Admin"])
async def clear_logs(
    request: Request,
    current_admin: User = Depends(get_current_superuser)
):
    """清空日志文件（超级管理员）。"""
    try:
        if os.path.exists(LOG_FILE_PATH):
            # 清空文件
            with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write("")

            # 记录审计日志
            _create_audit_log(
                db=None,  # 不需要db
                user_id=current_admin.id,
                action="logs_cleared",
                request=request
            )

            logger.info(f"Logs cleared by admin {current_admin.username}")
            return {
                "success": True,
                "message": "日志已清空"
            }
        else:
            return {
                "success": True,
                "message": "日志文件不存在"
            }
    except Exception as e:
        logger.error(f"Failed to clear logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空日志失败: {str(e)}"
        )


# ==================== 辅助函数 ====================

def _create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    request: Request,
    details: dict = None
):
    """创建审计日志记录。"""
    try:
        if db is None:
            # 如果没有db，只记录到系统日志
            logger.info(f"Audit: user_id={user_id}, action={action}, details={details}")
            return

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
        logger.error(f"Failed to create audit log: {e}")
