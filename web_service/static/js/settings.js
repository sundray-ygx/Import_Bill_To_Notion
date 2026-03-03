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

        // 初始化邮箱配置（当切换到该部分时）
        const emailSection = document.querySelector('.sidebar-item[data-section="email"]');
        if (emailSection) {
            emailSection.addEventListener('click', () => {
                setTimeout(loadEmailConfigs, 100);
            });
        }

        // 添加邮箱配置按钮事件
        const addEmailBtn = document.getElementById('add-email-config-btn');
        if (addEmailBtn) {
            addEmailBtn.addEventListener('click', openEmailConfigModal);
        }
    }

    // ==================== 邮箱配置相关 ====================

    // 邮箱服务商模板
    const emailProviders = {
        qq: {
            name: 'QQ邮箱',
            imap_server: 'imap.qq.com',
            imap_port: 993,
            use_ssl: true,
            hint: 'QQ邮箱需要开启IMAP服务并使用授权码。请在QQ邮箱设置中生成授权码。'
        },
        '163': {
            name: '163邮箱',
            imap_server: 'imap.163.com',
            imap_port: 993,
            use_ssl: true,
            hint: '163邮箱需要开启IMAP服务并使用授权码。请在邮箱设置中开启IMAP并设置授权码。'
        },
        gmail: {
            name: 'Gmail',
            imap_server: 'imap.gmail.com',
            imap_port: 993,
            use_ssl: true,
            hint: 'Gmail需要使用应用专用密码。请前往Google账户设置生成应用专用密码。'
        },
        outlook: {
            name: 'Outlook',
            imap_server: 'outlook.office365.com',
            imap_port: 993,
            use_ssl: true,
            hint: 'Outlook/Hotmail邮箱，直接使用登录密码即可。'
        },
        custom: {
            name: '自定义',
            imap_server: '',
            imap_port: 993,
            use_ssl: true,
            hint: '请根据您的邮箱服务商填写IMAP服务器信息。'
        }
    };

    // 加载邮箱配置列表
    async function loadEmailConfigs() {
        try {
            const response = await window.Auth.apiRequest('/api/email/configs');
            if (response && response.ok) {
                const data = await response.json();
                displayEmailConfigs(data.configs || []);
            }
        } catch (error) {
            console.error('Failed to load email configs:', error);
            showToast('加载邮箱配置失败', 'error');
        }
    }

    // 显示邮箱配置列表
    function displayEmailConfigs(configs) {
        const listContainer = document.getElementById('email-configs-list');
        const emptyState = document.getElementById('no-email-configs');

        if (!listContainer) return;

        listContainer.innerHTML = '';

        if (configs.length === 0) {
            listContainer.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        listContainer.style.display = 'block';
        if (emptyState) emptyState.style.display = 'none';

        configs.forEach(config => {
            const card = createEmailConfigCard(config);
            listContainer.appendChild(card);
        });
    }

    // 创建邮箱配置卡片
    function createEmailConfigCard(config) {
        const card = document.createElement('div');
        card.className = 'email-config-card';
        card.dataset.configId = config.id;

        const statusClass = config.is_verified ? 'verified' : 'unverified';
        const statusText = config.is_verified ? '已验证' : '未验证';

        const lastCheckText = config.last_check_at ?
            new Date(config.last_check_at).toLocaleString('zh-CN') : '未检查';

        card.innerHTML = `
            <div class="email-config-header">
                <div class="email-config-info">
                    <h3 class="email-config-name">${escapeHtml(config.config_name)}</h3>
                    <div class="email-config-address">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                            <polyline points="22,6 12,13 2,6"/>
                        </svg>
                        ${escapeHtml(config.email_address)}
                    </div>
                </div>
                <div class="email-config-actions">
                    <span class="status-badge ${statusClass}">
                        <span class="status-dot"></span>
                        ${statusText}
                    </span>
                    <button class="btn btn-secondary btn-sm" onclick="testEmailConnection(${config.id})">测试</button>
                    <button class="btn btn-primary btn-sm" onclick="checkEmailBills(${config.id})">立即检查邮箱</button>
                    <button class="btn btn-secondary btn-sm" onclick="editEmailConfig(${config.id})">编辑</button>
                    <button class="btn btn-danger btn-sm" onclick="confirmDeleteEmailConfig(${config.id})">删除</button>
                </div>
            </div>
            <div class="email-config-details">
                <div class="email-config-detail">
                    <span class="email-config-detail-label">服务商</span>
                    <span class="email-config-detail-value">${config.provider || '自定义'}</span>
                </div>
                <div class="email-config-detail">
                    <span class="email-config-detail-label">IMAP服务器</span>
                    <span class="email-config-detail-value">${escapeHtml(config.imap_server)}</span>
                </div>
                <div class="email-config-detail">
                    <span class="email-config-detail-label">检查频率</span>
                    <span class="email-config-detail-value">${getFrequencyText(config.check_frequency)}</span>
                </div>
                <div class="email-config-detail">
                    <span class="email-config-detail-label">最后检查</span>
                    <span class="email-config-detail-value">${lastCheckText}</span>
                </div>
            </div>
        `;

        return card;
    }

    // 获取检查频率文本
    function getFrequencyText(frequency) {
        const map = {
            'hourly': '每小时',
            'daily': '每天',
            'weekly': '每周'
        };
        return map[frequency] || frequency;
    }

    // 打开邮箱配置模态框
    function openEmailConfigModal(configId = null, skipReset = false) {
        const modal = document.getElementById('email-config-modal');
        const title = document.getElementById('modal-title');
        const form = document.getElementById('email-config-form');

        if (!modal) return;

        // 只在添加新配置时重置表单
        if (!skipReset) {
            form.reset();
            document.getElementById('config-id').value = '';
            document.getElementById('selected-provider').value = '';

            // 清除服务商选择
            document.querySelectorAll('.provider-option').forEach(opt => {
                opt.classList.remove('selected');
            });

            // 隐藏提示
            const hint = document.getElementById('provider-hint');
            if (hint) hint.style.display = 'none';
        }

        if (configId) {
            title.textContent = '编辑邮箱配置';
        } else {
            title.textContent = '添加邮箱配置';
        }

        modal.classList.add('active');
    }

    // 关闭邮箱配置模态框
    function closeEmailConfigModal() {
        const modal = document.getElementById('email-config-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    // 选择服务商
    function selectProvider(provider) {
        document.querySelectorAll('.provider-option').forEach(opt => {
            opt.classList.remove('selected');
        });

        const selectedOption = document.querySelector(`.provider-option[data-provider="${provider}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }

        document.getElementById('selected-provider').value = provider;

        // 填充服务商信息
        const providerData = emailProviders[provider];
        if (providerData) {
            document.getElementById('imap-server').value = providerData.imap_server;
            document.getElementById('imap-port').value = providerData.imap_port;
            document.getElementById('use-ssl').checked = providerData.use_ssl;

            // 显示提示
            const hint = document.getElementById('provider-hint');
            if (hint && providerData.hint) {
                hint.textContent = providerData.hint;
                hint.style.display = 'block';
            }
        }
    }

    // 保存邮箱配置
    async function saveEmailConfig() {
        const form = document.getElementById('email-config-form');
        if (!form.checkValidity()) {
            showToast('请填写所有必填字段', 'error');
            return;
        }

        const configId = document.getElementById('config-id').value;
        const isEdit = !!configId;

        const configData = {
            email_address: document.getElementById('email-address').value,
            password: document.getElementById('email-password').value,
            imap_server: document.getElementById('imap-server').value,
            imap_port: parseInt(document.getElementById('imap-port').value),
            use_ssl: document.getElementById('use-ssl').checked,
            provider: document.getElementById('selected-provider').value || null,
            config_name: document.getElementById('config-name').value || '默认邮箱',
            check_frequency: document.getElementById('check-frequency').value
        };

        try {
            const url = isEdit ? `/api/email/config/${configId}` : '/api/email/config';
            const method = isEdit ? 'PUT' : 'POST';

            const response = await window.Auth.apiRequest(url, {
                method: method,
                body: JSON.stringify(configData)
            });

            if (response && response.ok) {
                showToast(isEdit ? '邮箱配置已更新' : '邮箱配置已添加', 'success');
                closeEmailConfigModal();
                loadEmailConfigs();
            } else {
                const error = await response.json();
                const errorMsg = error.detail || '保存失败';

                // 检查是否是密码加密相关的错误
                if (errorMsg.includes('PASSWORD_ENCRYPTION_KEY') || errorMsg.includes('密码加密')) {
                    showToast('服务器配置错误：缺少密码加密密钥', 'error');
                    console.error('Server configuration error:', errorMsg);

                    // 显示详细错误信息
                    setTimeout(() => {
                        alert('服务器配置错误\n\n请联系管理员配置以下环境变量：\n- PASSWORD_ENCRYPTION_KEY\n\n详细信息：\n' + errorMsg);
                    }, 500);
                } else {
                    showToast(errorMsg, 'error');
                }
            }
        } catch (error) {
            console.error('Failed to save email config:', error);
            showToast('保存邮箱配置失败', 'error');
        }
    }

    // 测试邮箱连接
    async function testEmailConnection(configId) {
        try {
            showToast('正在测试连接...', 'info');

            const response = await window.Auth.apiRequest(`/api/email/config/${configId}/verify`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                showToast('邮箱连接验证成功', 'success');
                loadEmailConfigs();
            } else {
                showToast(result.message || '验证失败', 'error');
            }
        } catch (error) {
            console.error('Failed to test connection:', error);
            showToast('测试连接失败', 'error');
        }
    }

    // 立即检查邮箱并导入账单
    async function checkEmailBills(configId) {
        try {
            showToast('正在检查邮箱账单...', 'info');

            const response = await window.Auth.apiRequest('/api/email/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ config_id: configId })
            });

            const result = await response.json();

            if (result.success) {
                showToast(result.message || '邮箱检查完成', 'success');

                // 显示详细结果
                if (result.total_imported > 0) {
                    showToast(`成功导入 ${result.total_imported} 条账单记录`, 'success');
                }

                if (result.total_failed > 0) {
                    showToast(`${result.total_failed} 条记录导入失败`, 'warning');
                }

                // 刷新配置列表以更新"最后检查"时间
                loadEmailConfigs();
            } else {
                showToast(result.message || '检查失败', 'error');
            }
        } catch (error) {
            console.error('Failed to check email:', error);
            showToast('检查邮箱失败：' + (error.message || '未知错误'), 'error');
        }
    }

    // 编辑邮箱配置
    async function editEmailConfig(configId) {
        try {
            // 先打开模态框（不重置表单）
            openEmailConfigModal(configId, true);

            // 然后加载配置数据
            const response = await window.Auth.apiRequest(`/api/email/config/${configId}`);
            if (response && response.ok) {
                const config = await response.json();

                // 调试日志：检查返回的数据
                console.log('编辑邮箱配置 - API 返回数据:', config);
                console.log('关键字段检查:', {
                    email_address: config.email_address,
                    imap_server: config.imap_server,
                    imap_port: config.imap_port,
                    use_ssl: config.use_ssl,
                    provider: config.provider,
                    config_name: config.config_name,
                    check_frequency: config.check_frequency
                });

                // 验证必需字段
                if (!config.email_address || !config.imap_server) {
                    console.error('API 返回的数据缺少必需字段:', config);
                    showToast('配置数据不完整，请刷新页面重试', 'error');
                    closeEmailConfigModal();
                    return;
                }

                // 填充表单
                const configIdField = document.getElementById('config-id');
                const emailField = document.getElementById('email-address');
                const serverField = document.getElementById('imap-server');
                const portField = document.getElementById('imap-port');
                const sslField = document.getElementById('use-ssl');
                const nameField = document.getElementById('config-name');
                const freqField = document.getElementById('check-frequency');

                if (!configIdField || !emailField || !serverField || !portField ||
                    !sslField || !nameField || !freqField) {
                    console.error('表单字段未找到，可能模态框未正确初始化');
                    showToast('表单初始化失败，请刷新页面', 'error');
                    closeEmailConfigModal();
                    return;
                }

                configIdField.value = config.id;
                emailField.value = config.email_address;
                serverField.value = config.imap_server;
                portField.value = config.imap_port;
                sslField.checked = config.use_ssl;
                nameField.value = config.config_name || '';
                freqField.value = config.check_frequency || 'hourly';

                console.log('表单填充完成:', {
                    configId: configIdField.value,
                    email: emailField.value,
                    server: serverField.value,
                    port: portField.value,
                    ssl: sslField.checked,
                    name: nameField.value,
                    frequency: freqField.value
                });

                // 选择服务商
                if (config.provider) {
                    selectProvider(config.provider);
                }
            } else {
                showToast('加载配置失败', 'error');
                closeEmailConfigModal();
            }
        } catch (error) {
            console.error('Failed to load email config:', error);
            showToast('加载配置失败', 'error');
            closeEmailConfigModal();
        }
    }

    // 确认删除邮箱配置
    function confirmDeleteEmailConfig(configId) {
        const modal = document.getElementById('delete-confirm-modal');
        const confirmBtn = document.getElementById('confirm-delete-btn');

        if (modal && confirmBtn) {
            confirmBtn.onclick = () => deleteEmailConfig(configId);
            modal.classList.add('active');
        }
    }

    // 关闭删除确认模态框
    function closeDeleteModal() {
        const modal = document.getElementById('delete-confirm-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    // 删除邮箱配置
    async function deleteEmailConfig(configId) {
        try {
            const response = await window.Auth.apiRequest(`/api/email/config/${configId}`, {
                method: 'DELETE'
            });

            if (response && response.ok) {
                const result = await response.json();
                showToast(result.message || '邮箱配置已删除', 'success');
                closeDeleteModal();
                loadEmailConfigs();
            } else {
                const error = await response.json();
                showToast(error.detail || '删除失败', 'error');
            }
        } catch (error) {
            console.error('Failed to delete email config:', error);
            showToast('删除邮箱配置失败', 'error');
        }
    }

    // HTML 转义
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 将函数暴露到全局作用域
    window.openEmailConfigModal = openEmailConfigModal;
    window.closeEmailConfigModal = closeEmailConfigModal;
    window.selectProvider = selectProvider;
    window.saveEmailConfig = saveEmailConfig;
    window.testEmailConnection = testEmailConnection;
    window.editEmailConfig = editEmailConfig;
    window.confirmDeleteEmailConfig = confirmDeleteEmailConfig;
    window.closeDeleteModal = closeDeleteModal;

    // DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
