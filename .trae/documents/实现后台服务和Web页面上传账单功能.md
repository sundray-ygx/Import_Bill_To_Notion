# 实现后台服务和Web页面上传账单功能（独立目录方案）

## 1. 方案概述

为了不影响现有功能的完整性，我们将创建一个独立的目录来实现后台服务和Web页面上传账单功能，同时保持与原有代码的兼容性。

## 2. 目录结构设计

```
Import_Bill_To_Notion/
├── # 原有目录结构（保持不变）
├── main.py              # 原有主入口文件
├── config.py            # 原有配置管理
├── importer.py          # 原有导入核心逻辑
├── notion_api.py        # 原有Notion API客户端
├── scheduler.py         # 原有定时任务调度器
├── parsers/             # 原有解析器模块
├── gui/                 # 原有GUI模块
├── 
├── # 新增独立目录
└── web_service/         # Web服务独立目录
    ├── main.py          # Web服务主入口
    ├── config.py        # Web服务配置
    ├── app.py           # FastAPI应用实例
    ├── routes/          # API路由
    │   ├── __init__.py
    │   ├── upload.py    # 文件上传路由
    │   ├── task.py      # 任务管理路由
    │   └── system.py    # 系统管理路由
    ├── services/        # 业务逻辑服务
    │   ├── __init__.py
    │   ├── file_service.py  # 文件管理服务
    │   ├── task_service.py  # 任务调度服务
    │   └── import_service.py # 账单导入服务
    ├── models/          # 数据模型
    │   ├── __init__.py
    │   ├── request.py   # 请求模型
    │   └── response.py  # 响应模型
    ├── templates/       # HTML模板
    ├── static/          # 静态资源
    ├── uploads/         # 上传文件存储目录
    ├── logs/            # Web服务日志目录
    ├── requirements.txt # Web服务依赖
    └── web_service.service # Systemd服务配置文件
```

## 3. 核心功能实现

### 3.1 Web服务层
- **FastAPI应用**：创建独立的FastAPI应用实例
- **API路由**：
  - `/api/upload`：文件上传接口，支持选择同步时机
  - `/api/tasks`：任务管理接口（创建、查询、取消）
  - `/api/status`：服务状态接口
  - `/api/config`：配置管理接口
- **Web页面**：
  - 上传页面：支持文件上传和同步时机选择（立即执行/定时执行）
  - 任务列表页面：显示和管理任务
  - 服务状态页面：显示服务运行状态
  - 配置页面：修改服务配置

### 3.2 任务调度层
- **任务类型**：
  - 即时任务：用户选择立即执行时创建
  - 定时任务：按照配置的定时规则执行
- **任务队列**：使用APScheduler管理任务队列
- **任务执行**：调用原有导入逻辑执行账单导入

### 3.3 文件管理层
- **文件上传**：支持多文件上传，验证文件类型和大小
- **文件存储**：将上传的文件存储到uploads目录
- **文件管理**：支持查看、删除上传的文件

### 3.4 配置管理
- **配置文件**：独立的配置文件，避免影响原有配置
- **动态配置**：支持在Web页面上修改配置
- **配置同步**：配置变更后自动同步到服务

## 4. 实现步骤

### 4.1 目录创建
- 创建web_service目录及子目录结构
- 创建必要的配置文件和模板

### 4.2 依赖安装
- 创建web_service/requirements.txt文件
- 安装FastAPI、Uvicorn等Web相关依赖

### 4.3 代码实现
1. **应用初始化**：创建FastAPI应用实例
2. **路由实现**：实现文件上传、任务管理等路由
3. **服务层实现**：实现文件管理、任务调度、导入服务等
4. **模板开发**：创建Web页面模板
5. **静态资源**：添加CSS、JS等静态资源

### 4.4 服务配置
- 创建Systemd服务配置文件
- 配置服务运行参数
- 测试服务启动和停止

### 4.5 集成原有功能
- 在import_service.py中调用原有importer.py的功能
- 确保与原有配置的兼容性
- 测试完整的导入流程

## 5. 安全性考虑
- **文件上传安全**：验证文件类型和大小，防止恶意文件上传
- **API认证**：添加基本认证，保护API端点
- **敏感信息保护**：确保敏感配置安全存储
- **日志安全**：确保日志中不包含敏感信息

## 6. 监控与维护
- **健康检查**：添加健康检查端点
- **日志管理**：配置日志轮转
- **性能监控**：记录服务运行指标

## 7. 部署说明

### 7.1 安装依赖
```bash
cd web_service
pip install -r requirements.txt
```

### 7.2 启动服务
```bash
# 开发模式
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式（使用systemd）
sudo cp web_service.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable web_service
sudo systemctl start web_service
```

### 7.3 访问Web页面
```
http://your-server-ip:8000
```

这个方案将新功能放在独立的目录中，不影响原有代码的完整性，同时保持了与原有功能的兼容性，满足用户的需求。