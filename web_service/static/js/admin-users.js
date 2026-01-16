/**
 * 用户管理页面逻辑
 */

(function() {
    'use strict';

    // 当前状态
    let currentPage = 1;
    let pageSize = 20;
    let totalItems = 0;
    let totalPages = 0;
    let currentFilters = {
        search: '',
        is_active: null,
        is_superuser: null
    };
    let selectedUserId = null;

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

        // 3秒后自动消失
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // 加载系统统计
    async function loadStats() {
        try {
            const response = await fetch('/api/admin/stats', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const stats = await response.json();
                document.getElementById('total-users').textContent = stats.total_users || 0;
                document.getElementById('active-users').textContent = stats.active_users || 0;
                document.getElementById('new-users-today').textContent = stats.uploads_today || 0;
                document.getElementById('total-uploads').textContent = stats.total_uploads || 0;
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    // 加载用户列表
    async function loadUsers() {
        const tableBody = document.getElementById('users-table-body');
        if (!tableBody) return;

        // 显示加载中
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: #9ca3af;">
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

            if (currentFilters.search) {
                params.append('search', currentFilters.search);
            }
            if (currentFilters.is_active !== null) {
                params.append('is_active', currentFilters.is_active);
            }
            if (currentFilters.is_superuser !== null) {
                params.append('is_superuser', currentFilters.is_superuser);
            }

            const response = await fetch(`/api/admin/users?${params}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                totalItems = data.total;
                totalPages = Math.ceil(totalItems / pageSize);

                renderUsersTable(data.users);
                updatePagination();
            } else if (response.status === 401) {
                // 未授权，跳转到登录页
                window.location.href = '/login';
            } else {
                throw new Error('加载失败');
            }
        } catch (error) {
            console.error('Failed to load users:', error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 40px; color: #ef4444;">
                        加载失败，请刷新页面重试
                    </td>
                </tr>
            `;
        }
    }

    // 渲染用户表格
    function renderUsersTable(users) {
        const tableBody = document.getElementById('users-table-body');
        if (!tableBody) return;

        if (users.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 40px; color: #9ca3af;">
                        暂无用户数据
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = users.map(user => `
            <tr>
                <td>
                    <input type="checkbox" class="user-checkbox" data-user-id="${user.id}">
                </td>
                <td>
                    <div class="user-cell">
                        <div class="user-cell-avatar">${user.username.charAt(0).toUpperCase()}</div>
                        <div class="user-cell-info">
                            <div class="user-cell-name">${escapeHtml(user.username)}</div>
                            <div class="user-cell-email">${escapeHtml(user.email)}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="role-badge ${user.is_superuser ? 'superuser' : 'user'}">
                        ${user.is_superuser ? '超级管理员' : '普通用户'}
                    </span>
                </td>
                <td>
                    <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                        ${user.is_active ? '活跃' : '未激活'}
                    </span>
                </td>
                <td>
                    <span class="stat-number" data-user-id="${user.id}" data-stat="uploads">-</span>
                </td>
                <td>
                    <span class="date-text">${formatDate(user.created_at)}</span>
                </td>
                <td>
                    <span class="date-text">${user.last_login ? formatDate(user.last_login) : '从未登录'}</span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-icon" data-action="view" data-user-id="${user.id}" title="查看详情">
                            👁
                        </button>
                        <button class="btn-icon" data-action="edit" data-user-id="${user.id}" title="编辑">
                            ✏
                        </button>
                        <button class="btn-icon danger" data-action="delete" data-user-id="${user.id}" title="删除">
                            🗑
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        // 加载每个用户的统计
        loadUserStats(users.map(u => u.id));

        // 绑定操作按钮事件
        bindActionButtons();
    }

    // 加载用户统计
    async function loadUserStats(userIds) {
        for (const userId of userIds) {
            try {
                const response = await fetch(`/api/admin/users/${userId}`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    const uploadsEl = document.querySelector(`[data-user-id="${userId}"][data-stat="uploads"]`);
                    if (uploadsEl) {
                        uploadsEl.textContent = data.stats?.total_uploads || 0;
                    }
                }
            } catch (error) {
                console.error(`Failed to load stats for user ${userId}:`, error);
            }
        }
    }

    // 绑定操作按钮事件
    function bindActionButtons() {
        document.querySelectorAll('.btn-icon[data-action]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const userId = parseInt(btn.dataset.userId);
                const action = btn.dataset.action;

                if (action === 'view') {
                    await showUserDetail(userId);
                } else if (action === 'edit') {
                    await editUser(userId);
                } else if (action === 'delete') {
                    await deleteUser(userId);
                }
            });
        });
    }

    // 显示用户详情
    async function showUserDetail(userId) {
        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                selectedUserId = userId;

                const modal = document.getElementById('user-detail-modal');
                const modalBody = document.getElementById('modal-body-content');

                modalBody.innerHTML = `
                    <div class="user-detail-section">
                        <h3>基本信息</h3>
                        <div class="detail-row">
                            <span class="detail-label">用户名：</span>
                            <span class="detail-value">${escapeHtml(data.user.username)}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">邮箱：</span>
                            <span class="detail-value">${escapeHtml(data.user.email)}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">角色：</span>
                            <span class="detail-value">${data.user.is_superuser ? '超级管理员' : '普通用户'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">状态：</span>
                            <span class="detail-value">${data.user.is_active ? '活跃' : '未激活'}</span>
                        </div>
                    </div>
                    <div class="user-detail-section">
                        <h3>使用统计</h3>
                        <div class="detail-row">
                            <span class="detail-label">上传次数：</span>
                            <span class="detail-value">${data.stats.total_uploads}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">导入记录：</span>
                            <span class="detail-value">${data.stats.total_imports}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Notion配置：</span>
                            <span class="detail-value">${data.notion_configured ? '已配置' : '未配置'}</span>
                        </div>
                    </div>
                    <div class="user-detail-section">
                        <h3>时间信息</h3>
                        <div class="detail-row">
                            <span class="detail-label">注册时间：</span>
                            <span class="detail-value">${formatDate(data.user.created_at)}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">最后登录：</span>
                            <span class="detail-value">${data.user.last_login ? formatDate(data.user.last_login) : '从未登录'}</span>
                        </div>
                    </div>
                `;

                modal.style.display = 'flex';

                // 绑定模态框按钮事件
                bindModalButtons(userId);
            }
        } catch (error) {
            console.error('Failed to load user detail:', error);
            showToast('加载用户详情失败', 'error');
        }
    }

    // 绑定模态框按钮事件
    function bindModalButtons(userId) {
        const editBtn = document.getElementById('edit-user-btn');
        const resetBtn = document.getElementById('reset-password-btn');
        const deleteBtn = document.getElementById('delete-user-btn');
        const closeBtn = document.getElementById('modal-close');

        // 移除旧的事件监听器
        editBtn.replaceWith(editBtn.cloneNode(true));
        resetBtn.replaceWith(resetBtn.cloneNode(true));
        deleteBtn.replaceWith(deleteBtn.cloneNode(true));
        closeBtn.replaceWith(closeBtn.cloneNode(true));

        // 重新获取元素并绑定事件
        document.getElementById('edit-user-btn').addEventListener('click', () => editUser(userId));
        document.getElementById('reset-password-btn').addEventListener('click', () => resetPassword(userId));
        document.getElementById('delete-user-btn').addEventListener('click', () => deleteUser(userId));
        document.getElementById('modal-close').addEventListener('click', closeModal);
    }

    // 编辑用户
    async function editUser(userId) {
        const newEmail = prompt('请输入新的邮箱地址：');
        if (!newEmail) return;

        const isActive = confirm('用户是否活跃？\n确定 = 活跃\n取消 = 未激活');
        const isSuperuser = confirm('是否设为超级管理员？\n确定 = 是\n取消 = 否');

        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: newEmail,
                    is_active: isActive,
                    is_superuser: isSuperuser
                })
            });

            if (response.ok) {
                showToast('用户已更新');
                closeModal();
                loadUsers();
            } else {
                const data = await response.json();
                showToast(data.detail || '更新失败', 'error');
            }
        } catch (error) {
            console.error('Failed to update user:', error);
            showToast('网络错误', 'error');
        }
    }

    // 重置密码
    async function resetPassword(userId) {
        const newPassword = prompt('请输入新密码：');
        if (!newPassword) return;

        const confirm = window.confirm('确定要重置该用户的密码吗？这会使该用户的所有会话失效。');
        if (!confirm) return;

        try {
            const response = await fetch(`/api/admin/users/${userId}/reset-password`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ new_password: newPassword })
            });

            if (response.ok) {
                showToast('密码已重置');
                closeModal();
            } else {
                const data = await response.json();
                showToast(data.detail || '重置失败', 'error');
            }
        } catch (error) {
            console.error('Failed to reset password:', error);
            showToast('网络错误', 'error');
        }
    }

    // 删除用户
    async function deleteUser(userId) {
        const confirm = window.confirm('确定要删除该用户吗？此操作不可撤销！');
        if (!confirm) return;

        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                showToast('用户已删除');
                closeModal();
                loadUsers();
                loadStats();
            } else {
                const data = await response.json();
                showToast(data.detail || '删除失败', 'error');
            }
        } catch (error) {
            console.error('Failed to delete user:', error);
            showToast('网络错误', 'error');
        }
    }

    // 关闭模态框
    function closeModal() {
        const modal = document.getElementById('user-detail-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        selectedUserId = null;
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
                loadUsers();
            });
        });
    }

    // 初始化搜索 - 使用 PerfUtils.debounce 优化性能
    function initSearch() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;

        const debouncedSearch = PerfUtils.debounce(() => {
            currentFilters.search = searchInput.value;
            currentPage = 1;
            loadUsers();
        }, 500);

        searchInput.addEventListener('input', debouncedSearch);
    }

    // 初始化筛选器
    function initFilters() {
        const statusFilter = document.getElementById('status-filter');
        const roleFilter = document.getElementById('role-filter');

        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                const value = statusFilter.value;
                currentFilters.is_active = value === '' ? null : value === 'active';
                currentPage = 1;
                loadUsers();
            });
        }

        if (roleFilter) {
            roleFilter.addEventListener('change', () => {
                const value = roleFilter.value;
                currentFilters.is_superuser = value === '' ? null : value === 'superuser';
                currentPage = 1;
                loadUsers();
            });
        }
    }

    // 初始化添加用户按钮
    function initAddUser() {
        const addBtn = document.getElementById('add-user-btn');
        if (!addBtn) return;

        addBtn.addEventListener('click', async () => {
            const username = prompt('请输入用户名：');
            if (!username) return;

            const email = prompt('请输入邮箱地址：');
            if (!email) return;

            const password = prompt('请输入密码：');
            if (!password) return;

            const isSuperuser = confirm('是否设为超级管理员？\n确定 = 是\n取消 = 否');

            try {
                const response = await fetch('/api/admin/users', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username,
                        email,
                        password,
                        is_superuser: isSuperuser,
                        is_active: true
                    })
                });

                if (response.ok) {
                    showToast('用户已创建');
                    loadUsers();
                    loadStats();
                } else {
                    const data = await response.json();
                    showToast(data.detail || '创建失败', 'error');
                }
            } catch (error) {
                console.error('Failed to create user:', error);
                showToast('网络错误', 'error');
            }
        });
    }

    // 初始化分页按钮
    function initPagination() {
        document.getElementById('prev-page').addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                loadUsers();
            }
        });

        document.getElementById('next-page').addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                loadUsers();
            }
        });
    }

    // 初始化全选
    function initSelectAll() {
        const selectAll = document.getElementById('select-all-users');
        if (!selectAll) return;

        selectAll.addEventListener('change', () => {
            document.querySelectorAll('.user-checkbox').forEach(checkbox => {
                checkbox.checked = selectAll.checked;
            });
        });
    }

    // HTML转义
    function escapeHtml(text) {
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
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
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
        loadStats();
        loadUsers();
        initSearch();
        initFilters();
        initAddUser();
        initPagination();
        initSelectAll();

        // 绑定模态框背景关闭
        const backdrop = document.getElementById('modal-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', closeModal);
        }
    }

    // DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
