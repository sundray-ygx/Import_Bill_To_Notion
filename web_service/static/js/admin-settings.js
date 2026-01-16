/**
 * 系统设置页面逻辑
 */

(function() {
    'use strict';

    let currentSettings = {};

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

    // 加载系统设置
    async function loadSettings() {
        try {
            const response = await fetch('/api/admin/settings', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                currentSettings = await response.json();
                populateForms(currentSettings);
            } else if (response.status === 401) {
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
            showToast('加载设置失败', 'error');
        }
    }

    // 填充表单
    function populateForms(settings) {
        // 通用设置
        document.getElementById('max-file-size').value = settings.max_file_size || 52428800;
        document.getElementById('allowed-file-types').value = Array.isArray(settings.allowed_file_types)
            ? settings.allowed_file_types.join(',')
            : settings.allowed_file_types || '.csv,.txt,.xls,.xlsx';

        // 安全设置
        document.getElementById('session-timeout').value = settings.session_timeout_minutes || 15;
        document.getElementById('max-login-attempts').value = settings.max_login_attempts || 5;
        document.getElementById('lockout-duration').value = settings.lockout_duration_minutes || 30;

        // 注册设置
        document.getElementById('registration-enabled').checked = settings.registration_enabled || false;
    }

    // 切换设置面板
    function initCategoryTabs() {
        const tabs = document.querySelectorAll('.category-tab');
        const panels = document.querySelectorAll('.settings-panel');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const category = tab.dataset.category;

                // 更新标签状态
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                // 更新面板显示
                panels.forEach(panel => {
                    panel.classList.remove('active');
                    if (panel.id === `panel-${category}`) {
                        panel.classList.add('active');
                    }
                });
            });
        });
    }

    // 初始化通用设置表单
    function initGeneralSettingsForm() {
        const form = document.getElementById('general-settings-form');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const settings = {
                max_file_size: parseInt(document.getElementById('max-file-size').value),
                allowed_file_types: document.getElementById('allowed-file-types').value.split(',').map(s => s.trim())
            };

            await saveSettings(settings);
        });
    }

    // 初始化安全设置表单
    function initSecuritySettingsForm() {
        const form = document.getElementById('security-settings-form');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const settings = {
                session_timeout_minutes: parseInt(document.getElementById('session-timeout').value),
                max_login_attempts: parseInt(document.getElementById('max-login-attempts').value),
                lockout_duration_minutes: parseInt(document.getElementById('lockout-duration').value)
            };

            await saveSettings(settings);
        });
    }

    // 初始化注册设置表单
    function initRegistrationSettingsForm() {
        const form = document.getElementById('registration-settings-form');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const settings = {
                registration_enabled: document.getElementById('registration-enabled').checked
            };

            await saveSettings(settings);
        });
    }

    // 保存设置
    async function saveSettings(settings) {
        try {
            const response = await fetch('/api/admin/settings', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                showToast('设置已保存');
                // 重新加载设置
                await loadSettings();
            } else {
                const data = await response.json();
                showToast(data.detail || '保存失败', 'error');
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            showToast('网络错误', 'error');
        }
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
        loadSettings();
        initCategoryTabs();
        initGeneralSettingsForm();
        initSecuritySettingsForm();
        initRegistrationSettingsForm();
    }

    // DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
