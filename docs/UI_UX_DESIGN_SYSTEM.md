# Notion Bill Importer - UI/UX 设计系统规范

> 版本: 2.0
> 更新日期: 2025-02-05
> 设计风格: Ethereal Fintech Pro (空灵金融科技专业版)

---

## 1. 设计理念

### 1.1 核心原则
- **专业可信**: 金融级别的数据安全感和可靠性
- **清晰高效**: 信息层次分明，操作流程简洁
- **现代优雅**: 玻璃态设计语言，未来科技感
- **多租户友好**: 支持品牌化和个性化配置

### 1.2 设计关键词
```
Fintech Professional / Glassmorphism / Trustworthy / Modern SaaS / Multi-tenant
```

---

## 2. 色彩系统

### 2.1 主色调 (Primary Colors)
```css
:root {
  /* 品牌主色 - 紫色渐变 */
  --color-primary-50: #f5f3ff;
  --color-primary-100: #ede9fe;
  --color-primary-200: #ddd6fe;
  --color-primary-300: #c4b5fd;
  --color-primary-400: #a78bfa;
  --color-primary-500: #8b5cf6;
  --color-primary-600: #7c3aed;
  --color-primary-700: #6d28d9;
  --color-primary-800: #5b21b6;
  --color-primary-900: #4c1d95;

  /* 主色渐变 */
  --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-primary-hover: linear-gradient(135deg, #5a67d8 0%, #6b46a0 100%);
}
```

### 2.2 功能色 (Semantic Colors)
```css
:root {
  /* 成功 */
  --color-success-50: #ecfdf5;
  --color-success-500: #10b981;
  --color-success-600: #059669;

  /* 错误 */
  --color-error-50: #fef2f2;
  --color-error-500: #ef4444;
  --color-error-600: #dc2626;

  /* 警告 */
  --color-warning-50: #fffbeb;
  --color-warning-500: #f59e0b;
  --color-warning-600: #d97706;

  /* 信息 */
  --color-info-50: #eff6ff;
  --color-info-500: #3b82f6;
  --color-info-600: #2563eb;
}
```

### 2.3 中性色 (Neutral Colors)
```css
:root {
  /* 亮色模式 */
  --color-slate-50: #f8fafc;
  --color-slate-100: #f1f5f9;
  --color-slate-200: #e2e8f0;
  --color-slate-300: #cbd5e1;
  --color-slate-400: #94a3b8;
  --color-slate-500: #64748b;
  --color-slate-600: #475569;
  --color-slate-700: #334155;
  --color-slate-800: #1e293b;
  --color-slate-900: #0f172a;
}
```

### 2.4 玻璃态效果 (Glassmorphism)
```css
:root {
  /* 毛玻璃效果 */
  --glass-bg-light: rgba(255, 255, 255, 0.85);
  --glass-bg-dark: rgba(15, 23, 42, 0.75);
  --glass-border: rgba(255, 255, 255, 0.18);
  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  --glass-blur: blur(12px);
}
```

---

## 3. 字体系统

### 3.1 字体族 (Font Families)
```css
:root {
  /* 主字体 */
  --font-display: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-body: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
}
```

### 3.2 字体大小 (Font Sizes)
```css
:root {
  --font-xs: 0.75rem;     /* 12px */
  --font-sm: 0.875rem;    /* 14px */
  --font-base: 1rem;      /* 16px */
  --font-lg: 1.125rem;    /* 18px */
  --font-xl: 1.25rem;     /* 20px */
  --font-2xl: 1.5rem;     /* 24px */
  --font-3xl: 1.875rem;   /* 30px */
  --font-4xl: 2.25rem;    /* 36px */
  --font-5xl: 3rem;       /* 48px */
}
```

### 3.3 行高 (Line Heights)
```css
:root {
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;
}
```

### 3.4 字重 (Font Weights)
```css
:root {
  --font-light: 300;
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
}
```

---

## 4. 间距系统

### 4.1 间距刻度 (Spacing Scale)
```css
:root {
  --spacing-0: 0;
  --spacing-px: 1px;
  --spacing-0_5: 2px;
  --spacing-1: 4px;
  --spacing-2: 8px;
  --spacing-3: 12px;
  --spacing-4: 16px;
  --spacing-5: 20px;
  --spacing-6: 24px;
  --spacing-8: 32px;
  --spacing-10: 40px;
  --spacing-12: 48px;
  --spacing-16: 64px;
  --spacing-20: 80px;
  --spacing-24: 96px;
}
```

### 4.2 容器宽度 (Container Widths)
```css
:root {
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;
  --container-2xl: 1536px;
}
```

---

## 5. 圆角系统

```css
:root {
  --radius-none: 0;
  --radius-sm: 4px;
  --radius-base: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 20px;
  --radius-3xl: 24px;
  --radius-full: 9999px;
}
```

---

## 6. 阴影系统

```css
:root {
  /* 基础阴影 */
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-base: 0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04);
  --shadow-xl: 0 25px 50px rgba(0, 0, 0, 0.25);

  /* 内阴影 */
  --shadow-inner: inset 0 2px 4px rgba(0, 0, 0, 0.06);

  /* 玻璃态阴影 */
  --shadow-glass: 0 8px 32px rgba(31, 38, 135, 0.15);
}
```

---

## 7. 动画系统

### 7.1 缓动函数 (Easing)
```css
:root {
  --ease-linear: linear;
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
```

### 7.2 持续时间 (Duration)
```css
:root {
  --duration-75: 75ms;
  --duration-100: 100ms;
  --duration-150: 150ms;
  --duration-200: 200ms;
  --duration-300: 300ms;
  --duration-500: 500ms;
  --duration-700: 700ms;
  --duration-1000: 1000ms;
}
```

### 7.3 动画规则
- **微交互**: 150-200ms
- **页面切换**: 300-400ms
- **复杂动画**: 500ms以内
- **尊重用户偏好**: 检测 `prefers-reduced-motion`

---

## 8. Z-Index 层级

```css
:root {
  --z-dropdown: 1000;
  --z-sticky: 1020;
  --z-fixed: 1030;
  --z-modal-backdrop: 1040;
  --z-modal: 1050;
  --z-popover: 1060;
  --z-tooltip: 1070;
  --z-toast: 1080;
}
```

---

## 9. 组件规范

### 9.1 按钮 (Buttons)

#### 主按钮 (Primary Button)
```css
.btn-primary {
  background: var(--gradient-primary);
  color: white;
  padding: var(--spacing-3) var(--spacing-6);
  border-radius: var(--radius-lg);
  font-weight: var(--font-semibold);
  transition: all var(--duration-200) var(--ease-out);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  border: none;
}

.btn-primary:hover {
  background: var(--gradient-primary-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
```

#### 次要按钮 (Secondary Button)
```css
.btn-secondary {
  background: var(--glass-bg-light);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  color: var(--color-slate-700);
  padding: var(--spacing-3) var(--spacing-6);
  border-radius: var(--radius-lg);
  font-weight: var(--font-medium);
  transition: all var(--duration-200) var(--ease-out);
  cursor: pointer;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: var(--shadow-sm);
}
```

### 9.2 输入框 (Inputs)
```css
.input {
  width: 100%;
  padding: var(--spacing-3) var(--spacing-4);
  background: white;
  border: 1px solid var(--color-slate-200);
  border-radius: var(--radius-md);
  font-size: var(--font-base);
  transition: all var(--duration-150) var(--ease-out);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.input:disabled {
  background: var(--color-slate-50);
  cursor: not-allowed;
}

.input-error {
  border-color: var(--color-error-500);
}

.input-error:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}
```

### 9.3 卡片 (Cards)
```css
.card {
  background: var(--glass-bg-light);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-glass);
  overflow: hidden;
  transition: all var(--duration-300) var(--ease-out);
}

.card-hoverable:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### 9.4 表格 (Tables)
```css
.table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.table thead th {
  background: var(--color-slate-50);
  padding: var(--spacing-3) var(--spacing-4);
  text-align: left;
  font-weight: var(--font-semibold);
  color: var(--color-slate-700);
  border-bottom: 1px solid var(--color-slate-200);
  position: sticky;
  top: 0;
}

.table tbody td {
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--color-slate-100);
}

.table tbody tr:hover {
  background: var(--color-slate-50);
}
```

### 9.5 徽章 (Badges)
```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-1) var(--spacing-2_5);
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: var(--font-medium);
}

.badge-success {
  background: var(--color-success-50);
  color: var(--color-success-600);
}

.badge-error {
  background: var(--color-error-50);
  color: var(--color-error-600);
}

.badge-warning {
  background: var(--color-warning-50);
  color: var(--color-warning-600);
}

.badge-info {
  background: var(--color-info-50);
  color: var(--color-info-600);
}
```

---

## 10. 响应式断点

```css
/* 移动优先 */
/* 默认 < 640px (手机) */

@media (min-width: 640px) {
  /* sm: 平板竖屏 */
}

@media (min-width: 768px) {
  /* md: 平板横屏 */
}

@media (min-width: 1024px) {
  /* lg: 桌面 */
}

@media (min-width: 1280px) {
  /* xl: 大屏桌面 */
}

@media (min-width: 1536px) {
  /* 2xl: 超大屏 */
}
```

---

## 11. 无障碍访问 (Accessibility)

### 11.1 颜色对比度
- **正文文本**: 最低 4.5:1
- **大文本 (18px+)**: 最低 3:1
- **UI 组件**: 最低 3:1

### 11.2 键盘导航
- 所有交互元素可键盘访问
- 清晰的焦点状态 (`:focus`)
- Tab 顺序符合逻辑

### 11.3 语义化 HTML
- 正确使用 heading 层级
- 表单元素关联 label
- 按钮和链接有明确文案

### 11.4 ARIA 属性
```html
<!-- 模态框 -->
<div role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <h2 id="modal-title">标题</h2>
</div>

<!-- 加载状态 -->
<div role="status" aria-live="polite">
  <span class="sr-only">加载中...</span>
</div>

<!-- 图标按钮 -->
<button aria-label="关闭">
  <svg>...</svg>
</button>
```

---

## 12. 性能优化

### 12.1 CSS 优化
- 使用 CSS 变量实现主题切换
- 避免深层嵌套 (最多3层)
- 使用 transform 代替位置变化
- 使用 will-change 优化动画

### 12.2 图片优化
- 使用 WebP 格式
- 提供多种尺寸 (srcset)
- 实现懒加载

### 12.3 字体优化
- 使用 font-display: swap
- 预加载关键字体
- 使用 font-family fallback

---

## 13. 常见模式

### 13.1 加载状态
```css
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-slate-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin var(--duration-1000) linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

### 13.2 骨架屏
```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-slate-100) 0%,
    var(--color-slate-200) 50%,
    var(--color-slate-100) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-loading var(--duration-1500) ease-in-out infinite;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### 13.3 Toast 通知
```css
.toast {
  position: fixed;
  bottom: var(--spacing-6);
  right: var(--spacing-6);
  padding: var(--spacing-4) var(--spacing-5);
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  animation: slide-in var(--duration-300) var(--ease-out);
  z-index: var(--z-toast);
}

@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

---

## 14. 图标规范

### 14.1 图标库
- **推荐**: Heroicons, Lucide
- **格式**: SVG
- **尺寸**: 统一使用 24x24 viewBox

### 14.2 使用规范
```html
<!-- 正确: SVG 图标 -->
<button class="btn-primary">
  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
  </svg>
  保存
</button>

<!-- 错误: Emoji 图标 -->
<button class="btn-primary">
  ✅ 保存
</button>
```

---

## 15. 交付检查清单

在交付 UI 代码前，请确认:

### 视觉质量
- [ ] 无 emoji 图标，使用 SVG
- [ ] 图标来自一致的图标集
- [ ] Hover 状态不导致布局偏移
- [ ] 使用主题色变量，而非硬编码
- [ ] 文本对比度 >= 4.5:1

### 交互
- [ ] 所有可点击元素有 `cursor-pointer`
- [ ] Hover 状态有清晰的视觉反馈
- [ ] 过渡动画平滑 (150-300ms)
- [ ] 键盘导航有可见焦点状态

### 响应式
- [ ] 测试 375px, 768px, 1024px, 1440px
- [ ] 移动端无横向滚动
- [ ] 触控目标 >= 44x44px
- [ ] 固定导航栏留有内容间距

### 性能
- [ ] 图片懒加载
- [ ] 字体预加载
- [ ] 关键 CSS 内联
- [ ] 非关键资源异步加载

### 无障碍
- [ ] 图片有 alt 文本
- [ ] 表单有 label 关联
- [ ] 颜色非唯一指示器
- [ ] `prefers-reduced-motion` 尊重用户偏好

---

## 16. 实现优先级

| 优先级 | 任务 | 影响 |
|--------|------|------|
| P0 | 统一组件样式 | 关键 |
| P0 | 修复颜色对比度问题 | 关键 |
| P1 | 优化导航栏交互 | 高 |
| P1 | 改进表单验证反馈 | 高 |
| P2 | 统一图标系统 | 中 |
| P2 | 优化加载状态 | 中 |
| P3 | 增强动画效果 | 低 |

---

此设计系统为 Notion Bill Importer 项目的 UI/UX 规范，所有设计和开发工作应遵循此规范以确保一致性和专业性。
