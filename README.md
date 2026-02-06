# 个人财务管理平台

一站式个人财务管理平台：支持支付宝、微信、银联账单自动导入，智能分类统计，月度/季度/年度财务复盘，让理财更简单。

[![GitHub stars](https://img.shields.io/github/stars/sundray-ygx/Import_Bill_To_Notion)](https://github.com/sundray-ygx/Import_Bill_To_Notion)
[![GitHub license](https://img.shields.io/github/license/sundray-ygx/Import_Bill_To_Notion)](https://github.com/sundray-ygx/Import_Bill_To_Notion/blob/main/LICENSE)

---

## 📋 目录

- [快速开始](#快速开始)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [安装部署](#安装部署)
- [使用说明](#使用说明)
- [项目结构](#项目结构)
- [配置说明](#配置说明)
- [开发说明](#开发说明)
- [常见问题](#常见问题)
- [更新日志](#更新日志)

---

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/sundray-ygx/Import_Bill_To_Notion.git
cd Import_Bill_To_Notion

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填写必要的配置

# 启动服务
python3 -m web_service.main
```

访问：`http://localhost:8000`

---

## 💡 核心功能

### 1. 多平台账单导入
- 支持支付宝、微信支付、银联账单一键导入
- 自动识别账单格式和编码
- 智能检测平台，无需手动选择

### 2. 智能分类统计
- 根据收/支自动路由到不同数据库
- 智能过滤"不计收支"记录
- 自动识别交易类别

### 3. 财务复盘分析
- 月度、季度、年度财务复盘报告
- 账单导入后智能提示生成复盘
- 自定义周期复盘生成
- 复盘数据预览功能
- 洞察消费趋势，优化财务决策

### 4. 数据安全可靠
- 多租户数据隔离
- 企业级安全标准
- JWT会话管理
- 密码加密存储

### 5. 导入历史追踪
- 完整的导入记录和历史查询
- 详细的导入状态和结果
- 按用户和时间过滤

### 6. 多用户支持
- 多租户架构
- 每个用户数据独立隔离
- 个性化的Notion配置
- 支持团队协作

<details>
<summary><b>📱 Web服务功能详情</b>（点击展开）</summary>

#### 用户认证
- 🔐 注册新用户
- 🔑 用户登录/登出
- 🔧 个人设置管理
- 📧 密码找回功能

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

</details>

---

## 🛠 技术栈

<details>
<summary><b>后端技术</b></summary>

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

</details>

<details>
<summary><b>数据库</b></summary>

- **SQLite** - 默认数据库（支持PostgreSQL/MySQL）
- **用户数据管理** - 用户、账单历史、审计日志

</details>

<details>
<summary><b>前端技术</b></summary>

- **HTML5** - 页面结构
- **CSS3** - 样式设计
- **JavaScript (ES6+)** - 交互逻辑
- **Jinja2** - 模板引擎

</details>

---

## 📦 安装部署

<details>
<summary><b>1. 克隆代码仓库</b></summary>

```bash
git clone https://github.com/sundray-ygx/Import_Bill_To_Notion.git
cd Import_Bill_To_Notion
```

</details>

<details>
<summary><b>2. 安装依赖</b></summary>

```bash
pip install -r requirements.txt
```

</details>

<details>
<summary><b>3. 配置环境变量</b></summary>

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
vi .env
```

</details>

<details>
<summary><b>环境变量说明</b></summary>

| 配置项 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `NOTION_API_KEY` | Notion API密钥 | `secret_xxx` | 否 |
| `NOTION_INCOME_DATABASE_ID` | 收入数据库ID | `1234567890abcdef` | 否 |
| `NOTION_EXPENSE_DATABASE_ID` | 支出数据库ID | `1234567890abcdef` | 否 |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/users.db` | 否 |
| `SECRET_KEY` | JWT密钥 | `your-secret-key` | **是** |
| `SCHEDULER_ENABLED` | 是否启用定时任务 | `false` | 否 |

</details>

<details>
<summary><b>4. 启动服务</b></summary>

```bash
# Web服务模式
python3 -m web_service.main

# 后台定时服务模式
python3 main.py --schedule

# 手动导入单文件
python3 main.py --file <bill-file-path>
```

**访问地址**：`http://localhost:8000`

</details>

---

## 📖 使用说明

<details>
<summary><b>1. 首次使用</b></summary>

#### 注册账号
1. 访问 `http://localhost:8000/register`
2. 填写用户名、邮箱和密码
3. 完成注册后自动登录

#### 配置Notion API
1. 登录后访问"设置"页面
2. 填写Notion API密钥和数据库ID
3. 点击"验证配置"按钮
4. 验证通过后保存配置即可使用

</details>

<details>
<summary><b>2. Web服务使用</b></summary>

#### 账单管理
1. 访问 `http://localhost:8000/bill-management`
2. 点击"选择账单文件"上传CSV格式的账单文件
3. 选择同步类型（立即执行或定时执行）
4. 点击"上传并导入"开始导入

#### 账单历史
1. 访问 `http://localhost:8000/history`
2. 查看所有导入历史记录
3. 可按日期和状态过滤记录

#### 账单复盘
1. 访问 `http://localhost:8000/review`
2. 快速生成：点击月度/季度/年度卡片一键生成
3. 自定义生成：选择复盘类型和周期，点击生成
4. 预览数据：生成前可预览即将创建的复盘内容

</details>

---

## 📁 项目结构

```
.
├── src/                          # 核心源代码
│   ├── __init__.py
│   ├── auth.py                   # 认证工具（密码、JWT）
│   ├── config.py                 # 配置管理
│   ├── importer.py               # 导入功能核心逻辑
│   ├── main.py                   # CLI和调度器入口
│   ├── models.py                 # SQLAlchemy ORM模型
│   ├── notion_api.py             # Notion API客户端
│   ├── review_service.py         # 复盘服务
│   ├── scheduler.py              # 定时任务调度器
│   ├── schemas.py                # Pydantic数据验证模型
│   ├── utils.py                  # 共享工具（日志、编码检测）
│   └── services/                 # 业务服务
│       ├── __init__.py
│       ├── database.py           # 数据库连接管理
│       └── dependencies.py       # FastAPI依赖项
├── parsers/                      # 账单解析器
│   ├── __init__.py              # 解析器工厂和自动检测
│   ├── base_parser.py           # 解析器基类
│   ├── alipay_parser.py         # 支付宝账单解析器
│   ├── wechat_parser.py         # 微信支付账单解析器
│   └── unionpay_parser.py       # 银联账单解析器
├── web_service/                  # Web服务
│   ├── main.py                   # FastAPI主入口
│   ├── routes/                   # API路由
│   ├── templates/                # HTML模板
│   ├── static/                   # 静态资源
│   └── logs/                     # 日志目录
├── tests/                        # 测试文件
├── docs/                         # 对外文档
│   ├── API_REFERENCE.md          # API参考文档
│   └── MULTI_TENANT_SETUP.md     # 多租户设置指南
├── .env.example                  # 环境变量示例
├── requirements.txt              # 依赖列表
├── CHANGELOG.md                  # 更新日志
├── README.md                     # 项目说明文档
└── CLAUDE.md                     # Claude Code开发指南
```

---

## ⚙️ 配置说明

<details>
<summary><b>Notion数据库配置</b></summary>

### 收入/支出数据库
包含以下属性：
- **Name** (标题) - 账单记录名称
- **Price** (数字) - 金额
- **Date** (日期) - 交易日期
- **Category** (选择) - 交易分类
- **Counterparty** (富文本) - 交易对方
- **Remarks** (富文本) - 备注
- **Income/Expense** (选择) - 收支类型
- **Payment Method** (选择) - 支付方式
- **From** (选择) - 支付平台

### 复盘数据库（可选）
- **Name** (标题) - 复盘报告名称
- **Period** (富文本) - 复盘周期
- **Total Income** (数字) - 总收入
- **Total Expense** (数字) - 总支出
- **Net Balance** (数字) - 净收入
- **Summary** (富文本) - 汇总信息
- **Categories** (富文本) - 分类统计

</details>

<details>
<summary><b>核心实现说明</b></summary>

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

</details>

---

## 🔧 开发说明

<details>
<summary><b>运行测试</b></summary>

```bash
# 运行所有测试
python -m pytest

# 运行特定测试文件
python -m pytest tests/test_wechat_parser.py -v

# 运行测试并生成覆盖率报告
python -m pytest --cov=. --cov-report=html
```

</details>

<details>
<summary><b>添加新平台解析器</b></summary>

1. 在`parsers/`目录下创建新的解析器文件
2. 继承`BaseBillParser`基类
3. 实现`parse()`和`_convert_to_notion()`方法
4. 在`parsers/__init__.py`中注册新解析器

</details>

---

## ❓ 常见问题

<details>
<summary><b>问题与解决方案</b></summary>

**Q: 提示"Cannot detect format"**
A: 请检查账单文件格式是否正确，或使用`--platform`参数手动指定平台

**Q: Notion连接失败**
A: 请检查`.env`文件中的API密钥和数据库ID是否正确

**Q: 部分记录导入失败**
A: 检查日志文件查看详细错误信息，可能是字段格式不匹配

**Q: 定时任务不执行**
A: 确保`SCHEDULER_ENABLED=true`且cron表达式格式正确

</details>

---

## 📜 更新日志

<details>
<summary><b>v2.2.0</b> (2026-02-03) - 账单复盘功能</summary>

- ✨ 新增账单复盘功能
  - 支持月度、季度、年度三种复盘类型
  - 账单导入后智能提示生成复盘
  - 自定义生成指定周期的复盘
  - 数据预览功能
  - 复盘配置管理（设置页面）
  - 独立的复盘管理页面
- 🔧 注册复盘API路由
- 📝 补充复盘服务单元测试

</details>

<details>
<summary><b>v2.1.0</b> (2026-01-19) - 配置验证优化</summary>

- ✨ 新增分步验证Notion配置
  - 实时显示验证进度条
  - 逐步验证API密钥、收入数据库、支出数据库
  - 显示详细信息（用户名、数据库名称等）
- 🐛 修复导入历史耗时统计错误
- 🎨 优化日志管理页面显示

</details>

<details>
<summary><b>v2.0.0</b> (2026-01-16) - 多用户支持</summary>

- ✨ 新增用户认证系统
- ✨ 新增多用户支持
- ✨ 新增管理后台
- ✨ 新增账单历史记录

</details>

<details>
<summary><b>v1.0.0</b> (2025-12-31) - 初始版本</summary>

- 支持支付宝、微信支付、银联账单导入
- Web服务界面
- 定时自动导入功能

</details>

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

- 查看 [API_REFERENCE.md](docs/API_REFERENCE.md) 了解API文档
- 查看 [CLAUDE.md](CLAUDE.md) 了解开发指南

---

**⭐ 如果这个项目对您有帮助，请给个 Star 支持一下！**

GitHub: https://github.com/sundray-ygx/Import_Bill_To_Notion
