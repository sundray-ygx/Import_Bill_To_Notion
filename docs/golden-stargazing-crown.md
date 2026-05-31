# 账单导入服务云部署 + 微信小程序实现计划

## 概述

将现有的FastAPI账单导入服务部署到云服务器，并开发微信小程序前端，实现通过微信聊天选择文件上传账单的功能。

## 架构设计

```
┌─────────────────────────────────────────────────┐
│              微信小程序客户端                      │
│   - 文件选择（wx.chooseMessageFile）             │
│   - 文件上传（wx.uploadFile）                    │
│   - 文件管理                                     │
└─────────────────────┬───────────────────────────┘
                      │ HTTPS
                      │ X-API-Key 认证
┌─────────────────────▼───────────────────────────┐
│              云服务器                             │
├─────────────────────────────────────────────────┤
│  Nginx (443端口)                                 │
│    ├── SSL/TLS (Let's Encrypt)                  │
│    ├── 反向代理 → Uvicorn:8000                  │
│    └── 请求限制: 50MB                           │
├─────────────────────────────────────────────────┤
│  Uvicorn + FastAPI (8000端口, 内网)             │
│    └── API认证中间件                            │
├─────────────────────────────────────────────────┤
│  Systemd服务管理                                 │
│  文件目录: /var/www/bill-uploads                │
└─────────────────────────────────────────────────┘
```

---

## 第一阶段：后端服务改造

### 1.1 API认证中间件

**新建文件**: `web_service/middleware/auth.py`

```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from config import Config
import logging

class APIKeyMiddleware(BaseHTTPMiddleware):
    """API Key认证中间件"""

    # 不需要认证的路径
    EXEMPT_PATHS = ["/", "/api/service-info", "/api/logs"]

    async def dispatch(self, request: Request, call_next):
        # GET请求豁免认证
        if request.method == "GET":
            return await call_next(request)

        # 检查豁免路径
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # 验证API Key
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API Key")

        valid_keys = Config.API_KEYS.split(",") if Config.API_KEYS else []
        if api_key not in [k.strip() for k in valid_keys]:
            raise HTTPException(status_code=403, detail="Invalid API Key")

        return await call_next(request)
```

### 1.2 更新配置

**修改文件**: `config.py`

新增配置项:
```python
# API Configuration
API_KEYS = os.getenv("API_KEYS", "")  # 逗号分隔的API密钥列表

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
```

**修改文件**: `.env.example`
```bash
# API Authentication
API_KEYS=your_api_key_here_1,your_api_key_here_2

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### 1.3 更新主应用

**修改文件**: `web_service/main.py`

```python
from .middleware.auth import APIKeyMiddleware

# 在创建app后添加中间件
app.add_middleware(APIKeyMiddleware)
```

### 1.4 新增API端点

**修改文件**: `web_service/routes/upload.py`

新增端点:
```python
@router.get("/config/platforms")
async def get_platforms():
    """获取支持的支付平台列表"""
    return {
        "platforms": [
            {"id": "alipay", "name": "支付宝"},
            {"id": "wechat", "name": "微信支付"},
            {"id": "unionpay", "name": "银联"}
        ]
    }

@router.post("/auth/validate")
async def validate_api_key(request: Request):
    """验证API Key（小程序初始化时使用）"""
    api_key = request.headers.get("X-API-Key")
    valid_keys = Config.API_KEYS.split(",") if Config.API_KEYS else []
    if api_key in [k.strip() for k in valid_keys]:
        return {"valid": True}
    raise HTTPException(status_code=403, detail="Invalid API Key")
```

---

## 第二阶段：云服务器部署

### 2.1 服务器环境准备

**系统要求**: Ubuntu 20.04+ / CentOS 7+

**安装脚本**:
```bash
#!/bin/bash
# install.sh

# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和pip
sudo apt install -y python3 python3-pip python3-venv

# 安装Nginx
sudo apt install -y nginx

# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 创建项目目录
sudo mkdir -p /opt/bill-import
sudo mkdir -p /var/www/bill-uploads
sudo mkdir -p /var/log/bill-service

# 创建虚拟环境
cd /opt/bill-import
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r web_service/requirements.txt
```

### 2.2 Nginx配置

**新建文件**: `/etc/nginx/sites-available/bill-import`

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;

    # 上传文件大小限制
    client_max_body_size 50M;

    # 超时配置
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 2.3 Systemd服务配置

**新建文件**: `/etc/systemd/system/bill-import.service`

```ini
[Unit]
Description=Notion Bill Import Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/bill-import
Environment="PATH=/opt/bill-import/venv/bin"
ExecStart=/opt/bill-import/venv/bin/python -m uvicorn web_service.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2.4 部署步骤

```bash
# 1. 克隆代码
sudo git clone <repo-url> /opt/bill-import

# 2. 配置环境变量
sudo cp /opt/bill-import/.env.example /opt/bill-import/.env
sudo nano /opt/bill-import/.env  # 填入配置

# 3. 设置权限
sudo chown -R www-data:www-data /opt/bill-import
sudo chown -R www-data:www-data /var/www/bill-uploads
sudo chown -R www-data:www-data /var/log/bill-service

# 4. 启用Nginx配置
sudo ln -s /etc/nginx/sites-available/bill-import /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 5. 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 6. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable bill-import
sudo systemctl start bill-import

# 7. 配置防火墙
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 第三阶段：微信小程序开发

### 3.1 小程序项目结构

```
miniprogram/
├── app.js                    # 小程序入口
├── app.json                  # 小程序配置
├── app.wxss                  # 全局样式
├── sitemap.json              # 站点地图
├── project.config.json       # 项目配置
├── pages/
│   ├── index/                # 首页
│   │   ├── index.js
│   │   ├── index.json
│   │   ├── index.wxml
│   │   └── index.wxss
│   ├── upload/               # 上传页面
│   │   ├── upload.js
│   │   ├── upload.json
│   │   ├── upload.wxml
│   │   └── upload.wxss
│   ├── files/                # 文件列表
│   │   ├── files.js
│   │   ├── files.json
│   │   ├── files.wxml
│   │   └── files.wxss
│   └── settings/             # 设置页面
│       ├── settings.js
│       ├── settings.json
│       ├── settings.wxml
│       └── settings.wxss
├── utils/
│   ├── api.js                # API请求封装
│   └── constants.js          # 常量定义
└── components/
    └── file-card/            # 文件卡片组件
        ├── file_card.js
        ├── file_card.json
        ├── file_card.wxml
        └── file_card.wxss
```

### 3.2 核心代码

**utils/api.js**:
```javascript
const API_BASE_URL = 'https://your-domain.com/api';

function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    const apiKey = wx.getStorageSync('apiKey') || '';

    wx.request({
      url: `${API_BASE_URL}${url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      },
      timeout: 60000,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(res.data);
        }
      },
      fail: reject
    });
  });
}

function uploadFile(filePath, formData = {}) {
  return new Promise((resolve, reject) => {
    const apiKey = wx.getStorageSync('apiKey') || '';

    wx.uploadFile({
      url: `${API_BASE_URL}/upload`,
      filePath,
      name: 'file',
      formData,
      header: {
        'X-API-Key': apiKey
      },
      timeout: 120000,
      success: (res) => {
        const data = JSON.parse(res.data);
        if (data.success) {
          resolve(data);
        } else {
          reject(data);
        }
      },
      fail: reject
    });
  });
}

module.exports = {
  getPlatforms: () => request('/config/platforms'),
  validateApiKey: () => request('/auth/validate', { method: 'POST' }),
  uploadFile,
  getFiles: () => request('/files'),
  deleteFile: (fileName) => request(`/file/${encodeURIComponent(fileName)}`, { method: 'DELETE' }),
  getServiceInfo: () => request('/service-info')
};
```

**pages/upload/upload.js**:
```javascript
const api = require('../../utils/api');

Page({
  data: {
    platforms: [],
    selectedPlatform: '',
    uploading: false,
    uploadProgress: 0
  },

  onLoad() {
    this.loadPlatforms();
  },

  async loadPlatforms() {
    try {
      const res = await api.getPlatforms();
      this.setData({ platforms: res.platforms });
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'error' });
    }
  },

  onPlatformChange(e) {
    this.setData({ selectedPlatform: this.data.platforms[e.detail.value].id });
  },

  chooseFile() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['csv', 'txt', 'xls', 'xlsx'],
      success: (res) => {
        const file = res.tempFiles[0];
        this.uploadFile(file);
      }
    });
  },

  async uploadFile(file) {
    this.setData({ uploading: true, uploadProgress: 0 });

    const uploadTask = api.uploadFile(file.path, {
      platform: this.data.selectedPlatform,
      sync_type: 'immediate'
    });

    uploadTask.onProgressUpdate((res) => {
      this.setData({ uploadProgress: res.progress });
    });

    try {
      const result = await uploadTask;
      wx.showToast({ title: '上传成功', icon: 'success' });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    } catch (e) {
      wx.showToast({ title: e.message || '上传失败', icon: 'error' });
    } finally {
      this.setData({ uploading: false, uploadProgress: 0 });
    }
  }
});
```

**pages/upload/upload.wxml**:
```xml
<view class="container">
  <view class="form-item">
    <text class="label">支付平台</text>
    <picker mode="selector" range="{{platforms}}" range-key="name" bindchange="onPlatformChange">
      <view class="picker">
        {{selectedPlatform ? platforms[platforms.findIndex(p => p.id === selectedPlatform)].name : '请选择（可选自动检测）'}}
      </view>
    </picker>
  </view>

  <button type="primary" bindtap="chooseFile" disabled="{{uploading}}">
    选择账单文件
  </button>

  <view wx:if="{{uploading}}" class="progress">
    <text>上传中... {{uploadProgress}}%</text>
    <progress percent="{{uploadProgress}}" stroke-width="4" />
  </view>

  <view class="tips">
    <text class="tips-title">支持的文件格式：</text>
    <text>.csv, .txt, .xls, .xlsx</text>
  </view>
</view>
```

### 3.3 小程序配置

**app.json**:
```json
{
  "pages": [
    "pages/index/index",
    "pages/upload/upload",
    "pages/files/files",
    "pages/settings/settings"
  ],
  "window": {
    "backgroundTextStyle": "light",
    "navigationBarBackgroundColor": "#1890ff",
    "navigationBarTitleText": "账单导入",
    "navigationBarTextStyle": "white",
    "backgroundColor": "#f5f5f5"
  },
  "networkTimeout": {
    "request": 60000,
    "uploadFile": 120000,
    "downloadFile": 60000
  },
  "sitemapLocation": "sitemap.json"
}
```

### 3.4 微信小程序平台配置

1. **注册小程序账号**: https://mp.weixin.qq.com/
2. **配置服务器域名白名单**:
   - 登录小程序管理后台
   - 开发 → 开发管理 → 开发设置 → 服务器域名
   - 添加: `https://your-domain.com`

3. **配置业务域名**（如果需要）:
   - 同样在开发设置中配置

---

## 关键文件清单

### 需要修改的文件

| 文件路径 | 修改内容 |
|---------|---------|
| `config.py` | 新增 `API_KEYS`, `SERVER_HOST`, `SERVER_PORT` 配置项 |
| `web_service/main.py` | 添加 `APIKeyMiddleware` 中间件 |
| `web_service/routes/upload.py` | 新增 `/config/platforms` 和 `/auth/validate` 端点 |
| `.env.example` | 添加API认证和服务器配置示例 |

### 需要新建的文件

| 文件路径 | 用途 |
|---------|------|
| `web_service/middleware/auth.py` | API Key认证中间件 |
| `web_service/middleware/__init__.py` | 中间件包初始化 |
| `/etc/nginx/sites-available/bill-import` | Nginx配置 |
| `/etc/systemd/system/bill-import.service` | Systemd服务配置 |

### 微信小程序文件

| 文件路径 | 用途 |
|---------|------|
| `miniprogram/utils/api.js` | API请求封装 |
| `miniprogram/pages/upload/*` | 上传页面 |
| `miniprogram/pages/files/*` | 文件列表页面 |
| `miniprogram/pages/settings/*` | 设置页面 |

---

## 验证步骤

### 后端验证

```bash
# 1. 启动服务
sudo systemctl start bill-import

# 2. 检查服务状态
sudo systemctl status bill-import

# 3. 查看日志
sudo journalctl -u bill-import -f

# 4. 测试API（无认证）
curl https://your-domain.com/api/service-info

# 5. 测试API（带认证）
curl -X POST -H "X-API-Key: your_key" https://your-domain.com/api/auth/validate
```

### 小程序验证

1. **开发者工具测试**:
   - 打开微信开发者工具
   - 导入小程序项目
   - 测试文件选择和上传功能

2. **真机测试**:
   - 预览到手机
   - 从微信聊天选择文件上传
   - 验证Notion同步结果

---

## 安全建议

1. **API Key管理**:
   - 使用强随机密钥（至少32字符）
   - 定期轮换密钥
   - 不同用户使用不同密钥

2. **HTTPS强制**:
   - Nginx自动重定向HTTP到HTTPS
   - 使用TLS 1.2+

3. **请求频率限制**（可选）:
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   @limiter.limit("60/minute")
   ```

4. **文件验证**:
   - 验证文件扩展名
   - 限制文件大小
   - 扫描恶意内容

---

## 成本估算

| 项目 | 费用 |
|-----|------|
| 云服务器（2核2GB） | ¥200-500/月 |
| 域名 | ¥50-100/年 |
| SSL证书 | 免费（Let's Encrypt） |
| 小程序认证 | ¥300/年（如需） |

---

## 预估时间

| 阶段 | 时间 |
|-----|------|
| 后端改造 | 1-2天 |
| 服务器部署 | 1天 |
| 小程序开发 | 3-4天 |
| 测试调试 | 1-2天 |
| **总计** | **6-9天** |
