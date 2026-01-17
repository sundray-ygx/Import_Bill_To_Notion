# 多租户账单导入系统部署文档

## 目录

- [系统概述](#系统概述)
- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [配置说明](#配置说明)
- [运行服务](#运行服务)
- [生产部署](#生产部署)
- [故障排除](#故障排除)

## 系统概述

多租户账单导入服务是一个基于 FastAPI 的 Web 应用，支持多个用户独立管理各自的 Notion 账单数据库。

### 核心功能

- **用户认证**：JWT Token 认证，支持用户注册、登录、登出
- **数据隔离**：每个用户的数据完全隔离，包括上传文件、导入记录、Notion 配置
- **后台管理**：超级管理员可以管理用户和系统设置
- **多平台支持**：支持支付宝、微信支付、银联账单导入
- **配置向导**：首次启动时通过向导完成系统初始化

### 技术栈

- **后端**：FastAPI + SQLAlchemy + SQLite
- **认证**：JWT (PyJWT) + BCrypt 密码加密
- **前端**：原生 JavaScript + Jinja2 模板
- **数据库**：SQLite（可扩展为 PostgreSQL）

## 环境要求

### 系统要求

- **操作系统**：Linux / macOS / Windows
- **Python 版本**：Python 3.8 或更高版本
- **内存**：至少 512MB RAM
- **磁盘空间**：至少 100MB 可用空间

### Python 依赖

```
fastapi>=0.68.0
uvicorn[standard]>=0.15.0
sqlalchemy>=1.4.0
pyjwt>=2.1.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.5
python-dotenv>=0.19.0
pandas>=1.3.0
notion-client>=0.8.0
```

## 安装步骤

### 1. 克隆代码

```bash
cd /path/to/your/project
git clone <repository-url>
cd Import_Bill_To_Notion
```

### 2. 创建虚拟环境

```bash
# 使用 venv
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 使用 conda
conda create -n bill-import python=3.8
conda activate bill-import
```

### 3. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装 Web 服务依赖
pip install -r web_service/requirements.txt
```

### 4. 创建环境配置文件

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# ==================== 多租户配置 ====================
# 启用多租户模式：true/false/auto
# auto 模式会自动检测是否存在数据库文件
MULTI_TENANT_ENABLED=auto

# ==================== 数据库配置 ====================
# SQLite 数据库文件路径（相对于项目根目录）
DATABASE_URL=sqlite:///data/database.sqlite

# ==================== JWT 配置 ====================
# JWT 密钥（生产环境请使用强随机字符串）
SECRET_KEY=your-secret-key-here-change-in-production
# Access Token 过期时间（分钟）
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
# Refresh Token 过期时间（天）
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ==================== 安全配置 ====================
# 会话超时时间（分钟）
SESSION_TIMEOUT_MINUTES=15
# 最大登录尝试次数
MAX_LOGIN_ATTEMPTS=5
# 账户锁定时间（分钟）
LOCKOUT_DURATION_MINUTES=30

# ==================== 文件上传配置 ====================
# 最大文件大小（字节）
MAX_FILE_SIZE=52428800
# 允许的文件类型
ALLOWED_FILE_TYPES=.csv,.txt,.xls,.xlsx
# 上传目录
UPLOAD_DIR=./uploads

# ==================== 用户注册配置 ====================
# 是否允许新用户注册
REGISTRATION_ENABLED=true

# ==================== 单用户模式配置（可选） ====================
# 如果要在单用户模式下使用，配置以下项
NOTION_API_KEY=your_notion_api_key
NOTION_INCOME_DATABASE_ID=your_income_db_id
NOTION_EXPENSE_DATABASE_ID=your_expense_db_id

# ==================== 日志配置 ====================
# 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

### 5. 创建必要的目录

```bash
# 创建数据目录
mkdir -p data

# 创建上传目录
mkdir -p uploads

# 创建日志目录
mkdir -p web_service/logs
```

## 配置说明

### 多租户模式 vs 单用户模式

#### 单用户模式

适用于个人使用，直接使用全局配置的 Notion API。

**配置**：
```bash
MULTI_TENANT_ENABLED=false
NOTION_API_KEY=your_notion_api_key
NOTION_INCOME_DATABASE_ID=your_income_db_id
NOTION_EXPENSE_DATABASE_ID=your_expense_db_id
```

#### 多租户模式

适用于多个用户，每个用户配置自己的 Notion 数据库。

**配置**：
```bash
MULTI_TENANT_ENABLED=true
DATABASE_URL=sqlite:///data/database.sqlite
SECRET_KEY=your-secret-key
```

### 自动模式（推荐）

```bash
MULTI_TENANT_ENABLED=auto
```

- 如果数据库文件存在，使用多租户模式
- 如果数据库文件不存在，使用单用户模式（需要配置环境变量中的 Notion 凭据）

## 运行服务

### 开发模式

```bash
# 启动 Web 服务（自动重载）
python3 -m web_service.main
```

服务将在 `http://localhost:8000` 启动。

### 生产模式

```bash
# 使用 uvicorn 启动
uvicorn web_service.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 使用 systemd（Linux）

创建服务文件 `/etc/systemd/system/bill-import.service`：

```ini
[Unit]
Description=Bill Import Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/Import_Bill_To_Notion
Environment="PATH=/path/to/Import_Bill_To_Notion/venv/bin"
ExecStart=/path/to/Import_Bill_To_Notion/venv/bin/uvicorn web_service.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用和启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable bill-import
sudo systemctl start bill-import
sudo systemctl status bill-import
```

### 使用 Docker

创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r web_service/requirements.txt

# 创建必要的目录
RUN mkdir -p data uploads web_service/logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "web_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  bill-import:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./web_service/logs:/app/web_service/logs
    environment:
      - MULTI_TENANT_ENABLED=auto
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=sqlite:///data/database.sqlite
    restart: unless-stopped
```

运行：

```bash
docker-compose up -d
```

## 生产部署

### 安全建议

1. **使用强随机 SECRET_KEY**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **使用 HTTPS**
   - 使用 Nginx 或 Caddy 作为反向代理
   - 配置 SSL 证书（Let's Encrypt）

3. **限制 CORS**
   - 在生产环境中限制 `allow_origins`

4. **定期备份数据库**
   ```bash
   # 备份 SQLite 数据库
   cp data/database.sqlite data/database.sqlite.backup.$(date +%Y%m%d)
   ```

5. **监控日志**
   - 定期检查 `web_service/logs/web_service.log`
   - 设置日志轮转

### Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/Import_Bill_To_Notion/web_service/static;
    }

    client_max_body_size 50M;
}
```

### 性能优化

1. **使用 PostgreSQL**（大量用户时）
   ```bash
   pip install psycopg2-binary
   ```

   修改 `DATABASE_URL`：
   ```
   DATABASE_URL=postgresql://user:password@localhost/bill_import
   ```

2. **配置缓存**
   - 使用 Redis 缓存用户会话
   - 配置 CDN 加载静态资源

3. **数据库连接池**
   - 在 `database.py` 中配置连接池参数

## 故障排除

### 常见问题

#### 1. 数据库初始化失败

**错误**：`OperationalError: unable to open database file`

**解决方案**：
```bash
# 确保数据目录存在
mkdir -p data

# 检查文件权限
chmod 755 data
```

#### 2. JWT Token 验证失败

**错误**：`Could not validate credentials`

**解决方案**：
- 检查 `SECRET_KEY` 是否配置正确
- 确保 Token 未过期
- 清除浏览器 localStorage 中的旧 Token

#### 3. 文件上传失败

**错误**：`File too large`

**解决方案**：
- 检查 `MAX_FILE_SIZE` 配置
- 检查 Nginx `client_max_body_size` 配置

#### 4. Notion API 错误

**错误**：`Unauthorized` 或 `Object not found`

**解决方案**：
- 验证 Notion API Key 是否有效
- 确认数据库 ID 正确
- 检查集成权限是否正确配置

### 日志查看

```bash
# 查看 Web 服务日志
tail -f web_service/logs/web_service.log

# 查看系统日志
journalctl -u bill-import -f
```

### 数据库维护

```bash
# SQLite 数据库完整性检查
sqlite3 data/database.sqlite "PRAGMA integrity_check;"

# 创建数据库备份
sqlite3 data/database.sqlite ".backup data/database.sqlite.backup"
```

## 更新升级

### 备份数据

```bash
# 备份数据库
cp data/database.sqlite data/database.sqlite.backup

# 备份上传文件
tar -czf uploads-backup.tar.gz uploads/
```

### 更新代码

```bash
# 拉取最新代码
git pull origin main

# 安装新依赖
pip install -r requirements.txt
pip install -r web_service/requirements.txt

# 重启服务
sudo systemctl restart bill-import
```

### 数据库迁移

如果有数据库结构变更，运行迁移脚本：

```bash
python3 -m database.migrations
```

## 支持与帮助

- 查看日志：`web_service/logs/web_service.log`
- GitHub Issues：[项目地址]
- 文档：`docs/` 目录

## 许可证

本项目采用 MIT 许可证。
