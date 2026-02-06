"""Bill management routes for upload, list, preview, and delete operations."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from datetime import datetime

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from src.config import Config
from src.services.database import get_db
from src.services.dependencies import get_current_active_user, get_pagination_params, get_client_ip, get_user_agent
from src.importer import import_bill, parse_bill_only, parse_bill_raw
from src.models import User, UserUpload, ImportHistory, AuditLog
from src.schemas import UploadResponse, FileUploadResponse, FileListResponse, ImportHistoryResponse
from web_service.services.user_file_service import UserFileService

logger = logging.getLogger(__name__)
router = APIRouter()
file_service = UserFileService()


# ==================== 账单上传 ====================

@router.post("/upload", response_model=UploadResponse, tags=["Bills"])
async def upload_bill(
    request: Request,
    file: UploadFile = File(...),
    platform: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上传账单文件。

    Args:
        file: 上传的账单文件
        platform: 支付平台（alipay, wechat, unionpay），不指定则自动检测
    """
    # 创建上传记录
    upload = UserUpload(
        user_id=current_user.id,
        original_file_name=file.filename,
        platform=platform or "auto",
        upload_type="manual",
        status="pending"
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    try:
        # 保存文件
        file_path = await file_service.save_file(
            user_id=current_user.id,
            upload_id=upload.id,
            file=file,
            original_filename=file.filename
        )

        # 更新上传记录
        upload.file_name = file_path.split("/")[-1]
        upload.file_path = file_path
        upload.file_size = file_service.get_file_size(current_user.id, upload.id, upload.file_name)

        # 如果平台为auto，立即进行平台检测
        detected_platform = None
        if upload.platform == "auto":
            try:
                # 调用平台检测逻辑
                from parsers import get_parser
                parser = get_parser(file_path)
                if parser:
                    detected_platform = parser.get_platform()
                    # 映射平台名称到数据库存储格式
                    platform_mapping = {
                        'Alipay': 'alipay',
                        'WeChat': 'wechat',
                        'UnionPay': 'unionpay'
                    }
                    upload.platform = platform_mapping.get(detected_platform, detected_platform.lower())
                    logger.info(f"Auto-detected platform: {upload.platform} for file {file.filename}")
                else:
                    # 无法检测，保持auto
                    upload.platform = "auto"
            except Exception as e:
                logger.warning(f"Platform detection failed for {file.filename}: {e}, keeping as 'auto'")
                upload.platform = "auto"

        db.commit()

        # 记录审计日志
        _create_audit_log(
            db=db,
            user_id=current_user.id,
            action="bill_uploaded",
            request=request,
            details={
                "upload_id": upload.id,
                "file_name": file.filename,
                "platform": upload.platform,
                "detected_platform": detected_platform
            }
        )

        # 上传成功，等待用户手动导入
        db.commit()

        return {
            "success": True,
            "message": "File uploaded successfully. Please import manually from the file list.",
            "upload_id": upload.id,
            "file": FileUploadResponse.model_validate(upload)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        upload.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


# ==================== 账单列表 ====================

@router.get("/uploads", response_model=FileListResponse, tags=["Bills"])
async def get_user_uploads(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的上传列表。

    支持分页和状态筛选。
    """
    # 构建查询
    query = db.query(UserUpload).filter(UserUpload.user_id == current_user.id)

    if status_filter:
        query = query.filter(UserUpload.status == status_filter)

    # 计算总数
    total = query.count()

    # 分页
    uploads = query.order_by(UserUpload.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "files": [FileUploadResponse.model_validate(u) for u in uploads],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/uploads/{upload_id}", response_model=FileUploadResponse, tags=["Bills"])
async def get_upload_detail(
    upload_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取指定上传的详细信息。

    包括导入历史记录。
    """
    upload = db.query(UserUpload).filter(
        UserUpload.id == upload_id,
        UserUpload.user_id == current_user.id
    ).first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )

    return FileUploadResponse.model_validate(upload)


# ==================== 账单导入 ====================

@router.post("/uploads/{upload_id}/import", tags=["Bills"])
async def import_uploaded_bill(
    upload_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """导入已上传的账单文件到 Notion。

    Args:
        upload_id: 上传记录ID

    Returns:
        导入结果，包括成功/失败状态、导入记录数等
    """
    # 获取上传记录
    upload = db.query(UserUpload).filter(
        UserUpload.id == upload_id,
        UserUpload.user_id == current_user.id
    ).first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )

    # 检查文件是否存在
    if not file_service.file_exists(current_user.id, upload_id, upload.file_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    # 检查是否已经导入过
    if upload.status == "completed":
        return {
            "success": True,
            "message": "This file has already been imported.",
            "upload_id": upload_id,
            "status": "already_imported"
        }

    # 更新状态为处理中
    upload.status = "processing"
    db.commit()

    file_path = file_service.get_file_path(current_user.id, upload_id, upload.file_name)

    try:
        # 使用用户的 Notion 配置导入
        platform_param = None if upload.platform == 'auto' else upload.platform
        import_result = import_bill(file_path, platform_param, user_id=current_user.id)

        # 更新平台为检测到的实际平台
        if import_result.get('detected_platform'):
            upload.platform = import_result['detected_platform']

        # 计算导入耗时
        completed_at = datetime.utcnow()
        started_at = upload.created_at
        duration_seconds = int((completed_at - started_at).total_seconds())

        if import_result.get('success'):
            upload.status = "completed"

            # 记录导入历史
            import_history = ImportHistory(
                user_id=current_user.id,
                upload_id=upload.id,
                total_records=import_result.get('total_records', 0),
                imported_records=import_result.get('imported', 0),
                skipped_records=import_result.get('skipped', 0),
                failed_records=0,
                status="success",
                completed_at=completed_at,
                duration_seconds=duration_seconds
            )
            db.add(import_history)

            _create_audit_log(
                db=db,
                user_id=current_user.id,
                action="bill_imported",
                request=request,
                details={
                    "upload_id": upload.id,
                    "platform": upload.platform,
                    "imported": import_result.get('imported', 0)
                }
            )

            db.commit()

            return {
                "success": True,
                "message": "Bill imported successfully",
                "upload_id": upload_id,
                "status": "completed",
                "detected_platform": upload.platform,
                "total_records": import_result.get('total_records', 0),
                "imported": import_result.get('imported', 0),
                "skipped": import_result.get('skipped', 0)
            }
        else:
            upload.status = "failed"
            error_msg = import_result.get('error', 'Import failed')

            import_history = ImportHistory(
                user_id=current_user.id,
                upload_id=upload.id,
                total_records=import_result.get('total_records', 0),
                imported_records=0,
                skipped_records=0,
                failed_records=import_result.get('total_records', 0),
                status="failed",
                error_message=error_msg,
                completed_at=completed_at,
                duration_seconds=duration_seconds
            )
            db.add(import_history)
            db.commit()

            return {
                "success": False,
                "message": error_msg,
                "upload_id": upload_id,
                "status": "failed"
            }

    except ValueError as e:
        # 处理 Notion 配置缺失等特定错误
        error_msg = str(e)
        logger.warning(f"Import failed for user {current_user.id}: {error_msg}")

        upload.status = "failed"
        error_message = "Notion configuration not found. Please configure your Notion API settings."

        completed_at = datetime.utcnow()
        started_at = upload.created_at
        duration_seconds = int((completed_at - started_at).total_seconds())

        import_history = ImportHistory(
            user_id=current_user.id,
            upload_id=upload.id,
            total_records=0,
            imported_records=0,
            skipped_records=0,
            failed_records=0,
            status="failed",
            error_message=error_message,
            completed_at=completed_at,
            duration_seconds=duration_seconds
        )
        db.add(import_history)
        db.commit()

        return {
            "success": False,
            "message": error_message,
            "upload_id": upload_id,
            "status": "failed",
            "error_code": "NOTION_CONFIG_MISSING"
        }

    except Exception as e:
        logger.error(f"Import failed: {e}")
        upload.status = "failed"

        completed_at = datetime.utcnow()
        started_at = upload.created_at
        duration_seconds = int((completed_at - started_at).total_seconds())

        import_history = ImportHistory(
            user_id=current_user.id,
            upload_id=upload.id,
            total_records=0,
            imported_records=0,
            skipped_records=0,
            failed_records=0,
            status="failed",
            error_message=str(e),
            completed_at=completed_at,
            duration_seconds=duration_seconds
        )
        db.add(import_history)
        db.commit()

        return {
            "success": False,
            "message": str(e),
            "upload_id": upload_id,
            "status": "failed"
        }


# ==================== 文件预览 ====================

@router.get("/uploads/{upload_id}/preview", tags=["Bills"])
async def preview_upload_file(
    upload_id: int,
    max_rows: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """预览上传的 CSV 文件内容。

    返回文件的前几行数据用于预览。
    """
    upload = db.query(UserUpload).filter(
        UserUpload.id == upload_id,
        UserUpload.user_id == current_user.id
    ).first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )

    # 检查文件是否存在
    if not file_service.file_exists(current_user.id, upload_id, upload.file_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    file_path = file_service.get_file_path(current_user.id, upload_id, upload.file_name)

    # 解析文件预览
    try:
        # 如果平台为 auto，则传递 None 进行自动检测
        platform_param = None if upload.platform == 'auto' else upload.platform
        result = parse_bill_raw(file_path, platform_param, max_rows)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to parse file"
            )

        # 如果检测到平台且当前是auto，更新数据库中的平台
        detected_platform = result.get('detected_platform')
        if detected_platform and upload.platform == 'auto':
            upload.platform = detected_platform
            db.commit()

        return {
            "upload_id": upload_id,
            "file_name": upload.original_file_name,
            "platform": upload.platform,  # 返回更新后的平台
            "detected_platform": result.get('detected_platform', upload.platform),
            "total_records": result.get('total_rows', 0),
            "preview_records": len(result.get('data', [])),
            "columns": result.get('columns', []),
            "data": result.get('data', [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )


# ==================== 删除上传 ====================

@router.post("/uploads/batch-delete", tags=["Bills"])
async def delete_upload_batch(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """批量删除指定的上传记录和相关文件。"""
    # 从请求体中获取 upload_ids
    body = await request.body()
    data = json.loads(body) if body else {}
    upload_ids = data.get('upload_ids', [])

    if not upload_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No upload IDs provided"
        )

    # 查询所有要删除的上传
    uploads = db.query(UserUpload).filter(
        UserUpload.id.in_(upload_ids),
        UserUpload.user_id == current_user.id
    ).all()

    if not uploads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No uploads found"
        )

    deleted_count = 0
    failed_uploads = []

    for upload in uploads:
        try:
            # 删除文件
            file_service.delete_user_files(current_user.id, upload.id)

            # 删除数据库记录
            db.delete(upload)
            deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete upload {upload.id}: {e}")
            failed_uploads.append(upload.id)

    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_user.id,
        action="bills_batch_deleted",
        request=request,
        details={
            "upload_ids": upload_ids,
            "deleted_count": deleted_count,
            "failed_ids": failed_uploads
        }
    )

    logger.info(f"Batch delete completed: user_id={current_user.id}, deleted={deleted_count}, failed={len(failed_uploads)}")

    return {
        "success": True,
        "message": f"Deleted {deleted_count} uploads successfully" + (f", {len(failed_uploads)} failed" if failed_uploads else ""),
        "deleted_count": deleted_count,
        "failed_ids": failed_uploads
    }


@router.delete("/uploads/{upload_id}", tags=["Bills"])
async def delete_upload(
    upload_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除指定的上传记录和相关文件。"""
    upload = db.query(UserUpload).filter(
        UserUpload.id == upload_id,
        UserUpload.user_id == current_user.id
    ).first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )

    # 删除文件
    file_service.delete_user_files(current_user.id, upload_id)

    # 删除数据库记录
    db.delete(upload)
    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_user.id,
        action="bill_deleted",
        request=request,
        details={"upload_id": upload_id, "file_name": upload.original_file_name}
    )

    logger.info(f"Upload deleted: user_id={current_user.id}, upload_id={upload_id}")
    return {
        "success": True,
        "message": "Upload deleted successfully"
    }


# ==================== 导入历史 ====================

@router.get("/history/stats", tags=["Bills"])
async def get_import_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的导入统计数据。"""
    # 总导入次数
    total = db.query(ImportHistory).filter(
        ImportHistory.user_id == current_user.id
    ).count()

    # 成功导入次数
    successful = db.query(ImportHistory).filter(
        ImportHistory.user_id == current_user.id,
        ImportHistory.status == 'success'
    ).count()

    # 总记录数
    from sqlalchemy import func
    total_records_result = db.query(func.sum(ImportHistory.total_records)).filter(
        ImportHistory.user_id == current_user.id
    ).first()
    total_records = total_records_result[0] or 0

    # 平均耗时
    avg_duration_result = db.query(func.avg(ImportHistory.duration_seconds)).filter(
        ImportHistory.user_id == current_user.id,
        ImportHistory.duration_seconds.isnot(None)
    ).first()
    avg_duration = round(avg_duration_result[0], 2) if avg_duration_result[0] else None

    return {
        "total": total,
        "successful": successful,
        "total_records": total_records,
        "avg_duration": avg_duration
    }


@router.get("/history", tags=["Bills"])
async def get_import_history(
    page: int = 1,
    page_size: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的导入历史记录。

    支持分页和时间范围过滤。
    """
    from sqlalchemy.orm import joinedload

    # 构建查询
    query = db.query(ImportHistory).filter(
        ImportHistory.user_id == current_user.id
    )

    # 时间范围过滤
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(ImportHistory.started_at >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(ImportHistory.started_at <= end_dt)
        except ValueError:
            pass

    # 计算总数
    total = query.count()

    # 分页查询，预加载关联的 UserUpload
    history = query.options(
        joinedload(ImportHistory.upload)
    ).order_by(ImportHistory.started_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # 构建响应，包含 UserUpload 的字段
    history_data = []
    for h in history:
        h_dict = {
            "id": h.id,
            "upload_id": h.upload_id,
            "total_records": h.total_records,
            "imported_records": h.imported_records,
            "skipped_records": h.skipped_records,
            "failed_records": h.failed_records,
            "status": h.status,
            "error_message": h.error_message,
            "started_at": h.started_at,
            "completed_at": h.completed_at,
            "duration_seconds": h.duration_seconds,
            # 从关联的 UserUpload 获取字段
            "file_name": h.upload.file_name if h.upload else None,
            "original_file_name": h.upload.original_file_name if h.upload else None,
            "platform": h.upload.platform if h.upload else None
        }
        history_data.append(ImportHistoryResponse(**h_dict))

    return {
        "history": history_data,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.delete("/history/{history_id}", tags=["Bills"])
async def delete_import_history_item(
    history_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除指定的导入历史记录。"""
    history = db.query(ImportHistory).filter(
        ImportHistory.id == history_id,
        ImportHistory.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History not found"
        )

    db.delete(history)
    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_user.id,
        action="import_history_deleted",
        request=request,
        details={"history_id": history_id}
    )

    return {
        "success": True,
        "message": "History deleted successfully"
    }


@router.post("/history/batch-delete", tags=["Bills"])
async def delete_import_history_batch(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """批量删除导入历史记录。"""
    body = await request.body()
    data = json.loads(body) if body else {}
    history_ids = data.get('history_ids', [])

    if not history_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No history IDs provided"
        )

    # 查询所有要删除的历史记录
    history_items = db.query(ImportHistory).filter(
        ImportHistory.id.in_(history_ids),
        ImportHistory.user_id == current_user.id
    ).all()

    if not history_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No history records found"
        )

    deleted_count = 0
    for item in history_items:
        db.delete(item)
        deleted_count += 1

    db.commit()

    # 记录审计日志
    _create_audit_log(
        db=db,
        user_id=current_user.id,
        action="import_history_batch_deleted",
        request=request,
        details={"history_ids": history_ids, "deleted_count": deleted_count}
    )

    return {
        "success": True,
        "message": f"Deleted {deleted_count} history records successfully",
        "deleted_count": deleted_count
    }


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
