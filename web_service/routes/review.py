"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
复盘功能 API 路由
提供账单复盘的生成、查询和配置接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import logging

from src.services.dependencies import get_current_user
from src.review_service import ReviewService


router = APIRouter()

# 简单的内存缓存
_review_list_cache = {
    "data": None,
    "timestamp": 0,
    "user_id": None
}
CACHE_TTL = 60  # 缓存60秒
logger = logging.getLogger(__name__)


def clear_review_list_cache():
    """清除复盘列表缓存"""
    global _review_list_cache
    _review_list_cache = {
        "data": None,
        "timestamp": 0,
        "user_id": None
    }
    logger.info("Review list cache cleared")


# ==================== Request/Response Models ====================

class ReviewGenerateRequest(BaseModel):
    """复盘生成请求"""
    review_type: str = Field(..., description="复盘类型: monthly/quarterly/yearly")
    year: int = Field(..., description="年份", ge=2020, le=2030)
    month: Optional[int] = Field(None, description="月份 (1-12), 月度复盘必填", ge=1, le=12)
    quarter: Optional[int] = Field(None, description="季度 (1-4), 季度复盘必填", ge=1, le=4)


class ReviewBatchRequest(BaseModel):
    """批量复盘生成请求"""
    review_type: str = Field(..., description="复盘类型: monthly/quarterly/yearly")
    start_date: str = Field(..., description="开始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)")


class ReviewConfigUpdateRequest(BaseModel):
    """复盘配置更新请求"""
    notion_monthly_review_db: Optional[str] = None
    notion_quarterly_review_db: Optional[str] = None
    notion_yearly_review_db: Optional[str] = None
    notion_monthly_template_id: Optional[str] = None
    notion_quarterly_template_id: Optional[str] = None
    notion_yearly_template_id: Optional[str] = None


class ReviewResponse(BaseModel):
    """复盘响应"""
    success: bool
    period: str
    page_id: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None


# ==================== API Endpoints ====================

@router.post("/generate", response_model=ReviewResponse)
async def generate_review(
    request: ReviewGenerateRequest,
    current_user = Depends(get_current_user)
):
    """生成复盘报告

    根据指定的复盘类型和时间周期，生成账单复盘报告并写入 Notion
    """
    user_id = current_user.id if hasattr(current_user, 'id') else None
    service = ReviewService(user_id=user_id)

    try:
        if request.review_type == "monthly":
            if not request.month:
                raise HTTPException(status_code=400, detail="月份参数必填")
            result = service.generate_monthly_review(request.year, request.month)

        elif request.review_type == "quarterly":
            if not request.quarter:
                raise HTTPException(status_code=400, detail="季度参数必填")
            result = service.generate_quarterly_review(request.year, request.quarter)

        elif request.review_type == "yearly":
            result = service.generate_yearly_review(request.year)

        else:
            raise HTTPException(status_code=400, detail="不支持的复盘类型")

        # 如果生成成功，清除缓存
        if result.get("success"):
            clear_review_list_cache()

        return ReviewResponse(**result)

    except Exception as e:
        return ReviewResponse(
            success=False,
            period="",
            error=str(e)
        )


@router.post("/batch")
async def batch_generate_reviews(
    request: ReviewBatchRequest,
    current_user = Depends(get_current_user)
):
    """批量生成复盘报告

    在指定日期范围内，批量生成多个周期的复盘报告
    """
    user_id = current_user.id if hasattr(current_user, 'id') else None

    try:
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")

    service = ReviewService(user_id=user_id)
    results = service.batch_generate_reviews(
        start_date,
        end_date,
        request.review_type
    )

    success_count = sum(1 for r in results if r.get("success"))
    fail_count = len(results) - success_count

    return {
        "total": len(results),
        "success": success_count,
        "failed": fail_count,
        "results": results
    }


@router.get("/config")
async def get_review_config(current_user = Depends(get_current_user)):
    """获取复盘配置

    返回当前用户的复盘数据库和模板配置
    """
    from src.config import Config
    import os

    user_id = current_user.id if hasattr(current_user, 'id') else None

    # 从环境变量获取默认配置
    config = {
        "monthly_review_db": os.getenv("NOTION_MONTHLY_REVIEW_DB", ""),
        "quarterly_review_db": os.getenv("NOTION_QUARTERLY_REVIEW_DB", ""),
        "yearly_review_db": os.getenv("NOTION_YEARLY_REVIEW_DB", ""),
        "monthly_template_id": os.getenv("NOTION_MONTHLY_TEMPLATE_ID", ""),
        "quarterly_template_id": os.getenv("NOTION_QUARTERLY_TEMPLATE_ID", ""),
        "yearly_template_id": os.getenv("NOTION_YEARLY_TEMPLATE_ID", "")
    }

    # 多租户模式：从用户配置获取
    if user_id and Config.is_multi_tenant_mode():
        from src.services.database import get_db_context
        from src.models import UserNotionConfig

        with get_db_context() as db:
            user_config = db.query(UserNotionConfig).filter(
                UserNotionConfig.user_id == user_id
            ).first()

            if user_config:
                config["monthly_review_db"] = getattr(user_config, "notion_monthly_review_db", config["monthly_review_db"])
                config["quarterly_review_db"] = getattr(user_config, "notion_quarterly_review_db", config["quarterly_review_db"])
                config["yearly_review_db"] = getattr(user_config, "notion_yearly_review_db", config["yearly_review_db"])
                config["monthly_template_id"] = getattr(user_config, "notion_monthly_template_id", config["monthly_template_id"])
                config["quarterly_template_id"] = getattr(user_config, "notion_quarterly_template_id", config["quarterly_template_id"])
                config["yearly_template_id"] = getattr(user_config, "notion_yearly_template_id", config["yearly_template_id"])

    return config


@router.post("/config")
async def update_review_config(
    request: ReviewConfigUpdateRequest,
    current_user = Depends(get_current_user)
):
    """更新复盘配置

    更新复盘数据库和模板配置：
    - 多租户模式：保存到用户配置
    - 单用户模式：更新环境变量（仅限当前进程，需要手动更新 .env 文件持久化）
    """
    from src.config import Config
    import os

    user_id = current_user.id if hasattr(current_user, 'id') else None

    if user_id and Config.is_multi_tenant_mode():
        # 多租户模式：保存到数据库
        from src.services.database import get_db_context
        from src.models import UserNotionConfig

        with get_db_context() as db:
            user_config = db.query(UserNotionConfig).filter(
                UserNotionConfig.user_id == user_id
            ).first()

            if not user_config:
                raise HTTPException(status_code=404, detail="用户配置不存在")

            # 更新配置
            if request.notion_monthly_review_db is not None:
                user_config.notion_monthly_review_db = request.notion_monthly_review_db
            if request.notion_quarterly_review_db is not None:
                user_config.notion_quarterly_review_db = request.notion_quarterly_review_db
            if request.notion_yearly_review_db is not None:
                user_config.notion_yearly_review_db = request.notion_yearly_review_db
            if request.notion_monthly_template_id is not None:
                user_config.notion_monthly_template_id = request.notion_monthly_template_id
            if request.notion_quarterly_template_id is not None:
                user_config.notion_quarterly_template_id = request.notion_quarterly_template_id
            if request.notion_yearly_template_id is not None:
                user_config.notion_yearly_template_id = request.notion_yearly_template_id

            user_config.updated_at = datetime.utcnow()
            db.commit()

        # 清除数据库结构缓存，以便使用新的配置
        ReviewService.clear_database_cache()

        return {"success": True, "message": "配置已更新"}

    else:
        # 单用户模式：更新环境变量（仅限当前进程）
        if request.notion_monthly_review_db is not None:
            os.environ["NOTION_MONTHLY_REVIEW_DB"] = request.notion_monthly_review_db
            Config.NOTION_MONTHLY_REVIEW_DB = request.notion_monthly_review_db
        if request.notion_quarterly_review_db is not None:
            os.environ["NOTION_QUARTERLY_REVIEW_DB"] = request.notion_quarterly_review_db
            Config.NOTION_QUARTERLY_REVIEW_DB = request.notion_quarterly_review_db
        if request.notion_yearly_review_db is not None:
            os.environ["NOTION_YEARLY_REVIEW_DB"] = request.notion_yearly_review_db
            Config.NOTION_YEARLY_REVIEW_DB = request.notion_yearly_review_db
        if request.notion_monthly_template_id is not None:
            os.environ["NOTION_MONTHLY_TEMPLATE_ID"] = request.notion_monthly_template_id
            Config.NOTION_MONTHLY_TEMPLATE_ID = request.notion_monthly_template_id
        if request.notion_quarterly_template_id is not None:
            os.environ["NOTION_QUARTERLY_TEMPLATE_ID"] = request.notion_quarterly_template_id
            Config.NOTION_QUARTERLY_TEMPLATE_ID = request.notion_quarterly_template_id
        if request.notion_yearly_template_id is not None:
            os.environ["NOTION_YEARLY_TEMPLATE_ID"] = request.notion_yearly_template_id
            Config.NOTION_YEARLY_TEMPLATE_ID = request.notion_yearly_template_id

        # 清除数据库结构缓存，以便使用新的配置
        ReviewService.clear_database_cache()

        return {
            "success": True,
            "message": "配置已更新（单用户模式：配置仅在当前进程生效，重启后失效。请在 .env 文件中手动添加配置以持久化）",
            "mode": "single_user"
        }


@router.get("/preview")
async def preview_review(
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    review_title: Optional[str] = Query(None, description="复盘标题（可选）"),
    current_user = Depends(get_current_user)
):
    """预览复盘数据

    根据日期范围生成复盘预览，包含属性和 Markdown 内容
    """
    user_id = current_user.id if hasattr(current_user, 'id') else None

    try:
        # 解析日期
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")

    logger.info(f"Preview review request: user_id={user_id}, {start_date} to {end_date}")

    try:
        service = ReviewService(user_id=user_id)
    except ValueError as e:
        logger.error(f"Notion config error: {e}")
        raise HTTPException(status_code=400, detail="请先配置 Notion API 密钥和数据库 ID")
    except Exception as e:
        logger.error(f"Service initialization error: {e}")
        raise HTTPException(status_code=500, detail=f"初始化复盘服务失败: {str(e)}")

    try:
        # 获取交易数据
        try:
            transactions = service.fetch_transactions(start_dt, end_dt)
        except Exception as e:
            logger.error(f"Failed to fetch transactions: {e}")
            raise HTTPException(status_code=500, detail=f"获取交易数据失败: {str(e)}")

        # 计算汇总
        summary = service.calculate_summary(transactions)

        # 按分类聚合
        categories = service.aggregate_by_category(transactions)

        # 构建属性数据
        attributes = service.build_review_attributes(
            start_dt,
            end_dt,
            summary,
            review_title
        )

        # 生成 Markdown 内容
        markdown_content = service.generate_review_markdown(
            start_dt,
            end_dt,
            transactions,
            summary,
            categories,
            review_title
        )

        return {
            "success": True,
            "attributes": attributes,
            "markdown_content": markdown_content,
            "transaction_count": len(transactions)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-connection")
async def test_notion_connection(current_user = Depends(get_current_user)):
    """测试用户的 Notion API 连接

    验证用户的 Notion API 密钥和数据库配置是否正确
    """
    import socket
    import asyncio
    from functools import partial

    user_id = current_user.id if hasattr(current_user, 'id') else None
    logger.info(f"Test connection request: user_id={user_id}")

    # 辅助函数：带超时的同步调用
    async def call_with_timeout(func, *args, timeout=15, **kwargs):
        """在单独的线程中执行同步函数，带超时控制"""
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, partial(func, *args, **kwargs)),
                timeout=timeout
            )
            return result, None
        except asyncio.TimeoutError:
            return None, "timeout"
        except Exception as e:
            return None, str(e)

    # 首先进行基础网络连通性测试
    logger.info("Performing network diagnostics...")
    network_diag = {
        "dns_resolution": False,
        "tcp_connection": False,
        "notion_api_reachable": False
    }

    try:
        # 测试 DNS 解析
        notion_host = "api.notion.com"
        ip_address = socket.gethostbyname(notion_host)
        network_diag["dns_resolution"] = True
        network_diag["ip_address"] = ip_address
        logger.info(f"DNS resolution successful: {notion_host} -> {ip_address}")

        # 测试 TCP 连接（Notion API 使用 HTTPS，端口 443）
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 秒超时
        result = sock.connect_ex((ip_address, 443))
        sock.close()

        if result == 0:
            network_diag["tcp_connection"] = True
            network_diag["notion_api_reachable"] = True
            logger.info("TCP connection to api.notion.com:443 successful")
        else:
            logger.warning(f"TCP connection to api.notion.com:443 failed with code {result}")
    except socket.gaierror as e:
        logger.error(f"DNS resolution failed: {e}")
        network_diag["dns_error"] = str(e)
    except socket.timeout:
        logger.error("TCP connection timeout")
        network_diag["tcp_error"] = "Connection timeout"
    except Exception as e:
        logger.error(f"Network diagnostic error: {e}")
        network_diag["diagnostic_error"] = str(e)

    try:
        service = ReviewService(user_id=user_id)
    except ValueError as e:
        logger.error(f"Notion config error: {e}")
        return {
            "api_key_valid": False,
            "income_db_valid": False,
            "expense_db_valid": False,
            "monthly_review_db_valid": False,
            "quarterly_review_db_valid": False,
            "yearly_review_db_valid": False,
            "error": "请先配置 Notion API 密钥和数据库 ID"
        }
    except Exception as e:
        logger.error(f"Service initialization error: {e}", exc_info=True)
        return {
            "api_key_valid": False,
            "income_db_valid": False,
            "expense_db_valid": False,
            "monthly_review_db_valid": False,
            "quarterly_review_db_valid": False,
            "yearly_review_db_valid": False,
            "error": f"初始化复盘服务失败: {str(e)}"
        }

    # 测试 API 连接
    result = {
        "api_key_valid": False,
        "income_db_valid": False,
        "expense_db_valid": False,
        "monthly_review_db_valid": None,  # None 表示未配置
        "quarterly_review_db_valid": None,
        "yearly_review_db_valid": None
    }

    # 测试 API 密钥
    logger.info("Testing API key...")
    user_info, error = await call_with_timeout(service.notion_client.client.users.me, timeout=15)

    if error:
        logger.error(f"API key test failed: {error}")
        error_str = error.lower() if error else ""

        # 处理网络连接错误
        if error == "timeout" or "timeout" in error_str:
            result["error"] = "Notion API 连接超时。请检查网络连接或配置代理服务器。"
            return result
        elif "connection" in error_str and ("reset" in error_str or "refused" in error_str):
            result["error"] = "无法连接到 Notion API（连接被重置）。请检查：1) 网络连接 2) 是否需要配置代理 3) 防火墙设置"
            return result
        elif "unauthorized" in error_str:
            result["error"] = "Notion API 密钥无效，请检查配置"
            return result
        else:
            result["error"] = f"API 密钥验证失败: {error}"
            return result
    else:
        result["api_key_valid"] = True
        result["user_name"] = user_info.get("name", "unknown")
        logger.info(f"API key valid, user: {result['user_name']}")

    # 测试收入数据库
    logger.info("Testing income database...")
    income_db, error = await call_with_timeout(
        service.notion_client.client.databases.retrieve,
        database_id=service.notion_client.income_db,
        timeout=15
    )

    if error:
        logger.error(f"Income DB error: {error}")
        error_str = error.lower() if error else ""
        if error == "timeout" or "timeout" in error_str:
            result["income_db_error"] = "收入数据库查询超时"
        elif "not found" in error_str:
            result["income_db_error"] = "收入数据库不存在"
        else:
            result["income_db_error"] = error
    else:
        result["income_db_valid"] = True
        result["income_db_title"] = income_db.get('title', [{}])[0].get('text', {}).get('content', 'unknown')
        logger.info(f"Income DB valid: {result['income_db_title']}")

    # 测试支出数据库
    logger.info("Testing expense database...")
    expense_db, error = await call_with_timeout(
        service.notion_client.client.databases.retrieve,
        database_id=service.notion_client.expense_db,
        timeout=15
    )

    if error:
        logger.error(f"Expense DB error: {error}")
        error_str = error.lower() if error else ""
        if error == "timeout" or "timeout" in error_str:
            result["expense_db_error"] = "支出数据库查询超时"
        elif "not found" in error_str:
            result["expense_db_error"] = "支出数据库不存在"
        else:
            result["expense_db_error"] = error
    else:
        result["expense_db_valid"] = True
        result["expense_db_title"] = expense_db.get('title', [{}])[0].get('text', {}).get('content', 'unknown')
        logger.info(f"Expense DB valid: {result['expense_db_title']}")

    # 测试复盘数据库（从用户配置或环境变量获取）
    review_dbs = {
        "monthly": service.get_review_database_id("monthly"),
        "quarterly": service.get_review_database_id("quarterly"),
        "yearly": service.get_review_database_id("yearly")
    }

    for review_type, db_id in review_dbs.items():
        result_key = f"{review_type}_review_db_valid"
        title_key = f"{review_type}_review_db_title"
        error_key = f"{review_type}_review_db_error"

        if db_id:
            logger.info(f"Testing {review_type} review database: {db_id[:8]}...")
            review_db, error = await call_with_timeout(
                service.notion_client.client.databases.retrieve,
                database_id=db_id,
                timeout=15
            )

            if error:
                logger.error(f"{review_type.capitalize()} review DB error: {error}")
                error_str = error.lower() if error else ""
                if error == "timeout" or "timeout" in error_str:
                    result[error_key] = f"{review_type.capitalize()}复盘数据库查询超时"
                elif "not found" in error_str:
                    result[error_key] = f"{review_type.capitalize()}复盘数据库不存在"
                else:
                    result[error_key] = error
            else:
                result[result_key] = True
                result[title_key] = review_db.get('title', [{}])[0].get('text', {}).get('content', 'unknown')
                logger.info(f"{review_type.capitalize()} review DB valid: {result[title_key]}")
        else:
            logger.info(f"{review_type.capitalize()} review database not configured")
            result[result_key] = None

    # 添加网络诊断结果
    result["network_diagnostic"] = network_diag

    return result


@router.get("/list")
async def list_reviews(
    review_type: Optional[str] = Query(None, description="复盘类型: monthly/quarterly/yearly"),
    limit: int = Query(10, description="返回数量限制", ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """获取历史复盘列表

    从 Notion 数据库中查询已生成的复盘报告列表
    使用缓存机制提高性能
    """
    global _review_list_cache
    user_id = current_user.id if hasattr(current_user, 'id') else None

    # 检查缓存
    current_time = time.time()
    cache_key = f"{user_id}_{review_type}_{limit}"

    if (_review_list_cache["user_id"] == user_id and
        _review_list_cache["timestamp"] > current_time - CACHE_TTL and
        _review_list_cache["data"] is not None):
        logger.info(f"Returning cached review list for user {user_id}")
        return _review_list_cache["data"]

    # 缓存未命中，查询数据
    logger.info(f"Cache miss, fetching review list for user {user_id}")
    service = ReviewService(user_id=user_id)

    try:
        # 获取复盘数据库ID
        database_id = None
        if review_type == "monthly":
            database_id = service.get_review_database_id(service.TYPE_MONTHLY)
        elif review_type == "quarterly":
            database_id = service.get_review_database_id(service.TYPE_QUARTERLY)
        elif review_type == "yearly":
            database_id = service.get_review_database_id(service.TYPE_YEARLY)
        else:
            # 如果没有指定类型，尝试获取月度复盘数据库
            database_id = service.get_review_database_id(service.TYPE_MONTHLY)

        if not database_id:
            return {
                "success": False,
                "reviews": [],
                "error": "复盘数据库未配置"
            }

        # 查询数据库中的页面
        logger.info(f"Querying review database: {database_id[:8]}...")

        # 使用正确的 API 调用方式
        # 方式1: 使用 client.request 方法（推荐）
        try:
            response = service.notion_client.client.request(
                path=f"/databases/{database_id}/query",
                method="POST",
                body={}
            )
        except AttributeError:
            # 方式2: 如果 request 方法不可用，使用直接调用
            response = service.notion_client.client.databases.retrieve(database_id=database_id)
            # 对于 retrieve，我们需要手动获取页面
            # 暂时返回空列表，因为 retrieve 只返回数据库信息，不返回页面列表
            logger.warning("Using database retrieve instead of query - this won't return page list")
            return {
                "success": True,
                "reviews": [],
                "total": 0,
                "warning": "数据库查询功能需要更新 Notion 客户端版本"
            }

        results = response.get("results", [])

        # 解析结果
        reviews = []
        for page in results[:limit]:
            review_data = {
                "id": page.get("id"),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time"),
                "properties": {}
            }

            # 解析属性
            properties = page.get("properties", {})
            for prop_name, prop_data in properties.items():
                prop_type = prop_data.get("type")
                if prop_type == "title":
                    title_parts = prop_data.get("title", [])
                    title = "".join([part.get("text", {}).get("content", "") for part in title_parts])
                    review_data["properties"][prop_name] = title
                    review_data["title"] = title
                elif prop_type == "number":
                    review_data["properties"][prop_name] = prop_data.get("number")
                elif prop_type == "date":
                    date_data = prop_data.get("date")
                    if date_data:
                        review_data["properties"][prop_name] = date_data.get("start")

            reviews.append(review_data)

        # 按创建时间倒序排序
        reviews.sort(key=lambda x: x.get("created_time", ""), reverse=True)

        logger.info(f"Found {len(reviews)} reviews")

        result = {
            "success": True,
            "reviews": reviews,
            "total": len(reviews)
        }

        # 更新缓存
        _review_list_cache = {
            "data": result,
            "timestamp": current_time,
            "user_id": user_id
        }

        return result

    except Exception as e:
        logger.error(f"Failed to list reviews: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "reviews": [],
            "error": str(e)
        }


@router.post("/submit")
async def submit_review(
    request: dict,
    current_user = Depends(get_current_user)
):
    """提交复盘到 Notion

    接收用户编辑后的属性和 Markdown 内容，创建复盘页面

    Request body:
        {
            "review_type": "monthly",
            "attributes": {
                "title": "2026年1月复盘",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "status": "完成",
                "summary": "...",
                "total_income": 10000,
                "total_expense": 5000,
                "net_balance": 5000,
                "transaction_count": 50
            },
            "markdown_content": "# 复盘内容..."
        }
    """
    user_id = current_user.id if hasattr(current_user, 'id') else None

    try:
        # 解析请求
        review_type = request.get("review_type", "monthly")
        attributes = request.get("attributes", {})
        markdown_content = request.get("markdown_content", "")

        if not attributes:
            raise HTTPException(status_code=400, detail="缺少属性数据")

        if not markdown_content:
            raise HTTPException(status_code=400, detail="缺少复盘内容")

        logger.info(f"Submitting review: {attributes.get('title')}")

        # 创建服务实例
        service = ReviewService(user_id=user_id)

        # 创建复盘页面
        page_id = service.create_review_from_content(
            review_type,
            attributes,
            markdown_content
        )

        if page_id:
            logger.info(f"Review page created successfully: {page_id}")
            return {
                "success": True,
                "page_id": page_id,
                "url": f"https://www.notion.so/{page_id.replace('-', '')}"
            }
        else:
            raise HTTPException(status_code=500, detail="创建复盘页面失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit review: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提交复盘失败: {str(e)}")
