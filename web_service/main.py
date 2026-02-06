"""FastAPI web service for bill import."""

import os
from typing import Optional, Tuple
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from utils import setup_logging
from config import Config


# Setup
web_service_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

# Configure logging
log_dir = os.path.join(web_service_dir, "logs")
os.makedirs(log_dir, exist_ok=True)
setup_logging("INFO", os.path.join(log_dir, 'web_service.log'))

import logging
logger = logging.getLogger(__name__)

# 禁用 watchfiles 的 INFO 日志，避免循环打印
logging.getLogger('watchfiles').setLevel(logging.WARNING)
logging.getLogger('watchfiles.main').setLevel(logging.WARNING)

# 初始化数据库（多租户模式）
if Config.is_multi_tenant_mode():
    try:
        from database import init_db
        init_db()
        logger.info(f"Multi-tenant mode: Database initialized at {Config.DATABASE_URL}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
else:
    logger.info("Single-user mode: Using global Notion configuration")

# Create FastAPI app
app = FastAPI(
    title="Bill Import Service",
    description="Upload and sync bills to Notion - Multi-tenant SaaS Platform",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory=os.path.join(web_service_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(web_service_dir, "templates"))

# Routes
from .routes import upload, auth, users, bills, admin, review
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/user", tags=["User"])
app.include_router(bills.router, prefix="/api/bills", tags=["Bills"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(review.router, prefix="/api/review", tags=["Review"])


# ==================== 页面鉴权辅助函数 ====================

def get_access_token_from_cookie(request: Request) -> Optional[str]:
    """从Cookie中获取access token。

    Args:
        request: FastAPI请求对象

    Returns:
        access token字符串，如果不存在返回None
    """
    return request.cookies.get("access_token")


def verify_page_auth(request: Request) -> Tuple[bool, Optional[dict]]:
    """验证页面的认证状态。

    检查Cookie中的access_token是否有效。

    Args:
        request: FastAPI请求对象

    Returns:
        (是否已认证, 用户信息字典)
    """
    if not Config.is_multi_tenant_mode():
        # 单用户模式不需要认证
        return True, None

    token = get_access_token_from_cookie(request)
    if not token:
        return False, None

    try:
        from auth import verify_access_token
        payload = verify_access_token(token)
        if payload:
            return True, payload
        return False, None
    except Exception as e:
        logger.error(f"Page auth verification error: {e}")
        return False, None


def require_page_auth(request: Request) -> Optional[dict]:
    """要求页面认证的依赖函数。

    如果未认证，抛出HTTPException重定向到登录页。

    Args:
        request: FastAPI请求对象

    Returns:
        用户信息payload

    Raises:
        HTTPException: 未认证时抛出302重定向
    """
    is_authenticated, payload = verify_page_auth(request)
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"}
        )
    return payload


# ==================== 公开页面路由（无需认证）====================

@app.get("/")
def home(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login")
def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register")
def register_page(request: Request):
    """注册页面"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/forgot-password")
def forgot_password_page(request: Request):
    """忘记密码页面"""
    return templates.TemplateResponse("forgot-password.html", {"request": request})


@app.get("/setup")
def setup_page(request: Request):
    """配置向导页面"""
    return templates.TemplateResponse("setup.html", {"request": request})


@app.get("/features")
def features_page(request: Request):
    """功能介绍页面"""
    return templates.TemplateResponse("features.html", {"request": request})


@app.get("/docs")
def docs_page(request: Request):
    """帮助文档页面"""
    return templates.TemplateResponse("docs.html", {"request": request})


@app.get("/terms")
def terms_page(request: Request):
    """服务条款页面"""
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/privacy")
def privacy_page(request: Request):
    """隐私政策页面"""
    return templates.TemplateResponse("privacy.html", {"request": request})


# ==================== 需要认证的页面路由 ====================

@app.get("/bill-management")
def bill_management(request: Request):
    """账单管理页面 - 需要认证"""
    try:
        require_page_auth(request)
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/login")
        raise
    return templates.TemplateResponse("bill_management.html", {"request": request})


@app.get("/history")
def history_page(request: Request):
    """导入历史页面 - 需要认证"""
    try:
        require_page_auth(request)
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/login")
        raise
    return templates.TemplateResponse("history.html", {"request": request})


@app.get("/settings")
def settings_page(request: Request):
    """用户设置页面 - 需要认证"""
    try:
        require_page_auth(request)
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/login")
        raise
    return templates.TemplateResponse("settings.html", {"request": request})


@app.get("/review")
def review_page(request: Request):
    """复盘管理页面 - 需要认证"""
    try:
        require_page_auth(request)
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/login")
        raise
    return templates.TemplateResponse("review.html", {"request": request})


# ==================== 管理员页面路由（需要管理员权限）====================

@app.get("/service-management")
def service_management(request: Request):
    """服务管理页面 - 需要管理员认证"""
    try:
        payload = require_page_auth(request)
        # TODO: 添加管理员权限检查
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/login")
        raise
    return templates.TemplateResponse("service_management.html", {"request": request})


@app.get("/log-management")
def log_management(request: Request):
    """日志管理页面 - 需要管理员认证"""
    try:
        payload = require_page_auth(request)
        # TODO: 添加管理员权限检查
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/login")
        raise
    return templates.TemplateResponse("log_management.html", {"request": request})


@app.get("/admin/users")
def admin_users_page(request: Request):
    """后台用户管理页面 - 需要管理员认证"""
    try:
        payload = require_page_auth(request)
        # TODO: 添加管理员权限检查
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/login")
        raise
    return templates.TemplateResponse("admin/users.html", {"request": request})


@app.get("/admin/users/form")
def admin_user_form_page(request: Request, mode: str = "create", user_id: int = None):
    """后台用户表单页面（创建/编辑用户） - 需要管理员认证"""
    try:
        payload = require_page_auth(request)
        # TODO: 添加管理员权限检查
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/login")
        raise
    return templates.TemplateResponse("admin/user-form.html", {
        "request": request,
        "mode": mode,
        "user_id": user_id
    })


@app.get("/admin/settings")
def admin_settings_page(request: Request):
    """后台系统设置页面 - 需要管理员认证"""
    try:
        payload = require_page_auth(request)
        # TODO: 添加管理员权限检查
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/login")
        raise
    return templates.TemplateResponse("admin/settings.html", {"request": request})


@app.get("/admin/audit-logs")
def admin_audit_logs_page(request: Request):
    """后台审计日志页面 - 需要管理员认证"""
    try:
        payload = require_page_auth(request)
        # TODO: 添加管理员权限检查
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/login")
        raise
    return templates.TemplateResponse("admin/audit_logs.html", {"request": request})


# ==================== 废弃的页面路由 ====================

@app.get("/workspace")
def workspace(request: Request):
    """财务工作空间 - 已废弃，重定向到首页"""
    return RedirectResponse(url="/")


if __name__ == "__main__":
    import uvicorn

    # 使用 reload_dirs 明确指定要监控的目录
    # 只监控源代码目录，避免监控 logs、uploads、data 等目录
    reload_dirs = [
        "web_service",  # 监控 web_service 目录（代码文件）
        ".",            # 监控根目录（但排除特定文件）
    ]

    # 排除特定目录和文件
    reload_excludes = [
        # 日志文件
        "*.log",
        "*.log.*",
        # 数据库文件
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        # 环境配置
        ".env",
        ".env.*",
        ".env.bk",
        # Python 缓存
        "__pycache__",
        "*.pyc",
        ".pytest_cache",
        # 上传文件目录
        "uploads/*",
        "web_service/uploads/*",
        "web_service/uploads/**",
        # 日志目录
        "logs/*",
        "logs/**",
        "web_service/logs/*",
        "web_service/logs/**",
        # 数据目录
        "data/*",
        "data/**",
        # 测试文件
        "test_*.py",
        "tests/*",
        # 文档和临时文件
        "*.tmp",
        "*.md",
        "*.txt",
    ]

    uvicorn.run(
        "web_service.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=reload_dirs,
        reload_excludes=reload_excludes,
        reload_delay=0.5  # 增加延迟到 0.5 秒，减少频繁检测
    )
