# API索引

本文档提供 Import_Bill_To_Notion 项目的完整 API 端点索引。

## 目录

- [认证API](#认证api)
- [用户API](#用户api)
- [账单上传API](#账单上传api)
- [账单历史API](#账单历史api)
- [复盘API](#复盘api)
- [管理员API](#管理员api)
- [响应格式](#响应格式)

---

## 认证API

### POST /api/auth/register

注册新用户。

**请求体**:
```json
{
  "username": "string (3-50字符)",
  "email": "valid@email.com",
  "password": "string (至少8位，含大小写字母和数字)"
}
```

**响应** (201 Created):
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "username": "string",
    "email": "valid@email.com",
    "is_superuser": false,
    "is_active": true,
    "require_password_change": false,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": null
  }
}
```

**错误响应**:
- 400: 用户名已存在 / 邮箱已存在 / 密码强度不足
- 403: 注册已禁用

**代码位置**: `web_service/routes/auth.py`

---

### POST /api/auth/login

用户登录。

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应** (200 OK):
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 900,
  "user": { ... }
}
```

**错误响应**:
- 401: 用户名或密码错误 / 账户被锁定

**代码位置**: `web_service/routes/auth.py`

---

### POST /api/auth/logout

用户登出。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

**代码位置**: `web_service/routes/auth.py`

---

### POST /api/auth/refresh

刷新访问令牌。

**请求体**:
```json
{
  "refresh_token": "string"
}
```

**响应** (200 OK):
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 900
}
```

**错误响应**:
- 401: 无效的刷新令牌

**代码位置**: `web_service/routes/auth.py`

---

### POST /api/auth/change-password

修改密码。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

**响应** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

**错误响应**:
- 400: 当前密码错误 / 新密码强度不足

**代码位置**: `web_service/routes/auth.py`

---

## 用户API

### GET /api/user/me

获取当前用户信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "id": 1,
  "username": "string",
  "email": "valid@email.com",
  "is_superuser": false,
  "is_active": true,
  "require_password_change": false,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z",
  "total_uploads": 10,
  "total_imports": 10,
  "notion_configured": true,
  "session_timeout_minutes": 15
}
```

**代码位置**: `web_service/routes/users.py`

---

### PATCH /api/user/me

更新当前用户信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "email": "new@email.com",
  "session_timeout_minutes": 30
}
```

**响应** (200 OK):
```json
{
  "id": 1,
  "username": "string",
  "email": "new@email.com",
  ...
}
```

**代码位置**: `web_service/routes/users.py`

---

### GET /api/user/notion-config

获取当前用户的Notion配置。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "id": 1,
  "user_id": 1,
  "notion_api_key": "secret_***",
  "notion_income_database_id": "abc123...",
  "notion_expense_database_id": "def456...",
  "config_name": "默认配置",
  "is_verified": true,
  "last_verified_at": "2024-01-01T00:00:00Z",
  "notion_monthly_review_db": "...",
  "notion_quarterly_review_db": "...",
  "notion_yearly_review_db": "...",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**代码位置**: `web_service/routes/users.py`

---

### POST /api/user/notion-config

创建或更新Notion配置。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "notion_api_key": "secret_...",
  "notion_income_database_id": "32字符ID",
  "notion_expense_database_id": "32字符ID",
  "config_name": "我的配置"
}
```

**响应** (200 OK):
```json
{
  "id": 1,
  "user_id": 1,
  ...
}
```

**代码位置**: `web_service/routes/users.py`

---

### GET /api/user/notion-config/verify-step

分步验证Notion配置。

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `step`: `api_key` | `income_db` | `expense_db`

**响应** (200 OK):
```json
{
  "step": "income_db",
  "status": "success",
  "message": "收入数据库验证成功",
  "details": {
    "title": "我的收入数据库",
    "id": "abc123..."
  },
  "error": null
}
```

**代码位置**: `web_service/routes/users.py`

---

### GET /api/user/notion-config/verify-all

验证所有Notion配置。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "current_step": 3,
  "total_steps": 3,
  "steps": [
    {
      "step": "api_key",
      "status": "success",
      "message": "API密钥验证成功",
      "details": { "name": "集成名称" },
      "error": null
    },
    ...
  ],
  "is_complete": true,
  "all_success": true
}
```

**代码位置**: `web_service/routes/users.py`

---

## 账单上传API

### POST /api/upload

上传账单文件并导入。

**请求头**:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**表单数据**:
- `file`: 账单文件（CSV/TXT/XLS/XLSX）
- `platform`: 支付平台（可选）: `alipay` | `wechat` | `unionpay` | `auto`
- `sync_type`: 同步类型: `immediate` | `scheduled`

**响应** (200 OK):
```json
{
  "success": true,
  "message": "File uploaded and import started",
  "file_path": "/path/to/file.csv",
  "import_result": {
    "success": true,
    "detected_platform": "WeChatPay",
    "total_records": 150,
    "imported": 148,
    "updated": 0,
    "skipped": 2
  }
}
```

**错误响应**:
- 400: 文件格式不支持 / 文件过大
- 401: 未认证

**代码位置**: `web_service/routes/upload.py`

---

### GET /api/files

获取已上传的文件列表。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "files": [
    {
      "name": "bill_202401.csv",
      "size": 12345,
      "upload_time": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**代码位置**: `web_service/routes/upload.py`

---

### GET /api/file/{file_name}/content

获取文件内容预览。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "file_name": "bill.csv",
  "file_type": "CSV",
  "columns": ["交易时间", "交易类型", "金额"],
  "data": [
    {"交易时间": "2024-01-01 10:00", "交易类型": "餐饮", "金额": "35.00"},
    ...
  ]
}
```

**代码位置**: `web_service/routes/upload.py`

---

### DELETE /api/file/{file_name}

删除已上传的文件。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "success": true,
  "message": "File deleted"
}
```

**代码位置**: `web_service/routes/upload.py`

---

### GET /api/service-info

获取服务信息。

**响应** (200 OK):
```json
{
  "start_time": "2024-01-01 00:00:00",
  "uptime": "1天 5小时 30分钟",
  "uptime_seconds": 111600,
  "version": "1.0.0",
  "python_version": "3.10.0",
  "memory_usage": "125.50 MB",
  "stats": {
    "total_uploads": 100,
    "success_imports": 95,
    "failed_imports": 5
  }
}
```

**代码位置**: `web_service/routes/upload.py`

---

### GET /api/logs

获取服务日志。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
[
  {
    "level": "INFO",
    "time": "2024-01-01 12:00:00",
    "message": "Import completed successfully"
  },
  ...
]
```

**代码位置**: `web_service/routes/upload.py`

---

## 账单历史API

### GET /api/bills/history

获取导入历史记录。

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `status`: 状态过滤 (`success` | `partial` | `failed`)

**响应** (200 OK):
```json
{
  "history": [
    {
      "id": 1,
      "upload_id": 10,
      "file_name": "bill_202401.csv",
      "original_file_name": "alipay_bill.csv",
      "platform": "Alipay",
      "total_records": 150,
      "imported_records": 148,
      "skipped_records": 2,
      "failed_records": 0,
      "status": "success",
      "error_message": null,
      "started_at": "2024-01-01T10:00:00Z",
      "completed_at": "2024-01-01T10:01:30Z",
      "duration_seconds": 90
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

**代码位置**: `web_service/routes/bills.py`

---

### GET /api/bills/history/{history_id}

获取单条历史记录详情。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "id": 1,
  ...
}
```

**错误响应**:
- 404: 记录不存在

**代码位置**: `web_service/routes/bills.py`

---

## 复盘API

### GET /api/review/config

获取复盘配置。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "monthly_review_db": "abc123...",
  "quarterly_review_db": "def456...",
  "yearly_review_db": "ghi789...",
  "monthly_template_id": "...",
  "quarterly_template_id": "...",
  "yearly_template_id": "..."
}
```

**代码位置**: `web_service/routes/review.py`

---

### POST /api/review/config

更新复盘配置。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "monthly_review_db": "abc123...",
  "quarterly_review_db": "def456...",
  "yearly_review_db": "ghi789...",
  "monthly_template_id": "...",
  "quarterly_template_id": "...",
  "yearly_template_id": "..."
}
```

**响应** (200 OK):
```json
{
  "message": "Review configuration updated"
}
```

**代码位置**: `web_service/routes/review.py`

---

### GET /api/review/preview

预览复盘数据。

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `type`: `monthly` | `quarterly` | `yearly`
- `year`: 年份（如：2024）
- `month`: 月份（1-12，月度复盘必需）
- `quarter`: 季度（1-4，季度复盘必需）

**响应** (200 OK):
```json
{
  "period": "2024-01",
  "summary": {
    "total_income": 15000.00,
    "total_expense": 8500.00,
    "net_balance": 6500.00,
    "transaction_count": 120
  },
  "categories": {
    "餐饮": {"income": 0, "expense": 1200.00},
    "交通": {"income": 0, "expense": 500.00}
  },
  "transactions_count": 120
}
```

**代码位置**: `web_service/routes/review.py`

---

### POST /api/review/generate

生成复盘报告。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "type": "monthly",
  "year": 2024,
  "month": 1
}
```

或

```json
{
  "type": "quarterly",
  "year": 2024,
  "quarter": 1
}
```

或

```json
{
  "type": "yearly",
  "year": 2024
}
```

**响应** (200 OK):
```json
{
  "success": true,
  "period": "2024-01",
  "page_id": "abc123...",
  "page_url": "https://www.notion.so/abc123",
  "data": { ... }
}
```

**错误响应**:
- 400: 复盘数据库未配置
- 500: 生成失败

**代码位置**: `web_service/routes/review.py`

---

## 管理员API

> 所有管理员API需要超级用户权限。

### GET /api/admin/users

获取所有用户列表。

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `search`: 搜索关键词

**响应** (200 OK):
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "is_superuser": true,
      "is_active": true,
      "require_password_change": false,
      "created_at": "2024-01-01T00:00:00Z",
      "last_login": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

**代码位置**: `web_service/routes/admin.py`

---

### POST /api/admin/users

创建新用户。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "Password123",
  "is_superuser": false,
  "is_active": true
}
```

**响应** (201 Created):
```json
{
  "id": 2,
  "username": "newuser",
  ...
}
```

**代码位置**: `web_service/routes/admin.py`

---

### PATCH /api/admin/users/{user_id}

更新用户信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "email": "newemail@example.com",
  "is_superuser": false,
  "is_active": true
}
```

**响应** (200 OK):
```json
{
  "id": 1,
  ...
}
```

**代码位置**: `web_service/routes/admin.py`

---

### DELETE /api/admin/users/{user_id}

删除用户。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "message": "User deleted successfully"
}
```

**代码位置**: `web_service/routes/admin.py`

---

### POST /api/admin/users/{user_id}/reset-password

重置用户密码。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "new_password": "NewPassword123"
}
```

**响应** (200 OK):
```json
{
  "message": "Password reset successfully",
  "new_password": "NewPassword123"
}
```

**代码位置**: `web_service/routes/admin.py`

---

### GET /api/admin/stats

获取系统统计信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "total_users": 50,
  "active_users": 45,
  "total_uploads": 500,
  "total_imports": 480,
  "success_rate": 96.0,
  "uploads_today": 10,
  "imports_today": 9
}
```

**代码位置**: `web_service/routes/admin.py`

---

### GET /api/admin/audit-logs

获取审计日志。

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `page`: 页码
- `page_size`: 每页数量
- `user_id`: 用户过滤
- `action`: 操作类型过滤

**响应** (200 OK):
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "username": "admin",
      "action": "login",
      "resource_type": null,
      "resource_id": null,
      "ip_address": "127.0.0.1",
      "details": null,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

**代码位置**: `web_service/routes/admin.py`

---

### GET /api/admin/settings

获取系统设置。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应** (200 OK):
```json
{
  "registration_enabled": true,
  "max_file_size": 52428800,
  "allowed_file_types": [".csv", ".txt", ".xls", ".xlsx"],
  "session_timeout_minutes": 15,
  "max_login_attempts": 5,
  "lockout_duration_minutes": 30
}
```

**代码位置**: `web_service/routes/admin.py`

---

### PATCH /api/admin/settings

更新系统设置。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "registration_enabled": false,
  "max_file_size": 104857600,
  "session_timeout_minutes": 30
}
```

**响应** (200 OK):
```json
{
  "message": "Settings updated successfully"
}
```

**代码位置**: `web_service/routes/admin.py`

---

## 响应格式

### 成功响应

```json
{
  "data": { ... }
}
```

或直接返回数据对象。

### 错误响应

```json
{
  "detail": "错误描述信息"
}
```

或

```json
{
  "detail": "错误描述信息",
  "error_code": "ERROR_CODE"
}
```

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | OK - 请求成功 |
| 201 | Created - 资源创建成功 |
| 400 | Bad Request - 请求参数错误 |
| 401 | Unauthorized - 未认证 |
| 403 | Forbidden - 无权限 |
| 404 | Not Found - 资源不存在 |
| 422 | Unprocessable Entity - 数据验证失败 |
| 500 | Internal Server Error - 服务器错误 |

---

## 相关文档

- [技术知识库/数据结构](./数据结构.md) - 请求/响应数据结构
- [技术知识库/排障指南](./排障指南.md) - API错误排查
- [业务知识库/业务流程索引](../业务知识库/业务流程索引.md) - 业务流程说明
