# 邮箱配置保存功能修复指南

## 问题描述

用户在设置页面填写邮箱配置并点击"保存配置"时，显示"保存配置失败"错误。

## 根本原因

邮箱配置功能需要使用 `PasswordEncryption` 类来加密邮箱密码后存储到数据库。该类在初始化时要求 `PASSWORD_ENCRYPTION_KEY` 环境变量必须存在。

由于项目中缺少 `.env` 文件（只有 `.env.example` 示例文件），导致密码加密服务无法初始化，从而使整个保存流程中断。

## 诊断过程

### 错误堆栈

```
ValueError: PASSWORD_ENCRYPTION_KEY not set
  at src/utils/crypto.py:42
  at web_service/routes/email.py:106 (create_email_config)
```

### 数据流分析

1. 前端收集表单数据 → POST /api/email/config
2. 后端验证请求体 (Pydantic EmailConfigCreate schema) → ✓ 通过
3. 尝试创建 PasswordEncryption 实例 → ✗ 失败
4. 返回 HTTP 500 错误 → 前端显示"保存配置失败"

## 解决方案

### 快速修复（推荐）

使用提供的自动化脚本生成 `.env` 文件：

```bash
# 1. 生成 .env 文件（包含安全的随机密钥）
python3 scripts/setup_env.py

# 2. 测试配置
./scripts/test_email_config.sh

# 3. 启动服务
./scripts/start.sh
```

### 手动修复

1. **创建 .env 文件**：
```bash
cp .env.example .env
```

2. **生成安全密钥**：
```bash
# 生成 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# 生成 PASSWORD_ENCRYPTION_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. **编辑 .env 文件**，添加生成的密钥：
```bash
# 多租户模式配置
MULTI_TENANT_ENABLED=true
SECRET_KEY=<生成的48字符密钥>
PASSWORD_ENCRYPTION_KEY=<生成的32字符密钥>
DATABASE_URL=sqlite:///data/database.sqlite

# 单用户模式Notion配置（可选）
NOTION_API_KEY=your_notion_api_key
NOTION_INCOME_DATABASE_ID=your_income_db_id
NOTION_EXPENSE_DATABASE_ID=your_expense_db_id
```

4. **重启服务**：
```bash
python3 -m web_service.main
```

## 代码改进

### 1. 增强错误提示 (`crypto.py`)

修改了 `PasswordEncryption` 类的初始化方法，提供更详细的错误信息：

```python
if not self.master_key:
    raise ValueError(
        "PASSWORD_ENCRYPTION_KEY not set. Please add this environment variable "
        "to your .env file. Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
```

### 2. 添加错误处理 (`email.py`)

在创建和更新邮箱配置的路由中添加了 try-except 块：

```python
try:
    crypto = PasswordEncryption()
    password_encrypted = crypto.encrypt(config_data.password)
    logger.info(f"Password encrypted successfully for user {current_user.id}")
except ValueError as e:
    logger.error(f"Password encryption failed for user {current_user.id}: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"密码加密失败：{str(e)}。请检查服务器配置。"
    )
```

### 3. 前端错误提示优化 (`settings.js`)

添加了针对密码加密错误的特殊处理：

```javascript
if (errorMsg.includes('PASSWORD_ENCRYPTION_KEY') || errorMsg.includes('密码加密')) {
    showToast('服务器配置错误：缺少密码加密密钥', 'error');
    setTimeout(() => {
        alert('服务器配置错误\n\n请联系管理员配置以下环境变量：\n- PASSWORD_ENCRYPTION_KEY');
    }, 500);
}
```

## 验证步骤

1. **环境配置测试**：
```bash
./scripts/test_email_config.sh
```

2. **功能测试**：
   - 登录系统
   - 进入"设置" → "邮箱配置"
   - 点击"添加邮箱"
   - 填写表单并提交
   - 验证配置是否成功保存

3. **日志验证**：
```bash
tail -f web_service/logs/web_service.log | grep -i "email\|encryption"
```

预期看到：
```
INFO - Password encrypted successfully for user X
INFO - User X created email config Y
```

## 预防措施

### 1. 环境检查

使用提供的 `start.sh` 启动脚本，会在启动前自动检查环境配置：

```bash
./scripts/start.sh
```

### 2. 配置验证

添加了 `scripts/test_email_config.sh` 测试脚本，可随时验证配置正确性。

### 3. 文档更新

- 更新了 `.env.example` 文件，添加了 `PASSWORD_ENCRYPTION_KEY` 的详细说明
- 创建了本修复指南文档
- 添加了自动化配置脚本

## 安全建议

1. **密钥管理**：
   - 永远不要将 `.env` 文件提交到版本控制系统
   - 生产环境使用强随机密钥
   - 定期轮换密钥（使用 `PasswordEncryption.rotate_key()` 方法）

2. **文件权限**：
   ```bash
   chmod 600 .env  # 仅所有者可读写
   ```

3. **备份**：
   - 定期备份 `.env` 文件到安全位置
   - 记录密钥生成时间和轮换计划

## 相关文件

### 修改的文件
- `src/utils/crypto.py` - 增强错误提示
- `web_service/routes/email.py` - 添加错误处理和日志
- `web_service/static/js/settings.js` - 优化前端错误提示

### 新增的文件
- `scripts/setup_env.py` - 自动生成 .env 文件
- `scripts/start.sh` - 启动检查脚本
- `scripts/test_email_config.sh` - 配置测试脚本
- `docs/EMAIL_CONFIG_FIX.md` - 本文档

## 技术细节

### 密码加密机制

项目使用 Fernet 对称加密（AES-128-CBC + HMAC-SHA256）：

1. **密钥派生**：
   - 从 `PASSWORD_ENCRYPTION_KEY` 通过 PBKDF2-HMAC-SHA256 派生32字节密钥
   - 使用固定盐值 `notion_bill_importer`
   - 100,000 次迭代以增加暴力破解难度

2. **加密流程**：
   ```
   明文密码 → Fernet.encrypt() → Base64编码 → 存储到数据库
   ```

3. **解密流程**：
   ```
   数据库 → Base64解码 → Fernet.decrypt() → 明文密码
   ```

### 数据库架构

```sql
CREATE TABLE user_email_configs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    password_encrypted VARCHAR(500) NOT NULL,  -- 加密存储
    imap_server VARCHAR(255) NOT NULL,
    imap_port INTEGER NOT NULL,
    use_ssl BOOLEAN NOT NULL,
    provider VARCHAR(50),
    config_name VARCHAR(100),
    is_active BOOLEAN NOT NULL,
    is_verified BOOLEAN NOT NULL,
    last_check_at DATETIME,
    last_check_status VARCHAR(20),
    check_frequency VARCHAR(20),
    next_check_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);
```

## 故障排查

### 问题：保存后仍显示失败

1. 检查服务是否重启：
```bash
ps aux | grep "web_service.main"
```

2. 查看详细日志：
```bash
tail -50 web_service/logs/web_service.log
```

3. 验证环境变量：
```bash
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('PASSWORD_ENCRYPTION_KEY'))"
```

### 问题：密码解密失败

可能原因：
- 密钥已更改（需要重新加密所有密码）
- 数据库损坏（需要从备份恢复）

解决方案：
```python
# 使用 rotate_key() 方法重新加密
from src.utils.crypto import PasswordEncryption
crypto = PasswordEncryption()
new_encrypted = crypto.rotate_key(old_encrypted, new_master_key)
```

## 联系支持

如果问题仍未解决，请提供以下信息：

1. 系统环境：
   ```bash
   python3 --version
   pip list | grep -E "cryptography|fastapi|pydantic"
   ```

2. 日志文件：
   ```bash
   tail -100 web_service/logs/web_service.log > debug.log
   ```

3. 错误详情：
   - 前端控制台错误
   - 浏览器 Network 标签中的请求/响应
   - 完整的错误堆栈

---

**文档版本**: 1.0
**更新日期**: 2026-03-02
**维护者**: Development Team
