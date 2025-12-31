## 实现计划

### 1. 目录结构设计
创建独立的`web_service`目录，包含以下子目录和文件：

```
web_service/
├── main.py              # FastAPI应用入口
├── routes/              # API路由
│   ├── __init__.py
│   └── upload.py        # 上传相关路由
├── services/            # 业务逻辑服务
│   ├── __init__.py
│   ├── file_service.py  # 文件处理服务
│   └── import_service.py # 导入服务（封装原有逻辑）
├── templates/           # HTML模板
│   ├── index.html       # 首页
│   └── upload.html      # 上传页面
├── static/              # 静态资源
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── uploads/             # 上传文件存储目录
├── logs/                # Web服务日志目录
├── requirements.txt     # Web服务依赖
└── web_service.service  # Systemd服务配置
```

### 2. 核心功能实现

#### 2.1 FastAPI应用（web_service/main.py）
- 初始化FastAPI应用
- 配置CORS、静态文件和模板
- 注册路由
- 实现页面路由

#### 2.2 文件上传功能（web_service/routes/upload.py）
- 实现文件上传API
- 支持选择同步类型（立即/定时）
- 返回上传结果和任务信息

#### 2.3 服务层（web_service/services/）
- `file_service.py`：处理文件验证、保存和管理
- `import_service.py`：封装原有导入逻辑，调用`importer.py`的功能

#### 2.4 Web页面（web_service/templates/）
- 简洁的上传页面，支持文件选择和同步类型选择
- 实时显示上传进度和结果
- 任务状态查看

#### 2.5 后台服务配置
- 提供systemd服务配置文件
- 支持后台运行和自启动

### 3. 与原有代码的兼容性

- **无需修改原有代码**：通过封装调用现有功能
- **共享配置**：复用现有的`config.py`和`.env`文件
- **共享导入逻辑**：通过`import_service.py`调用`importer.py`
- **独立日志**：Web服务使用自己的日志文件

### 4. 实现步骤

1. 创建`web_service`目录结构
2. 实现基础FastAPI应用
3. 实现文件上传API
4. 实现导入服务封装
5. 创建Web页面模板
6. 添加静态资源
7. 配置systemd服务
8. 测试功能完整性

### 5. 使用说明

- **启动Web服务**：`python3 -m web_service.main` 或使用systemd服务
- **访问Web页面**：http://localhost:8000/upload
- **API文档**：http://localhost:8000/docs
- **后台运行**：使用systemd服务管理

### 6. 技术栈

- FastAPI：Web框架
- Jinja2：模板引擎
- APScheduler：任务调度
- Python-multipart：文件上传
- Systemd：后台服务管理

该方案采用独立目录设计，不修改原有代码，保持良好的兼容性，同时实现了Web页面上传和后台服务功能。