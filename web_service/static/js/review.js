/**
 * 账单复盘页面逻辑
 * 现代化设计 + 进度反馈
 */

// ==================== 状态管理 ====================
const state = {
    currentPreview: null,  // 当前预览数据
    notionPageUrl: null,   // 创建的 Notion 页面 URL
    reviewType: 'monthly',  // 当前复盘类型
    progressStep: 0        // 当前进度步骤
};

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    initDateInputs();
    initEventListeners();
    initTypeSelector();
    initLineNumbers();
    checkNotionConnection();
});

// 初始化日期输入（默认选择本月）
function initDateInputs() {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    document.getElementById('start-date').value = formatDateForInput(firstDay);
    document.getElementById('end-date').value = formatDateForInput(lastDay);
}

// 初始化事件监听
function initEventListeners() {
    // 生成预览按钮
    document.getElementById('generate-preview-btn').addEventListener('click', generatePreview);

    // 状态选择变更（同步到预览）
    document.getElementById('review-status').addEventListener('change', (e) => {
        const attrStatus = document.getElementById('attr-status');
        if (attrStatus) attrStatus.value = e.target.value;
    });

    // 关闭预览
    document.getElementById('close-preview-btn').addEventListener('click', closePreview);
    document.getElementById('preview-cancel-btn').addEventListener('click', closePreview);

    // 提交到 Notion
    document.getElementById('submit-to-notion-btn').addEventListener('click', submitToNotion);

    // 提交模态框关闭按钮
    const submitCloseBtn = document.getElementById('submit-modal-close-btn');
    if (submitCloseBtn) {
        submitCloseBtn.addEventListener('click', closeSubmitModal);
    }

    // 测试连接按钮
    document.getElementById('test-connection-btn').addEventListener('click', testNotionConnection);

    // 成功模态框
    document.getElementById('success-close-btn').addEventListener('click', closeSuccessModal);
    document.getElementById('success-view-btn').addEventListener('click', openNotionPage);

    // Markdown 编辑器行号同步
    const markdownEditor = document.getElementById('markdown-editor');
    if (markdownEditor) {
        markdownEditor.addEventListener('input', updateLineNumbers);
        markdownEditor.addEventListener('scroll', syncScroll);
    }
}

// 初始化类型选择器
function initTypeSelector() {
    const typeOptions = document.querySelectorAll('.type-option');
    const hiddenInput = document.getElementById('review-type');

    typeOptions.forEach(option => {
        option.addEventListener('click', () => {
            // 移除所有激活状态
            typeOptions.forEach(opt => opt.classList.remove('active'));
            // 激活当前选项
            option.classList.add('active');
            // 更新隐藏输入
            hiddenInput.value = option.dataset.type;
            // 触发类型变更处理
            onReviewTypeChange(option.dataset.type);
        });
    });
}

// 初始化行号
function initLineNumbers() {
    updateLineNumbers();
}

// 更新行号
function updateLineNumbers() {
    const editor = document.getElementById('markdown-editor');
    const lineNumbers = document.getElementById('line-numbers');
    if (!editor || !lineNumbers) return;

    const lines = editor.value.split('\n').length;
    lineNumbers.innerHTML = Array.from({ length: lines }, (_, i) => i + 1).join('<br>');
}

// 同步滚动
function syncScroll() {
    const editor = document.getElementById('markdown-editor');
    const lineNumbers = document.getElementById('line-numbers');
    if (!editor || !lineNumbers) return;

    lineNumbers.scrollTop = editor.scrollTop;
}

// 复盘类型变更处理
function onReviewTypeChange(reviewType) {
    state.reviewType = reviewType;

    const today = new Date();
    let startDate, endDate;

    switch (reviewType) {
        case 'monthly':
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
            endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            break;
        case 'quarterly':
            const currentQuarter = Math.floor(today.getMonth() / 3);
            startDate = new Date(today.getFullYear(), currentQuarter * 3, 1);
            endDate = new Date(today.getFullYear(), currentQuarter * 3 + 3, 0);
            break;
        case 'yearly':
            startDate = new Date(today.getFullYear(), 0, 1);
            endDate = new Date(today.getFullYear(), 11, 31);
            break;
        case 'custom':
            return;
    }

    document.getElementById('start-date').value = formatDateForInput(startDate);
    document.getElementById('end-date').value = formatDateForInput(endDate);
}

// ==================== Notion 连接检查 ====================
async function checkNotionConnection() {
    const statusIndicator = document.getElementById('status-indicator-wrapper');
    const statusCoreStatus = document.getElementById('status-core-status');
    const testBtn = document.getElementById('test-connection-btn');

    // 设置检查中状态
    statusIndicator.className = 'status-indicator-wrapper checking';
    statusCoreStatus.textContent = '检查中...';
    testBtn.disabled = true;

    // 重置数据库状态
    resetDatabaseStatus();

    try {
        const response = await window.Auth.apiRequest('/api/review/test-connection');

        if (response && response.ok) {
            const data = await response.json();
            updateConnectionStatus(data);
        } else {
            statusIndicator.className = 'status-indicator-wrapper error';
            statusCoreStatus.textContent = '连接失败';
            testBtn.disabled = false;
        }
    } catch (error) {
        console.error('[ERROR] checkNotionConnection failed:', error);
        statusIndicator.className = 'status-indicator-wrapper error';
        statusCoreStatus.textContent = '连接失败';
        testBtn.disabled = false;
    }
}

function resetDatabaseStatus() {
    // 重置所有数据库状态为检查中
    const badges = document.querySelectorAll('.database-status-badge');
    badges.forEach(badge => {
        badge.className = 'database-status-badge checking';
        badge.textContent = '检查中...';
    });
}

function updateConnectionStatus(data) {
    const statusIndicator = document.getElementById('status-indicator-wrapper');
    const statusCoreStatus = document.getElementById('status-core-status');
    const testBtn = document.getElementById('test-connection-btn');

    if (data.error) {
        console.error('[ERROR] API returned error:', data.error);
        statusIndicator.className = 'status-indicator-wrapper error';
        statusCoreStatus.textContent = '连接失败';
        testBtn.disabled = false;
        return;
    }

    if (data.api_key_valid === true) {
        statusIndicator.className = 'status-indicator-wrapper success';
        statusCoreStatus.textContent = '已连接';
        testBtn.disabled = false;

        // 更新收入数据库状态
        updateDatabaseBadge('income-database-status', 0, data.income_db_valid, data.income_db_error, '已连接');
        updateDatabaseBadge('income-database-status', 1, data.expense_db_valid, data.expense_db_error, '已连接');

        // 更新复盘数据库状态
        updateDatabaseBadge('review-databases-status', 0, data.monthly_review_db_valid, null, '已配置');
        updateDatabaseBadge('review-databases-status', 1, data.quarterly_review_db_valid, null, '已配置');
        updateDatabaseBadge('review-databases-status', 2, data.yearly_review_db_valid, null, '已配置');
    } else {
        statusIndicator.className = 'status-indicator-wrapper error';
        statusCoreStatus.textContent = '未连接';
        testBtn.disabled = false;
    }
}

function updateDatabaseBadge(containerId, index, isValid, errorMsg, defaultText) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const items = container.querySelectorAll('.database-item');
    if (!items[index]) return;

    const badge = items[index].querySelector('.database-status-badge');

    if (isValid === true) {
        badge.className = 'database-status-badge valid';
        badge.textContent = defaultText || '已配置';
    } else if (isValid === false) {
        badge.className = 'database-status-badge invalid';
        badge.textContent = errorMsg || '未配置';
    } else {
        badge.className = 'database-status-badge';
        badge.textContent = '未配置';
    }
}

async function testNotionConnection() {
    const testBtn = document.getElementById('test-connection-btn');
    const statusIndicator = document.getElementById('status-indicator-wrapper');
    const statusCoreStatus = document.getElementById('status-core-status');
    const originalText = testBtn.innerHTML;

    testBtn.disabled = true;
    testBtn.innerHTML = '<span>测试中...</span>';

    // 设置检查中状态
    statusIndicator.className = 'status-indicator-wrapper checking';
    statusCoreStatus.textContent = '测试中...';
    resetDatabaseStatus();

    try {
        const response = await window.Auth.apiRequest('/api/review/test-connection');

        if (response && response.ok) {
            const data = await response.json();
            updateConnectionStatus(data);
            showToast('连接测试完成', 'success');
        } else {
            statusIndicator.className = 'status-indicator-wrapper error';
            statusCoreStatus.textContent = '连接失败';
            showToast('连接测试失败', 'error');
        }
    } catch (error) {
        console.error('[ERROR] Test connection failed:', error);
        statusIndicator.className = 'status-indicator-wrapper error';
        statusCoreStatus.textContent = '连接失败';
        showToast('连接测试失败: ' + error.message, 'error');
    } finally {
        testBtn.disabled = false;
        testBtn.innerHTML = originalText;
    }
}

// ==================== 进度条管理 ====================
function showProgressModal() {
    const modal = document.getElementById('progress-modal');
    modal.style.display = 'flex';
    resetProgressSteps();
}

function hideProgressModal() {
    const modal = document.getElementById('progress-modal');
    modal.style.display = 'none';
}

function resetProgressSteps() {
    const steps = ['step-fetch', 'step-calculate', 'step-generate', 'step-complete'];
    steps.forEach((stepId, index) => {
        const step = document.getElementById(stepId);
        step.classList.remove('active', 'completed');
        step.querySelector('.step-status').textContent = '等待中...';
    });
}

function updateProgressStep(stepId, status, statusText) {
    const step = document.getElementById(stepId);
    if (!step) return;

    step.classList.remove('active', 'completed');

    if (status === 'active') {
        step.classList.add('active');
        step.querySelector('.step-status').textContent = statusText || '处理中...';
    } else if (status === 'completed') {
        step.classList.add('completed');
        step.querySelector('.step-status').textContent = statusText || '完成';
    } else {
        step.querySelector('.step-status').textContent = statusText || '等待中...';
    }
}

// ==================== 预览生成 ====================
async function generatePreview() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const reviewTitle = document.getElementById('review-title').value.trim();
    const reviewStatus = document.getElementById('review-status').value;

    // 验证输入
    if (!startDate || !endDate) {
        showToast('请选择开始日期和结束日期', 'error');
        return;
    }

    if (new Date(startDate) > new Date(endDate)) {
        showToast('开始日期不能晚于结束日期', 'error');
        return;
    }

    // 显示进度模态框
    showProgressModal();
    updateProgressStep('step-fetch', 'active', '正在查询交易数据...');

    try {
        let url = `/api/review/preview?start_date=${startDate}&end_date=${endDate}`;
        if (reviewTitle) {
            url += `&review_title=${encodeURIComponent(reviewTitle)}`;
        }

        const response = await window.Auth.apiRequest(url);

        if (response && response.ok) {
            updateProgressStep('step-fetch', 'completed', '查询完成');
            updateProgressStep('step-calculate', 'active', '正在计算统计数据...');

            // 模拟进度更新（后端是单次请求，所以用 setTimeout 模拟阶段）
            await new Promise(resolve => setTimeout(resolve, 500));
            updateProgressStep('step-calculate', 'completed', '计算完成');
            updateProgressStep('step-generate', 'active', '正在生成复盘内容...');

            const data = await response.json();

            await new Promise(resolve => setTimeout(resolve, 500));
            updateProgressStep('step-generate', 'completed', '生成完成');
            updateProgressStep('step-complete', 'completed', '完成');

            await new Promise(resolve => setTimeout(resolve, 500));
            hideProgressModal();

            if (data.success) {
                state.currentPreview = data;
                displayPreview(data);

                // 同步状态选择
                const attrStatus = document.getElementById('attr-status');
                if (attrStatus) attrStatus.value = reviewStatus;

                showToast('预览生成成功', 'success');
            } else {
                showToast('生成预览失败: ' + (data.error || '未知错误'), 'error');
            }
        } else {
            hideProgressModal();
            showToast('生成预览失败: ' + (response?.statusText || '网络错误'), 'error');
        }
    } catch (error) {
        console.error('[ERROR] Preview error:', error);
        hideProgressModal();
        showToast('生成预览失败: ' + error.message, 'error');
    }
}

function displayPreview(data) {
    const { attributes, markdown_content } = data;

    if (!attributes || !markdown_content) {
        showToast('预览数据格式错误', 'error');
        return;
    }

    // 填充基本属性
    try {
        document.getElementById('attr-title').value = attributes.title || '';
        document.getElementById('attr-start-date').value = attributes.start_date || '';
        document.getElementById('attr-end-date').value = attributes.end_date || '';
        document.getElementById('attr-status').value = attributes.status || '计划中';

        // 填充周期 (从日期生成)
        const startDate = new Date(attributes.start_date);
        const period = `${startDate.getFullYear()}-${String(startDate.getMonth() + 1).padStart(2, '0')}`;
        document.getElementById('attr-period').value = period;

        // 填充财务数据
        document.getElementById('attr-total-income').textContent = formatCurrency(attributes.total_income);
        document.getElementById('attr-total-expense').textContent = formatCurrency(attributes.total_expense);
        document.getElementById('attr-net-balance').textContent = formatCurrency(attributes.net_balance);
        document.getElementById('attr-transaction-count').textContent = attributes.transaction_count || 0;

        // 更新净收益颜色
        const netBalanceItem = document.getElementById('net-balance-item');
        if (netBalanceItem) {
            netBalanceItem.classList.remove('positive', 'negative');
            if (attributes.net_balance >= 0) {
                netBalanceItem.classList.add('positive');
            } else {
                netBalanceItem.classList.add('negative');
            }
        }

        // 填充可选属性（如果有）
        if (attributes.summary) {
            document.getElementById('attr-summary').value = attributes.summary;
        }
        if (attributes.categories) {
            document.getElementById('attr-categories').value = attributes.categories;
        }
    } catch (error) {
        console.error('[ERROR] Failed to fill attributes:', error);
        showToast('填充属性数据失败', 'error');
        return;
    }

    // 填充 Markdown
    try {
        document.getElementById('markdown-editor').value = markdown_content;
        updateLineNumbers();
    } catch (error) {
        console.error('[ERROR] Failed to fill markdown:', error);
        showToast('填充内容数据失败', 'error');
        return;
    }

    // 显示预览区域
    const previewSection = document.getElementById('preview-section');
    previewSection.style.display = 'block';

    // 滚动到预览区域
    try {
        previewSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        console.warn('[WARN] Scroll failed:', error);
    }
}

function closePreview() {
    document.getElementById('preview-section').style.display = 'none';
    state.currentPreview = null;
}

// ==================== 提交到 Notion ====================
let submitController = null;  // 用于取消请求

async function submitToNotion() {
    if (!state.currentPreview) {
        showToast('请先生成预览', 'error');
        return;
    }

    // 收集属性
    const attributes = {
        title: document.getElementById('attr-title').value,
        start_date: document.getElementById('attr-start-date').value,
        end_date: document.getElementById('attr-end-date').value,
        status: document.getElementById('attr-status').value,
        total_income: state.currentPreview.attributes.total_income,
        total_expense: state.currentPreview.attributes.total_expense,
        net_balance: state.currentPreview.attributes.net_balance,
        transaction_count: state.currentPreview.attributes.transaction_count
    };

    // 获取编辑后的 Markdown
    const markdownContent = document.getElementById('markdown-editor').value;

    // 显示提交模态框
    const modal = document.getElementById('submitting-modal');
    modal.style.display = 'flex';
    resetSubmitProgress();

    // 启用关闭按钮
    const closeBtn = document.getElementById('submit-modal-close-btn');
    closeBtn.disabled = false;
    closeBtn.title = '关闭（可离开页面，后台继续提交）';

    try {
        // 阶段1: 验证数据
        updateSubmitProgressStep('submit-step-validate', 'active', '正在验证数据...');
        await new Promise(resolve => setTimeout(resolve, 200));

        // 验证必填字段
        if (!attributes.title || !attributes.start_date || !attributes.end_date) {
            updateSubmitProgressStep('submit-step-validate', 'error', '数据验证失败');
            showToast('请填写完整的必填字段', 'error');
            await new Promise(resolve => setTimeout(resolve, 500));
            modal.style.display = 'none';
            return;
        }

        updateSubmitProgressStep('submit-step-validate', 'completed', '验证完成');
        updateSubmitProgressStep('submit-step-create', 'active', '正在连接 Notion...');

        // 准备提交数据
        const submitData = {
            review_type: state.reviewType,
            attributes: attributes,
            markdown_content: markdownContent
        };

        // 设置 60 秒超时（Notion API 创建页面可能需要较长时间）
        const response = await window.Auth.apiRequest('/api/review/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(submitData)
        }, 60000);  // 60 秒超时

        if (!response) {
            updateSubmitProgressStep('submit-step-create', 'error', '请求失败');
            showToast('请求失败，请检查网络连接', 'error');
            await new Promise(resolve => setTimeout(resolve, 500));
            modal.style.display = 'none';
            return;
        }

        if (!response.ok) {
            updateSubmitProgressStep('submit-step-create', 'error', '创建失败');
            // 尝试读取错误响应
            let errorText = response.statusText || '网络错误';
            try {
                const errorData = await response.json();
                errorText = errorData.detail || errorData.error || errorText;
            } catch (e) {
                // 忽略 JSON 解析错误
            }
            showToast('提交失败: ' + errorText, 'error');
            await new Promise(resolve => setTimeout(resolve, 500));
            modal.style.display = 'none';
            return;
        }

        // 请求成功，更新进度
        updateSubmitProgressStep('submit-step-create', 'completed', '页面创建完成');
        updateSubmitProgressStep('submit-step-content', 'active', '正在添加内容...');

        await new Promise(resolve => setTimeout(resolve, 300));
        updateSubmitProgressStep('submit-step-content', 'completed', '内容添加完成');
        updateSubmitProgressStep('submit-step-finalize', 'active', '正在完成...');

        const data = await response.json();

        await new Promise(resolve => setTimeout(resolve, 200));
        updateSubmitProgressStep('submit-step-finalize', 'completed', '完成');

        if (data.success) {
            state.notionPageUrl = data.url;
            await new Promise(resolve => setTimeout(resolve, 300));
            modal.style.display = 'none';
            showSuccessModal(attributes);
        } else {
            updateSubmitProgressStep('submit-step-finalize', 'error', '失败');
            showToast('提交失败: ' + (data.error || '未知错误'), 'error');
            await new Promise(resolve => setTimeout(resolve, 500));
            modal.style.display = 'none';
        }
    } catch (error) {
        console.error('[ERROR] Submit error:', error);

        // 更新错误状态
        const activeStep = document.querySelector('.progress-step.active');
        if (activeStep) {
            updateSubmitProgressStep(activeStep.id, 'error', '请求失败');
        }

        // 显示详细的错误提示
        let errorMsg = '未知错误';
        if (error.name === 'AbortError') {
            errorMsg = '请求超时，请检查网络连接或稍后重试';
        } else if (error.message) {
            if (error.message.includes('Connection reset') || error.message.includes('104')) {
                errorMsg = '网络连接中断，请检查网络后重试';
            } else if (error.message.includes('timeout') || error.message.includes('超时')) {
                errorMsg = '请求超时（60秒），请稍后重试';
            } else if (error.message.includes('fetch') || error.message.includes('network')) {
                errorMsg = '网络请求失败，请检查网络连接';
            } else {
                errorMsg = error.message;
            }
        }

        showToast('提交失败: ' + errorMsg, 'error');

        await new Promise(resolve => setTimeout(resolve, 1000));
        modal.style.display = 'none';
    }
}

// 关闭提交模态框（允许用户离开页面）
function closeSubmitModal() {
    const modal = document.getElementById('submitting-modal');
    const closeBtn = document.getElementById('submit-modal-close-btn');

    // 禁用关闭按钮，防止重复点击
    closeBtn.disabled = true;

    // 隐藏模态框
    modal.style.display = 'none';

    // 显示提示，告知用户可以离开
    showToast('提交仍在后台进行，您可以离开此页面', 'info');
}

// 重置提交进度
function resetSubmitProgress() {
    const steps = ['submit-step-validate', 'submit-step-create', 'submit-step-content', 'submit-step-finalize'];
    steps.forEach(stepId => {
        const step = document.getElementById(stepId);
        if (step) {
            step.classList.remove('active', 'completed', 'error');
            step.querySelector('.step-status').textContent = '等待中...';
        }
    });
}

// 更新提交进度步骤
function updateSubmitProgressStep(stepId, status, statusText) {
    const step = document.getElementById(stepId);
    if (!step) return;

    step.classList.remove('active', 'completed', 'error');

    if (status === 'active') {
        step.classList.add('active');
        step.querySelector('.step-status').textContent = statusText || '处理中...';
    } else if (status === 'completed') {
        step.classList.add('completed');
        step.querySelector('.step-status').textContent = statusText || '完成';
    } else if (status === 'error') {
        step.classList.add('error');
        step.querySelector('.step-status').textContent = statusText || '失败';
    } else {
        step.querySelector('.step-status').textContent = statusText || '等待中...';
    }
}

function showSuccessModal(attributes) {
    const detailsHtml = `
        <div class="result-item">
            <span class="label">标题</span>
            <span class="value">${attributes.title}</span>
        </div>
        <div class="result-item">
            <span class="label">周期</span>
            <span class="value">${attributes.start_date} 至 ${attributes.end_date}</span>
        </div>
        <div class="result-item">
            <span class="label">收入</span>
            <span class="value income">¥${formatCurrency(attributes.total_income)}</span>
        </div>
        <div class="result-item">
            <span class="label">支出</span>
            <span class="value expense">¥${formatCurrency(attributes.total_expense)}</span>
        </div>
        <div class="result-item">
            <span class="label">净收益</span>
            <span class="value ${attributes.net_balance >= 0 ? 'income' : 'expense'}">
                ¥${formatCurrency(attributes.net_balance)}
            </span>
        </div>
    `;

    document.getElementById('success-details').innerHTML = detailsHtml;
    document.getElementById('success-modal').style.display = 'flex';
}

function closeSuccessModal() {
    document.getElementById('success-modal').style.display = 'none';
    closePreview();
}

function openNotionPage() {
    if (state.notionPageUrl) {
        window.open(state.notionPageUrl, '_blank');
    }
}

// ==================== 工具函数 ====================
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatCurrency(value) {
    if (value === null || value === undefined) return '0.00';
    return parseFloat(value).toFixed(2);
}

function showToast(message, type = 'success') {
    if (window.toast) {
        const typeMap = {
            'success': 'success',
            'error': 'error',
            'warning': 'warning',
            'info': 'info'
        };
        window.toast[typeMap[type] || 'info'](message);
    } else {
        console.log(`[${type}] ${message}`);
    }
}
