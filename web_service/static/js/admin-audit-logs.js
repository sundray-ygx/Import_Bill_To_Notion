/**
 * 审计日志页面逻辑
 */

(function() {
    'use strict';

    // 当前状态
    let currentPage = 1;
    let pageSize = 50;
    let totalItems = 0;
    let totalPages = 0;
    let currentFilters = {
        action: '',
        user_id: null,
        time_range: ''
    };
    let allUsers = [];

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

    // 加载用户列表（用于筛选）
    async function loadUsersForFilter() {
        try {
            const response = await fetch('/api/admin/users?page_size=100', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                allUsers = data.users;

                const select = document.getElementById('user-filter');
                if (select) {
                    // 保留第一个选项（所有用户）
                    select.innerHTML = '<option value="">所有用户</option>';

                    allUsers.forEach(user => {
                        const option = document.createElement('option');
                        option.value = user.id;
                        option.textContent = `${user.username} (${user.email})`;
                        select.appendChild(option);
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load users:', error);
        }
    }

    // 加载审计日志
    async function loadLogs() {
        const tableBody = document.getElementById('logs-table-body');
        if (!tableBody) return;

        // 显示加载中
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px; color: #9ca3af;">
                    <div class="loading-spinner"></div>
                    <div style="margin-top: 12px;">加载中...</div>
                </td>
            </tr>
        `;

        try {
            // 构建查询参数
            const params = new URLSearchParams({
                page: currentPage,
                page_size: pageSize
            });

            if (currentFilters.action) {
                params.append('action', currentFilters.action);
            }
            if (currentFilters.user_id !== null) {
                params.append('user_id', currentFilters.user_id);
            }

            const response = await fetch(`/api/admin/audit-logs?${params}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                totalItems = data.total;
                totalPages = Math.ceil(totalItems / pageSize);

                renderLogsTable(data.logs);
                updatePagination();
            } else if (response.status === 401) {
                window.location.href = '/login';
            } else {
                throw new Error('加载失败');
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px; color: #ef4444;">
                        加载失败，请刷新页面重试
                    </td>
                </tr>
            `;
        }
    }

    // 渲染日志表格
    function renderLogsTable(logs) {
        const tableBody = document.getElementById('logs-table-body');
        if (!tableBody) return;

        if (logs.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px; color: #9ca3af;">
                        暂无日志数据
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = logs.map(log => `
            <tr class="log-row" data-log-id="${log.id}">
                <td>
                    <span class="date-text">${formatDateTime(log.created_at)}</span>
                </td>
                <td>
                    <span class="user-name">${log.username || '-'}</span>
                </td>
                <td>
                    <span class="action-badge">${getActionLabel(log.action)}</span>
                </td>
                <td>
                    <span class="resource-type">${log.resource_type || '-'}</span>
                </td>
                <td>
                    <span class="ip-address">${log.ip_address || '-'}</span>
                </td>
                <td>
                    <button class="btn-icon btn-sm" data-action="view-detail" data-log-id="${log.id}" title="查看详情">
                        👁
                    </button>
                </td>
            </tr>
        `).join('');

        // 绑定查看详情事件
        bindDetailButtons();
    }

    // 绑定详情按钮事件
    function bindDetailButtons() {
        document.querySelectorAll('.btn-icon[data-action="view-detail"]').forEach(btn => {
            btn.addEventListener('click', () => {
                const logId = parseInt(btn.dataset.logId);
                showLogDetail(logId);
            });
        });
    }

    // 显示日志详情
    function showLogDetail(logId) {
        const logRow = document.querySelector(`.log-row[data-log-id="${logId}"]`);
        if (!logRow) return;

        // 从行数据中获取信息
        const username = logRow.querySelector('.user-name')?.textContent || '-';
        const action = logRow.querySelector('.action-badge')?.textContent || '-';
        const resourceType = logRow.querySelector('.resource-type')?.textContent || '-';
        const ipAddress = logRow.querySelector('.ip-address')?.textContent || '-';
        const createdAt = logRow.querySelector('.date-text')?.textContent || '-';

        const modal = document.getElementById('log-detail-modal');
        const modalBody = document.getElementById('modal-body-content');

        modalBody.innerHTML = `
            <div class="log-detail-section">
                <h3>基本信息</h3>
                <div class="detail-row">
                    <span class="detail-label">操作时间：</span>
                    <span class="detail-value">${createdAt}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">操作用户：</span>
                    <span class="detail-value">${username}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">操作类型：</span>
                    <span class="detail-value">${action}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">资源类型：</span>
                    <span class="detail-value">${resourceType}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">IP地址：</span>
                    <span class="detail-value">${ipAddress}</span>
                </div>
            </div>
        `;

        modal.style.display = 'flex';

        // 绑定关闭按钮
        document.getElementById('modal-close').onclick = closeModal;
        document.getElementById('modal-ok').onclick = closeModal;
        document.getElementById('modal-backdrop').onclick = closeModal;
    }

    // 关闭模态框
    function closeModal() {
        const modal = document.getElementById('log-detail-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // 获取操作标签
    function getActionLabel(action) {
        const labels = {
            'user_created': '创建用户',
            'user_updated': '更新用户',
            'user_deleted': '删除用户',
            'password_reset': '重置密码',
            'password_changed': '修改密码',
            'login': '登录',
            'logout': '登出',
            'settings_updated': '更新设置',
            'notion_config_updated': '更新Notion配置',
            'notion_config_verified': '验证Notion配置'
        };
        return labels[action] || action;
    }

    // 更新分页
    function updatePagination() {
        const start = (currentPage - 1) * pageSize + 1;
        const end = Math.min(currentPage * pageSize, totalItems);

        document.getElementById('page-start').textContent = totalItems > 0 ? start : 0;
        document.getElementById('page-end').textContent = end;
        document.getElementById('total-items').textContent = totalItems;

        // 更新按钮状态
        document.getElementById('prev-page').disabled = currentPage <= 1;
        document.getElementById('next-page').disabled = currentPage >= totalPages;

        // 生成页码
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
        const start = Math.max(2, currentPage - 2);
        const end = Math.min(totalPages - 1, currentPage + 2);

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
                loadLogs();
            });
        });
    }

    // 初始化搜索 - 使用 PerfUtils.debounce 优化性能
    function initSearch() {
        const searchInput = document.getElementById('action-search');
        if (!searchInput) return;

        const debouncedSearch = PerfUtils.debounce(() => {
            currentFilters.action = searchInput.value;
            currentPage = 1;
            loadLogs();
        }, 500);

        searchInput.addEventListener('input', debouncedSearch);
    }

    // 初始化筛选器
    function initFilters() {
        const userFilter = document.getElementById('user-filter');
        const timeFilter = document.getElementById('time-filter');

        if (userFilter) {
            userFilter.addEventListener('change', () => {
                currentFilters.user_id = userFilter.value ? parseInt(userFilter.value) : null;
                currentPage = 1;
                loadLogs();
            });
        }

        if (timeFilter) {
            timeFilter.addEventListener('change', () => {
                currentFilters.time_range = timeFilter.value;
                // 时间筛选需要在后端实现，这里暂时只更新状态
                currentPage = 1;
                loadLogs();
            });
        }
    }

    // 初始化分页按钮
    function initPagination() {
        document.getElementById('prev-page').addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                loadLogs();
            }
        });

        document.getElementById('next-page').addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                loadLogs();
            }
        });
    }

    // 使用 DateTimeUtils 进行时间格式化（北京时间）
    function formatDateTime(dateStr) {
        return window.DateTimeUtils ? window.DateTimeUtils.formatFullDateTime(dateStr) : dateStr || '-';
    }

    // 页面初始化
    function init() {
        // 检查是否登录
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }

        // 检查是否为超级管理员
        const userStr = localStorage.getItem('user');
        if (userStr) {
            const user = JSON.parse(userStr);
            if (!user.is_superuser) {
                showToast('您没有权限访问此页面', 'error');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
                return;
            }
        }

        // 初始化各功能
        loadUsersForFilter();
        loadLogs();
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
