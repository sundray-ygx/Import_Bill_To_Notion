# Notion账单导入服务

一个功能完善的账单导入服务，支持多用户认证、管理后台和账单历史记录。自动将支付宝、微信支付和银联账单导入到Notion数据库。

## 功能特性

### 核心功能
- ✅ 支持多种支付平台账单导入
  - 支付宝账单
  - 微信支付账单
  - 银联账单
- ✅ 自动检测账单格式，无需手动选择平台
- ✅ 支持立即导入和定时自动导入两种模式
- ✅ **根据收/支分类自动导入到不同数据库**
  - 收入记录导入到收入数据库
  - 支出记录导入到支出数据库
  - 支持自定义数据库ID配置
- ✅ **智能过滤"不计收支"记录**，只同步有效交易
- ✅ **用户认证系统**
  - 用户注册和登录
  - 密码加密存储
  - JWT会话管理
  - 密码找回功能
- ✅ **多用户支持**
  - 每个用户独立的数据隔离
  - 个性化的Notion配置
  - 用户级别的文件管理
- ✅ **管理后台**
  - 用户管理（查看、编辑、删除用户）
  - 系统设置管理
  - 审计日志查看
  - 角色权限控制（管理员/普通用户）
- ✅ **账单历史记录**
  - 完整的导入操作记录
  - 详细的导入状态和结果
  - 按用户和时间过滤
- ✅ **账单复盘功能** 🆕
  - 支持月度、季度、年度复盘
  - 账单导入后智能提示生成复盘
  - 自定义生成指定周期的复盘
  - 数据预览功能
  - 复盘配置管理
- ✅ Web服务界面，方便管理和操作
- ✅ 实时日志记录和查看
- ✅ 支持文件管理，可查看和删除已上传的账单文件
- ✅ 服务状态监控

### Web服务功能

#### 用户认证
- 🔐 注册新用户
- 🔑 用户登录/登出
- 🔧 个人设置管理
- 📧 密码找回功能

#### Dashboard仪表盘 🆕
- 📊 财务概览卡片
  - 本月收入统计
  - 本月支出统计
  - 净余额计算
  - 交易笔数统计
- 📈 活动时间线
  - 显示最近账单导入记录
  - 显示复盘生成历史
  - 支持按类型筛选活动
- 🔄 数据刷新
  - 手动刷新按钮
  - 每60秒自动刷新
  - 刷新状态指示

#### 账单管理
- 📁 上传账单文件
- 📋 查看已上传文件列表
- **智能显示表头行之后的内容**，无需查看无关信息
- 🗑️ 删除账单文件
- ⚙️ 选择导入方式（立即执行/定时执行）
- 🔍 自动检测或手动选择账单平台

#### 账单历史
- 📊 查看所有导入历史记录
- 📈 导入状态跟踪
- 🔍 按日期和状态过滤
- 📝 查看详细导入结果

#### 个人设置
- ⚙️ 配置个人Notion API
- 🔑 修改密码
- 👤 管理个人信息
- 📊 查看使用统计
- ✓ **分步验证Notion配置** - 实时显示验证进度，快速定位问题
- 📊 **复盘配置** - 配置复盘数据库和模板

#### 账单复盘
- 📅 快速生成月度/季度/年度复盘
- 🔧 自定义生成指定周期复盘
- 👁️ 复盘数据预览
- 📊 复盘配置管理
- 🔗 直接跳转到Notion查看复盘

#### 管理后台（仅管理员）
- 👥 用户管理
  - 查看所有用户列表
  - 编辑用户信息
  - 删除用户账号
  - 重置用户密码
- ⚙️ 系统设置
  - 配置系统参数
  - 管理全局设置
- 📝 审计日志
  - 查看系统操作记录
  - 追踪用户活动

#### 服务管理
- 📊 查看服务运行状态
- 📈 监控服务统计信息

#### 日志管理
- 📝 实时查看服务日志
- 🔍 支持日志级别过滤
- 🔄 刷新日志内容

## 技术栈

### 后端技术
- **Python 3.8+** - 主要开发语言
- **FastAPI** - 现代化Web服务框架
- **Uvicorn** - ASGI服务器
- **SQLAlchemy** - ORM数据库框架
- **Pydantic** - 数据验证和序列化
- **APScheduler** - 任务调度框架
- **Notion SDK** - Notion API客户端
- **pandas** - 数据处理库
- **JWT** - JSON Web Token认证
- **bcrypt** - 密码加密

### 数据库
- **SQLite** - 默认数据库（支持PostgreSQL/MySQL）
- **用户数据管理** - 用户、账单历史、审计日志

### 前端技术
- **HTML5** - 页面结构
- **CSS3** - 样式设计
- **JavaScript (ES6+)** - 交互逻辑
- **Jinja2** - 模板引擎

## 安装部署

### 1. 克隆代码仓库
```bash
git clone <repository-url>
cd Import_Bill_To_Notion
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件，填写必要的配置项
vi .env
```

配置项说明：
- `NOTION_API_KEY` - Notion API密钥（可选，用户可在个人设置中配置）
- `NOTION_INCOME_DATABASE_ID` - 收入账单目标Notion数据库ID（可选，用户可在个人设置中配置）
- `NOTION_EXPENSE_DATABASE_ID` - 支出账单目标Notion数据库ID（可选，用户可在个人设置中配置）
- `DATABASE_URL` - 数据库连接字符串（默认：sqlite:///./data/users.db）
- `SECRET_KEY` - JWT密钥，用于加密会话token
- `ALGORITHM` - JWT算法（默认：HS256）
- `ACCESS_TOKEN_EXPIRE_MINUTES` - 访问令牌过期时间（默认：30分钟）
- `DEFAULT_BILL_DIR` - 定时任务默认账单目录
- `LOG_LEVEL` - 日志级别（DEBUG, INFO, WARNING, ERROR）
- `SCHEDULER_ENABLED` - 是否启用定时任务
- `SCHEDULER_CRON` - 定时任务执行频率（cron表达式）

### 4. 启动服务

#### 方式1：作为Web服务运行
```bash
python3 -m web_service.main
```

访问地址：`http://0.0.0.0:8000`

#### 方式2：作为后台定时服务运行
```bash
python3 main.py --schedule
```

#### 方式3：手动导入单个账单文件
```bash
python3 main.py --file <bill-file-path> [--platform <alipay/wechat/unionpay>]
```

## 使用说明

### 1. 首次使用

#### 注册账号
1. 访问 `http://0.0.0.0:8000/register`
2. 填写用户名、邮箱和密码
3. 完成注册后自动登录

#### 配置Notion API
1. 登录后访问"设置"页面
2. 填写Notion API密钥和数据库ID
3. 点击"验证配置"按钮，系统将分步验证：
   - ✓ 验证API密钥（显示Notion用户名）
   - ✓ 验证收入数据库（显示数据库名称）
   - ✓ 验证支出数据库（显示数据库名称）
4. 验证通过后保存配置即可使用

### 2. Web服务使用

#### Dashboard仪表盘 🆕
1. 登录后自动进入Dashboard页面
2. 查看财务概览卡片（收入、支出、余额、交易数）
3. 查看活动时间线（最近导入、复盘等操作）
4. 使用刷新按钮手动更新数据
5. 系统每60秒自动刷新数据

#### 账单管理
1. 访问 `http://0.0.0.0:8000/bill-management`
2. 点击"选择账单文件"上传CSV格式的账单文件
3. 选择同步类型（立即执行或定时执行）
4. 点击"上传并导入"开始导入
5. 导入完成后可在页面查看结果
6. 可在"已上传账单"列表中查看、删除文件

#### 账单历史
1. 访问 `http://0.0.0.0:8000/history`
2. 查看所有导入历史记录
3. 可按日期和状态过滤记录
4. 查看详细导入结果

#### 个人设置
1. 访问 `http://0.0.0.0:8000/settings`
2. 配置Notion API密钥和数据库ID
3. 修改密码
4. 查看个人使用统计

#### 账单复盘
1. 访问 `http://0.0.0.0:8000/review`
2. 快速生成：点击月度/季度/年度卡片一键生成
3. 自定义生成：选择复盘类型和周期，点击生成
4. 预览数据：生成前可预览即将创建的复盘内容
5. 查看复盘：生成后点击链接跳转到Notion查看

#### 复盘配置
1. 进入设置页面 → 复盘配置
2. 填写月度/季度/年度复盘数据库ID
3. （可选）填写复盘模板ID
4. 点击验证配置确认正确
5. 保存配置

#### 管理后台（仅管理员）
1. 访问 `http://0.0.0.0:8000/admin/users`
2. 管理用户账号
3. 访问 `http://0.0.0.0:8000/admin/settings`
4. 配置系统参数
5. 访问 `http://0.0.0.0:8000/admin/audit-logs`
6. 查看审计日志

#### 服务管理
1. 访问 `http://0.0.0.0:8000/service-management`
2. 查看服务运行状态和统计信息

#### 日志管理
1. 访问 `http://0.0.0.0:8000/log-management`
2. 查看实时服务日志
3. 可选择不同的日志级别进行过滤
4. 点击"刷新日志"更新日志内容

### 2. 命令行使用

#### 手动导入账单
```bash
# 自动检测平台
python3 main.py --file /path/to/bill.csv

# 手动指定平台
python3 main.py --file /path/to/bill.csv --platform alipay
```

#### 启动定时服务
```bash
python3 main.py --schedule
```

## 项目结构

```
.
├── config.py                  # 配置管理
├── importer.py                # 导入功能核心逻辑
├── main.py                    # CLI和调度器入口
├── notion_api.py              # Notion API客户端
├── utils.py                   # 共享工具（日志、编码检测）
├── scheduler.py               # 定时任务调度器
├── review_service.py          # 复盘服务
├── auth.py                    # 认证工具（密码、JWT）
├── database.py                # 数据库连接管理
├── models.py                  # SQLAlchemy ORM模型
├── schemas.py                 # Pydantic数据验证模型
├── dependencies.py            # FastAPI依赖项
├── parsers/                   # 账单解析器目录
│   ├── __init__.py            # 解析器工厂和自动检测
│   ├── base_parser.py         # 解析器基类
│   ├── alipay_parser.py       # 支付宝账单解析器
│   ├── wechat_parser.py       # 微信支付账单解析器
│   └── unionpay_parser.py     # 银联账单解析器
├── tests/                     # 测试文件目录
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_auth.py
│   ├── test_code_integrity.py
│   ├── test_import.py
│   ├── test_multi_tenant.py
│   ├── test_notion_connection.py
│   ├── test_review_service.py # 复盘服务测试
│   └── test_wechat_parser.py
├── web_service/               # Web服务目录
│   ├── __init__.py            # Web服务包
│   ├── main.py                # Web服务主入口
│   ├── routes/                # API路由
│   │   ├── __init__.py        # 路由入口
│   │   ├── upload.py          # 文件上传和导入路由
│   │   ├── auth.py            # 认证路由
│   │   ├── users.py           # 用户路由
│   │   ├── bills.py           # 账单历史路由
│   │   ├── review.py          # 复盘功能路由
│   │   └── admin.py           # 管理后台路由
│   ├── services/              # 业务服务
│   │   ├── __init__.py        # 服务入口
│   │   ├── file_service.py    # 文件服务
│   │   └── user_file_service.py  # 用户文件服务
│   ├── static/                # 静态资源
│   │   ├── css/               # CSS样式
│   │   │   ├── style.css
│   │   │   ├── settings.css
│   │   │   ├── review.css     # 复盘页面样式
│   │   │   ├── timeline.css   # 时间线样式 🆕
│   │   │   └── workspace-views.css  # 工作空间视图样式
│   │   └── js/                # JavaScript文件
│   │       ├── auth.js
│   │       ├── navbar.js
│   │       ├── settings.js
│   │       ├── review.js      # 复盘页面逻辑
│   │       ├── workspace.js   # 工作空间主逻辑
│   │       └── dashboard-view.js  # Dashboard视图 🆕
│   ├── templates/             # HTML模板
│   │   ├── index.html         # 首页
│   │   ├── workspace.html     # 工作空间主页面 🆕
│   │   ├── login.html         # 登录页面
│   │   ├── register.html      # 注册页面
│   │   ├── settings.html      # 设置页面
│   │   ├── history.html       # 账单历史页面
│   │   ├── review.html        # 复盘管理页面
│   │   ├── bill_management.html    # 账单管理
│   │   ├── service_management.html # 服务管理
│   │   ├── log_management.html     # 日志管理
│   │   └── admin/             # 管理后台模板
│   │       ├── users.html
│   │       ├── settings.html
│   │       └── audit_logs.html
│   ├── uploads/               # 上传文件存储目录
│   └── logs/                  # Web服务日志目录
├── data/                      # 数据目录（.gitignore）
├── docs/                      # 文档目录
│   ├── prompt/                # 提示词文档
│   └── *.md                   # 项目文档
├── .env                       # 环境变量配置
├── .env.example               # 环境变量示例
├── .gitignore                 # Git忽略文件
├── requirements.txt           # 依赖列表
├── CLAUDE.md                  # Claude Code开发指南
└── README.md                  # 项目说明文档
```

## 配置说明

### 环境变量

| 配置项 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| NOTION_API_KEY | Notion API密钥（全局默认值） | secret_xxxxxxxxxxxx | 否 |
| NOTION_INCOME_DATABASE_ID | 收入数据库ID（全局默认值） | 1234567890abcdef | 否 |
| NOTION_EXPENSE_DATABASE_ID | 支出数据库ID（全局默认值） | 1234567890abcdef | 否 |
| NOTION_MONTHLY_REVIEW_DB | 月度复盘数据库ID（全局默认值） | 1234567890abcdef | 否 |
| NOTION_QUARTERLY_REVIEW_DB | 季度复盘数据库ID（全局默认值） | 1234567890abcdef | 否 |
| NOTION_YEARLY_REVIEW_DB | 年度复盘数据库ID（全局默认值） | 1234567890abcdef | 否 |
| NOTION_MONTHLY_TEMPLATE_ID | 月度复盘模板ID（可选） | 1234567890abcdef | 否 |
| NOTION_QUARTERLY_TEMPLATE_ID | 季度复盘模板ID（可选） | 1234567890abcdef | 否 |
| NOTION_YEARLY_TEMPLATE_ID | 年度复盘模板ID（可选） | 1234567890abcdef | 否 |
| DATABASE_URL | 数据库连接字符串 | sqlite:///./data/users.db | 否 |
| SECRET_KEY | JWT密钥，用于加密会话token | your-secret-key-here | 是 |
| ALGORITHM | JWT加密算法 | HS256 | 否 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 访问令牌过期时间（分钟） | 30 | 否 |
| DEFAULT_BILL_DIR | 定时任务默认账单目录 | ./bills | 否 |
| DEFAULT_BILL_PLATFORM | 默认账单平台 | alipay | 否 |
| LOG_LEVEL | 日志级别 | INFO | 否 |
| SCHEDULER_ENABLED | 是否启用定时任务 | false | 否 |
| SCHEDULER_CRON | 定时任务cron表达式 | 0 0 1 * * | 否 |

### Notion数据库配置

需要在Notion中创建两个数据库：

#### 收入数据库
包含以下属性：
- **Name** (标题) - 账单记录名称
- **Price** (数字) - 金额
- **Date** (日期) - 交易日期
- **Category** (选择) - 交易分类
- **Counterparty** (富文本) - 交易对方
- **Remarks** (富文本) - 备注
- **Income/Expense** (选择) - 收支类型
- **Merchant Tracking Number** (富文本) - 商家订单号
- **Transaction Number** (富文本) - 交易订单号
- **Payment Method** (选择) - 支付方式
- **From** (选择) - 支付平台（支付宝/微信支付/银联）

#### 支出数据库
与收入数据库属性相同，用于存储支出记录

#### 复盘数据库（可选）
用于存储账单复盘报告，需要以下属性：
- **Name** (标题) - 复盘报告名称（如"2024-01 账单复盘"）
- **Period** (富文本) - 复盘周期（如"2024-01"）
- **Total Income** (数字) - 总收入
- **Total Expense** (数字) - 总支出
- **Net Balance** (数字) - 净收入
- **Transaction Count** (数字) - 交易笔数
- **Start Date** (日期) - 开始日期
- **End Date** (日期) - 结束日期
- **Summary** (富文本) - 汇总信息
- **Categories** (富文本) - 分类统计

支持月度、季度、年度三种复盘类型，可分别配置不同的数据库

## 核心实现

### 导入流程
1. **文件验证** - 检查文件存在性和可读性
2. **平台检测** - 自动检测账单类型（支付宝/微信/银联）
3. **数据解析** - 使用对应解析器处理CSV文件
4. **格式转换** - 转换为Notion数据库格式
5. **数据过滤** - 自动过滤"不计收支"记录
6. **数据库路由** - 根据收/支类型路由到对应数据库
7. **批量导入** - 每批10条记录导入到Notion

### 解析器特性
- **多编码支持** - 自动尝试GBK、UTF-8、GB2312编码
- **表头检测** - 自动定位表头行
- **列映射** - 将CSV列名映射到标准字段
- **金额清洗** - 自动去除货币符号和千位分隔符

### 日志功能
- **北京时区** - 所有日志使用UTC+8时区
- **分级记录** - 支持DEBUG、INFO、WARNING、ERROR级别
- **文件轮转** - 自动记录到文件和终端

## 注意事项

1. **账单格式要求**
   - 确保上传的账单文件符合各平台的标准格式
   - 目前只支持CSV格式的账单文件
   - 账单文件必须包含"收/支"列，用于区分收入和支出

2. **Notion API权限**
   - 确保Notion API密钥具有足够的权限访问目标数据库
   - 建议创建专门的集成，并仅授予所需的数据库访问权限

3. **定时任务配置**
   - 定时任务默认每月1日0点执行，可在`.env`文件中修改执行频率
   - 定时任务会自动读取`DEFAULT_BILL_DIR`目录下的最新账单文件

4. **日志管理**
   - CLI模式日志存储在`bill_import.log`
   - Web服务日志存储在`web_service/logs/web_service.log`
   - 可在配置文件中修改日志级别

5. **文件上传限制**
   - 单个文件大小限制为50MB
   - 支持的文件格式：CSV, TXT, XLS, XLSX

6. **数据同步规则**
   - "不计收支"的记录会被自动过滤，不会同步到Notion
   - 收入记录自动导入到收入数据库
   - 支出记录自动导入到支出数据库

## 开发说明

### 运行测试
```bash
# 运行所有测试
python -m pytest

# 运行特定测试文件
python -m pytest tests/test_wechat_parser.py -v

# 运行测试并生成覆盖率报告
python -m pytest --cov=. --cov-report=html
```

### 添加新平台解析器
1. 在`parsers/`目录下创建新的解析器文件
2. 继承`BaseBillParser`基类
3. 实现`parse()`和`_convert_to_notion()`方法
4. 在`parsers/__init__.py`中注册新解析器

### 代码结构
- **核心导入逻辑**：`importer.py` - `import_bill()`函数
- **账单解析**：`parsers/`目录下的各解析器
- **Notion集成**：`notion_api.py` - `NotionClient`类
- **用户认证**：`auth.py`, `database.py`, `models.py`, `schemas.py`
- **Web服务**：`web_service/`目录
- **定时任务**：`scheduler.py` - `BillScheduler`类
- **工具函数**：`utils.py` - 日志和编码检测

## 故障排除

### 常见问题

**Q: 提示"Cannot detect format"**
A: 请检查账单文件格式是否正确，或使用`--platform`参数手动指定平台

**Q: Notion连接失败**
A: 请检查`.env`文件中的API密钥和数据库ID是否正确

**Q: 部分记录导入失败**
A: 检查日志文件查看详细错误信息，可能是字段格式不匹配

**Q: 定时任务不执行**
A: 确保`SCHEDULER_ENABLED=true`且cron表达式格式正确

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

- **v2.3.0** (2026-02-06)
  - ✨ 新增Dashboard仪表盘视图
    - 财务概览卡片（收入、支出、余额、交易数）
    - 活动时间线（显示最近导入、复盘等操作）
    - 手动刷新和自动刷新功能（60秒间隔）
    - 统一的工作空间页面，整合所有功能
  - 🔧 优化前端架构
    - 新增dashboard-view.js模块
    - 新增timeline.css时间线样式
    - 改进workspace.js视图切换逻辑
  - 📝 完善端到端交付文档
    - Discovery需求发现报告
    - Exploration代码库分析报告
    - Design架构设计报告
    - Implementation实施报告
    - Verification验证报告
    - Delivery交付报告
  - ✅ 测试覆盖率达到100%

- **v2.2.0** (2026-02-03)
  - ✨ 新增账单复盘功能
    - 支持月度、季度、年度三种复盘类型
    - 账单导入后智能提示生成复盘
    - 自定义生成指定周期的复盘
    - 数据预览功能
    - 复盘配置管理（设置页面）
    - 独立的复盘管理页面
  - 🔧 注册复盘API路由
  - 📝 补充复盘服务单元测试
  - 📝 为关键JavaScript函数添加JSDoc注释
  - 📝 完善项目文档和提示词
  - 📁 新增docs目录，存储阶段性文档

- **v2.1.0** (2026-01-19)
  - ✨ 新增分步验证Notion配置
    - 实时显示验证进度条
    - 逐步验证API密钥、收入数据库、支出数据库
    - 显示详细信息（用户名、数据库名称等）
    - 快速定位配置问题，提升用户体验
  - 🐛 修复导入历史耗时统计错误
    - 统一时区为UTC，避免时区差异导致计算错误
  - 🎨 优化日志管理页面显示
    - 采用Linux终端风格
    - 黑底彩字，紧凑单行显示
    - 支持多种编码读取日志文件
  - 📝 更新项目文档
    - 添加分步验证功能说明
    - 更新架构和使用文档

- **v2.0.0** (2026-01-16)
  - ✨ 新增用户认证系统
    - 用户注册、登录、登出
    - JWT会话管理
    - 密码加密存储（bcrypt）
  - ✨ 新增多用户支持
    - 每个用户独立的数据隔离
    - 个性化的Notion配置
    - 用户级别的文件管理
  - ✨ 新增管理后台
    - 用户管理功能
    - 系统设置管理
    - 审计日志查看
    - 角色权限控制
  - ✨ 新增账单历史记录
    - 完整的导入操作记录
    - 详细的导入状态和结果
    - 按用户和时间过滤
  - 🔧 优化项目结构
    - 添加用户认证模块
    - 添加数据库模型和schemas
    - 更新Web服务路由结构
  - 📝 完善文档
    - 更新CLAUDE.md开发指南
    - 更新README.md用户文档

- **v1.1.0** (2026-01-08)
  - 优化项目结构和代码组织
  - 新增`utils.py`统一工具函数
  - 改进日志系统，支持北京时区
  - 完善开发文档和注释
  - 优化配置管理，支持动态更新

- **v1.0.0** (2025-12-31)
  - 初始版本
  - 支持支付宝、微信支付、银联账单导入
  - Web服务界面
  - 定时自动导入功能
  - 日志管理功能
  - 文件管理功能
