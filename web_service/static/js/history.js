/**
 * 导入历史页面逻辑
 */

(function() {
    'use strict';

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

    // 显示 Toast 消息
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

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

                document.getElementById('total-imports').textContent = stats.total || 0;
                document.getElementById('successful-imports').textContent = stats.successful || 0;
                document.getElementById('total-records').textContent = stats.total_records || 0;

                const avgDuration = stats.avg_duration
                    ? `${Math.round(stats.avg_duration)}秒`
                    : '-';
                document.getElementById('avg-duration').textContent = avgDuration;
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    // 加载导入历史
    async function loadHistory() {
        const container = document.getElementById('history-items');
        if (!container) return;

        // 显示加载中
        container.innerHTML = `
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
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <p>加载失败，请刷新页面重试</p>
                </div>
            `;
        }
    }

    // 渲染历史记录
    function renderHistory() {
        const container = document.getElementById('history-items');
        if (!container) return;

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
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <p>暂无导入记录</p>
                </div>
            `;
            clearSelection();
            return;
        }

        container.innerHTML = filteredHistory.map(item => `
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

    // 绑定历史记录项事件
    function bindHistoryItemEvents() {
        const container = document.getElementById('history-items');
        if (!container) return;

        // 绑定复选框事件
        container.querySelectorAll('.history-select-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const historyId = parseInt(e.target.dataset.historyId);
                if (e.target.checked) {
                    selectedHistoryIds.add(historyId);
                } else {
                    selectedHistoryIds.delete(historyId);
                }
                updateBulkActionsBar();
                updateSelectAllCheckbox();
            });

            // 阻止复选框冒泡
            checkbox.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        });

        // 绑定操作按钮事件
        container.querySelectorAll('.history-item-actions .action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const historyId = parseInt(btn.dataset.historyId);
                const action = btn.dataset.action;

                if (action === 'view') {
                    showDetail(historyId);
                } else if (action === 'delete') {
                    deleteHistoryItem(historyId);
                }
            });
        });

        // 绑定点击查看详情事件（排除复选框和操作按钮）
        container.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.history-checkbox') || e.target.closest('.history-item-actions')) {
                    return;
                }
                const historyId = parseInt(item.dataset.historyId);
                showDetail(historyId);
            });
        });
    }

    // 显示详情
    function showDetail(historyId) {
        const item = allHistory.find(h => h.id === historyId);
        if (!item) return;

        const modal = document.getElementById('detail-modal');
        const modalBody = document.getElementById('modal-body-content');

        modalBody.innerHTML = `
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

        modal.style.display = 'flex';

        // 绑定关闭按钮
        document.getElementById('modal-close').onclick = closeModal;
        document.getElementById('modal-ok').onclick = closeModal;
        document.getElementById('modal-backdrop').onclick = closeModal;
    }

    // 关闭模态框
    function closeModal() {
        const modal = document.getElementById('detail-modal');
        if (modal) {
            modal.style.display = 'none';
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
        document.getElementById('prev-page').disabled = currentPage <= 1;
        document.getElementById('next-page').disabled = currentPage >= totalPages;

        renderPaginationPages();
    }

    // 渲染页码
    function renderPaginationPages() {
        const container = document.getElementById('pagination-pages');
        if (!container) return;

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
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;

        const debouncedSearch = PerfUtils.debounce(() => {
            currentFilters.search = searchInput.value;
            renderHistory();
        }, 300);

        searchInput.addEventListener('input', debouncedSearch);
    }

    // 初始化筛选器
    function initFilters() {
        const statusFilter = document.getElementById('status-filter');
        const platformFilter = document.getElementById('platform-filter');
        const startDateInput = document.getElementById('start-date');
        const endDateInput = document.getElementById('end-date');
        const clearDateBtn = document.getElementById('clear-date-filter');
        const clearAllBtn = document.getElementById('clear-all-filters');

        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                currentFilters.status = statusFilter.value;
                renderHistory();
            });
        }

        if (platformFilter) {
            platformFilter.addEventListener('change', () => {
                currentFilters.platform = platformFilter.value;
                renderHistory();
            });
        }

        // 清除所有筛选
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => {
                currentFilters.search = '';
                currentFilters.status = '';
                currentFilters.platform = '';
                if (statusFilter) statusFilter.value = '';
                if (platformFilter) platformFilter.value = '';
                const searchInput = document.getElementById('search-input');
                if (searchInput) searchInput.value = '';
                renderHistory();
            });
        }

        // 日期过滤需要重新加载数据（服务端过滤）
        if (startDateInput) {
            startDateInput.addEventListener('change', () => {
                currentFilters.start_date = startDateInput.value || '';
                currentPage = 1;  // 重置到第一页
                loadHistory();
            });
        }

        if (endDateInput) {
            endDateInput.addEventListener('change', () => {
                currentFilters.end_date = endDateInput.value || '';
                currentPage = 1;  // 重置到第一页
                loadHistory();
            });
        }

        if (clearDateBtn) {
            clearDateBtn.addEventListener('click', () => {
                if (startDateInput) startDateInput.value = '';
                if (endDateInput) endDateInput.value = '';
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
        const bulkActionsBar = document.getElementById('bulk-actions-bar');
        const selectedCount = document.getElementById('selected-count');

        if (!bulkActionsBar) return;

        if (selectedHistoryIds.size > 0) {
            bulkActionsBar.style.display = 'flex';
            if (selectedCount) selectedCount.textContent = selectedHistoryIds.size;
        } else {
            bulkActionsBar.style.display = 'none';
        }
    }

    // 更新全选复选框状态
    function updateSelectAllCheckbox() {
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        const visibleCheckboxes = document.querySelectorAll('.history-select-checkbox');
        const checkedCount = document.querySelectorAll('.history-select-checkbox:checked').length;

        if (!selectAllCheckbox) return;

        if (visibleCheckboxes.length > 0 && checkedCount === visibleCheckboxes.length) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCount > 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
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
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        const visibleCheckboxes = document.querySelectorAll('.history-select-checkbox');

        if (!selectAllCheckbox) return;

        visibleCheckboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
            const historyId = parseInt(checkbox.dataset.historyId);
            if (selectAllCheckbox.checked) {
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
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
        const cancelSelectionBtn = document.getElementById('cancel-selection-btn');

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', toggleSelectAll);
        }

        if (bulkDeleteBtn) {
            bulkDeleteBtn.addEventListener('click', bulkDeleteHistory);
        }

        if (cancelSelectionBtn) {
            cancelSelectionBtn.addEventListener('click', clearSelection);
        }
    }

    // 初始化分页
    function initPagination() {
        document.getElementById('prev-page').addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                loadHistory();
            }
        });

        document.getElementById('next-page').addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                loadHistory();
            }
        });
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
