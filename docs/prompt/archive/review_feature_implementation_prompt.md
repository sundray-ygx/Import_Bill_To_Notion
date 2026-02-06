# 账单复盘功能前端集成 - 实施执行阶段提示词

## 项目信息
- **功能名称**: 账单复盘功能前端集成
- **项目**: Notion Bill Importer
- **实施日期**: 2026-02-03
- **编程语言**: Python (FastAPI), HTML, CSS, JavaScript (Vanilla)

---

## 输入上下文

### 设计方案（来自 Design 阶段）
**推荐方案C（混合方案）**：
- 在设置页面添加复盘配置section
- 在账单导入成功后显示复盘提示Banner
- 创建轻量级复盘管理页面

### 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `web_service/templates/review.html` | 新建 | 轻量级复盘管理页面 |
| `web_service/static/js/review.js` | 新建 | 复盘页面逻辑 |
| `web_service/static/css/review.css` | 新建 | 复盘页面样式 |
| `web_service/templates/components/navbar.html` | 修改 | 添加复盘导航链接 |
| `web_service/main.py` | 修改 | 添加 `/review` 路由和注册 review router |
| `web_service/templates/settings.html` | 修改 | 添加复盘配置section |
| `web_service/templates/bill_management.html` | 修改 | 添加复盘提示Banner |
| `web_service/static/js/settings.js` | 修改 | 添加复盘配置逻辑 |
| `web_service/static/css/settings.css` | 修改 | 添加复盘样式 |

### 后端API
- POST `/api/review/generate` - 生成复盘报告
- POST `/api/review/batch` - 批量生成复盘
- GET `/api/review/config` - 获取复盘配置
- POST `/api/review/config` - 更新复盘配置
- GET `/api/review/preview` - 预览复盘数据

### 技术约束
1. 项目使用原生JavaScript，不使用前端框架
2. 需要在main.py中注册review router（目前未注册）
3. 设计需与现有UI风格保持一致

---

## 实施任务

### Phase 1: 基础设置（注册Review Router）
**文件**: `web_service/main.py`
- 添加 `/review` 路由页面
- 注册 review router

### Phase 2: 设置页面集成
**文件**: `web_service/templates/settings.html`, `web_service/static/js/settings.js`, `web_service/static/css/settings.css`
- 添加复盘配置section（侧边栏导航项 + 内容区）
- 实现复盘配置表单（数据库ID、模板ID）
- 实现配置保存和验证功能

### Phase 3: 账单导入智能提示
**文件**: `web_service/templates/bill_management.html`
- 在导入成功后显示复盘提示Banner
- 实现一键生成复盘功能
- 添加关闭/稍后选项

### Phase 4: 复盘管理页面
**文件**: `web_service/templates/review.html`, `web_service/static/js/review.js`, `web_service/static/css/review.css`
- 创建轻量级复盘管理页面
- 实现快速生成卡片
- 实现生成复盘模态框（含预览）
- 实现复盘报告列表

### Phase 5: 导航集成
**文件**: `web_service/templates/components/navbar.html`
- 在导航栏添加复盘入口

---

## 编码规范

### Python 代码规范
- 遵循 PEP 8
- 使用类型提示
- 编写 docstring

### JavaScript 代码规范
- 使用严格模式 `'use strict'`
- 避免全局变量污染
- 使用 async/await 处理异步
- 统一错误处理

### HTML/CSS 规范
- 使用语义化标签
- 保持与现有样式一致
- 响应式设计支持

---

## 输出要求

实施完成后，请提供：

1. **代码变更摘要** - 修改/创建的文件列表和变更说明
2. **代码审查检查表** - 自审检查结果
3. **测试结果** - 功能测试结果
4. **遗留问题** - 如有未完成或已知问题

---

## 重要提醒

1. **必须先注册 review router** - 这是技术债务，必须优先解决
2. **保持代码风格一致** - 参考现有代码的命名和结构
3. **充分测试** - 确保所有功能正常工作
4. **保存阶段文档** - 将实施文档保存到 `/docs/` 目录
