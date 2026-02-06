# Implementation Phase Prompt

## 端到端交付 - Implementation Phase（实施执行阶段）

### 任务目标
根据架构设计报告，实现Dashboard视图的核心功能，包括财务概览卡片、活动时间线和数据刷新功能。

### 实施范围（MVP - 1周）

#### Phase 1: 基础设施（第1天）
1. 扩展dashboard API - 添加活动时间线接口
2. 创建dashboard视图HTML结构
3. 创建dashboard-view.js模块
4. 创建timeline.css样式文件

#### Phase 2: 核心组件（第2-3天）
1. 实现StatCard组件（收入、支出、余额、交易数）
2. 实现ActivityTimeline组件
3. 实现RefreshManager组件
4. 实现LoadingState组件

#### Phase 3: 集成与交互（第4天）
1. 集成到workspace.js的视图切换
2. 实现数据刷新功能
3. 实现错误处理
4. 添加Toast通知

#### Phase 4: 优化与测试（第5天）
1. 性能优化
2. 响应式测试
3. 跨浏览器测试
4. 无障碍检查

### 技术规范

#### 前端技术
- 纯JavaScript（无框架）
- CSS变量（已有variables.css）
- 组件化架构
- 简单状态管理

#### 后端技术
- FastAPI
- SQLAlchemy ORM
- 统一响应格式：`{success, data/message}`

#### 设计规范
- 颜色：使用CSS变量（--color-primary-*等）
- 间距：8px网格系统
- 字体：Outfit + DM Sans
- 圆角：--radius-md (8px)
- 阴影：--shadow-sm, --shadow-md

### 实施要求

1. **遵循TDD原则**
   - 先写测试（如果适用）
   - 保持简单，避免过度设计

2. **代码质量**
   - 遵循项目代码风格指南
   - 添加适当的注释
   - 保持函数简短（<50行）

3. **用户体验**
   - 加载状态反馈
   - 错误提示友好
   - 动画流畅（150-300ms）

4. **可维护性**
   - 组件化结构
   - 清晰的命名
   - 一致的代码风格

### 需要修改/创建的文件

#### 修改现有文件
1. `web_service/routes/dashboard.py` - 扩展API
2. `web_service/static/js/workspace.js` - 集成dashboard视图
3. `web_service/static/css/workspace-views.css` - 添加dashboard样式

#### 新增文件
1. `web_service/static/js/dashboard-view.js` - Dashboard视图逻辑
2. `web_service/static/css/timeline.css` - 时间线样式
3. `web_service/static/js/components/stat-card.js` - 统计卡片组件（可选）
4. `web_service/static/js/components/activity-timeline.js` - 时间线组件（可选）

### 实施步骤

请按照以下步骤实施：

1. **首先阅读现有代码**
   - web_service/routes/dashboard.py
   - web_service/static/js/workspace.js
   - web_service/templates/workspace.html
   - web_service/static/css/workspace-views.css

2. **然后创建/修改文件**
   - 按照Phase顺序实施
   - 每个Phase完成后验证功能
   - 提交代码（如果使用git）

3. **最后进行集成测试**
   - 测试所有视图切换
   - 测试数据刷新
   - 测试错误处理
   - 测试跨浏览器兼容性

### 成功标准

- [ ] Dashboard视图显示4个财务卡片
- [ ] 活动时间线正确显示
- [ ] 手动刷新功能正常工作
- [ ] 所有动画流畅
- [ ] 错误处理友好
- [ ] 代码符合项目规范
- [ ] 浏览器兼容性良好

请开始执行实施阶段，按照Phase顺序逐步实现功能。
