# Notion Bill Importer - 设计系统

**版本**: 3.0
**更新日期**: 2026-02-05
**设计风格**: Ethereal Fintech Pro → Clean Professional Dashboard

---

## 1. 设计理念

### 1.1 核心原则

| 原则 | 描述 | 应用 |
|------|------|------|
| **清晰至上** | 信息层次清晰，减少认知负担 | 高对比度文本，明确的功能分组 |
| **专业可信** | 传达专业性和可靠性 | 统一的视觉语言，精致的细节 |
| **现代简约** | 去除不必要的装饰 | 留白运用，简化视觉元素 |
| **响应优先** | 任何设备上都能良好使用 | 移动优先，渐进增强 |
| **无障碍友好** | 所有人都能使用 | WCAG 2.1 AA标准，键盘导航 |

### 1.2 品牌定位

- **产品类型**: 财务管理SaaS工具
- **目标用户**: 个人用户、小企业主、财务人员
- **品牌个性**: 专业、高效、可信、现代
- **情感诉求**: 让财务管理变得简单优雅

---

## 2. 色彩系统

### 2.1 主色调

```css
/* 品牌主色 - 专业蓝紫 */
--color-primary: #6366f1;        /* Indigo 500 */
--color-primary-light: #818cf8;  /* Indigo 400 */
--color-primary-dark: #4f46e5;   /* Indigo 600 */

/* 渐变应用 */
--gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--gradient-primary-hover: linear-gradient(135deg, #5a67d8 0%, #6b46a0 100%);
```

**使用场景**:
- 主要操作按钮（CTA）
- 重要链接和导航高亮
- 品牌识别元素
- 进度指示器

### 2.2 功能色

```css
/* 成功 - 收入/完成 */
--color-success: #10b981;
--color-success-light: #d1fae5;
--color-success-dark: #047857;

/* 警告 - 待处理/注意事项 */
--color-warning: #f59e0b;
--color-warning-light: #fef3c7;
--color-warning-dark: #b45309;

/* 错误 - 支出/失败 */
--color-error: #ef4444;
--color-error-light: #fee2e2;
--color-error-dark: #b91c1c;

/* 信息 - 中性/提示 */
--color-info: #3b82f6;
--color-info-light: #dbeafe;
--color-info-dark: #1d4ed8;
```

**使用规则**:
- 收入显示用绿色
- 支出显示用红色
- 警告状态用黄色
- 一般信息用蓝色

### 2.3 中性色系

```css
/* 文本色 */
--text-primary: #1e293b;      /* 主要文本 */
--text-secondary: #475569;    /* 次要文本 */
--text-muted: #94a3b8;        /* 弱化文本 */
--text-inverse: #ffffff;      /* 反色文本 */

/* 背景色 */
--bg-primary: #f8fafc;        /* 主背景 */
--bg-secondary: #ffffff;      /* 卡片/容器背景 */
--bg-tertiary: #f1f5f9;       /* 三级背景 */

/* 边框色 */
--border-light: #e2e8f0;      /* 浅边框 */
--border-medium: #cbd5e1;     /* 中等边框 */
--border-dark: #94a3b8;       /* 深边框 */
```

### 2.4 对比度要求

所有文本必须满足WCAG AA标准:
- **正常文本**: 最小4.5:1
- **大文本(18px+)**: 最小3:1
- **UI组件**: 最小3:1

---

## 3. 字体系统

### 3.1 字体家族

```css
/* Display字体 - 标题和品牌 */
--font-display: 'Outfit', -apple-system, sans-serif;

/* Body字体 - 正文内容 */
--font-body: 'DM Sans', -apple-system, sans-serif;

/* Mono字体 - 代码和数据 */
--font-mono: 'JetBrains Mono', 'SF Mono', monospace;
```

### 3.2 字体 scale

```css
--text-xs: 0.75rem;    /* 12px - 辅助信息 */
--text-sm: 0.875rem;   /* 14px - 次要文本 */
--text-base: 1rem;     /* 16px - 正文 */
--text-lg: 1.125rem;   /* 18px - 强调文本 */
--text-xl: 1.25rem;    /* 20px - 小标题 */
--text-2xl: 1.5rem;    /* 24px - 标题 */
--text-3xl: 1.875rem;  /* 30px - 大标题 */
--text-4xl: 2.25rem;   /* 36px - Hero标题 */
```

### 3.3 字重

```css
--font-normal: 400;    /* 正文 */
--font-medium: 500;    /* 强调 */
--font-semibold: 600;  /* 小标题 */
--font-bold: 700;      /* 标题 */
--font-extrabold: 800; /* 大标题 */
```

### 3.4 行高

```css
--leading-tight: 1.25;   /* 标题 */
--leading-normal: 1.5;   /* 正文 */
--leading-relaxed: 1.75; /* 长文本 */
```

---

## 4. 间距系统

基于4px网格的间距比例：

```css
--space-1: 4px;      /* 极小间距 */
--space-2: 8px;      /* 小间距 */
--space-3: 12px;     /* 默认间距 */
--space-4: 16px;     /* 常用间距 */
--space-5: 20px;     /* 中等间距 */
--space-6: 24px;     /* 大间距 */
--space-8: 32px;     /* 超大间距 */
--space-10: 40px;    /* 区域间距 */
--space-12: 48px;    /* 章节间距 */
--space-16: 64px;    /* 页面边距 */
```

**使用指南**:
- 组件内部: `space-2` ~ `space-4`
- 组件之间: `space-4` ~ `space-6`
- 区域分隔: `space-8` ~ `space-12`
- 页面边距: `space-6` ~ `space-16`

---

## 5. 组件规范

### 5.1 按钮 (Buttons)

#### 尺寸

| 尺寸 | 高度 | 内边距 | 字体大小 |
|------|------|--------|----------|
| sm | 32px | 6px 12px | 14px |
| md | 40px | 10px 16px | 16px |
| lg | 48px | 12px 24px | 16px |

#### 变体

**主按钮 (Primary)**
```css
.btn-primary {
  background: var(--gradient-primary);
  color: white;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn-primary:hover {
  background: var(--gradient-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(99, 102, 241, 0.3);
}
```

**次要按钮 (Secondary)**
```css
.btn-secondary {
  background: white;
  border: 1px solid var(--border-medium);
  color: var(--text-primary);
}
```

**幽灵按钮 (Ghost)**
```css
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}
```

#### 状态规则

- **悬停**: 所有可点击按钮必须有悬停反馈
- **禁用**: `opacity: 0.6` + `cursor: not-allowed`
- **加载**: 显示spinner，禁用点击
- **焦点**: `outline: 2px solid var(--color-primary)`

### 5.2 卡片 (Cards)

```css
.card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: var(--transition-base);
}

.card:hover {
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}
```

**变体**:
- **玻璃卡片**: 添加 `backdrop-filter: blur(12px)` + 半透明背景
- **可点击卡片**: 添加悬停效果 + `cursor: pointer`
- **紧凑卡片**: 减少内边距到 16px

### 5.3 表单 (Forms)

**输入框**
```css
.input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-medium);
  border-radius: 8px;
  font-size: 16px;
  transition: var(--transition-base);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.input.error {
  border-color: var(--color-error);
}

.input.success {
  border-color: var(--color-success);
}
```

**标签**
```css
.label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.label.required::after {
  content: '*';
  color: var(--color-error);
  margin-left: 4px;
}
```

### 5.4 模态框 (Modals)

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 16px;
  padding: 24px;
  max-width: 500px;
  width: 90%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
}
```

### 5.5 Toast通知

```css
.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
  animation: slideIn 0.3s ease-out;
}

.toast.success {
  border-left: 4px solid var(--color-success);
}

.toast.error {
  border-left: 4px solid var(--color-error);
}

.toast.warning {
  border-left: 4px solid var(--color-warning);
}
```

---

## 6. 布局系统

### 6.1 响应式断点

```css
--breakpoint-xs: 375px;   /* 小手机 */
--breakpoint-sm: 640px;   /* 手机 */
--breakpoint-md: 768px;   /* 平板竖屏 */
--breakpoint-lg: 1024px;  /* 平板横屏/小笔记本 */
--breakpoint-xl: 1280px;  /* 桌面 */
--breakpoint-2xl: 1536px; /* 大屏 */
```

### 6.2 容器

```css
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
}

@media (max-width: 768px) {
  .container {
    padding: 0 16px;
  }
}
```

### 6.3 网格系统

```css
.grid {
  display: grid;
  gap: 24px;
}

.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }

@media (max-width: 768px) {
  .grid-2, .grid-3, .grid-4 {
    grid-template-columns: 1fr;
  }
}
```

---

## 7. 动效系统

### 7.1 过渡时长

```css
--transition-instant: 100ms;   /* 即时反馈 */
--transition-fast: 150ms;      /* 快速交互 */
--transition-base: 200ms;      /* 默认过渡 */
--transition-slow: 300ms;      /* 复杂动画 */
--transition-slower: 500ms;    /* 页面切换 */
```

### 7.2 缓动函数

```css
--ease-out: cubic-bezier(0, 0, 0.2, 1);      /* 减速 */
--ease-in: cubic-bezier(0.4, 0, 1, 1);       /* 加速 */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1); /* 加速减速 */
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1); /* 弹性 */
```

### 7.3 动画原则

1. **目的驱动**: 每个动画都有明确目的
2. **自然流畅**: 模仿真实世界物理
3. **性能优先**: 使用transform和opacity
4. **尊重设置**: 支持`prefers-reduced-motion`

---

## 8. 阴影系统

```css
--shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
--shadow-2xl: 0 25px 50px rgba(0, 0, 0, 0.25);

/* 内阴影 */
--shadow-inner: inset 0 2px 4px rgba(0, 0, 0, 0.05);

/* 彩色阴影 */
--shadow-primary: 0 4px 14px rgba(99, 102, 241, 0.3);
--shadow-success: 0 4px 14px rgba(16, 185, 129, 0.3);
--shadow-error: 0 4px 14px rgba(239, 68, 68, 0.3);
```

---

## 9. 图标系统

### 9.1 图标规范

- **来源**: Heroicons / Lucide
- **格式**: SVG
- **尺寸**: 24x24px (可缩放)
- **描边**: 2px stroke-width

### 9.2 使用规则

```html
<!-- 图标按钮 -->
<button class="btn-icon">
  <svg class="icon" width="20" height="20">
    <!-- icon path -->
  </svg>
</button>

<!-- 带文本的图标 -->
<div class="flex items-center gap-2">
  <svg class="icon" width="16" height="16">
    <!-- icon path -->
  </svg>
  <span>文本</span>
</div>
```

### 9.3 颜色使用

- **默认**: 继承文本颜色
- **主色**: `fill: currentColor; color: var(--color-primary)`
- **弱化**: `color: var(--text-muted)`

---

## 10. 特殊效果

### 10.1 玻璃态 (Glassmorphism)

```css
.glass {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
}

@media (prefers-color-scheme: dark) {
  .glass {
    background: rgba(15, 23, 42, 0.75);
  }
}
```

**使用场景**:
- 导航栏
- 浮动面板
- 模态框背景

### 10.2 渐变效果

```css
/* 主渐变 */
.gradient-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 成功渐变 */
.gradient-success {
  background: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%);
}

/* 警告渐变 */
.gradient-warning {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}
```

---

## 11. 无障碍 (Accessibility)

### 11.1 键盘导航

- 所有交互元素可通过Tab访问
- 焦点指示清晰可见
- 逻辑焦点顺序

### 11.2 ARIA标签

```html
<!-- 按钮 -->
<button aria-label="关闭对话框">
  <svg>...</svg>
</button>

<!-- 表单 -->
<label for="email">邮箱</label>
<input id="email" type="email" required aria-required="true">

<!-- 状态 -->
<div role="status" aria-live="polite">操作成功</div>
```

### 11.3 色彩对比度

使用工具验证: https://webaim.org/resources/contrastchecker/

### 11.4 动效偏好

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 12. 暗色模式

### 12.1 色彩调整

```css
@media (prefers-color-scheme: dark) {
  :root {
    /* 背景调暗 */
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;

    /* 文本提亮 */
    --text-primary: #f1f5f9;
    --text-secondary: #cbd5e1;
    --text-muted: #64748b;

    /* 边框调整 */
    --border-light: #334155;
    --border-medium: #475569;

    /* 玻璃态更不透明 */
    --glass-bg: rgba(15, 23, 42, 0.85);
  }
}
```

### 12.2 对比度检查

暗色模式下同样需要满足对比度要求，特别注意:
- 玻璃卡片需要足够不透明度
- 文本在深色背景上清晰可读
- 边框在深色背景上可见

---

## 13. 性能优化

### 13.1 CSS优化

- 使用CSS自定义属性减少重复
- 避免深层嵌套选择器
- 使用contain属性优化渲染
- will-change提前告知浏览器

### 13.2 资源加载

```html
<!-- 字体预加载 -->
<link rel="preload" href="/fonts/outfit.woff2" as="font" crossorigin>

<!-- 关键CSS内联 -->
<style>
  /* 首屏关键样式 */
</style>

<!-- 非关键CSS异步加载 -->
<link rel="preload" href="/styles.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
```

### 13.3 图片优化

- 使用WebP格式
- 响应式图片(srcset)
- 懒加载(loading="lazy")
- 图片压缩

---

## 14. 浏览器支持

| 浏览器 | 版本 |
|--------|------|
| Chrome | 最新+2版本 |
| Firefox | 最新+2版本 |
| Safari | 14+ |
| Edge | 最新+2版本 |
| Mobile Safari | 14+ |
| Chrome Android | 最新+2版本 |

### 渐进增强

基础功能在所有浏览器可用，现代效果在支持的浏览器中优雅降级。

---

## 15. 代码规范

### 15.1 CSS类命名

使用BEM方法论:

```css
/* Block */
.card {}

/* Block__modifier */
.card--featured {}

/* Block__element */
.card__title {}

/* Block__element--modifier */
.card__title--large {}
```

### 15.2 组织结构

```css
/* 1. CSS变量 */
:root {}

/* 2. 基础样式 */
html, body {}

/* 3. 布局组件 */
.container, .grid {}

/* 4. UI组件 */
.btn, .card, .input {}

/* 5. 工具类 */
.text-center, .mt-4 {}

/* 6. 响应式 */
@media (max-width: 768px) {}
```

### 15.3 注释规范

```css
/* ========================================
   组件名称 - 简短描述
   ======================================== */

/**
 * 详细说明
 * @author 作者
 * @version 版本
 */
```

---

## 16. 设计交付清单

### 16.1 设计文件

- [ ] 完整的UI设计稿(Figma/Sketch)
- [ ] 组件库文档
- [ ] 交互原型
- [ ] 动效说明

### 16.2 开发资源

- [ ] SVG图标文件
- [ ] 字体文件
- [ ] 设计token导出
- [ ] 切图资源

### 16.3 测试

- [ ] 浏览器兼容性测试
- [ ] 响应式测试
- [ ] 无障碍测试
- [ ] 性能测试

---

## 17. 变更日志

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 3.0 | 2026-02-05 | 统一设计系统，整合variables.css和workspace.css |
| 2.0 | 2025-12-XX | 添加Ethereal Fintech Pro风格 |
| 1.0 | 2025-XX-XX | 初始版本 |

---

## 18. 快速参考

### 常用颜色

- 主色: `#6366f1`
- 成功: `#10b981`
- 警告: `#f59e0b`
- 错误: `#ef4444`

### 常用间距

- 小: `8px`
- 默认: `16px`
- 大: `24px`
- 超大: `32px`

### 常用圆角

- 小: `4px`
- 默认: `8px`
- 大: `12px`
- 超大: `16px`

### 常用阴影

- 浅: `0 1px 2px rgba(0,0,0,0.05)`
- 默认: `0 4px 6px rgba(0,0,0,0.1)`
- 深: `0 10px 15px rgba(0,0,0,0.1)`

---

**维护者**: Claude Code
**最后更新**: 2026-02-05
