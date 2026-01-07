# Notion账单导入服务

一个用于将支付宝、微信支付和银联账单自动导入到Notion数据库的服务，支持手动导入和定时自动导入功能。

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
- ✅ Web服务界面，方便管理和操作
- ✅ 实时日志记录和查看
- ✅ 支持文件管理，可查看和删除已上传的账单文件
- ✅ 服务状态监控

### Web服务功能
- 📁 账单管理
  - 上传账单文件
  - 查看已上传文件列表
  - **智能显示表头行之后的内容**，无需查看无关信息
  - 删除账单文件
  - 选择导入方式（立即执行/定时执行）
  - 自动检测或手动选择账单平台

- 📊 服务管理
  - 查看服务运行状态
  - 监控服务统计信息

- 📝 日志管理
  - 实时查看服务日志
  - 支持日志级别过滤
  - 刷新日志内容

## 技术栈

### 后端技术
- **Python 3.8+** - 主要开发语言
- **FastAPI** - Web服务框架
- **Uvicorn** - ASGI服务器
- **APScheduler** - 任务调度框架
- **Notion SDK** - Notion API客户端
- **pandas** - 数据处理库

### 前端技术
- **HTML5** - 页面结构
- **CSS3** - 样式设计
- **JavaScript (ES6+)** - 交互逻辑

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
- `NOTION_API_KEY` - Notion API密钥
- `NOTION_INCOME_DATABASE_ID` - 收入账单目标Notion数据库ID
- `NOTION_EXPENSE_DATABASE_ID` - 支出账单目标Notion数据库ID
- `UPLOAD_DIR` - 上传文件存储目录
- `LOG_LEVEL` - 日志级别（DEBUG, INFO, WARNING, ERROR）

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

### 1. Web服务使用

#### 账单管理
1. 访问 `http://0.0.0.0:8000/bill-management`
2. 点击"选择账单文件"上传CSV格式的账单文件
3. 选择同步类型（立即执行或定时执行）
4. 点击"上传并导入"开始导入
5. 导入完成后可在页面查看结果
6. 可在"已上传账单"列表中查看、删除文件

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
├── main.py                    # 主入口文件
├── notion_api.py              # Notion API客户端
├── parsers/                   # 账单解析器目录
│   ├── __init__.py            # 解析器入口
│   ├── alipay_parser.py       # 支付宝账单解析器
│   ├── wechat_parser.py       # 微信支付账单解析器
│   └── unionpay_parser.py     # 银联账单解析器
├── scheduler.py               # 定时任务调度器
├── web_service/               # Web服务目录
│   ├── __init__.py            # Web服务包
│   ├── main.py                # Web服务主入口
│   ├── routes/                # API路由
│   │   ├── __init__.py        # 路由入口
│   │   └── upload.py          # 文件上传路由
│   ├── services/              # 业务服务
│   │   ├── __init__.py        # 服务入口
│   │   ├── file_service.py    # 文件服务
│   │   └── import_service.py  # 导入服务
│   ├── static/                # 静态资源
│   │   ├── css/               # CSS样式
│   │   └── js/                # JavaScript文件
│   └── templates/             # HTML模板
│       ├── index.html         # 首页
│       ├── bill_management.html  # 账单管理
│       ├── service_management.html  # 服务管理
│       └── log_management.html      # 日志管理
├── .env                       # 环境变量配置
├── .env.example               # 环境变量示例
├── .gitignore                 # Git忽略文件
├── bill_import.log            # 日志文件
├── requirements.txt           # 依赖列表
└── README.md                  # 项目说明文档
```

## 配置说明

### 环境变量

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| NOTION_API_KEY | Notion API密钥，用于访问Notion API | secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |
| NOTION_INCOME_DATABASE_ID | 收入账单目标Notion数据库ID | 1234567890abcdef1234567890abcdef |
| NOTION_EXPENSE_DATABASE_ID | 支出账单目标Notion数据库ID | 1234567890abcdef1234567890abcdef |
| DEFAULT_BILL_DIR | 定时任务默认账单目录 | ./bills |
| LOG_LEVEL | 日志级别，可选值：DEBUG, INFO, WARNING, ERROR | INFO |
| SCHEDULER_ENABLED | 是否启用定时任务 | true |
| SCHEDULER_CRON | 定时任务执行频率（cron表达式） | 0 0 1 * * |

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
- **Income Expense** (选择) - 收支类型
- **Merchant Tracking Number** (富文本) - 商家订单号
- **Transaction Number** (富文本) - 交易订单号
- **Payment Method** (选择) - 支付方式
- **From** (选择) - 支付平台（支付宝/微信支付/银联）

#### 支出数据库
与收入数据库属性相同，用于存储支出记录

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
   - 日志文件默认存储在`bill_import.log`
   - 可在配置文件中修改日志级别和存储位置

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
python -m pytest test_wechat_parser.py -v
```

### 代码结构
- 核心导入逻辑：`importer.py`
- 账单解析：`parsers/`目录下的各解析器
- Web服务：`web_service/`目录
- 定时任务：`scheduler.py`

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

- v1.1.0 (2026-01-07)
  - **新增**：根据收/支分类自动导入到不同数据库
  - **新增**：智能过滤"不计收支"记录
  - **优化**：Web页面只显示表头行之后的内容
  - **优化**：支持自定义收入和支出数据库ID配置
  - **优化**：配置文件支持更多自定义选项

- v1.0.0 (2025-12-31)
  - 初始版本
  - 支持支付宝、微信支付、银联账单导入
  - Web服务界面
  - 定时自动导入功能
  - 日志管理功能
  - 文件管理功能
