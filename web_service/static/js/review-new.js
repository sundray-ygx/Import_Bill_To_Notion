/**
 * 账单复盘管理页面 - JavaScript逻辑
 * 处理复盘生成、预览和管理功能
 */

// ========================================
// 全局状态
// ========================================

const state = {
    reviews: [],
    isLoading: false,
    currentPeriod: {
        monthly: { year: 2026, month: 1 },
        quarterly: { year: 2026, quarter: 1 },
        yearly: { year: 2025 }
    }
};

// ========================================
// 初始化
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    initPeriodDisplays();
    initFormHandlers();
    loadReviewHistory();
});

/**
 * 初始化周期显示
 */
function initPeriodDisplays() {
    const now = new Date();
    state.currentPeriod = {
        monthly: { year: now.getFullYear(), month: now.getMonth() + 1 },
        quarterly: {
            year: now.getFullYear(),
            quarter: Math.floor(now.getMonth() / 3) + 1
        },
        yearly: { year: now.getFullYear() - 1 }
    };

    updatePeriodDisplays();
}

/**
 * 更新周期显示
 */
function updatePeriodDisplays() {
    const { monthly, quarterly, yearly } = state.currentPeriod;

    document.getElementById('monthly-period').textContent =
        `${monthly.year}年${monthly.month}月`;
    document.getElementById('quarterly-period').textContent =
        `${quarterly.year}年Q${quarterly.quarter}`;
    document.getElementById('yearly-period').textContent =
        `${yearly.year}年度`;

    // 更新表单默认值
    document.getElementById('review-year').value = monthly.year;
    document.getElementById('review-month').value = monthly.month;
    document.getElementById('review-quarter').value = quarterly.quarter;
}

/**
 * 初始化表单处理器
 */
function initFormHandlers() {
    // 复盘类型切换
    const typeSelect = document.getElementById('review-type');
    typeSelect.addEventListener('change', (e) => {
        const type = e.target.value;
        const monthGroup = document.getElementById('month-group');
        const quarterGroup = document.getElementById('quarter-group');

        if (type === 'monthly') {
            monthGroup.style.display = 'flex';
            quarterGroup.style.display = 'none';
        } else if (type === 'quarterly') {
            monthGroup.style.display = 'none';
            quarterGroup.style.display = 'flex';
        } else {
            monthGroup.style.display = 'none';
            quarterGroup.style.display = 'none';
        }
    });

    // 自定义表单提交
    const customForm = document.getElementById('custom-form');
    customForm.addEventListener('submit', (e) => {
        e.preventDefault();
        handleCustomSubmit();
    });

    // 模态框点击外部关闭
    const modal = document.getElementById('preview-modal');
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // ESC键关闭模态框
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

// ========================================
// 复盘生成
// ========================================

/**
 * 生成复盘
 * @param {string} type - 复盘类型 (monthly/quarterly/yearly)
 */
async function generateReview(type) {
    if (state.isLoading) return;

    const { year, quarter, month } = state.currentPeriod[type];

    const params = { review_type: type, year };

    if (type === 'monthly') {
        params.month = month;
    } else if (type === 'quarterly') {
        params.quarter = quarter;
    }

    await performGenerateRequest(params);
}

/**
 * 处理自定义表单提交
 */
async function handleCustomSubmit() {
    if (state.isLoading) return;

    const type = document.getElementById('review-type').value;
    const year = parseInt(document.getElementById('review-year').value);
    const month = parseInt(document.getElementById('review-month').value);
    const quarter = parseInt(document.getElementById('review-quarter').value);

    const params = { review_type: type, year };

    if (type === 'monthly') {
        params.month = month;
    } else if (type === 'quarterly') {
        params.quarter = quarter;
    }

    await performGenerateRequest(params);
}

/**
 * 执行生成请求
 * @param {Object} params - 请求参数
 */
async function performGenerateRequest(params) {
    setLoading(true);

    try {
        const response = await fetch('/api/review/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });

        const result = await response.json();

        if (result.success) {
            showToast('success', '复盘生成成功！');
            await loadReviewHistory();

            // 如果有数据，显示预览
            if (result.data) {
                showPreview(result.data);
            }
        } else {
            showToast('error', result.error || '复盘生成失败');
        }
    } catch (error) {
        console.error('生成复盘失败:', error);
        showToast('error', '网络错误，请稍后重试');
    } finally {
        setLoading(false);
    }
}

// ========================================
// 复盘历史
// ========================================

/**
 * 加载复盘历史
 */
async function loadReviewHistory() {
    try {
        const response = await fetch('/api/review/list');
        const result = await response.json();

        if (result.success && result.data) {
            state.reviews = result.data;
            renderReviewList();
        }
    } catch (error) {
        console.error('加载复盘历史失败:', error);
    }
}

/**
 * 渲染复盘列表
 */
function renderReviewList() {
    const tbody = document.getElementById('review-list');

    if (state.reviews.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; color: var(--text-secondary);">
                    暂无复盘记录，点击上方按钮生成您的第一个复盘报告
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = state.reviews.map(review => `
        <tr>
            <td><strong>${review.title}</strong></td>
            <td>${getTypeLabel(review.type)}</td>
            <td>${review.period}</td>
            <td>${formatDate(review.created_at)}</td>
            <td>${getStatusBadge(review.status)}</td>
            <td>
                <a href="#" class="review-action-link" onclick="showPreviewById('${review.id}')">预览</a>
            </td>
        </tr>
    `).join('');
}

/**
 * 获取类型标签
 * @param {string} type - 复盘类型
 * @returns {string} 类型标签
 */
function getTypeLabel(type) {
    const labels = {
        monthly: '月度复盘',
        quarterly: '季度复盘',
        yearly: '年度复盘'
    };
    return labels[type] || type;
}

/**
 * 格式化日期
 * @param {string} dateString - 日期字符串
 * @returns {string} 格式化的日期
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 获取状态徽章
 * @param {string} status - 状态
 * @returns {string} 状态徽章HTML
 */
function getStatusBadge(status) {
    const className = status === 'completed'
        ? 'review-status-badge--completed'
        : 'review-status-badge--pending';

    const text = status === 'completed' ? '已完成' : '处理中';

    return `<span class="review-status-badge ${className}">${text}</span>`;
}

// ========================================
// 预览模态框
// ========================================

/**
 * 显示预览
 * @param {Object} data - 复盘数据
 */
function showPreview(data) {
    const modal = document.getElementById('preview-modal');
    const title = document.getElementById('modal-title');
    const content = document.getElementById('modal-content');

    title.textContent = data.title || '复盘预览';

    content.innerHTML = renderPreviewContent(data);

    modal.classList.add('review-modal-overlay--active');
    document.body.style.overflow = 'hidden';
}

/**
 * 根据ID显示预览
 * @param {string} id - 复盘ID
 */
async function showPreviewById(id) {
    try {
        const response = await fetch(`/api/review/${id}/preview`);
        const result = await response.json();

        if (result.success) {
            showPreview(result.data);
        } else {
            showToast('error', '加载预览失败');
        }
    } catch (error) {
        console.error('加载预览失败:', error);
        showToast('error', '网络错误');
    }
}

/**
 * 渲染预览内容
 * @param {Object} data - 复盘数据
 * @returns {string} HTML内容
 */
function renderPreviewContent(data) {
    if (!data) return '<p>暂无数据</p>';

    const summary = data.summary || {};

    return `
        <div style="space-y: 24px;">
            <!-- 总览 -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px;">
                <div style="padding: 16px; background: rgba(16, 185, 129, 0.1); border-radius: 12px;">
                    <div style="font-size: 0.85rem; color: var(--text-secondary);">总收入</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--success-color);">
                        ¥${(summary.total_income || 0).toFixed(2)}
                    </div>
                </div>
                <div style="padding: 16px; background: rgba(239, 68, 68, 0.1); border-radius: 12px;">
                    <div style="font-size: 0.85rem; color: var(--text-secondary);">总支出</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--danger-color);">
                        ¥${(summary.total_expense || 0).toFixed(2)}
                    </div>
                </div>
                <div style="padding: 16px; background: rgba(102, 126, 234, 0.1); border-radius: 12px;">
                    <div style="font-size: 0.85rem; color: var(--text-secondary);">净余额</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary-color);">
                        ¥${(summary.net_balance || 0).toFixed(2)}
                    </div>
                </div>
                <div style="padding: 16px; background: rgba(245, 158, 11, 0.1); border-radius: 12px;">
                    <div style="font-size: 0.85rem; color: var(--text-secondary);">交易笔数</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--warning-color);">
                        ${summary.transaction_count || 0}
                    </div>
                </div>
            </div>

            <!-- 分类统计 -->
            ${data.categories ? renderCategories(data.categories) : ''}

            <!-- 操作按钮 -->
            <div style="display: flex; gap: 12px; margin-top: 24px;">
                <button onclick="submitToNotion('${data.id}')" class="review-form-button">
                    提交到Notion
                </button>
                <button onclick="closeModal()" class="review-form-button" style="background: var(--text-secondary);">
                    关闭
                </button>
            </div>
        </div>
    `;
}

/**
 * 渲染分类统计
 * @param {Object} categories - 分类数据
 * @returns {string} HTML内容
 */
function renderCategories(categories) {
    const expenseCategories = categories.expense || {};
    const incomeCategories = categories.income || {};

    let html = '<div style="margin-top: 24px;">';

    if (Object.keys(expenseCategories).length > 0) {
        html += `
            <h4 style="margin-bottom: 12px;">支出分类</h4>
            <div style="display: grid; gap: 8px;">
        `;

        for (const [name, amount] of Object.entries(expenseCategories)) {
            html += `
                <div style="display: flex; justify-content: space-between; padding: 12px; background: rgba(239, 68, 68, 0.05); border-radius: 8px;">
                    <span>${name}</span>
                    <strong>¥${amount.toFixed(2)}</strong>
                </div>
            `;
        }

        html += '</div>';
    }

    html += '</div>';
    return html;
}

/**
 * 关闭模态框
 */
function closeModal() {
    const modal = document.getElementById('preview-modal');
    modal.classList.remove('review-modal-overlay--active');
    document.body.style.overflow = '';
}

/**
 * 提交到Notion
 * @param {string} id - 复盘ID
 */
async function submitToNotion(id) {
    try {
        const response = await fetch('/api/review/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id })
        });

        const result = await response.json();

        if (result.success) {
            showToast('success', '已提交到Notion！');
            closeModal();
            await loadReviewHistory();
        } else {
            showToast('error', result.error || '提交失败');
        }
    } catch (error) {
        console.error('提交失败:', error);
        showToast('error', '网络错误');
    }
}

// ========================================
// 工具函数
// ========================================

/**
 * 设置加载状态
 * @param {boolean} loading - 是否加载中
 */
function setLoading(loading) {
    state.isLoading = loading;
    const loadingState = document.getElementById('loading-state');

    if (loading) {
        loadingState.style.display = 'flex';
    } else {
        loadingState.style.display = 'none';
    }
}

/**
 * 显示消息提示
 * @param {string} type - 消息类型 (success/error)
 * @param {string} message - 消息内容
 */
function showToast(type, message) {
    const toast = document.getElementById('toast');
    const icon = document.getElementById('toast-icon');
    const messageEl = document.getElementById('toast-message');

    toast.className = `review-toast review-toast--${type} review-toast--active`;
    icon.textContent = type === 'success' ? '✓' : '✕';
    messageEl.textContent = message;

    setTimeout(() => {
        toast.classList.remove('review-toast--active');
    }, 3000);
}
