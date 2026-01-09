"""Upload and bill management routes."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from ..services.file_service import FileService
import pandas as pd
import os
import logging
import datetime

# Import directly from project root
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import psutil, but handle gracefully if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from importer import import_bill


router = APIRouter()
file_service = FileService()

# Track service start time
SERVICE_START_TIME = datetime.datetime.now()

# Track import statistics
import_stats = {
    "total_uploads": 0,
    "success_imports": 0,
    "failed_imports": 0
}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    platform: str = Form(None),
    sync_type: str = Form("immediate")
):
    """Upload bill file and trigger import."""
    import_stats["total_uploads"] += 1
    try:
        file_path = await file_service.save_file(file)

        if sync_type == "immediate":
            result = import_bill(file_path, platform)
            if result and result.get("success"):
                import_stats["success_imports"] += 1
            else:
                import_stats["failed_imports"] += 1
            return {
                "success": True,
                "message": "File uploaded and import started",
                "file_path": file_path,
                "import_result": result
            }
        else:
            return {
                "success": True,
                "message": "File uploaded, scheduled import pending",
                "file_path": file_path,
                "import_result": None
            }
    except ValueError as e:
        import_stats["failed_imports"] += 1
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import_stats["failed_imports"] += 1
        return {"success": False, "message": f"Upload failed: {e}", "file_path": None}


@router.get("/files")
async def get_files():
    """List uploaded files."""
    return JSONResponse(status_code=200, content={"files": file_service.list_files()})


@router.get("/file/{file_name}/content")
async def get_file_content(file_name: str):
    """Get CSV file content for preview."""
    try:
        file_path = os.path.join(file_service.upload_dir, file_name)

        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"message": "File not found"})

        if not file_name.endswith('.csv'):
            return JSONResponse(status_code=400, content={"message": "Only CSV files supported"})

        # Try multiple encodings
        encodings = ['gbk', 'utf-8', 'gb2312', 'latin-1']
        df = None
        header_line = None

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()

                for i, line in enumerate(lines):
                    if any(kw in line for kw in ['交易时间', '交易分类']):
                        header_line = i
                        break

                if header_line is not None:
                    df = pd.read_csv(file_path, encoding=encoding, skiprows=header_line, header=0, nrows=20)
                    break
            except Exception:
                continue

        if df is None:
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, nrows=20)
                    break
                except Exception:
                    continue

        if df is None:
            return JSONResponse(status_code=500, content={"message": "Cannot read file"})

        # Clean data for JSON
        df = df.replace([float('inf'), -float('inf')], float('nan'))
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna('')

        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                value = row[col]
                if isinstance(value, float) and not (float('-inf') < value < float('inf')):
                    record[col] = None
                else:
                    record[col] = value
            records.append(record)

        return JSONResponse(status_code=200, content={
            "file_name": file_name,
            "columns": df.columns.tolist(),
            "data": records
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Read failed: {str(e)}"})


@router.delete("/file/{file_name}")
async def delete_file(file_name: str):
    """Delete uploaded file."""
    try:
        file_path = os.path.join(file_service.upload_dir, file_name)

        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"success": False, "message": "File not found"})

        os.remove(file_path)
        return JSONResponse(status_code=200, content={"success": True, "message": "File deleted"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": f"Delete failed: {str(e)}"})


@router.get("/logs")
async def get_logs():
    """Get service logs."""
    try:
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "web_service.log")

        if not os.path.exists(log_file):
            return [{"level": "INFO", "time": "2025-01-01 00:00:00", "message": f"Log file not found: {log_file}"}]

        log_lines = []
        best_encoding = None
        best_lines = []

        # Try to find the best encoding by checking for decode errors
        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
            try:
                with open(log_file, "r", encoding=encoding) as f:
                    lines = f.readlines()
                    # Check if all lines can be decoded properly
                    # by checking for common artifacts of wrong encoding
                    artifact_count = 0
                    for line in lines:
                        # Check for replacement characters or other artifacts
                        if '' in line or '?' in line:
                            artifact_count += 1

                    # Store the encoding with least artifacts
                    if not best_lines or artifact_count < best_lines[1]:
                        best_lines = (lines, artifact_count)
                        best_encoding = encoding
                        if artifact_count == 0:
                            break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if best_lines:
            log_lines = best_lines[0]
        else:
            return [{"level": "ERROR", "time": "2025-01-01 00:00:00", "message": "Cannot read log file with any encoding"}]

        if not log_lines:
            return [{"level": "ERROR", "time": "2025-01-01 00:00:00", "message": "Log file is empty"}]

        logs = []
        for line in log_lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split(" - ")
            if len(parts) >= 5:
                # Format: timestamp - name - file:line - level - message
                logs.append({"level": parts[3], "time": parts[0], "message": " - ".join(parts[4:])})
            else:
                logs.append({"level": "INFO", "time": "", "message": line})

        return logs[-100:][::-1]
    except Exception as e:
        return [{"level": "ERROR", "time": "2025-01-01 00:00:00", "message": f"Read logs failed: {str(e)}"}]


@router.get("/service-info")
async def get_service_info():
    """Get service information including start time and statistics."""
    try:
        # Calculate uptime
        uptime_seconds = (datetime.datetime.now() - SERVICE_START_TIME).total_seconds()
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)

        uptime_str = ""
        if uptime_days > 0:
            uptime_str += f"{uptime_days}天 "
        if uptime_hours > 0 or uptime_days > 0:
            uptime_str += f"{uptime_hours}小时 "
        uptime_str += f"{uptime_minutes}分钟"

        # Get memory usage (only if psutil is available)
        memory_mb = "未知"
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_mb = f"{round(memory_info.rss / 1024 / 1024, 2)} MB"
            except Exception:
                memory_mb = "未知"

        return {
            "start_time": SERVICE_START_TIME.strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": uptime_str,
            "uptime_seconds": int(uptime_seconds),
            "version": "1.0.0",
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "memory_usage": memory_mb,
            "stats": import_stats.copy()
        }
    except Exception as e:
        return {
            "start_time": SERVICE_START_TIME.strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": "未知",
            "version": "1.0.0",
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "memory_usage": "未知",
            "stats": import_stats.copy(),
            "error": str(e)
        }
