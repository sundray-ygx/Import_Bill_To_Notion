# Exploration Agent - 代码库探索阶段

## 执行时间
2025-01-23

## 项目结构分析

### 核心模块
- **config.py**: 配置管理，支持单用户和多租户模式
- **notion_api.py**: Notion API 客户端，支持多用户
- **importer.py**: 账单导入核心逻辑
- **parsers/**: 账单解析器（支付宝、微信、银联）
- **auth.py**: 认证模块
- **database.py**: 数据库连接管理
- **models.py**: SQLAlchemy ORM 模型
- **schemas.py**: Pydantic 数据验证模型

### Web 服务
- **web_service/main.py**: FastAPI 主入口
- **web_service/routes/**: API 路由
  - auth.py: 认证路由
  - users.py: 用户路由
  - bills.py: 账单路由
  - admin.py: 管理员路由
  - upload.py: 上传路由

## 可复用组件

### Notion API 客户端
- **类**: NotionClient
- **方法**: create_page(), batch_import(), verify_connection()
- **复用方式**: 扩展支持复盘数据库读写

### 配置管理
- **类**: Config
- **方法**: is_single_user_mode(), is_multi_tenant_mode()
- **复用方式**: 添加复盘数据库配置

### 多租户支持
- **模型**: User, UserNotionConfig
- **复用方式**: 添加复盘配置到用户配置

## 集成点

### 1. 数据库扩展
在 UserNotionConfig 表中添加复盘数据库 ID 字段

### 2. Notion API 扩展
在 NotionClient 类中添加复盘数据读写方法

### 3. 新增模块
创建 review_service.py 提供复盘功能

### 4. API 路由
在 web_service/routes/ 下创建 review.py

## 技术债务
无重大技术债务，代码结构清晰，易于扩展
