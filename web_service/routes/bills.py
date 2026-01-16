"""Bill management routes for upload, list, preview, and delete operations."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User, UserUpload, ImportHistory
from schemas import UploadResponse, FileUploadResponse, FileListResponse, ImportHistoryResponse
from dependencies import get_current_active_user, get_pagination_params
from web_service.services.user_file_service import UserFileService
from importer import import_bill, parse_bill_only, parse_bill_raw
from config import Config
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()
file_service = UserFileService()


# ==================== 账单上传 ====================

@router.post("/upload", response_model=UploadResponse, tags=["Bills"])
async def upload_bill(
    request: Request,
    file: UploadFile = File(...),
    platform: Optional[str] = Form(None),
    sync_type: str = Form("immediate"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上传账单文件并导入到 Notion。

    Args:
        file: 上传的账单文件
        platform: 支付平台（alipay, wechat, unionpay），不指定则自动检测
        sync_type: 同步类型（immediate=立即导入, scheduled=定时导入）
    """
    # 创建上传记录
    upload = UserUpload(
        user_id=current_user.id,
        original_file_name=file.filename,
        platform=platform or "auto",
        upload_type=sync_type,
        status="processing"
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
                "platform": platform or "auto",
                "sync_type": sync_type
            }
        )

        # 立即导入
        if sync_type == "immediate":
            try:
                # 使用用户的 Notion 配置导入
                import_result = import_bill(file_path, platform, user_id=current_user.id)

                # 更新平台为检测到的实际平台
                if import_result.get('detected_platform'):
                    upload.platform = import_result['detected_platform']

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
                        status="success"
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
                        error_message=error_msg
                    )
                    db.add(import_history)

                db.commit()

                return {
                    "success": True,
                    "message": "File uploaded and imported successfully" if import_result.get('success') else f"File uploaded but import failed: {import_result.get('error', 'Unknown error')}",
                    "upload_id": upload.id,
                    "file": FileUploadResponse(**upload.__dict__),
                    "import_result": {
                        "status": upload.status,
                        "message": "Import completed" if import_result.get('success') else import_result.get('error', 'Import failed'),
                        "detected_platform": upload.platform,
                        "total_records": import_result.get('total_records', 0),
                        "imported": import_result.get('imported', 0),
                        "skipped": import_result.get('skipped', 0)
                    }
                }

            except ValueError as e:
                # 处理 Notion 配置缺失等特定错误
                error_msg = str(e)
                logger.warning(f"Import failed for user {current_user.id}: {error_msg}")

                upload.status = "failed"
                error_message = "Notion configuration not found. Please configure your Notion API settings."

                import_history = ImportHistory(
                    user_id=current_user.id,
                    upload_id=upload.id,
                    total_records=0,
                    imported_records=0,
                    skipped_records=0,
                    failed_records=0,
                    status="failed",
                    error_message=error_message
                )
                db.add(import_history)
                db.commit()

                # 返回成功（文件已上传），但导入失败
                return {
                    "success": True,
                    "message": "File uploaded successfully, but import failed. Please configure your Notion API settings.",
                    "upload_id": upload.id,
                    "file": FileUploadResponse(**upload.__dict__),
                    "import_result": {
                        "status": "failed",
                        "message": error_message,
                        "error_code": "NOTION_CONFIG_MISSING"
                    }
                }

            except Exception as e:
                logger.error(f"Import failed: {e}")
                upload.status = "failed"

                import_history = ImportHistory(
                    user_id=current_user.id,
                    upload_id=upload.id,
                    total_records=0,
                    imported_records=0,
                    skipped_records=0,
                    failed_records=0,
                    status="failed",
                    error_message=str(e)
                )
                db.add(import_history)
                db.commit()

                # 返回成功（文件已上传），但导入失败
                return {
                    "success": True,
                    "message": f"File uploaded successfully, but import failed: {str(e)}",
                    "upload_id": upload.id,
                    "file": FileUploadResponse(**upload.__dict__),
                    "import_result": {
                        "status": "failed",
                        "message": str(e)
                    }
                }
        else:
            # 定时导入
            upload.status = "pending"
            db.commit()

            return {
                "success": True,
                "message": "File uploaded, scheduled import pending",
                "upload_id": upload.id,
                "file": FileUploadResponse(**upload.__dict__),
                "import_result": {
                    "status": "pending",
                    "message": "Scheduled import pending"
                }
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
        "files": [FileUploadResponse(**u.__dict__) for u in uploads],
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

    return FileUploadResponse(**upload.__dict__)


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

        return {
            "upload_id": upload_id,
            "file_name": upload.original_file_name,
            "platform": upload.platform,
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
        from models import AuditLog
        from dependencies import get_client_ip, get_user_agent

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
