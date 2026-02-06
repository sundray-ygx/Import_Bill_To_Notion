/**
 * 设置页面逻辑
 */

(function() {
    'use strict';

    // 当前激活的部分
    let currentSection = 'profile';

    // 显示 Toast 消息
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        container.appendChild(toast);

        // 3秒后自动消失
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // 切换部分
    function switchSection(sectionId) {
        // 隐藏所有部分
        document.querySelectorAll('.settings-section').forEach(section => {
            section.style.display = 'none';
        });

        // 显示选中的部分
        const targetSection = document.getElementById(`${sectionId}-section`);
        if (targetSection) {
            targetSection.style.display = 'block';
        }

        // 更新侧边栏高亮
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.classList.remove('active');
        });
        const activeItem = document.querySelector(`.sidebar-item[data-section="${sectionId}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }

        currentSection = sectionId;
    }

    // 加载用户资料
    async function loadUserProfile() {
        try {
            const response = await window.Auth.apiRequest('/api/user/profile');
            if (response && response.ok) {
                const profile = await response.json();

                // 更新显示
                document.getElementById('profile-username').textContent = profile.username;
                document.getElementById('profile-email').textContent = profile.email;
                document.getElementById('profile-username-input').value = profile.username;
                document.getElementById('profile-email-input').value = profile.email;

                // 更新统计
                document.getElementById('stat-uploads').textContent = profile.total_uploads || 0;
                document.getElementById('stat-records').textContent = profile.total_imports || 0;

                // 计算注册时长
                if (profile.created_at) {
                    const createdDate = new Date(profile.created_at);
                    const now = new Date();
                    const days = Math.floor((now - createdDate) / (1000 * 60 * 60 * 24));
                    document.getElementById('stat-days').textContent = `${days}天`;
                }
            }
        } catch (error) {
            console.error('Failed to load profile:', error);
            showToast('加载用户资料失败', 'error');
        }
    }

    // 初始化个人资料表单
    function initProfileForm() {
        const form = document.getElementById('profile-form');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('profile-email-input').value;

            try {
                const response = await window.Auth.apiRequest('/api/user/profile', {
                    method: 'PUT',
                    body: JSON.stringify({ email })
                });

                if (response && response.ok) {
                    showToast('资料已更新');
                    await loadUserProfile(); // 重新加载
                } else {
                    const data = await response.json();
                    showToast(data.detail || '更新失败', 'error');
                }
            } catch (error) {
                console.error('Update error:', error);
                showToast('网络错误，请稍后重试', 'error');
            }
        });
    }

    // 初始化密码表单
    function initPasswordForm() {
        const form = document.getElementById('password-form');
        const passwordInput = document.getElementById('new-password');
        const toggleBtn = document.getElementById('toggle-new-password');

        if (!form) return;

        // 密码切换
        if (toggleBtn && passwordInput) {
            toggleBtn.addEventListener('click', () => {
                const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
            });
        }

        // 密码强度检测
        if (passwordInput) {
            passwordInput.addEventListener('input', () => {
                const password = passwordInput.value;
                const strength = checkPasswordStrength(password);
                updateStrengthIndicator(strength);
            });
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-new-password').value;

            if (newPassword !== confirmPassword) {
                showToast('两次输入的密码不一致', 'error');
                return;
            }

            try {
                const response = await window.Auth.apiRequest('/api/auth/change-password', {
                    method: 'POST',
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword
                    })
                });

                if (response && response.ok) {
                    showToast('密码已修改，请重新登录');
                    setTimeout(() => {
                        window.Auth.logout();
                    }, 1500);
                } else {
                    const data = await response.json();
                    showToast(data.detail || '修改失败', 'error');
                }
            } catch (error) {
                console.error('Password change error:', error);
                showToast('网络错误，请稍后重试', 'error');
            }
        });
    }

    // 检查密码强度
    function checkPasswordStrength(password) {
        if (!password) return { score: 0, level: 'weak', text: '未输入' };

        let score = 0;
        if (password.length >= 8) score++;
        if (password.length >= 12) score++;
        if (/[a-z]/.test(password)) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/[0-9]/.test(password)) score++;
        if (/[^a-zA-Z0-9]/.test(password)) score++;

        if (score <= 2) return { score, level: 'weak', text: '弱' };
        if (score <= 4) return { score, level: 'medium', text: '中等' };
        return { score, level: 'strong', text: '强' };
    }

    // 更新强度指示器
    function updateStrengthIndicator(strength) {
        const fill = document.getElementById('password-strength-fill');
        const text = document.getElementById('password-strength-text');

        if (!fill || !text) return;

        fill.className = 'strength-fill';
        text.textContent = `密码强度：${strength.text}`;

        if (strength.score > 0) {
            fill.classList.add(strength.level);
        }
    }

    // 初始化复盘配置
    async function initReviewConfig() {
        // 加载复盘配置
        try {
            const response = await window.Auth.apiRequest('/api/review/config');
            if (response && response.ok) {
                const config = await response.json();

                // 填充表单
                document.getElementById('monthly-review-db').value = config.monthly_review_db || '';
                document.getElementById('monthly-template-id').value = config.monthly_template_id || '';
                document.getElementById('quarterly-review-db').value = config.quarterly_review_db || '';
                document.getElementById('quarterly-template-id').value = config.quarterly_template_id || '';
                document.getElementById('yearly-review-db').value = config.yearly_review_db || '';
                document.getElementById('yearly-template-id').value = config.yearly_template_id || '';
            }
        } catch (error) {
            console.error('Failed to load review config:', error);
        }

        // 表单提交
        const form = document.getElementById('review-config-form');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const configData = {
                notion_monthly_review_db: document.getElementById('monthly-review-db').value,
                notion_monthly_template_id: document.getElementById('monthly-template-id').value,
                notion_quarterly_review_db: document.getElementById('quarterly-review-db').value,
                notion_quarterly_template_id: document.getElementById('quarterly-template-id').value,
                notion_yearly_review_db: document.getElementById('yearly-review-db').value,
                notion_yearly_template_id: document.getElementById('yearly-template-id').value
            };

            try {
                const response = await window.Auth.apiRequest('/api/review/config', {
                    method: 'POST',
                    body: JSON.stringify(configData)
                });

                if (response && response.ok) {
                    const data = await response.json();
                    // 显示后端返回的消息（包含单用户模式提示）
                    showToast(data.message || '复盘配置已保存');
                } else {
                    const data = await response.json();
                    showToast(data.detail || '保存失败', 'error');
                }
            } catch (error) {
                console.error('Review config save error:', error);
                showToast('网络错误，请稍后重试', 'error');
            }
        });

        // 重新加载按钮
        const reloadBtn = document.getElementById('load-review-config-btn');
        if (reloadBtn) {
            reloadBtn.addEventListener('click', async () => {
                reloadBtn.disabled = true;
                reloadBtn.textContent = '加载中...';
                try {
                    const response = await window.Auth.apiRequest('/api/review/config');
                    if (response && response.ok) {
                        const config = await response.json();
                        document.getElementById('monthly-review-db').value = config.monthly_review_db || '';
                        document.getElementById('monthly-template-id').value = config.monthly_template_id || '';
                        document.getElementById('quarterly-review-db').value = config.quarterly_review_db || '';
                        document.getElementById('quarterly-template-id').value = config.quarterly_template_id || '';
                        document.getElementById('yearly-review-db').value = config.yearly_review_db || '';
                        document.getElementById('yearly-template-id').value = config.yearly_template_id || '';
                        showToast('配置已重新加载');
                    }
                } catch (error) {
                    console.error('Failed to reload review config:', error);
                    showToast('加载失败', 'error');
                } finally {
                    reloadBtn.disabled = false;
                    reloadBtn.textContent = '🔄 重新加载';
                }
            });
        }
    }

    // 初始化Notion配置
    // 存储当前配置状态，用于判断是否需要更新API密钥
    let currentConfig = {
        is_configured: false,
        is_verified: false,
        has_api_key: false
    };

    async function initNotionConfig() {
        // 加载现有配置
        try {
            const response = await window.Auth.apiRequest('/api/user/notion-config');
            if (response && response.ok) {
                const config = await response.json();

                // 更新当前配置状态
                currentConfig = {
                    is_configured: config.is_configured,
                    is_verified: config.is_verified,
                    has_api_key: !!config.notion_api_key
                };

                // 填充表单（除了API密钥）
                document.getElementById('config-name').value = config.config_name || '默认配置';
                document.getElementById('income-db-id').value = config.notion_income_database_id || '';
                document.getElementById('expense-db-id').value = config.notion_expense_database_id || '';

                // API密钥输入框特殊处理
                const apiKeyInput = document.getElementById('notion-api-key');
                if (apiKeyInput) {
                    if (config.is_configured && config.notion_api_key) {
                        // 如果已有配置，显示占位符而不是脱敏的值
                        apiKeyInput.value = '';
                        apiKeyInput.placeholder = '已配置密钥（留空则保持不变）';
                    } else {
                        apiKeyInput.placeholder = '请输入Notion API密钥';
                    }
                }

                // 更新状态显示
                updateConfigStatus(config.is_configured, config.is_verified);
            }
        } catch (error) {
            // 可能还没有配置
            updateConfigStatus(false);
        }

        // 表单提交
        const form = document.getElementById('notion-config-form');
        if (!form) return;

        // API Key 切换
        const toggleBtn = document.getElementById('toggle-api-key');
        const apiKeyInput = document.getElementById('notion-api-key');
        if (toggleBtn && apiKeyInput) {
            toggleBtn.addEventListener('click', () => {
                const type = apiKeyInput.getAttribute('type') === 'password' ? 'text' : 'password';
                apiKeyInput.setAttribute('type', type);
            });
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const apiKeyValue = document.getElementById('notion-api-key').value.trim();
            const configData = {
                notion_income_database_id: document.getElementById('income-db-id').value,
                notion_expense_database_id: document.getElementById('expense-db-id').value,
                config_name: document.getElementById('config-name').value
            };

            // 只有当用户输入了新的API密钥时才包含在请求中
            // 如果留空且已有配置，后端会保留原有的密钥
            if (apiKeyValue) {
                configData.notion_api_key = apiKeyValue;
            }

            try {
                const response = await window.Auth.apiRequest('/api/user/notion-config', {
                    method: 'POST',
                    body: JSON.stringify(configData)
                });

                if (response && response.ok) {
                    showToast('配置已保存');
                    // 重新加载配置以更新状态
                    await initNotionConfig();
                } else {
                    const data = await response.json();
                    showToast(data.detail || '保存失败', 'error');
                }
            } catch (error) {
                console.error('Config save error:', error);
                showToast('网络错误，请稍后重试', 'error');
            }
        });

        // 验证配置
        const verifyBtn = document.getElementById('verify-config-btn');
        if (verifyBtn) {
            verifyBtn.addEventListener('click', async () => {
                try {
                    verifyBtn.disabled = true;
                    verifyBtn.textContent = '验证中...';

                    const response = await window.Auth.apiRequest('/api/user/notion-config/verify', {
                        method: 'POST'
                    });

                    const data = await response.json();

                    if (data.success) {
                        showToast('配置验证成功');
                        currentConfig.is_verified = true;
                        updateConfigStatus(true, true);
                    } else {
                        showToast(data.message || '配置验证失败', 'error');
                        updateConfigStatus(currentConfig.is_configured, false);
                    }
                } catch (error) {
                    console.error('Config verify error:', error);
                    showToast('网络错误，请稍后重试', 'error');
                } finally {
                    verifyBtn.disabled = false;
                    verifyBtn.textContent = '✓ 验证配置';
                }
            });
        }
    }

    // 更新配置状态显示
    function updateConfigStatus(hasConfig, isVerified = false) {
        const icon = document.getElementById('config-status-icon');
        const title = document.getElementById('config-status-title');
        const desc = document.getElementById('config-status-desc');

        if (!hasConfig) {
            if (icon) icon.textContent = '❓';
            if (title) title.textContent = '未配置';
            if (desc) desc.textContent = '您还没有配置Notion集成';
        } else if (isVerified) {
            if (icon) {
                icon.textContent = '✅';
                icon.className = 'config-status-icon verified';
            }
            if (title) title.textContent = '已验证';
            if (desc) desc.textContent = '您的Notion配置已验证通过';
        } else {
            if (icon) {
                icon.textContent = '⚠️';
                icon.className = 'config-status-icon unverified';
            }
            if (title) title.textContent = '未验证';
            if (desc) desc.textContent = '配置已保存，请验证配置';
        }
    }

    // 侧边栏导航
    function initSidebarNav() {
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.getAttribute('data-section');
                if (section) {
                    switchSection(section);
                }
            });
        });
    }

    // 初始化会话超时表单
    function initSessionTimeoutForm() {
        const form = document.getElementById('session-timeout-form');
        const timeoutInput = document.getElementById('session-timeout');
        const presetButtons = document.querySelectorAll('.timeout-preset-btn');

        if (!form || !timeoutInput) return;

        // 加载当前设置
        loadSessionTimeout();

        // 预设按钮点击事件
        presetButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const timeout = parseInt(btn.dataset.timeout);
                timeoutInput.value = timeout;

                // 更新按钮激活状态
                presetButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // 输入框变化时更新按钮状态
        timeoutInput.addEventListener('input', () => {
            presetButtons.forEach(btn => {
                btn.classList.remove('active');
                if (parseInt(btn.dataset.timeout) === parseInt(timeoutInput.value)) {
                    btn.classList.add('active');
                }
            });
        });

        // 表单提交
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const timeoutMinutes = parseInt(timeoutInput.value);

            // 验证
            if (timeoutMinutes < 5 || timeoutMinutes > 1440) {
                showToast('超时时间必须在 5-1440 分钟之间', 'error');
                return;
            }

            try {
                const response = await window.Auth.apiRequest('/api/user/profile', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_timeout_minutes: timeoutMinutes
                    })
                });

                if (response && response.ok) {
                    showToast('会话超时设置已保存，下次登录生效');
                } else {
                    showToast('保存失败', 'error');
                }
            } catch (error) {
                console.error('Session timeout update error:', error);
                showToast('保存失败', 'error');
            }
        });
    }

    // 加载会话超时设置
    async function loadSessionTimeout() {
        try {
            const response = await window.Auth.apiRequest('/api/user/profile');
            if (response && response.ok) {
                const profile = await response.json();
                const timeoutInput = document.getElementById('session-timeout');
                const presetButtons = document.querySelectorAll('.timeout-preset-btn');

                if (timeoutInput && profile.session_timeout_minutes !== undefined) {
                    timeoutInput.value = profile.session_timeout_minutes;

                    // 更新预设按钮状态
                    presetButtons.forEach(btn => {
                        btn.classList.remove('active');
                        if (parseInt(btn.dataset.timeout) === profile.session_timeout_minutes) {
                            btn.classList.add('active');
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load session timeout:', error);
        }
    }

    // 撤销所有会话
    function initRevokeSessions() {
        const btn = document.getElementById('revoke-all-sessions-btn');
        if (!btn) return;

        btn.addEventListener('click', async () => {
            if (!confirm('确定要撤销所有其他会话吗？这会使其他设备上的登录失效。')) {
                return;
            }

            try {
                btn.disabled = true;
                const response = await window.Auth.apiRequest('/api/auth/logout', {
                    method: 'POST',
                    body: JSON.stringify({ refresh_token: window.Auth.getRefreshToken() })
                });

                if (response) {
                    showToast('所有会话已撤销，请重新登录');
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 1500);
                }
            } catch (error) {
                console.error('Revoke sessions error:', error);
                showToast('操作失败', 'error');
            } finally {
                btn.disabled = false;
            }
        });
    }

    // 初始化注销账户功能
    function initDeleteAccount() {
        const deleteAccountBtn = document.getElementById('delete-account-btn');
        if (!deleteAccountBtn) return;

        deleteAccountBtn.addEventListener('click', async () => {
            // 二次确认
            if (!confirm('确定要注销您的账户吗？此操作不可撤销！')) {
                return;
            }

            // 显示警告
            if (!confirm('警告：注销账户将永久删除您的所有数据，包括：\n\n' +
                '• 上传的账单文件\n' +
                '• 导入历史记录\n' +
                '• Notion配置信息\n' +
                '• 个人资料和设置\n\n' +
                '此操作无法恢复，是否继续？')) {
                return;
            }

            // 要求输入密码确认
            const password = prompt('请输入当前密码以确认注销：');
            if (!password) {
                showToast('已取消注销', 'info');
                return;
            }

            if (!password || password.length < 1) {
                showToast('请输入密码', 'error');
                return;
            }

            deleteAccountBtn.disabled = true;
            deleteAccountBtn.textContent = '处理中...';

            try {
                const response = await window.Auth.apiRequest('/api/user/delete-account', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ password: password })
                });

                if (response && response.ok) {
                    showToast('账户已注销，即将跳转到首页...');
                    // 清除本地存储
                    localStorage.clear();
                    sessionStorage.clear();
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                } else {
                    const data = await response.json();
                    showToast(data.detail || '注销失败：' + (data.detail || '未知错误'), 'error');
                }
            } catch (error) {
                console.error('Delete account error:', error);
                showToast('操作失败，请检查网络连接', 'error');
            } finally {
                deleteAccountBtn.disabled = false;
                deleteAccountBtn.textContent = '注销账户';
            }
        });
    }

    // 页面初始化
    function init() {
        // 检查登录状态
        if (!window.Auth.isLoggedIn()) {
            window.location.href = '/login';
            return;
        }

        // 初始化各个部分
        initSidebarNav();
        initProfileForm();
        initPasswordForm();
        initSessionTimeoutForm();
        initRevokeSessions();
        initDeleteAccount();

        // 加载用户资料
        loadUserProfile();

        // 初始化Notion配置（当切换到该部分时）
        const notionSection = document.querySelector('.sidebar-item[data-section="notion"]');
        if (notionSection) {
            notionSection.addEventListener('click', () => {
                setTimeout(initNotionConfig, 100);
            });
        }

        // 初始化复盘配置（当切换到该部分时）
        const reviewSection = document.querySelector('.sidebar-item[data-section="review"]');
        if (reviewSection) {
            reviewSection.addEventListener('click', () => {
                setTimeout(initReviewConfig, 100);
            });
        }
    }

    // DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
