/**
 * 系统设置向导逻辑
 * 包含管理员创建和Notion配置
 */

(function() {
    'use strict';

    // 当前步骤
    let currentStep = 1;
    // 总步骤数
    const totalSteps = 4;
    // 管理员信息
    let adminInfo = null;
    // Notion配置信息
    let notionConfigured = false;

    // ==================== 工具函数 ====================

    function showToast(message, type) {
        type = type || 'success';
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast ' + type;

        const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
        toast.innerHTML = '<div class="toast-content"><span class="toast-icon">' + icon + '</span><span class="toast-message">' + message + '</span></div>';
        container.appendChild(toast);

        setTimeout(function() { toast.remove(); }, 3000);
    }

    function showAlert(message, type) {
        type = type || 'info';
        const container = document.getElementById('alert-container') || document.getElementById('alert-container-2');
        if (!container) return;

        container.innerHTML = '<div class="alert alert-' + type + '">' + message + '</div>';
        setTimeout(function() { container.innerHTML = ''; }, 5000);
    }

    function goToStep(step) {
        // 隐藏所有步骤
        document.querySelectorAll('.setup-step').forEach(function(s) { s.classList.remove('active'); });
        // 显示目标步骤
        const targetStep = document.getElementById('step-' + step);
        if (targetStep) {
            targetStep.classList.add('active');
        }

        // 更新进度指示器
        document.querySelectorAll('.progress-step').forEach(function(s) { s.classList.remove('active'); });
        for (let i = 1; i <= totalSteps; i++) {
            const stepEl = document.querySelector('.progress-step[data-step="' + i + '"]');
            if (stepEl) {
                if (i <= step) stepEl.classList.add('active');
            }
        }

        currentStep = step;
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

        if (score <= 2) return { score: score, level: 'weak', text: '弱' };
        if (score <= 4) return { score: score, level: 'medium', text: '中等' };
        return { score: score, level: 'strong', text: '强' };
    }

    function updateStrengthIndicator(strength) {
        const fill = document.getElementById('strength-fill');
        const text = document.getElementById('strength-text');
        const indicator = document.getElementById('password-strength-indicator');

        if (!fill || !text) return;

        if (indicator) indicator.style.display = 'block';

        fill.className = 'strength-fill';
        text.textContent = '密码强度：' + strength.text;

        if (strength.score > 0) {
            fill.classList.add(strength.level);
        }
    }

    // ==================== 管理员创建逻辑 ====================

    function initAdminForm() {
        const form = document.getElementById('admin-setup-form');
        if (!form) return;

        // 密码切换
        const toggleBtn = document.getElementById('toggle-admin-password');
        const passwordInput = document.getElementById('admin-password');
        if (toggleBtn && passwordInput) {
            toggleBtn.addEventListener('click', function() {
                const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
            });
        }

        // 密码强度检测
        if (passwordInput) {
            passwordInput.addEventListener('input', function() {
                const strength = checkPasswordStrength(passwordInput.value);
                updateStrengthIndicator(strength);
            });
        }

        // 表单提交 - 已废弃，请使用注册流程
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            // 引导用户使用注册页面
            showAlert('请使用注册页面创建账户。首个注册用户将自动成为超级管理员。', 'info');

            setTimeout(function() {
                window.location.href = '/register';
            }, 2000);
        });
    }

    // ==================== Notion配置逻辑 ====================

    function initNotionForm() {
        const form = document.getElementById('notion-setup-form');
        if (!form) return;

        // API密钥切换
        const toggleBtn = document.getElementById('toggle-api-key');
        const apiKeyInput = document.getElementById('notion-api-key');
        if (toggleBtn && apiKeyInput) {
            toggleBtn.addEventListener('click', function() {
                const type = apiKeyInput.getAttribute('type') === 'password' ? 'text' : 'password';
                apiKeyInput.setAttribute('type', type);
            });
        }

        // 表单提交
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const payload = {
                config_name: document.getElementById('config-name').value,
                notion_api_key: document.getElementById('notion-api-key').value,
                notion_income_database_id: document.getElementById('income-db-id').value,
                notion_expense_database_id: document.getElementById('expense-db-id').value
            };

            const btn = document.getElementById('verify-config-btn');
            btn.disabled = true;
            btn.textContent = '保存中...';

            try {
                const response = await fetch('/api/user/notion-config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('access_token')
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    notionConfigured = true;
                    showToast('配置保存成功！');
                    updateSummary();
                    goToStep(4);
                } else {
                    const data = await response.json();
                    showAlert(data.detail || '配置保存失败', 'error');
                }
            } catch (err) {
                console.error('Config save error:', err);
                showAlert('网络错误，请重试', 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = '验证并保存';
            }
        });
    }

    // ==================== 完成页面逻辑 ====================

    function updateSummary() {
        if (adminInfo) {
            document.getElementById('summary-username').textContent = adminInfo.username;
        }
        document.getElementById('summary-notion').textContent = notionConfigured ? '已配置' : '稍后配置';
    }

    // ==================== 初始化 ====================

    function bindEvents() {
        // 步骤1 -> 步骤2
        const startBtn = document.getElementById('start-setup-btn');
        if (startBtn) {
            startBtn.addEventListener('click', function() { goToStep(2); });
        }

        // 步骤2 -> 步骤1
        const back1Btn = document.getElementById('back-step-1');
        if (back1Btn) {
            back1Btn.addEventListener('click', function() { goToStep(1); });
        }

        // 步骤3 -> 步骤2
        const back2Btn = document.getElementById('back-step-2');
        if (back2Btn) {
            back2Btn.addEventListener('click', function() { goToStep(2); });
        }

        // 跳过Notion配置
        const skipBtn = document.getElementById('skip-step-3');
        if (skipBtn) {
            skipBtn.addEventListener('click', function() {
                notionConfigured = false;
                updateSummary();
                goToStep(4);
            });
        }

        // 完成设置
        const goDashboardBtn = document.getElementById('go-to-dashboard-btn');
        if (goDashboardBtn) {
            goDashboardBtn.addEventListener('click', function() {
                window.location.href = '/bill-management';
            });
        }
    }

    async function checkSetupStatus() {
        try {
            const response = await fetch('/api/auth/setup/check');
            if (response.ok) {
                const data = await response.json();
                // 检查用户是否已登录
                const hasToken = localStorage.getItem('access_token');

                // 如果用户已登录，直接跳转到第3步
                if (hasToken && data.setup_type !== 'first_user') {
                    goToStep(3);
                } else if (data.setup_type === 'promote_available') {
                    // 有用户但没有超级管理员，跳过管理员创建步骤
                    goToStep(3);
                }
                // 否则显示欢迎页（第1步）
                return true;
            }
        } catch (err) {
            console.error('Check setup status error:', err);
        }
        return true;
    }

    async function init() {
        // 检查设置状态
        const shouldContinue = await checkSetupStatus();
        if (!shouldContinue) return;

        // 绑定事件
        bindEvents();

        // 初始化表单
        initAdminForm();
        initNotionForm();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
