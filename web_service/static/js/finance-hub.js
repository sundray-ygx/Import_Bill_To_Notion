/**
 * 财务指挥中心 - JavaScript交互逻辑
 * 处理数据加载、状态管理和用户交互
 */

// ========================================
// 应用状态
// ========================================

const AppState = {
    stats: {
        monthlyIncome: 0,
        monthlyExpense: 0,
        netBalance: 0,
        transactionCount: 0
    },
    recentActivity: [],
    isLoading: false
};

// ========================================
// 初始化
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    initNavigation();
    initQuickActions();
});

/**
 * 初始化仪表板
 */
async function initDashboard() {
    showLoading(true);

    try {
        // 并行加载数据
        const [stats, activity] = await Promise.all([
            fetchStats(),
            fetchRecentActivity()
        ]);

        AppState.stats = stats;
        AppState.recentActivity = activity;

        renderStats();
        renderActivity();
    } catch (error) {
        console.error('加载数据失败:', error);
        showError('加载数据失败，请刷新页面重试');
    } finally {
        showLoading(false);
    }
}

/**
 * 初始化导航交互
 */
function initNavigation() {
    // 侧边栏导航项点击
    const navItems = document.querySelectorAll('.sidebar-nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            // 移除所有active类
            navItems.forEach(nav => nav.classList.remove('active'));
            // 添加active类到当前项
            e.currentTarget.classList.add('active');
        });
    });
}

/**
 * 初始化快速操作按钮
 */
function initQuickActions() {
    // 上传账单按钮
    const uploadBtn = document.querySelector('.sidebar-quick-btn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            window.location.href = '/bill-management';
        });
    }
}

// ========================================
// 数据获取
// ========================================

/**
 * 获取统计数据
 */
async function fetchStats() {
    try {
        const response = await fetch('/api/dashboard/stats');
        if (!response.ok) throw new Error('获取统计数据失败');

        const result = await response.json();
        return result.data || getDefaultStats();
    } catch (error) {
        console.error('获取统计数据失败:', error);
        return getDefaultStats();
    }
}

/**
 * 获取最近活动
 */
async function fetchRecentActivity() {
    try {
        const response = await fetch('/api/dashboard/activity?limit=5');
        if (!response.ok) throw new Error('获取活动失败');

        const result = await response.json();
        return result.data || getDefaultActivity();
    } catch (error) {
        console.error('获取活动失败:', error);
        return getDefaultActivity();
    }
}

/**
 * 获取默认统计数据
 */
function getDefaultStats() {
    return {
        monthlyIncome: 0,
        monthlyExpense: 0,
        netBalance: 0,
        transactionCount: 0,
        incomeTrend: 0,
        expenseTrend: 0
    };
}

/**
 * 获取默认活动数据
 */
function getDefaultActivity() {
    return [
        {
            type: 'import',
            title: '欢迎使用账单管理系统',
            description: '上传您的第一个账单文件开始使用',
            time: '刚刚',
            status: 'info'
        }
    ];
}

// ========================================
// 渲染函数
// ========================================

/**
 * 渲染统计卡片
 */
function renderStats() {
    const { monthlyIncome, monthlyExpense, netBalance, transactionCount } = AppState.stats;

    // 更新收入卡片
    updateStatCard(0, {
        value: formatCurrency(monthlyIncome),
        trend: calculateTrend(monthlyIncome, AppState.stats.incomeTrend),
        label: '本月收入'
    });

    // 更新支出卡片
    updateStatCard(1, {
        value: formatCurrency(monthlyExpense),
        trend: calculateTrend(monthlyExpense, AppState.stats.expenseTrend),
        label: '本月支出'
    });

    // 更新余额卡片
    updateStatCard(2, {
        value: formatCurrency(netBalance),
        trend: { text: `${netBalance >= 0 ? '↑' : '↓'} ${Math.abs(netBalance / 100).toFixed(2)}w`, positive: netBalance >= 0 },
        label: '净余额'
    });

    // 更新交易卡片
    updateStatCard(3, {
        value: transactionCount.toLocaleString(),
        text: '笔',
        label: '本年交易'
    });
}

/**
 * 更新单个统计卡片
 */
function updateStatCard(index, data) {
    const cards = document.querySelectorAll('.stat-card');
    if (!cards[index]) return;

    const card = cards[index];
    const valueEl = card.querySelector('.stat-card-value');
    const trendEl = card.querySelector('.stat-card-trend');

    if (valueEl) valueEl.textContent = data.value;

    if (trendEl && data.trend) {
        trendEl.className = `stat-card-trend ${data.trend.positive ? 'positive' : 'negative'}`;
        trendEl.innerHTML = `
            <span>${data.trend.text}</span>
            ${data.trend.extra ? `<span>${data.trend.extra}</span>` : ''}
        `;
    }
}

/**
 * 渲染活动列表
 */
function renderActivity() {
    const activityList = document.querySelector('.activity-list');
    if (!activityList) return;

    activityList.innerHTML = AppState.recentActivity.map(activity => `
        <div class="activity-item">
            <div class="activity-item-icon ${activity.type}">
                ${getActivityIcon(activity.type)}
            </div>
            <div class="activity-item-content">
                <div class="activity-item-title">${activity.title}</div>
                <div class="activity-item-meta">
                    <span class="activity-item-time">
                        <span>🕐</span>
                        <span>${activity.time}</span>
                    </span>
                    ${activity.description ? `<span>${activity.description}</span>` : ''}
                </div>
            </div>
            <span class="activity-item-status ${activity.status}">
                ${getStatusLabel(activity.status)}
            </span>
        </div>
    `).join('');
}

/**
 * 获取活动图标
 */
function getActivityIcon(type) {
    const icons = {
        import: '📤',
        review: '📊',
        error: '⚠️',
        success: '✅',
        warning: '⚡'
    };
    return icons[type] || '📌';
}

/**
 * 获取状态标签
 */
function getStatusLabel(status) {
    const labels = {
        success: '成功',
        error: '失败',
        pending: '处理中',
        info: '信息'
    };
    return labels[status] || status;
}

// ========================================
// 工具函数
// ========================================

/**
 * 格式化货币
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * 计算趋势
 */
function calculateTrend(current, previous) {
    if (!previous) return { text: '无数据', positive: true };

    const change = ((current - previous) / previous * 100).toFixed(1);
    const isPositive = change >= 0;

    return {
        text: `${isPositive ? '↑' : '↓'} ${Math.abs(change)}%`,
        positive: isPositive,
        extra: '较上月'
    };
}

/**
 * 显示加载状态
 */
function showLoading(show) {
    AppState.isLoading = show;

    const mainContent = document.querySelector('.finance-main');
    if (mainContent) {
        mainContent.style.opacity = show ? '0.5' : '1';
        mainContent.style.pointerEvents = show ? 'none' : 'auto';
    }
}

/**
 * 显示错误消息
 */
function showError(message) {
    // 创建toast元素
    const toast = document.createElement('div');
    toast.className = 'toast toast-error';
    toast.innerHTML = `
        <span class="toast-icon">⚠️</span>
        <span class="toast-message">${message}</span>
    `;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 16px 24px;
        background: white;
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(toast);

    // 3秒后自动消失
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 添加动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ========================================
// 自动刷新
// ========================================

// 每30秒自动刷新数据
setInterval(() => {
    if (!document.hidden) {
        initDashboard();
    }
}, 30000);

// 页面获得焦点时刷新
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        initDashboard();
    }
});
