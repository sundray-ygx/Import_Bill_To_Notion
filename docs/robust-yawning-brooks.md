# 多租户账单导入系统实施计划

## 需求概述

将现有的单用户账单导入系统扩展为多租户SaaS平台，支持：
1. 用户注册、登录认证（JWT Token）
2. 每个用户绑定独立的Notion数据库
3. 用户数据隔离（上传文件、导入记录）
4. 后台管理模块（超级管理员）
5. UI/UX优化（扁平化设计 + 卡片式布局 + 增强玻璃态）
6. 保持向后兼容单用户模式

## 用户确认的设计决策

| 决策项 | 选择 |
|--------|------|
| 认证方式 | JWT Token |
| 单用户兼容 | 是，保持兼容 |
| 管理员初始化 | 配置向导 |
| UI风格 | 扁平化 + 卡片式 + 增强玻璃态 |

---

## 数据库设计

### SQLite数据库文件位置
```
/mnt/hgfs/code/share/python/Import_Bill_To_Notion/data/
├── database.sqlite          # 主数据库
└── database.sqlite-shm      # WAL共享内存文件
```

### 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_superuser BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    require_password_change BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL
);

-- 用户会话表
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_revoked BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 用户Notion配置表
CREATE TABLE user_notion_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    notion_api_key VARCHAR(255) NOT NULL,
    notion_income_database_id VARCHAR(100) NOT NULL,
    notion_expense_database_id VARCHAR(100) NOT NULL,
    config_name VARCHAR(100) DEFAULT '默认配置',
    is_verified BOOLEAN DEFAULT 0,
    last_verified_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 用户上传记录表
CREATE TABLE user_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    original_file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    platform VARCHAR(20) NOT NULL,
    upload_type VARCHAR(20) DEFAULT 'immediate',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 导入历史表
CREATE TABLE import_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    upload_id INTEGER,
    total_records INTEGER NOT NULL,
    imported_records INTEGER DEFAULT 0,
    skipped_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    duration_seconds INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (upload_id) REFERENCES user_uploads(id) ON DELETE SET NULL
);

-- 系统设置表
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    updated_by INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 审计日志表
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    ip_address VARCHAR(45),
    user_agent TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
```

### 文件存储结构
```
web_service/uploads/
├── {user_id}/
│   ├── {upload_id}/
│   │   ├── original/
│   │   │   └── {timestamp}_{original_filename}
│   │   └── processed/
│   │       └── {timestamp}_{original_filename}.json
│   └── temp/
│       └── {temp_id}/
```

---

## 分阶段实施计划

### 阶段1：数据库和认证基础设施

**新建文件：**
- `database.py` - SQLite初始化、Session管理
- `models.py` - SQLAlchemy ORM模型
- `schemas.py` - Pydantic验证schemas
- `auth.py` - JWT认证、密码加密
- `dependencies.py` - FastAPI依赖注入

**修改文件：**
- `config.py` - 添加多租户配置项
- `requirements.txt` - 添加新依赖

**关键代码要点：**

```python
# config.py - 模式检测
class Config:
    # 原有配置
    NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
    NOTION_INCOME_DATABASE_ID = os.getenv("NOTION_INCOME_DATABASE_ID", "")
    NOTION_EXPENSE_DATABASE_ID = os.getenv("NOTION_EXPENSE_DATABASE_ID", "")

    # 新增配置
    MULTI_TENANT_ENABLED = os.getenv("MULTI_TENANT_ENABLED", "auto")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/database.sqlite")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))

    @classmethod
    def is_single_user_mode(cls):
        """检测是否为单用户模式"""
        if cls.MULTI_TENANT_ENABLED == "false":
            return True
        if cls.MULTI_TENANT_ENABLED == "true":
            return False
        # auto模式：检测是否有多租户数据库
        return not os.path.exists("data/database.sqlite")

# notion_api.py - 支持多用户
class NotionClient:
    def __init__(self, user_id=None):
        self.user_id = user_id

        if Config.is_single_user_mode():
            # 单用户模式：使用全局配置
            self.client = NotionApiClient(auth=Config.NOTION_API_KEY)
            self.income_db = Config.NOTION_INCOME_DATABASE_ID
            self.expense_db = Config.NOTION_EXPENSE_DATABASE_ID
        else:
            # 多用户模式：从数据库获取配置
            if not user_id:
                raise ValueError("user_id is required in multi-tenant mode")
            config = self._get_user_notion_config(user_id)
            self.client = NotionApiClient(auth=config.notion_api_key)
            self.income_db = config.notion_income_database_id
            self.expense_db = config.notion_expense_database_id
```

---

### 阶段2：认证API开发

**新建文件：**
- `web_service/routes/auth.py` - 注册、登录、登出、刷新token

**修改文件：**
- `web_service/main.py` - 注册auth路由

**API端点：**
```
POST /api/auth/register  - 用户注册
POST /api/auth/login     - 用户登录
POST /api/auth/logout    - 用户登出
POST /api/auth/refresh   - 刷新access token
GET  /api/auth/me        - 获取当前用户信息
```

---

### 阶段3：用户配置管理API

**新建文件：**
- `web_service/routes/users.py` - 用户配置管理

**API端点：**
```
GET  /api/user/notion-config         - 获取Notion配置
POST /api/user/notion-config         - 创建/更新Notion配置
POST /api/user/notion-config/verify  - 验证Notion配置
GET  /api/user/profile               - 获取用户资料
PUT  /api/user/profile               - 更新用户资料
POST /api/user/change-password       - 修改密码
```

---

### 阶段4：文件上传API改造

**修改文件：**
- `web_service/services/file_service.py` - 支持用户文件隔离
- `web_service/routes/upload.py` - 添加认证，记录用户上传

**新建文件：**
- `web_service/routes/bills.py` - 账单管理路由

**API端点（需认证）：**
```
POST /api/bills/upload              - 上传账单
GET  /api/bills/uploads             - 获取上传列表
GET  /api/bills/uploads/{id}        - 获取上传详情
GET  /api/bills/uploads/{id}/preview - 预览文件
DELETE /api/bills/uploads/{id}      - 删除上传
GET  /api/bills/history             - 获取导入历史
```

---

### 阶段5：前端认证界面

**新建文件：**
- `web_service/templates/login.html` - 登录页面
- `web_service/templates/register.html` - 注册页面
- `web_service/static/css/auth.css` - 认证页面样式
- `web_service/static/js/auth.js` - 认证通用逻辑
- `web_service/static/js/login.js` - 登录逻辑
- `web_service/static/js/register.js` - 注册逻辑

**UI风格：**
- 左右分栏布局（品牌信息 + 表单）
- 扁平化设计 + 卡片式布局
- 增强玻璃态效果
- 密码强度实时指示

---

### 阶段6：导航栏和布局改造

**新建文件：**
- `web_service/templates/components/navbar.html` - 导航栏组件
- `web_service/static/js/navbar.js` - 导航栏交互

**修改文件：**
- `web_service/templates/*.html` - 所有页面使用新导航栏
- `web_service/static/css/style.css` - 更新全局样式

**导航栏特性：**
- 根据登录状态显示不同内容
- 用户下拉菜单（个人资料、设置、登出）
- 超级管理员专属入口
- 移动端响应式

---

### 阶段7：用户设置页面

**新建文件：**
- `web_service/templates/settings.html` - 用户设置页面
- `web_service/static/css/settings.css` - 设置页面样式
- `web_service/static/js/settings.js` - 设置页面逻辑

**页面结构：**
- 侧边栏导航（个人资料、安全设置、Notion配置）
- 个人资料编辑
- 密码修改
- Notion配置管理

---

### 阶段8：后台管理界面

**新建文件：**
- `web_service/routes/admin.py` - 后台管理API
- `web_service/templates/admin/users.html` - 用户管理
- `web_service/templates/admin/settings.html` - 系统设置
- `web_service/templates/admin/audit_logs.html` - 审计日志
- `web_service/static/css/admin.css` - 后台样式
- `web_service/static/js/admin-users.js` - 用户管理逻辑

**API端点（需超级管理员）：**
```
GET    /api/admin/users           - 用户列表
POST   /api/admin/users           - 创建用户
PUT    /api/admin/users/{id}      - 更新用户
DELETE /api/admin/users/{id}      - 删除用户
POST   /api/admin/users/{id}/reset-password - 重置密码
GET    /api/admin/stats           - 系统统计
GET    /api/admin/audit-logs      - 审计日志
GET    /api/admin/settings        - 系统设置
PUT    /api/admin/settings        - 更新设置
```

---

### 阶段9：配置向导（首次启动）

**新建文件：**
- `web_service/templates/setup.html` - 配置向导页面
- `web_service/static/js/setup.js` - 向导逻辑

**向导流程：**
1. 检测是否为首次启动（无数据库）
2. 设置超级管理员账户
3. 配置系统设置（可选）
4. 完成初始化

---

### 阶段10：性能优化

**优化内容：**
- CSS模块化和变量管理
- JavaScript防抖、节流
- API请求缓存
- 图片懒加载
- 资源预加载

---

### 阶段11：测试和文档

**新建文件：**
- `tests/test_auth.py` - 认证测试
- `tests/test_api.py` - API测试
- `tests/test_multi_tenant.py` - 多租户测试
- `docs/MULTI_TENANT_SETUP.md` - 部署文档
- `docs/API_REFERENCE.md` - API文档

---

## 关键文件清单

### 需要新建的文件
1. `database.py` - 数据库管理
2. `models.py` - ORM模型
3. `schemas.py` - Pydantic schemas
4. `auth.py` - 认证逻辑
5. `dependencies.py` - FastAPI依赖
6. `web_service/routes/auth.py` - 认证路由
7. `web_service/routes/users.py` - 用户路由
8. `web_service/routes/admin.py` - 管理路由
9. `web_service/services/user_file_service.py` - 用户文件服务

### 需要修改的文件
1. `config.py` - 添加多租户配置
2. `notion_api.py` - 支持多用户
3. `importer.py` - 传递user_id
4. `web_service/main.py` - 注册新路由
5. `web_service/routes/upload.py` - 添加认证
6. `requirements.txt` - 新依赖

### 前端文件
1. `login.html`, `register.html`, `setup.html`
2. `settings.html`
3. `admin/users.html`, `admin/settings.html`, `admin/audit_logs.html`
4. `components/navbar.html`
5. `auth.css`, `settings.css`, `admin.css`
6. `auth.js`, `login.js`, `register.js`, `navbar.js`, `settings.js`, `admin-users.js`, `setup.js`

---

## 验收标准

### 功能验收
- [ ] 用户可以注册和登录
- [ ] 用户可以配置自己的Notion数据库
- [ ] 用户上传的文件存储在独立目录
- [ ] 用户只能看到自己的上传记录
- [ ] 超级管理员可以管理所有用户
- [ ] 单用户模式向后兼容

### 性能验收
- [ ] 页面首次加载 < 2秒
- [ ] API响应时间 < 500ms
- [ ] 文件上传进度实时显示

### 安全验收
- [ ] 密码使用bcrypt加密
- [ ] JWT token正确验证
- [ ] API权限控制正确
- [ ] 敏感日志脱敏

---

## 实施顺序

1. **阶段1-2**：基础设施 + 认证（5-7天）
2. **阶段3-4**：用户配置 + 文件上传改造（4-6天）
3. **阶段5-6**：前端认证界面 + 导航栏（5-7天）
4. **阶段7-8**：用户设置 + 后台管理（6-8天）
5. **阶段9**：配置向导（2-3天）
6. **阶段10-11**：优化 + 测试文档（4-6天）

**总计：26-37天**
