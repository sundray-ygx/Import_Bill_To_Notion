# 实现微信支付、支付宝账单导入Notion（含扩展功能）

## 项目结构

```
Import_Bill_To_Notion/
├── config.py              # 配置管理
├── notion_api.py          # Notion API 客户端
├── importer.py            # 导入功能核心模块
├── parsers/
│   ├── __init__.py
│   ├── base_parser.py     # 基础解析器类
│   ├── alipay_parser.py   # 支付宝账单解析器
│   ├── wechat_parser.py   # 微信支付账单解析器
│   └── unionpay_parser.py # 银联支付账单解析器（扩展）
├── gui/
│   ├── __init__.py
│   └── main_window.py     # 主窗口
├── scheduler.py           # 定时任务管理器
├── main.py                # 主程序入口
├── requirements.txt       # 依赖包
└── .env.example           # 环境变量示例
```

## 实现步骤

### 1. 项目初始化

* 创建完整项目结构

* 编写 requirements.txt，包含所有依赖

* 创建 .env.example 示例配置文件

### 2. 配置管理

* 使用 python-dotenv 管理环境变量

* 配置项包括：

  * NOTION\_API\_KEY：Notion API 密钥

  * NOTION\_DATABASE\_ID：目标数据库 ID

  * 定时任务配置

  * GUI 设置等

### 3. 基础解析器与多平台支持

* 实现 `base_parser.py` 作为所有解析器的基类

* 实现 **支付宝解析器**：支持支付宝 CSV 账单格式

* 实现 **微信支付解析器**：支持微信支付 CSV 账单格式

* 实现 **银联支付解析器**：支持银联账单格式（扩展功能）

* 所有解析器统一接口，便于扩展更多平台

### 4. 自动账单类型识别

* 在 `parsers/__init__.py` 中实现账单类型识别功能

* 通过分析文件内容特征自动判断账单平台

* 支持的识别方式：

  * 文件头关键字匹配

  * 字段名匹配

  * 特殊格式标记识别

### 5. Notion API 集成

* 实现 `notion_api.py`，封装 Notion API 操作

* 功能包括：

  * 连接到 Notion 数据库

  * 创建/更新账单记录

  * 检查重复记录

  * 批量导入优化

### 6. GUI 界面

* 使用 Tkinter 或 PyQt 实现图形界面

* 主要功能：

  * 配置设置界面

  * 账单文件选择

  * 实时导入进度显示

  * 导入结果统计

  * 定时任务设置

### 7. 定时自动导入

* 使用 `schedule` 或 `APScheduler` 实现定时任务

* 功能包括：

  * 设置定时规则（如每月1日自动导入上月账单）

  * 自动查找指定目录下的最新账单文件

  * 自动执行导入流程

  * 发送导入结果通知

### 8. 主程序逻辑

* 支持两种运行模式：命令行模式和 GUI 模式

* 命令行模式：适合脚本自动化

* GUI 模式：适合普通用户操作

* 统一的导入流程：

  1. 读取配置
  2. 识别账单类型
  3. 解析账单文件
  4. 导入到 Notion 数据库
  5. 生成导入报告

## 依赖包

* `notion-client`：Notion API 客户端

* `pandas`：CSV 文件解析

* `python-dotenv`：环境变量管理

* `APScheduler`：定时任务调度

* `pillow`：图片处理

* `PyQt5`：GUI 界面（通过系统包管理器安装）

## 使用流程

### 命令行模式

```bash
python main.py --file /path/to/bill.csv --platform alipay
```

### GUI 模式

1. 启动程序，打开图形界面
2. 在设置中配置 Notion API 密钥和数据库 ID
3. 选择账单文件，系统自动识别类型
4. 点击"导入"按钮，查看实时进度
5. 查看导入结果统计
6. 设置定时任务（可选）

## 扩展功能

* **多平台支持**：已集成支付宝、微信支付、银联，可轻松扩展其他平台

* **自动识别**：无需手动选择账单类型

* **GUI界面**：友好的用户交互

* **定时导入**：自动执行，无需人工干预

* **重复处理**：智能识别并处理重复记录

* **导入报告**：详细的导入结果统计

* **错误处理**：完善的异常处理和日志记录

