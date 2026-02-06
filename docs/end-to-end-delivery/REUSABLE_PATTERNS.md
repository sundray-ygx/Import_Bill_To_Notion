# 可复用模式提取与知识沉淀

**项目**: Notion Bill Importer - Dashboard视图重构
**日期**: 2026-02-06
**版本**: v2.3.0

---

## 执行摘要

本文档总结了Dashboard视图重构项目中提取的可复用设计模式、代码模式和最佳实践，为后续项目提供参考。

---

## 1. 设计模式

### 1.1 IIFE模块模式（立即执行函数表达式）

#### 问题

需要创建可复用的JavaScript模块，同时避免全局变量污染。

#### 方案

```javascript
const DashboardView = (function() {
  'use strict';

  // 私有变量
  let state = {
    stats: null,
    activities: [],
    loading: false,
    error: null,
    lastUpdate: null
  };

  let refreshTimer = null;

  // 私有方法
  function loadData() {
    // 加载数据逻辑
  }

  function render() {
    // 渲染逻辑
  }

  function startAutoRefresh() {
    // 自动刷新逻辑
  }

  // 公共接口
  return {
    /**
     * 初始化Dashboard视图
     * @public
     */
    init: function() {
      loadData();
      render();
      startAutoRefresh();
    },

    /**
     * 清理资源
     * @public
     */
    cleanup: function() {
      if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
      }
      state = {
        stats: null,
        activities: [],
        loading: false,
        error: null,
        lastUpdate: null
      };
    },

    /**
     * 手动刷新数据
     * @param {boolean} showToast - 是否显示提示
     * @public
     */
    refresh: function(showToast = true) {
      loadData();
    },

    /**
     * 获取当前状态
     * @returns {object} 状态对象
     * @public
     */
    getState: function() {
      return {...state};
    }
  };
})();
```

#### 优点

- **封装性好**: 私有变量和方法不会暴露到全局作用域
- **避免污染**: 不创建全局变量
- **清晰接口**: 公共API明确
- **易于测试**: 模块独立，易于单元测试
- **易于维护**: 代码组织清晰

#### 适用场景

- 单页面应用视图组件
- 需要状态管理的模块
- 可复用的功能模块
- 需要清理资源的组件（定时器、事件监听）

#### 参考位置

- 文件: `/mnt/hgfs/code/share/python/Import_Bill_To_Notion/web_service/static/js/dashboard-view.js`
- 行数: 1-420

---

### 1.2 响应式布局模式

#### 问题

需要在不同屏幕尺寸下显示合适的布局。

#### 方案

```css
/* 默认：桌面大屏（4列） */
.stat-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-4);
}

/* 平板/小桌面（2列） */
@media (max-width: 1199px) {
  .stat-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 手机（1列） */
@media (max-width: 767px) {
  .stat-cards-grid {
    grid-template-columns: 1fr;
  }
}
```

#### 优点

- **适应性强**: 自动适应不同设备
- **代码简洁**: 使用CSS Grid，代码量少
- **易于维护**: 响应式规则集中管理
- **性能好**: 纯CSS实现，无JavaScript开销

#### 断点建议

| 断点 | 屏幕宽度 | 列数 | 适用设备 |
|------|----------|------|----------|
| 大屏 | ≥1200px | 4列 | 桌面电脑 |
| 中屏 | 768-1199px | 2列 | 平板、小桌面 |
| 小屏 | <768px | 1列 | 手机 |

#### 参考位置

- 文件: `/mnt/hgfs/code/share/python/Import_Bill_To_Notion/web_service/static/css/timeline.css`
- 行数: 1-380

---

### 1.3 视图切换模式（SPA）

#### 问题

单页面应用需要在不同视图间切换，同时管理视图状态和资源。

#### 方案

```javascript
// 视图配置
const VIEWS = [
  {
    id: 'dashboard',
    name: '仪表板',
    icon: '📊',
    init: () => DashboardView.init(),
    cleanup: () => DashboardView.cleanup()
  },
  {
    id: 'bills',
    name: '账单管理',
    icon: '💳',
    init: () => BillsView.init(),
    cleanup: () => BillsView.cleanup()
  }
  // ... 其他视图
];

let currentView = null;

function switchView(viewId) {
  // 1. 清理当前视图
  if (currentView && currentView.cleanup) {
    currentView.cleanup();
  }

  // 2. 隐藏所有视图
  document.querySelectorAll('.view-section').forEach(view => {
    view.style.display = 'none';
    view.style.opacity = '0';
  });

  // 3. 查找并显示新视图
  const newView = VIEWS.find(v => v.id === viewId);
  if (newView) {
    const viewElement = document.getElementById(`${viewId}-view`);
    if (viewElement) {
      viewElement.style.display = 'block';
      // 淡入动画
      setTimeout(() => {
        viewElement.style.opacity = '1';
      }, 10);

      // 初始化视图
      if (newView.init) {
        newView.init();
      }

      currentView = newView;
    }
  }

  // 4. 更新导航状态
  updateNavigation(viewId);
}
```

#### 优点

- **资源管理**: 切换时自动清理旧视图资源
- **状态清晰**: 当前视图状态明确
- **扩展性好**: 添加新视图只需配置
- **动画流畅**: 视图切换有淡入淡出效果

#### 参考位置

- 文件: `/mnt/hgfs/code/share/python/Import_Bill_To_Notion/web_service/static/js/workspace.js`
- 行数: 1-200

---

## 2. 代码模式

### 2.1 并行请求模式

#### 问题

需要同时请求多个API，减少总加载时间。

#### 方案

```javascript
/**
 * 并行加载Dashboard数据
 * @returns {Promise<{stats: object, activity: array}>}
 */
async function loadDashboardData() {
  try {
    // 并行请求stats和activity
    const [statsResponse, activityResponse] = await Promise.all([
      fetch('/api/dashboard/stats'),
      fetch('/api/dashboard/activity?limit=10')
    ]);

    // 检查响应状态
    if (!statsResponse.ok || !activityResponse.ok) {
      throw new Error('API请求失败');
    }

    // 解析JSON
    const stats = await statsResponse.json();
    const activity = await activityResponse.json();

    return { stats, activity };
  } catch (error) {
    console.error('加载数据失败:', error);
    throw error;
  }
}
```

#### 优点

- **性能提升**: 并行请求减少总时间
- **代码简洁**: 使用Promise.all，代码清晰
- **错误处理**: 统一的错误处理

#### 适用场景

- 多个独立的API请求
- 需要同时获取多个数据源
- 对加载时间敏感的场景

#### 参考位置

- 文件: `/mnt/hgfs/code/share/python/Import_Bill_To_Notion/web_service/static/js/dashboard-view.js`
- 行数: 150-180

---

### 2.2 清理资源模式

#### 问题

SPA视图切换时需要清理定时器和事件监听，防止内存泄漏。

#### 方案

```javascript
/**
 * 清理Dashboard视图资源
 * @public
 */
function cleanup() {
  // 1. 清理自动刷新定时器
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }

  // 2. 移除事件监听
  const refreshButton = document.getElementById('refresh-button');
  if (refreshButton) {
    refreshButton.removeEventListener('click', handleRefresh);
  }

  // 3. 重置状态
  state = {
    stats: null,
    activities: [],
    loading: false,
    error: null,
    lastUpdate: null
  };

  // 4. 清理缓存
  if (window.dashboardCache) {
    delete window.dashboardCache;
  }
}
```

#### 清理清单

- [ ] 定时器 (setInterval, setTimeout)
- [ ] 事件监听器 (addEventListener)
- [ ] 全局变量
- [ ] 缓存数据
- [ ] DOM引用

#### 参考位置

- 文件: `/mnt/hgfs/code/share/python/Import_Bill_To_Notion/web_service/static/js/dashboard-view.js`
- 行数: 350-380

---

### 2.3 防抖/节流模式

#### 问题

频繁触发的事件（如刷新按钮点击）需要防抖处理。

#### 方案

```javascript
/**
 * 防抖函数
 * @param {Function} fn - 要防抖的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
function debounce(fn, delay) {
  let timer = null;
  return function(...args) {
    if (timer) {
      clearTimeout(timer);
    }
    timer = setTimeout(() => {
      fn.apply(this, args);
      timer = null;
    }, delay);
  };
}

/**
 * 节流函数
 * @param {Function} fn - 要节流的函数
 * @param {number} interval - 间隔时间（毫秒）
 * @returns {Function} 节流后的函数
 */
function throttle(fn, interval) {
  let last = 0;
  return function(...args) {
    const now = Date.now();
    if (now - last > interval) {
      last = now;
      fn.apply(this, args);
    }
  };
}

// 使用示例
const debouncedRefresh = debounce(refreshData, 500);
const throttledScroll = throttle(handleScroll, 100);

// 绑定事件
refreshButton.addEventListener('click', debouncedRefresh);
window.addEventListener('scroll', throttledScroll);
```

#### 使用场景

- **防抖**: 输入框搜索、按钮点击、窗口resize
- **节流**: 滚动事件、鼠标移动

#### 参考位置

- 可在任何JavaScript模块中使用

---

### 2.4 状态管理模式

#### 问题

需要管理组件的状态，并在状态变化时触发渲染。

#### 方案

```javascript
// 简单的状态管理
const StateManager = (function() {
  'use strict';

  let state = {
    stats: null,
    activities: [],
    loading: false,
    error: null
  };

  let listeners = [];

  /**
   * 更新状态
   * @param {object} newState - 新状态
   */
  function setState(newState) {
    state = {...state, ...newState};
    notifyListeners();
  }

  /**
   * 获取状态
   * @returns {object} 当前状态
   */
  function getState() {
    return {...state};
  }

  /**
   * 订阅状态变化
   * @param {Function} listener - 监听函数
   */
  function subscribe(listener) {
    listeners.push(listener);
    return () => {
      listeners = listeners.filter(l => l !== listener);
    };
  }

  /**
   * 通知所有监听者
   */
  function notifyListeners() {
    listeners.forEach(listener => listener(state));
  }

  return {
    setState,
    getState,
    subscribe
  };
})();
```

#### 优点

- **单向数据流**: 状态变化可预测
- **解耦**: 组件不直接依赖状态
- **可扩展**: 易于添加新状态和监听者

#### 参考位置

- 可在任何需要状态管理的组件中使用

---

## 3. 最佳实践

### 3.1 命名规范

#### BEM命名规范（CSS）

```css
/* Block */
.stat-card {}

/* Element */
.stat-card__header {}
.stat-card__title {}
.stat-card__value {}
.stat-card__footer {}

/* Modifier */
.stat-card--income {}
.stat-card--expense {}
.stat-card--highlighted {}
```

#### JavaScript命名

```javascript
// 常量：全大写，下划线分隔
const API_BASE_URL = 'https://api.example.com';
const MAX_RETRY_COUNT = 3;

// 变量/函数：驼峰命名
let currentUser = null;
function getUserData() {}

// 类/构造函数：帕斯卡命名
class UserModel {}
function DashboardView() {}

// 私有变量/函数：前缀下划线（可选）
let _privateVar = null;
function _privateMethod() {}
```

#### 文件命名

```
// 组件文件：kebab-case
dashboard-view.js
activity-timeline.js

// 样式文件：kebab-case
timeline.css
workspace-views.css

// 测试文件：test_前缀
test_dashboard_simple.py
test_user_service.py
```

---

### 3.2 注释规范

#### JSDoc注释

```javascript
/**
 * 加载Dashboard数据
 * @async
 * @param {boolean} showLoading - 是否显示加载状态
 * @returns {Promise<{stats: object, activity: array}>}
 * @throws {Error} 当API请求失败时抛出错误
 * @example
 * const data = await loadDashboardData(true);
 * console.log(data.stats);
 */
async function loadDashboardData(showLoading = true) {
  // 实现...
}
```

#### 复杂逻辑注释

```javascript
// 计算净余额
// 公式: 收入 - 支出
// 注意: 需要处理null/undefined情况
const netBalance = (monthlyIncome || 0) - (monthlyExpense || 0);
```

#### TODO注释

```javascript
// TODO: 添加数据缓存机制（预计工作量: 4小时）
// TODO: 优化大量数据时的渲染性能
```

---

### 3.3 错误处理规范

#### 统一错误处理

```javascript
async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message || '请求失败');
    }

    return data.data;
  } catch (error) {
    console.error('API调用失败:', error);
    // 显示用户友好的错误提示
    showToast(error.message || '网络错误，请稍后重试', 'error');
    throw error;
  }
}
```

#### 错误日志

```javascript
function logError(context, error) {
  const errorInfo = {
    timestamp: new Date().toISOString(),
    context: context,
    error: {
      message: error.message,
      stack: error.stack,
      name: error.name
    },
    userAgent: navigator.userAgent,
    url: window.location.href
  };

  // 发送到错误追踪服务
  console.error('[Error]', errorInfo);

  // 或者发送到服务器
  // sendToServer('/api/errors', errorInfo);
}
```

---

### 3.4 测试规范

#### AAA模式

```python
def test_monthly_calculation():
    """
    测试月度统计计算
    验证收入、支出、余额计算正确性
    """
    # Arrange - 准备测试数据
    income = 10000
    expense = 6000
    expected_balance = 4000

    # Act - 执行计算
    actual_balance = calculate_balance(income, expense)

    # Assert - 验证结果
    assert actual_balance == expected_balance
    assert actual_balance >= 0
```

#### 测试覆盖清单

- [ ] 正常情况测试
- [ ] 边界情况测试
- [ ] 异常情况测试
- [ ] 性能测试
- [ ] 集成测试

---

### 3.5 性能优化实践

#### 1. DOM缓存

```javascript
// 不好的做法
function render() {
  document.querySelector('.stat-cards-grid').innerHTML = '...';
  document.querySelector('.activity-timeline').innerHTML = '...';
}

// 好的做法
const elements = {
  statsContainer: document.querySelector('.stat-cards-grid'),
  activityContainer: document.querySelector('.activity-timeline')
};

function render() {
  elements.statsContainer.innerHTML = '...';
  elements.activityContainer.innerHTML = '...';
}
```

#### 2. 事件委托

```javascript
// 不好的做法
items.forEach(item => {
  item.addEventListener('click', handleClick);
});

// 好的做法
container.addEventListener('click', (e) => {
  if (e.target.matches('.item')) {
    handleClick(e);
  }
});
```

#### 3. 懒加载

```javascript
// 按需加载模块
async function loadChartLibrary() {
  if (!window.Chart) {
    await import('./chart-library.js');
  }
  return window.Chart;
}
```

---

## 4. 项目模板

### 4.1 JavaScript组件模板

```javascript
/**
 * 组件名称
 * @description 组件描述
 */
const ComponentName = (function() {
  'use strict';

  // ==================== 私有变量 ====================
  let state = {
    // 状态定义
  };

  let timer = null;

  // ==================== 私有方法 ====================

  /**
   * 初始化组件
   * @private
   */
  function init() {
    // 初始化逻辑
  }

  /**
   * 渲染组件
   * @private
   */
  function render() {
    // 渲染逻辑
  }

  /**
   * 处理事件
   * @private
   */
  function handleEvent() {
    // 事件处理逻辑
  }

  // ==================== 公共接口 ====================

  return {
    /**
     * 初始化组件
     * @public
     */
    init: init,

    /**
     * 清理资源
     * @public
     */
    cleanup: function() {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
      state = {};
    },

    /**
     * 更新组件
     * @public
     * @param {object} newState - 新状态
     */
    update: function(newState) {
      state = {...state, ...newState};
      render();
    }
  };
})();
```

### 4.2 CSS组件模板

```css
/* ==================== Block ==================== */
.component-name {
  /* 布局 */
  display: flex;
  flex-direction: column;

  /* 盒模型 */
  padding: var(--spacing-4);
  gap: var(--spacing-2);

  /* 视觉 */
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);

  /* 动画 */
  transition: var(--transition-base);
}

/* ==================== Elements ==================== */
.component-name__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.component-name__title {
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.component-name__content {
  /* 内容样式 */
}

.component-name__footer {
  /* 底部样式 */
}

/* ==================== Modifiers ==================== */
.component-name--primary {
  background: var(--color-primary-50);
  border-color: var(--color-primary-200);
}

.component-name--disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* ==================== States ==================== */
.component-name:hover {
  box-shadow: var(--shadow-md);
}

.component-name:focus {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}

/* ==================== Responsive ==================== */
@media (max-width: 767px) {
  .component-name {
    padding: var(--spacing-3);
  }
}
```

---

## 5. 总结

### 5.1 核心模式总结

| 模式 | 用途 | 复用性 |
|------|------|--------|
| IIFE模块模式 | JavaScript模块封装 | ⭐⭐⭐ |
| 响应式布局 | 多设备适配 | ⭐⭐⭐ |
| 视图切换模式 | SPA视图管理 | ⭐⭐⭐ |
| 并行请求 | 性能优化 | ⭐⭐⭐ |
| 清理资源模式 | 内存管理 | ⭐⭐⭐ |
| 防抖/节流 | 性能优化 | ⭐⭐⭐ |
| 状态管理 | 数据流管理 | ⭐⭐ |

### 5.2 最佳实践总结

| 实践 | 领域 | 重要性 |
|------|------|--------|
| 命名规范 | 代码可读性 | ⭐⭐⭐ |
| 注释规范 | 代码可维护性 | ⭐⭐⭐ |
| 错误处理 | 代码健壮性 | ⭐⭐⭐ |
| 测试规范 | 代码质量 | ⭐⭐⭐ |
| 性能优化 | 用户体验 | ⭐⭐ |

### 5.3 使用建议

1. **优先使用成熟的模式**: 不要重复造轮子
2. **保持简单**: 避免过度设计
3. **文档同步**: 及时更新文档
4. **持续优化**: 根据实际情况调整

---

**文档版本**: 1.0
**最后更新**: 2026-02-06
**维护者**: 项目团队
