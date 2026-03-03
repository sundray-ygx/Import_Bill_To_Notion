# 邮箱账单自动导入功能 - 部署指南

本文档提供邮箱账单自动导入功能的完整部署指南，包括数据库迁移、环境配置、依赖安装和常见问题排查。

## 目录

1. [功能概述](#功能概述)
2. [部署前准备](#部署前准备)
3. [数据库迁移](#数据库迁移)
4. [环境配置](#环境配置)
5. [依赖安装](#依赖安装)
6. [服务启动](#服务启动)
7. [功能验证](#功能验证)
8. [常见问题](#常见问题)
9. [回滚方案](#回滚方案)

---

## 功能概述

邮箱账单自动导入功能允许系统自动从用户的邮箱中获取支付平台（支付宝、微信、银联）发送的账单邮件，并解析附件进行自动导入。

**核心功能**：
- ✅ 支持多邮箱配置（QQ邮箱、163邮箱、Gmail、Outlook、自定义IMAP）
- ✅ 自动检测账单邮件和附件
- ✅ 密码加密存储（Fernet对称加密）
- ✅ 定时自动检查（每小时/每天/每周）
- ✅ 手动触发检查
- ✅ 邮件去重（基于Message-ID）
- ✅ 用户数据隔离

**新增文件**：
```
src/services/email_service.py          # IMAP连接管理
src/services/email_parse_service.py   # 邮件解析
src/services/email_import_source.py   # 邮箱账单导入源
src/utils/crypto.py                   # 密码加密工具
web_service/routes/email.py           # 邮箱配置API
migrate_database.py                   # 数据库迁移（v3）
```

---

## 部署前准备

### 1. 系统要求

- **操作系统**: Linux/macOS/Windows
- **Python版本**: Python 3.8+ （推荐 3.12+）
- **数据库**: SQLite 3.0+
- **内存**: 最低 512MB，推荐 1GB+
- **磁盘**: 最低 100MB 可用空间

### 2. 依赖检查

```bash
# 检查 Python 版本
python3 --version

# 检查 pip 版本
pip3 --version

# 检查 SQLite 支持
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
```

### 3. 备份数据

**重要**: 在进行数据库迁移前，请备份现有数据！

```bash
# 备份数据库文件
cp data/database.sqlite data/database.sqlite.backup.$(date +%Y%m%d_%H%M%S)

# 备份配置文件
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
```

---

## 数据库迁移

### 步骤 1: 停止服务

```bash
# 如果服务正在运行，先停止
pkill -f "python3 -m web_service.main"
# 或使用 systemd
sudo systemctl stop bill-import
```

### 步骤 2: 检查当前数据库版本

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('data/database.sqlite')
cursor = conn.cursor()
cursor.execute('PRAGMA user_version')
version = cursor.fetchone()[0]
print(f'当前数据库版本: {version}')
conn.close()
"
```

### 步骤 3: 执行迁移

```bash
# 执行数据库迁移脚本
python3 migrate_database.py

# 预期输出：
# ===== 数据库迁移工具 =====
# 当前数据库版本: 2
# 数据库已迁移到版本 3
# ✓ 创建了 user_email_configs 表
# ✓ 创建了 email_processing_history 表
# ✓ 添加了索引
# 迁移完成！
```

### 步骤 4: 验证迁移

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('data/database.sqlite')
cursor = conn.cursor()

# 检查新表是否存在
cursor.execute(\"\"\"
    SELECT name FROM sqlite_master
    WHERE type='table' AND name IN ('user_email_configs', 'email_processing_history')
    \"\"\")
tables = cursor.fetchall()
print(f'新表: {[t[0] for t in tables]}')

# 检查索引
cursor.execute(\"\"\"
    SELECT name FROM sqlite_master
    WHERE type='index' AND tbl_name='user_email_configs'
    \"\"\")
indexes = cursor.fetchall()
print(f'索引数量: {len(indexes)}')

conn.close()
"
```

### 步骤 5: 设置迁移标记

```bash
# 如果迁移脚本没有自动更新版本号，手动设置
python3 -c "
import sqlite3
conn = sqlite3.connect('data/database.sqlite')
cursor = conn.cursor()
cursor.execute('PRAGMA user_version = 3')
conn.commit()
print('数据库版本已设置为 3')
conn.close()
"
```

---

## 环境配置

### 1. 生成密码加密密钥

**重要**: 此密钥用于加密邮箱密码，丢失后无法解密已保存的密码！

```bash
# 生成加密密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 示例输出:
# XKr7nN8vV9yZ2mK4pL6qR8sT0uW2xY4z
```

### 2. 更新 .env 文件

在 `.env` 文件中添加以下配置：

```bash
# ==================== 邮箱账单自动导入配置 ====================

# 密码加密密钥（必填，使用上面生成的密钥）
PASSWORD_ENCRYPTION_KEY=XKr7nN8vV9yZ2mK4pL6qR8sT0uW2xY4z

# 邮箱检查超时时间（秒）
EMAIL_CHECK_TIMEOUT=10

# 单次邮件最大附件数量
EMAIL_MAX_ATTACHMENTS=5

# 单个附件最大大小（字节，默认10MB）
EMAIL_MAX_ATTACHMENT_SIZE=10485760

# 邮件检查间隔（小时）
EMAIL_CHECK_INTERVAL_HOURLY=1
EMAIL_CHECK_INTERVAL_DAILY=24
EMAIL_CHECK_INTERVAL_WEEKLY=168
```

### 3. 验证配置

```bash
# 验证环境变量已设置
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
required_vars = ['PASSWORD_ENCRYPTION_KEY', 'SECRET_KEY', 'DATABASE_URL']
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f'✓ {var}: {"*"*10 if \"KEY\" in var or \"PASSWORD\" in var else value}')
    else:
        print(f'✗ {var}: 未设置')
"
```

---

## 依赖安装

### 1. 更新 requirements.txt

确保 `requirements.txt` 包含以下依赖：

```
# 邮箱账单自动导入新增依赖
imap-tools>=0.51.0
cryptography>=41.0.0
beautifulsoup4>=4.12.0
```

### 2. 安装依赖

```bash
# 使用 pip 安装
pip3 install -r requirements.txt

# 或使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. 验证安装

```bash
python3 -c "
from imap_tools import MailBox
from cryptography.fernet import Fernet
from bs4 import BeautifulSoup
print('✓ 所有依赖已安装')
print(f'  - imap-tools: {MailBox.__module__}')
print(f'  - cryptography: {Fernet.__module__}')
print(f'  - beautifulsoup4: {BeautifulSoup.__module__}')
"
```

---

## 服务启动

### 1. 测试启动

```bash
# 以测试模式启动（前台运行）
python3 -m web_service.main

# 预期输出：
# ===== Notion Bill Importer =====
# 应用版本: 2.2.0
# 数据库版本: 3
# 邮箱功能: 已启用
#
# 🚀 服务启动成功！
# 📍 访问地址: http://localhost:8000
# 📚 API文档: http://localhost:8000/docs
# ⏰ 定时任务: 已启用
```

### 2. 生产模式启动

#### 使用 systemd（推荐）

创建服务文件 `/etc/systemd/system/bill-import.service`：

```ini
[Unit]
Description=Notion Bill Importer with Email Support
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Import_Bill_To_Notion
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m web_service.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable bill-import

# 启动服务
sudo systemctl start bill-import

# 查看状态
sudo systemctl status bill-import

# 查看日志
sudo journalctl -u bill-import -f
```

#### 使用 supervisor

创建配置文件 `/etc/supervisor/conf.d/bill-import.conf`：

```ini
[program:bill-import]
command=/path/to/venv/bin/python -m web_service.main
directory=/path/to/Import_Bill_To_Notion
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/bill-import.err.log
stdout_logfile=/var/log/bill-import.out.log
```

启动服务：

```bash
# 重载配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动服务
sudo supervisorctl start bill-import

# 查看状态
sudo supervisorctl status bill-import
```

---

## 功能验证

### 1. API 端点测试

```bash
# 获取邮箱服务商模板
curl -X GET "http://localhost:8000/api/email/providers" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 预期响应：
{
  "providers": [
    {
      "provider": "qq",
      "name": "QQ邮箱",
      "imap_server": "imap.qq.com",
      "imap_port": 993,
      "use_ssl": true,
      "description": "QQ邮箱需要开启IMAP服务..."
    },
    ...
  ]
}
```

### 2. 前端界面验证

1. 访问 http://localhost:8000
2. 登录系统
3. 进入"设置"页面
4. 点击"邮箱配置"选项卡
5. 验证以下功能：
   - ✅ 邮箱服务商选择
   - ✅ 配置表单显示
   - ✅ 密码加密存储
   - ✅ 连接验证功能

### 3. 邮件检查测试

```bash
# 手动触发邮件检查
curl -X POST "http://localhost:8000/api/email/check" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"config_id": 1}'

# 预期响应：
{
  "success": true,
  "message": "邮箱检查完成，共处理 X 个账单",
  "checked_configs": 1,
  "total_imported": Y,
  "total_failed": Z,
  "details": []
}
```

### 4. 日志检查

```bash
# 查看最新日志
tail -f web_service/logs/web_service.log

# 预期日志内容：
# [INFO] 2026-03-02 10:00:00 - Checking email for config_id=1
# [INFO] 2026-03-02 10:00:05 - Found 2 new emails
# [INFO] 2026-03-02 10:00:10 - Imported 1 bill, skipped 1, failed 0
```

---

## 常见问题

### 问题 1: 数据库迁移失败

**症状**: 迁移脚本执行失败或报错

**解决方案**:
```bash
# 1. 检查数据库文件权限
ls -la data/database.sqlite

# 2. 确保数据库未被锁定
lsof data/database.sqlite

# 3. 手动执行迁移 SQL
sqlite3 data/database.sqlite < migrations/v3_email_tables.sql
```

### 问题 2: 密钥配置错误

**症状**: 启动时报错 `PASSWORD_ENCRYPTION_KEY not set`

**解决方案**:
```bash
# 1. 确认 .env 文件存在
ls -la .env

# 2. 检查环境变量
grep PASSWORD_ENCRYPTION_KEY .env

# 3. 重启服务使配置生效
sudo systemctl restart bill-import
```

### 问题 3: IMAP 连接失败

**症状**: 邮箱验证失败，提示"连接超时"或"认证失败"

**解决方案**:
```bash
# 1. 检查网络连接
telnet imap.qq.com 993

# 2. 验证邮箱设置
#    - QQ邮箱: 需要开启IMAP服务并使用授权码
#    - 163邮箱: 需要开启IMAP服务并设置授权码
#    - Gmail: 需要使用应用专用密码

# 3. 测试 IMAP 连接
python3 -c "
from imap_tools import MailBox
with MailBox('imap.qq.com', 993).login('your@qq.com', 'your_password') as mailbox:
    print('✓ 连接成功')
"
```

### 问题 4: 附件解析失败

**症状**: 邮件已获取但未导入账单

**解决方案**:
```bash
# 1. 检查附件类型
#    目前支持: .csv, .zip

# 2. 查看详细日志
tail -100 web_service/logs/web_service.log | grep "email"

# 3. 手动测试解析
python3 -c "
from src.services.email_parse_service import EmailParseService
# 测试邮件解析逻辑
"
```

### 问题 5: 定时任务不执行

**症状**: 定时邮件检查未运行

**解决方案**:
```bash
# 1. 检查调度器状态
curl -X GET "http://localhost:8000/api/scheduler/status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 验证 cron 表达式
#    每小时: 0 * * * *
#    每天: 0 0 * * *
#    每周: 0 0 * * 0

# 3. 手动触发检查
python3 -c "
from src.scheduler import BillScheduler
scheduler = BillScheduler()
scheduler._check_email()
"
```

---

## 回滚方案

### 1. 数据库回滚

```bash
# 1. 停止服务
sudo systemctl stop bill-import

# 2. 恢复数据库备份
cp data/database.sqlite.backup.YYYYMMDD_HHMMSS data/database.sqlite

# 3. 重置版本号
python3 -c "
import sqlite3
conn = sqlite3.connect('data/database.sqlite')
cursor = conn.cursor()
cursor.execute('PRAGMA user_version = 2')
conn.commit()
print('数据库已回滚到版本 2')
conn.close()
"

# 4. 重启服务
sudo systemctl start bill-import
```

### 2. 代码回滚

```bash
# 1. 切换到迁移前的 commit
git log --oneline -10
git checkout <previous-commit-hash>

# 2. 重新安装依赖
pip install -r requirements.txt

# 3. 重启服务
sudo systemctl restart bill-import
```

### 3. 配置回滚

```bash
# 恢复 .env 备份
cp .env.backup.YYYYMMDD_HHMMSS .env

# 重启服务
sudo systemctl restart bill-import
```

---

## 监控和维护

### 1. 日志监控

```bash
# 实时查看日志
tail -f web_service/logs/web_service.log

# 查看错误日志
grep "ERROR" web_service/logs/web_service.log

# 查看邮箱相关日志
grep "email" web_service/logs/web_service.log
```

### 2. 性能监控

```bash
# 检查服务状态
curl -X GET "http://localhost:8000/api/health"

# 检查数据库大小
du -h data/database.sqlite

# 检查邮件处理历史
python3 -c "
import sqlite3
conn = sqlite3.connect('data/database.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM email_processing_history')
count = cursor.fetchone()[0]
print(f'已处理邮件: {count}')
conn.close()
"
```

### 3. 定期维护

```bash
# 每周任务
# 1. 清理旧日志
find web_service/logs/ -name "*.log" -mtime +30 -delete

# 2. 优化数据库
sqlite3 data/database.sqlite "VACUUM;"

# 3. 备份数据
./scripts/backup.sh
```

---

## 附录

### A. 支持的邮箱服务商

| 服务商 | IMAP服务器 | 端口 | SSL | 特殊要求 |
|-------|----------|------|-----|---------|
| QQ邮箱 | imap.qq.com | 993 | 是 | 需要授权码 |
| 163邮箱 | imap.163.com | 993 | 是 | 需要授权码 |
| Gmail | imap.gmail.com | 993 | 是 | 需要应用专用密码 |
| Outlook | outlook.office365.com | 993 | 是 | 使用登录密码 |

### B. 环境变量完整列表

```bash
# 必填项
PASSWORD_ENCRYPTION_KEY=xxx     # 密码加密密钥
SECRET_KEY=xxx                  # JWT密钥
DATABASE_URL=xxx                # 数据库路径

# 可选项
EMAIL_CHECK_TIMEOUT=10          # 邮箱检查超时（秒）
EMAIL_MAX_ATTACHMENTS=5         # 最大附件数
EMAIL_MAX_ATTACHMENT_SIZE=10485760  # 最大附件大小（字节）
```

### C. 故障排查命令速查

```bash
# 检查服务状态
sudo systemctl status bill-import

# 查看日志
sudo journalctl -u bill-import -n 50

# 测试数据库
python3 -c "import sqlite3; conn = sqlite3.connect('data/database.sqlite'); print(conn.execute('PRAGMA user_version').fetchone())"

# 测试IMAP连接
python3 -c "from imap_tools import MailBox; print('OK' if MailBox('imap.qq.com', 993) else 'FAIL')"

# 检查端口
netstat -tuln | grep 8000
```

---

**文档版本**: 1.0.0
**更新日期**: 2026-03-02
**适用版本**: v2.2.0+
