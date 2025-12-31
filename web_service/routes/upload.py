from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from ..services.file_service import FileService
from ..services.import_service import ImportService
import pandas as pd
import os
import logging
import re

router = APIRouter()
file_service = FileService()
import_service = ImportService()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    platform: str = Form(None),
    sync_type: str = Form("immediate")  # immediate 或 scheduled
):
    """
    上传账单文件并选择同步时机
    
    - **file**: 账单文件
    - **platform**: 账单平台（可选，自动检测）
    - **sync_type**: 同步类型，immediate（立即执行）或 scheduled（定时执行）
    """
    try:
        # 保存上传的文件
        file_path = await file_service.save_file(file)
        
        # 根据同步类型处理
        if sync_type == "immediate":
            # 立即执行导入
            result = import_service.import_bill(file_path, platform)
            
            return {
                "success": True,
                "message": "文件上传成功并立即开始导入",
                "file_path": file_path,
                "import_result": result
            }
        elif sync_type == "scheduled":
            # 定时执行（这里可以扩展，当前版本只支持立即执行）
            # 可以在这里添加任务到调度器
            return {
                "success": True,
                "message": "文件上传成功，将按照既定调度执行导入",
                "file_path": file_path,
                "import_result": None
            }
        else:
            raise HTTPException(status_code=400, detail="sync_type 必须是 immediate 或 scheduled")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return {
            "success": False,
            "message": f"文件上传失败: {str(e)}",
            "file_path": None,
            "import_result": None
        }

@router.get("/files")
async def get_files():
    """
    获取上传文件列表
    """
    files = file_service.list_files()
    return JSONResponse(status_code=200, content={"files": files})

@router.get("/file/{file_name}/content")
async def get_file_content(file_name: str):
    """
    获取CSV文件内容
    """
    try:
        upload_dir = file_service.upload_dir
        file_path = os.path.join(upload_dir, file_name)
        
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"message": "文件不存在"})
        
        # 只允许查看CSV文件
        if not file_name.endswith('.csv'):
            return JSONResponse(status_code=400, content={"message": "只支持查看CSV文件"})
        
        # 读取CSV文件内容，只显示前20行，尝试多种编码
        encodings = ['gbk', 'utf-8', 'gb2312', 'latin-1']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, nrows=20)
                break
            except Exception as e:
                continue
        
        if df is None:
            return JSONResponse(status_code=500, content={"message": "无法读取文件内容，尝试多种编码均失败"})
        
        # 处理超出JSON范围的浮点数值
        df = df.replace([float('inf'), -float('inf')], float('nan'))  # 将无穷大转换为NaN
        # 使用fillna的正确方式，避免版本兼容性问题
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                df[col] = df[col].fillna(0)  # 数值列使用0填充
            else:
                df[col] = df[col].fillna('')  # 其他列使用空字符串填充
        
        # 转换为字典，确保所有数值都在JSON范围内
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                value = row[col]
                # 确保数值在JSON范围内
                if isinstance(value, (int, float)):
                    # 检查是否为有限数值
                    if isinstance(value, float) and not (float('-inf') < value < float('inf')):
                        record[col] = None
                    else:
                        record[col] = value
                else:
                    record[col] = value
            records.append(record)
        
        return JSONResponse(status_code=200, content={
            "file_name": file_name,
            "columns": df.columns.tolist(),
            "data": records
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"读取文件失败: {str(e)}"})

@router.delete("/file/{file_name}")
async def delete_file(file_name: str):
    """
    删除文件
    """
    try:
        upload_dir = file_service.upload_dir
        file_path = os.path.join(upload_dir, file_name)
        
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"success": False, "message": "文件不存在"})
        
        # 删除文件
        os.remove(file_path)
        return JSONResponse(status_code=200, content={"success": True, "message": "文件删除成功"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": f"删除文件失败: {str(e)}"})

@router.get("/logs")
async def get_logs():
    """
    获取服务日志
    """
    try:
        # 日志文件路径
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "web_service.log")
        
        # 检查日志文件是否存在
        if not os.path.exists(log_file_path):
            # 返回调试信息
            return [{"level": "INFO", "time": "2025-01-01 00:00:00", "message": f"日志文件不存在: {log_file_path}"}]
        
        # 读取日志文件内容，尝试多种编码
        log_lines = []
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(log_file_path, "r", encoding=encoding) as f:
                    log_lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        
        if not log_lines:
            return [{"level": "ERROR", "time": "2025-01-01 00:00:00", "message": "无法读取日志文件，所有编码尝试均失败"}]
        
        # 解析日志内容，使用更宽松的解析方式
        logs = []
        
        for line in log_lines:
            line = line.strip()
            if not line:
                continue
            
            # 使用更宽松的解析方式，只要能提取时间、级别和消息即可
            # 日志格式：2025-01-01 12:00:00 - __main__ - INFO - 服务运行正常
            parts = line.split(" - ")
            if len(parts) >= 4:
                time_str = parts[0]
                level = parts[2]
                message = " - ".join(parts[3:])
                logs.append({
                    "level": level,
                    "time": time_str,
                    "message": message
                })
            else:
                # 如果解析失败，将整行作为消息
                logs.append({
                    "level": "INFO",
                    "time": "",
                    "message": line
                })
        
        # 只返回最近的100条日志，反转顺序显示最新的日志在最前面
        return logs[-100:][::-1]
    except Exception as e:
        # 返回错误信息
        return [{"level": "ERROR", "time": "2025-01-01 00:00:00", "message": f"读取日志失败: {str(e)}"}]
