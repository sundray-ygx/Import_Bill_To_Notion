# 多租户账单导入系统 API 参考文档

## 目录

- [概述](#概述)
- [认证](#认证)
- [认证接口](#认证接口)
- [用户接口](#用户接口)
- [账单接口](#账单接口)
- [管理员接口](#管理员接口)
- [数据模型](#数据模型)
- [错误码](#错误码)

## 概述

API 基础 URL：`http://your-domain.com/api`

所有 API 请求和响应使用 JSON 格式。

## 认证

### JWT Token 认证

API 使用 JWT Bearer Token 认证。在请求头中包含：

```
Authorization: Bearer <access_token>
```

### Token 类型

1. **Access Token**：短期有效（默认 15 分钟），用于 API 访问
2. **Refresh Token**：长期有效（默认 7 天），用于获取新的 Access Token

### 获取 Token

通过登录接口获取：

```bash
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=<username>&password=<password>
```

响应：
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  }
}
```

---

## 认证接口

### 1. 用户注册

创建新用户账户。

**端点**：`POST /api/auth/register`

**请求体**：
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "Password123!"
}
```

**响应**：`200 OK`
```json
{
  "id": 2,
  "username": "newuser",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-15T10:30:00"
}
```

**错误**：`400 Bad Request`
```json
{
  "detail": "Username already exists"
}
```

**密码要求**：
- 至少 8 个字符
- 包含大写字母
- 包含小写字母
- 包含数字

### 2. 用户登录

使用用户名和密码登录，获取访问令牌。

**端点**：`POST /api/auth/login`

**请求体**：`application/x-www-form-urlencoded`
```
username=<username>&password=<password>
```

**响应**：`200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_active": true,
    "is_superuser": false
  }
}
```

**错误**：`401 Unauthorized`
```json
{
  "detail": "Incorrect username or password"
}
```

### 3. 用户登出

撤销当前用户的所有会话。

**端点**：`POST /api/auth/logout`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### 4. 刷新 Token

使用 Refresh Token 获取新的 Access Token。

**端点**：`POST /api/auth/refresh`

**请求体**：
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**响应**：`200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

**错误**：`401 Unauthorized`
```json
{
  "detail": "Invalid refresh token"
}
```

### 5. 获取当前用户信息

获取当前登录用户的详细信息。

**端点**：`GET /api/auth/me`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：`200 OK`
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-15T10:00:00",
  "last_login": "2025-01-15T14:30:00"
}
```

### 6. 修改密码

修改当前用户的密码。

**端点**：`POST /api/auth/change-password`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Password changed successfully. Please login again."
}
```

---

## 用户接口

### 1. 获取 Notion 配置

获取当前用户的 Notion 配置。

**端点**：`GET /api/user/notion-config`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：`200 OK`
```json
{
  "id": 1,
  "config_name": "默认配置",
  "notion_api_key": "secret_***",
  "notion_income_database_id": "abc123...",
  "notion_expense_database_id": "def456...",
  "is_verified": true,
  "last_verified_at": "2025-01-15T12:00:00",
  "created_at": "2025-01-15T10:00:00"
}
```

### 2. 创建/更新 Notion 配置

创建或更新 Notion 配置。

**端点**：`POST /api/user/notion-config`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```json
{
  "notion_api_key": "secret_...",
  "notion_income_database_id": "abc123...",
  "notion_expense_database_id": "def456...",
  "config_name": "我的配置"
}
```

**响应**：`200 OK`
```json
{
  "id": 1,
  "config_name": "我的配置",
  "is_verified": false
}
```

### 3. 验证 Notion 配置

验证 Notion API 密钥和数据库 ID 是否有效。

**端点**：`POST /api/user/notion-config/verify`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```json
{
  "notion_api_key": "secret_...",
  "notion_income_database_id": "abc123...",
  "notion_expense_database_id": "def456..."
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Notion configuration is valid"
}
```

### 4. 获取用户资料

获取当前用户的详细资料。

**端点**：`GET /api/user/profile`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：`200 OK`
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  },
  "stats": {
    "total_uploads": 10,
    "total_imports": 150
  }
}
```

### 5. 更新用户资料

更新当前用户的资料。

**端点**：`PUT /api/user/profile`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```json
{
  "email": "newemail@example.com"
}
```

**响应**：`200 OK`
```json
{
  "id": 1,
  "username": "admin",
  "email": "newemail@example.com"
}
```

---

## 账单接口

### 1. 上传账单文件

上传并处理账单文件。

**端点**：`POST /api/bills/upload`

**请求头**：
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**请求体**：
```
file: <binary file data>
platform: alipay | wechat | unionpay | auto
```

**响应**：`200 OK`
```json
{
  "upload_id": 123,
  "file_name": "alipay_record.csv",
  "platform": "alipay",
  "status": "processing",
  "created_at": "2025-01-15T15:00:00"
}
```

### 2. 获取上传列表

获取当前用户的文件上传列表。

**端点**：`GET /api/bills/uploads`

**请求头**：
```
Authorization: Bearer <access_token>
```

**查询参数**：
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 20）

**响应**：`200 OK`
```json
{
  "files": [
    {
      "id": 123,
      "file_name": "alipay_record.csv",
      "platform": "alipay",
      "status": "success",
      "created_at": "2025-01-15T15:00:00"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

### 3. 获取上传详情

获取指定上传的详细信息。

**端点**：`GET /api/bills/uploads/{upload_id}`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：`200 OK`
```json
{
  "id": 123,
  "file_name": "alipay_record.csv",
  "platform": "alipay",
  "status": "success",
  "total_records": 100,
  "imported_records": 95,
  "failed_records": 0,
  "created_at": "2025-01-15T15:00:00"
}
```

### 4. 删除上传

删除指定的上传记录和文件。

**端点**：`DELETE /api/bills/uploads/{upload_id}`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Upload deleted successfully"
}
```

### 5. 获取导入历史

获取当前用户的导入历史记录。

**端点**：`GET /api/bills/history`

**请求头**：
```
Authorization: Bearer <access_token>
```

**查询参数**：
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 10）

**响应**：`200 OK`
```json
{
  "history": [
    {
      "id": 456,
      "file_name": "alipay_record.csv",
      "platform": "alipay",
      "status": "success",
      "total_records": 100,
      "imported_records": 95,
      "started_at": "2025-01-15T15:00:00",
      "completed_at": "2025-01-15T15:01:30",
      "duration_seconds": 90
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 10
}
```

### 6. 获取导入统计

获取当前用户的导入统计数据。

**端点**：`GET /api/bills/history/stats`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：`200 OK`
```json
{
  "total": 45,
  "successful": 42,
  "failed": 2,
  "pending": 1,
  "total_records": 4500,
  "imported_records": 4350,
  "avg_duration": 85
}
```

---

## 管理员接口

*需要超级管理员权限*

### 1. 获取系统统计

获取系统级别的统计数据。

**端点**：`GET /api/admin/stats`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：`200 OK`
```json
{
  "total_users": 25,
  "active_users": 20,
  "uploads_today": 15,
  "total_uploads": 500
}
```

### 2. 获取用户列表

获取所有用户的列表。

**端点**：`GET /api/admin/users`

**请求头**：
```
Authorization: Bearer <access_token>
```

**查询参数**：
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 20）
- `search`: 搜索关键词（用户名或邮箱）
- `is_active`: 过滤活跃状态（true/false）
- `is_superuser`: 过滤管理员状态（true/false）

**响应**：`200 OK`
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "is_active": true,
      "is_superuser": true,
      "created_at": "2025-01-01T00:00:00",
      "last_login": "2025-01-15T15:00:00"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20
}
```

### 3. 获取用户详情

获取指定用户的详细信息。

**端点**：`GET /api/admin/users/{user_id}`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：`200 OK`
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_active": true,
    "is_superuser": true
  },
  "stats": {
    "total_uploads": 10,
    "total_imports": 150
  },
  "notion_configured": true
}
```

### 4. 创建用户

创建新用户。

**端点**：`POST /api/admin/users`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "Password123!",
  "is_superuser": false,
  "is_active": true
}
```

**响应**：`200 OK`
```json
{
  "id": 26,
  "username": "newuser",
  "email": "newuser@example.com",
  "is_active": true,
  "is_superuser": false
}
```

### 5. 更新用户

更新指定用户的信息。

**端点**：`PUT /api/admin/users/{user_id}`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```json
{
  "email": "updated@example.com",
  "is_active": false,
  "is_superuser": false
}
```

**响应**：`200 OK`
```json
{
  "id": 1,
  "username": "admin",
  "email": "updated@example.com",
  "is_active": false
}
```

### 6. 删除用户

删除指定用户。

**端点**：`DELETE /api/admin/users/{user_id}`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

### 7. 重置用户密码

重置指定用户的密码。

**端点**：`POST /api/admin/users/{user_id}/reset-password`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```json
{
  "new_password": "NewPassword123!"
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

### 8. 获取审计日志

获取系统审计日志。

**端点**：`GET /api/admin/audit-logs`

**请求头**：
```
Authorization: Bearer <access_token>
```

**查询参数**：
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 50）
- `action`: 操作类型过滤
- `user_id`: 用户 ID 过滤

**响应**：`200 OK`
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "username": "admin",
      "action": "user_created",
      "resource_type": "user",
      "ip_address": "192.168.1.1",
      "created_at": "2025-01-15T15:00:00"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50
}
```

### 9. 获取系统设置

获取系统配置。

**端点**：`GET /api/admin/settings`

**请求头**：
```
Authorization: Bearer <access_token>
```

**响应**：`200 OK`
```json
{
  "registration_enabled": true,
  "session_timeout_minutes": 15,
  "max_login_attempts": 5,
  "lockout_duration_minutes": 30
}
```

### 10. 更新系统设置

更新系统配置。

**端点**：`PUT /api/admin/settings`

**请求头**：
```
Authorization: Bearer <access_token>
```

**请求体**：
```json
{
  "registration_enabled": false,
  "session_timeout_minutes": 30
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Settings updated successfully"
}
```

---

## 配置向导接口

### 1. 检查是否需要初始化

检查系统是否需要初始化设置。

**端点**：`GET /api/auth/setup/check`

**响应**：`200 OK`
```json
{
  "needs_setup": true,
  "user_count": 0
}
```

### 2. 检查用户名是否可用

检查用户名是否已被使用。

**端点**：`POST /api/auth/setup/check-username`

**请求体**：
```json
{
  "username": "newuser"
}
```

**响应**：`200 OK`
```json
{
  "exists": false
}
```

### 3. 创建初始管理员

创建第一个管理员账户（仅在没有用户时可用）。

**端点**：`POST /api/auth/setup/create-admin`

**请求体**：
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "password": "AdminPassword123!",
  "settings": {
    "allow_registration": true,
    "session_timeout": 15,
    "max_login_attempts": 5
  }
}
```

**响应**：`200 OK`
```json
{
  "success": true,
  "message": "Admin user created successfully",
  "username": "admin"
}
```

---

## 数据模型

### User（用户）

```typescript
{
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;  // ISO 8601 日期时间
  updated_at: string;  // ISO 8601 日期时间
  last_login?: string;
  login_attempts: number;
  locked_until?: string;
}
```

### UserSession（用户会话）

```typescript
{
  id: number;
  user_id: number;
  token: string;
  refresh_token: string;
  expires_at: string;
  created_at: string;
  ip_address?: string;
  user_agent?: string;
  is_revoked: boolean;
}
```

### UserNotionConfig（Notion 配置）

```typescript
{
  id: number;
  user_id: number;
  notion_api_key: string;
  notion_income_database_id: string;
  notion_expense_database_id: string;
  config_name: string;
  is_verified: boolean;
  last_verified_at?: string;
  created_at: string;
  updated_at: string;
}
```

### UserUpload（用户上传）

```typescript
{
  id: number;
  user_id: number;
  file_name: string;
  original_file_name: string;
  file_path: string;
  file_size: number;
  platform: 'alipay' | 'wechat' | 'unionpay';
  upload_type: 'immediate' | 'scheduled';
  status: 'pending' | 'processing' | 'success' | 'failed';
  created_at: string;
}
```

### ImportHistory（导入历史）

```typescript
{
  id: number;
  user_id: number;
  upload_id?: number;
  total_records: number;
  imported_records: number;
  skipped_records: number;
  failed_records: number;
  status: 'pending' | 'success' | 'failed';
  error_message?: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
}
```

---

## 错误码

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（Token 无效或过期） |
| 403 | 禁止访问（权限不足） |
| 404 | 资源不存在 |
| 422 | 验证错误 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误信息

| 错误信息 | 说明 |
|----------|------|
| `Incorrect username or password` | 用户名或密码错误 |
| `Username already exists` | 用户名已存在 |
| `Email already exists` | 邮箱已存在 |
| `Invalid refresh token` | Refresh Token 无效或过期 |
| `User not found or inactive` | 用户不存在或未激活 |
| `Password is too weak` | 密码强度不足 |
| `Registration is currently disabled` | 注册功能已禁用 |
| `Account is temporarily locked` | 账户已被临时锁定 |

---

## 速率限制

为防止滥用，API 实施以下速率限制：

| 端点类型 | 限制 |
|----------|------|
| 登录 | 每 5 分钟 10 次 |
| 注册 | 每 1 小时 5 次 |
| 上传 | 每 1 分钟 10 次 |
| 其他 API | 每 1 分钟 100 次 |

超出限制时返回 `429 Too Many Requests`。

---

## 版本管理

当前 API 版本：`v2.0.0`

API 遵循语义化版本控制。重大变更会在次版本号更新时注明。
