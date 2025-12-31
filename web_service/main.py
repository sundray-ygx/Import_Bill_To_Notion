import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 获取web_service目录的绝对路径
web_service_dir = os.path.dirname(os.path.abspath(__file__))

# 加载环境变量
load_dotenv()

# 配置日志
log_dir = os.path.join(web_service_dir, "logs")
# 确保logs目录存在
os.makedirs(log_dir, exist_ok=True)

# 设置日志时区为北京时间
import datetime

# 创建一个Formatter，使用北京时间
class BeijingFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # 获取UTC时间，然后转换为北京时间（UTC+8）
        dt = datetime.datetime.utcfromtimestamp(record.created) + datetime.timedelta(hours=8)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

# 配置日志，使用北京时间
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, 'web_service.log'), encoding='utf-8')
    ]
)

# 重新配置日志处理器，使用北京时间
for handler in logging.getLogger().handlers:
    handler.setFormatter(BeijingFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="账单导入服务",
    description="提供账单上传和同步到Notion的服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件目录
static_dir = os.path.join(web_service_dir, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 配置模板目录
templates_dir = os.path.join(web_service_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

# 导入路由
from .routes import upload

# 注册路由
app.include_router(upload.router, prefix="/api", tags=["upload"])

# 首页路由
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 账单管理页面路由
@app.get("/bill-management")
def bill_management(request: Request):
    return templates.TemplateResponse("bill_management.html", {"request": request})

# 服务管理页面路由
@app.get("/service-management")
def service_management(request: Request):
    return templates.TemplateResponse("service_management.html", {"request": request})

# 日志管理页面路由
@app.get("/log-management")
def log_management(request: Request):
    return templates.TemplateResponse("log_management.html", {"request": request})

# 主函数
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web_service.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None
    )
