"""FastAPI web service for bill import."""

import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
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
from .routes import upload, auth, users, bills, admin
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/user", tags=["User"])
app.include_router(bills.router, prefix="/api/bills", tags=["Bills"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/bill-management")
def bill_management(request: Request):
    return templates.TemplateResponse("bill_management.html", {"request": request})


@app.get("/service-management")
def service_management(request: Request):
    return templates.TemplateResponse("service_management.html", {"request": request})


@app.get("/log-management")
def log_management(request: Request):
    return templates.TemplateResponse("log_management.html", {"request": request})


@app.get("/login")
def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register")
def register_page(request: Request):
    """注册页面"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/settings")
def settings_page(request: Request):
    """用户设置页面"""
    return templates.TemplateResponse("settings.html", {"request": request})


@app.get("/history")
def history_page(request: Request):
    """导入历史页面"""
    return templates.TemplateResponse("history.html", {"request": request})


@app.get("/admin/users")
def admin_users_page(request: Request):
    """后台用户管理页面"""
    return templates.TemplateResponse("admin/users.html", {"request": request})


@app.get("/admin/users/form")
def admin_user_form_page(request: Request, mode: str = "create", user_id: int = None):
    """后台用户表单页面（创建/编辑用户）"""
    return templates.TemplateResponse("admin/user-form.html", {
        "request": request,
        "mode": mode,
        "user_id": user_id
    })


@app.get("/admin/settings")
def admin_settings_page(request: Request):
    """后台系统设置页面"""
    return templates.TemplateResponse("admin/settings.html", {"request": request})


@app.get("/admin/audit-logs")
def admin_audit_logs_page(request: Request):
    """后台审计日志页面"""
    return templates.TemplateResponse("admin/audit_logs.html", {"request": request})


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


@app.get("/forgot-password")
def forgot_password_page(request: Request):
    """忘记密码页面"""
    return templates.TemplateResponse("forgot-password.html", {"request": request})


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
