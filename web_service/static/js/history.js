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
            return;
        }

        container.innerHTML = filteredHistory.map(item => `
            <div class="history-item" data-history-id="${item.id}">
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
            </div>
        `).join('');

        // 绑定点击事件
        container.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', () => {
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

    // 格式化日期
    function formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    }

    // 格式化日期时间
    function formatDateTime(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
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
    }

    // DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
