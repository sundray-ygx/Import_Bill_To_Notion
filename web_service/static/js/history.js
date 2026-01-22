/**
 * 导入历史页面逻辑
 */

(function() {
    'use strict';

    // DOM 元素缓存
    const dom = {
        historyItems: null,
        toastContainer: null,
        searchInput: null,
        statusFilter: null,
        platformFilter: null,
        startDateInput: null,
        endDateInput: null,
        clearDateBtn: null,
        clearAllBtn: null,
        selectAllCheckbox: null,
        bulkActionsBar: null,
        selectedCount: null,
        bulkDeleteBtn: null,
        cancelSelectionBtn: null,
        prevPageBtn: null,
        nextPageBtn: null,
        paginationPages: null,
        detailModal: null,
        modalBody: null,
        modalClose: null,
        modalOk: null,
        modalBackdrop: null,
        totalImports: null,
        successfulImports: null,
        totalRecords: null,
        avgDuration: null
    };

    // 当前状态
    let currentPage = 1;
    let pageSize = 10;
    let totalItems = 0;
    let totalPages = 0;
    let currentFilters = {
        search: '',
        status: '',
        platform: '',
        start_date: '',
        end_date: ''
    };
    let allHistory = [];
    let selectedHistoryIds = new Set();

    // 初始化 DOM 元素缓存
    function initDomCache() {
        dom.historyItems = document.getElementById('history-items');
        dom.toastContainer = document.getElementById('toast-container');
        dom.searchInput = document.getElementById('search-input');
        dom.statusFilter = document.getElementById('status-filter');
        dom.platformFilter = document.getElementById('platform-filter');
        dom.startDateInput = document.getElementById('start-date');
        dom.endDateInput = document.getElementById('end-date');
        dom.clearDateBtn = document.getElementById('clear-date-filter');
        dom.clearAllBtn = document.getElementById('clear-all-filters');
        dom.selectAllCheckbox = document.getElementById('select-all-checkbox');
        dom.bulkActionsBar = document.getElementById('bulk-actions-bar');
        dom.selectedCount = document.getElementById('selected-count');
        dom.bulkDeleteBtn = document.getElementById('bulk-delete-btn');
        dom.cancelSelectionBtn = document.getElementById('cancel-selection-btn');
        dom.prevPageBtn = document.getElementById('prev-page');
        dom.nextPageBtn = document.getElementById('next-page');
        dom.paginationPages = document.getElementById('pagination-pages');
        dom.detailModal = document.getElementById('detail-modal');
        dom.modalBody = document.getElementById('modal-body-content');
        dom.modalClose = document.getElementById('modal-close');
        dom.modalOk = document.getElementById('modal-ok');
        dom.modalBackdrop = document.getElementById('modal-backdrop');
        dom.totalImports = document.getElementById('total-imports');
        dom.successfulImports = document.getElementById('successful-imports');
        dom.totalRecords = document.getElementById('total-records');
        dom.avgDuration = document.getElementById('avg-duration');
    }

    // 显示 Toast 消息
    function showToast(message, type = 'success') {
        if (!dom.toastContainer) return;
        const container = dom.toastContainer;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
                <span class="toast-message">${message}</span>
            </div>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // 加载统计数据
    async function loadStats() {
        try {
            const response = await window.Auth.apiRequest('/api/bills/history/stats');
            if (response && response.ok) {
                const stats = await response.json();

                if (dom.totalImports) dom.totalImports.textContent = stats.total || 0;
                if (dom.successfulImports) dom.successfulImports.textContent = stats.successful || 0;
                if (dom.totalRecords) dom.totalRecords.textContent = stats.total_records || 0;

                const avgDuration = stats.avg_duration
                    ? `${Math.round(stats.avg_duration)}秒`
                    : '-';
                if (dom.avgDuration) dom.avgDuration.textContent = avgDuration;
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    // 加载导入历史
    async function loadHistory() {
        if (!dom.historyItems) return;

        // 显示加载中
        dom.historyItems.innerHTML = `
            <div class="loading-state">
                <div class="loading-spinner"></div>
                <p>加载中...</p>
            </div>
        `;

        try {
            // 构建查询参数
            const params = new URLSearchParams({
                page: currentPage,
                page_size: pageSize
            });

            // 添加日期过滤参数
            if (currentFilters.start_date) {
                params.append('start_date', currentFilters.start_date);
            }
            if (currentFilters.end_date) {
                params.append('end_date', currentFilters.end_date);
            }

            const response = await window.Auth.apiRequest(`/api/bills/history?${params}`);

            if (response && response.ok) {
                const data = await response.json();
                allHistory = data.history || [];
                totalItems = data.total || 0;
                totalPages = Math.ceil(totalItems / pageSize);

                renderHistory();
                updatePagination();
            } else if (response && response.status === 401) {
                window.location.href = '/login';
            } else {
                throw new Error('加载失败');
            }
        } catch (error) {
            console.error('Failed to load history:', error);
            dom.historyItems.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <p>加载失败，请刷新页面重试</p>
                </div>
            `;
        }
    }

    // 渲染历史记录
    function renderHistory() {
        if (!dom.historyItems) return;

        // 应用筛选
        let filteredHistory = allHistory.filter(item => {
            const fileName = item.original_file_name || item.file_name || '';
            const matchSearch = !currentFilters.search ||
                fileName.toLowerCase().includes(currentFilters.search.toLowerCase()) ||
                item.platform?.toLowerCase().includes(currentFilters.search.toLowerCase());

            const matchStatus = !currentFilters.status || item.status === currentFilters.status;
            const matchPlatform = !currentFilters.platform || item.platform === currentFilters.platform;

            return matchSearch && matchStatus && matchPlatform;
        });

        if (filteredHistory.length === 0) {
            dom.historyItems.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <p>暂无导入记录</p>
                </div>
            `;
            clearSelection();
            return;
        }

        dom.historyItems.innerHTML = filteredHistory.map(item => `
            <div class="history-item" data-history-id="${item.id}">
                <div class="history-checkbox">
                    <input type="checkbox" class="history-select-checkbox" data-history-id="${item.id}">
                </div>
                <div class="history-item-icon ${item.platform}">
                    ${getPlatformIcon(item.platform)}
                </div>
                <div class="history-item-content">
                    <div class="history-item-title">${escapeHtml(item.original_file_name || item.file_name || '未知文件')}</div>
                    <div class="history-item-meta">
                        <span class="history-item-meta-item">
                            📅 ${formatDate(item.started_at)}
                        </span>
                        <span class="history-item-meta-item">
                            ⏱ ${item.duration_seconds ? item.duration_seconds + '秒' : '-'}
                        </span>
                    </div>
                </div>
                <div class="history-item-status">
                    <span class="status-badge ${item.status}">
                        ${getStatusLabel(item.status)}
                    </span>
                    <div class="history-item-stats">
                        <span>${item.imported_records || 0}/${item.total_records || 0} 条</span>
                    </div>
                </div>
                <div class="history-item-actions">
                    <button class="action-btn action-btn-view" data-action="view" data-history-id="${item.id}" title="查看详情">
                        <span>👁</span>
                    </button>
                    <button class="action-btn action-btn-delete" data-action="delete" data-history-id="${item.id}" title="删除">
                        <span>🗑</span>
                    </button>
                </div>
            </div>
        `).join('');

        // 绑定事件
        bindHistoryItemEvents();
    }

    // 绑定历史记录项事件（使用事件委托优化性能）
    function bindHistoryItemEvents() {
        if (!dom.historyItems) return;

        // 使用事件委托处理所有事件
        dom.historyItems.addEventListener('change', (e) => {
            if (e.target.classList.contains('history-select-checkbox')) {
                const historyId = parseInt(e.target.dataset.historyId);
                if (e.target.checked) {
                    selectedHistoryIds.add(historyId);
                } else {
                    selectedHistoryIds.delete(historyId);
                }
                updateBulkActionsBar();
                updateSelectAllCheckbox();
                e.stopPropagation();
            }
        });

        dom.historyItems.addEventListener('click', (e) => {
            // 处理操作按钮
            const actionBtn = e.target.closest('.action-btn');
            if (actionBtn) {
                e.stopPropagation();
                const historyId = parseInt(actionBtn.dataset.historyId);
                const action = actionBtn.dataset.action;

                if (action === 'view') {
                    showDetail(historyId);
                } else if (action === 'delete') {
                    deleteHistoryItem(historyId);
                }
                return;
            }

            // 处理复选框
            if (e.target.classList.contains('history-select-checkbox')) {
                e.stopPropagation();
                return;
            }

            // 处理历史项点击（查看详情）
            const historyItem = e.target.closest('.history-item');
            if (historyItem && !e.target.closest('.history-checkbox') && !e.target.closest('.history-item-actions')) {
                const historyId = parseInt(historyItem.dataset.historyId);
                showDetail(historyId);
            }
        });
    }

    // 显示详情
    function showDetail(historyId) {
        const item = allHistory.find(h => h.id === historyId);
        if (!item || !dom.detailModal || !dom.modalBody) return;

        dom.modalBody.innerHTML = `
            <div class="detail-section">
                <h3>基本信息</h3>
                <div class="detail-row">
                    <span class="detail-label">文件名：</span>
                    <span class="detail-value">${escapeHtml(item.original_file_name || item.file_name || '-')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">平台：</span>
                    <span class="detail-value">${getPlatformLabel(item.platform)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">状态：</span>
                    <span class="detail-value">
                        <span class="status-badge ${item.status}">
                            ${getStatusLabel(item.status)}
                        </span>
                    </span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">开始时间：</span>
                    <span class="detail-value">${formatDateTime(item.started_at)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">完成时间：</span>
                    <span class="detail-value">${item.completed_at ? formatDateTime(item.completed_at) : '-'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">耗时：</span>
                    <span class="detail-value">${item.duration_seconds ? item.duration_seconds + ' 秒' : '-'}</span>
                </div>
            </div>

            <div class="detail-section">
                <h3>导入统计</h3>
                <div class="detail-stat-grid">
                    <div class="detail-stat-card">
                        <div class="detail-stat-value">${item.total_records || 0}</div>
                        <div class="detail-stat-label">总记录数</div>
                    </div>
                    <div class="detail-stat-card">
                        <div class="detail-stat-value">${item.imported_records || 0}</div>
                        <div class="detail-stat-label">成功导入</div>
                    </div>
                    <div class="detail-stat-card">
                        <div class="detail-stat-value">${item.skipped_records || 0}</div>
                        <div class="detail-stat-label">跳过记录</div>
                    </div>
                    <div class="detail-stat-card">
                        <div class="detail-stat-value">${item.failed_records || 0}</div>
                        <div class="detail-stat-label">失败记录</div>
                    </div>
                </div>
            </div>

            ${item.error_message ? `
            <div class="detail-section">
                <h3>错误信息</h3>
                <div style="background: #fef2f2; color: #dc2626; padding: 12px; border-radius: 8px; font-size: 0.9rem;">
                    ${escapeHtml(item.error_message)}
                </div>
            </div>
            ` : ''}
        `;

        dom.detailModal.style.display = 'flex';

        // 绑定关闭按钮
        if (dom.modalClose) dom.modalClose.onclick = closeModal;
        if (dom.modalOk) dom.modalOk.onclick = closeModal;
        if (dom.modalBackdrop) dom.modalBackdrop.onclick = closeModal;
    }

    // 关闭模态框
    function closeModal() {
        if (dom.detailModal) {
            dom.detailModal.style.display = 'none';
        }
    }

    // 获取平台图标
    function getPlatformIcon(platform) {
        const icons = {
            'alipay': '💰',
            'wechat': '💚',
            'unionpay': '💳'
        };
        return icons[platform] || '📄';
    }

    // 获取平台标签
    function getPlatformLabel(platform) {
        const labels = {
            'alipay': '支付宝',
            'wechat': '微信支付',
            'unionpay': '银联'
        };
        return labels[platform] || platform || '未知';
    }

    // 获取状态标签
    function getStatusLabel(status) {
        const labels = {
            'pending': '处理中',
            'success': '成功',
            'failed': '失败'
        };
        return labels[status] || status || '未知';
    }

    // 更新分页
    function updatePagination() {
        if (dom.prevPageBtn) dom.prevPageBtn.disabled = currentPage <= 1;
        if (dom.nextPageBtn) dom.nextPageBtn.disabled = currentPage >= totalPages;

        renderPaginationPages();
    }

    // 渲染页码
    function renderPaginationPages() {
        if (!dom.paginationPages) return;
        const container = dom.paginationPages;

        let pages = [];

        // 总是显示第一页
        pages.push(1);

        // 当前页附近的页码
        const start = Math.max(2, currentPage - 1);
        const end = Math.min(totalPages - 1, currentPage + 1);

        if (start > 2) {
            pages.push('...');
        }

        for (let i = start; i <= end; i++) {
            pages.push(i);
        }

        if (end < totalPages - 1) {
            pages.push('...');
        }

        // 总是显示最后一页
        if (totalPages > 1) {
            pages.push(totalPages);
        }

        container.innerHTML = pages.map(p => {
            if (p === '...') {
                return '<span class="pagination-ellipsis">...</span>';
            }
            return `
                <button class="pagination-page ${p === currentPage ? 'active' : ''}" data-page="${p}">
                    ${p}
                </button>
            `;
        }).join('');

        // 绑定页码点击事件
        container.querySelectorAll('.pagination-page[data-page]').forEach(btn => {
            btn.addEventListener('click', () => {
                currentPage = parseInt(btn.dataset.page);
                loadHistory();
            });
        });
    }

    // 初始化搜索 - 使用 PerfUtils.debounce 优化性能
    function initSearch() {
        if (!dom.searchInput) return;

        const debouncedSearch = PerfUtils.debounce(() => {
            currentFilters.search = dom.searchInput.value;
            renderHistory();
        }, 300);

        dom.searchInput.addEventListener('input', debouncedSearch);
    }

    // 初始化筛选器
    function initFilters() {
        if (dom.statusFilter) {
            dom.statusFilter.addEventListener('change', () => {
                currentFilters.status = dom.statusFilter.value;
                renderHistory();
            });
        }

        if (dom.platformFilter) {
            dom.platformFilter.addEventListener('change', () => {
                currentFilters.platform = dom.platformFilter.value;
                renderHistory();
            });
        }

        // 清除所有筛选
        if (dom.clearAllBtn) {
            dom.clearAllBtn.addEventListener('click', () => {
                currentFilters.search = '';
                currentFilters.status = '';
                currentFilters.platform = '';
                if (dom.statusFilter) dom.statusFilter.value = '';
                if (dom.platformFilter) dom.platformFilter.value = '';
                if (dom.searchInput) dom.searchInput.value = '';
                renderHistory();
            });
        }

        // 日期过滤需要重新加载数据（服务端过滤）
        if (dom.startDateInput) {
            dom.startDateInput.addEventListener('change', () => {
                currentFilters.start_date = dom.startDateInput.value || '';
                currentPage = 1;  // 重置到第一页
                loadHistory();
            });
        }

        if (dom.endDateInput) {
            dom.endDateInput.addEventListener('change', () => {
                currentFilters.end_date = dom.endDateInput.value || '';
                currentPage = 1;  // 重置到第一页
                loadHistory();
            });
        }

        if (dom.clearDateBtn) {
            dom.clearDateBtn.addEventListener('click', () => {
                if (dom.startDateInput) dom.startDateInput.value = '';
                if (dom.endDateInput) dom.endDateInput.value = '';
                currentFilters.start_date = '';
                currentFilters.end_date = '';
                currentPage = 1;
                loadHistory();
            });
        }
    }

    // ==================== 批量操作函数 ====================

    // 更新批量操作栏
    function updateBulkActionsBar() {
        if (!dom.bulkActionsBar) return;

        if (selectedHistoryIds.size > 0) {
            dom.bulkActionsBar.style.display = 'flex';
            if (dom.selectedCount) dom.selectedCount.textContent = selectedHistoryIds.size;
        } else {
            dom.bulkActionsBar.style.display = 'none';
        }
    }

    // 更新全选复选框状态
    function updateSelectAllCheckbox() {
        if (!dom.selectAllCheckbox) return;

        const visibleCheckboxes = document.querySelectorAll('.history-select-checkbox');
        const checkedCount = document.querySelectorAll('.history-select-checkbox:checked').length;

        if (visibleCheckboxes.length > 0 && checkedCount === visibleCheckboxes.length) {
            dom.selectAllCheckbox.checked = true;
            dom.selectAllCheckbox.indeterminate = false;
        } else if (checkedCount > 0) {
            dom.selectAllCheckbox.checked = false;
            dom.selectAllCheckbox.indeterminate = true;
        } else {
            dom.selectAllCheckbox.checked = false;
            dom.selectAllCheckbox.indeterminate = false;
        }
    }

    // 清空选择
    function clearSelection() {
        selectedHistoryIds.clear();
        document.querySelectorAll('.history-select-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        updateBulkActionsBar();
        updateSelectAllCheckbox();
    }

    // 全选/取消全选
    function toggleSelectAll() {
        if (!dom.selectAllCheckbox) return;

        const visibleCheckboxes = document.querySelectorAll('.history-select-checkbox');

        visibleCheckboxes.forEach(checkbox => {
            checkbox.checked = dom.selectAllCheckbox.checked;
            const historyId = parseInt(checkbox.dataset.historyId);
            if (dom.selectAllCheckbox.checked) {
                selectedHistoryIds.add(historyId);
            } else {
                selectedHistoryIds.delete(historyId);
            }
        });
        updateBulkActionsBar();
    }

    // 批量删除
    async function bulkDeleteHistory() {
        if (selectedHistoryIds.size === 0) {
            showToast('请先选择要删除的记录', 'warning');
            return;
        }

        const count = selectedHistoryIds.size;
        const confirm = window.confirm(`确定要删除选中的 ${count} 条记录吗？此操作不可撤销！`);
        if (!confirm) return;

        try {
            const response = await window.Auth.apiRequest('/api/bills/history/batch-delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ history_ids: Array.from(selectedHistoryIds) })
            });

            if (response && response.ok) {
                const data = await response.json();
                showToast(data.message || `成功删除 ${count} 条记录`);
                clearSelection();
                loadHistory();
                loadStats();
            } else {
                const data = await response.json();
                showToast(data.detail || '批量删除失败', 'error');
            }
        } catch (error) {
            console.error('Bulk delete error:', error);
            showToast('网络错误', 'error');
        }
    }

    // 删除单条记录
    async function deleteHistoryItem(historyId) {
        const confirm = window.confirm('确定要删除这条记录吗？此操作不可撤销！');
        if (!confirm) return;

        try {
            const response = await window.Auth.apiRequest(`/api/bills/history/${historyId}`, {
                method: 'DELETE'
            });

            if (response && response.ok) {
                showToast('记录已删除');
                loadHistory();
                loadStats();
            } else {
                const data = await response.json();
                showToast(data.detail || '删除失败', 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            showToast('网络错误', 'error');
        }
    }

    // 初始化批量操作
    function initBulkActions() {
        if (dom.selectAllCheckbox) {
            dom.selectAllCheckbox.addEventListener('change', toggleSelectAll);
        }

        if (dom.bulkDeleteBtn) {
            dom.bulkDeleteBtn.addEventListener('click', bulkDeleteHistory);
        }

        if (dom.cancelSelectionBtn) {
            dom.cancelSelectionBtn.addEventListener('click', clearSelection);
        }
    }

    // 初始化分页
    function initPagination() {
        if (dom.prevPageBtn) {
            dom.prevPageBtn.addEventListener('click', () => {
                if (currentPage > 1) {
                    currentPage--;
                    loadHistory();
                }
            });
        }

        if (dom.nextPageBtn) {
            dom.nextPageBtn.addEventListener('click', () => {
                if (currentPage < totalPages) {
                    currentPage++;
                    loadHistory();
                }
            });
        }
    }

    // HTML转义
    function escapeHtml(text) {
        if (!text) return '-';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 使用 DateTimeUtils 进行时间格式化（北京时间）
    function formatDate(dateStr) {
        return window.DateTimeUtils ? window.DateTimeUtils.formatDate(dateStr) : dateStr || '-';
    }

    // 格式化日期时间
    function formatDateTime(dateStr) {
        return window.DateTimeUtils ? window.DateTimeUtils.formatFullDateTime(dateStr) : dateStr || '-';
    }

    // 页面初始化
    function init() {
        // 检查登录状态
        if (!window.Auth.isLoggedIn()) {
            window.location.href = '/login';
            return;
        }

        // 初始化 DOM 元素缓存
        initDomCache();

        // 初始化各功能
        loadStats();
        loadHistory();
        initSearch();
        initFilters();
        initPagination();
        initBulkActions();
    }

    // DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
