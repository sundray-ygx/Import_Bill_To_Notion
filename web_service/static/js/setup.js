/**
 * 配置向导逻辑
 */

(function() {
    'use strict';

    // 当前步骤
    let currentStep = 1;
    const totalSteps = 4;

    // 管理员信息
    let adminInfo = {
        username: '',
        email: '',
        password: ''
    };

    // 系统设置
    let systemSettings = {
        allow_registration: true,
        session_timeout: 15,
        max_login_attempts: 5
    };

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
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // 切换步骤
    function goToStep(step) {
        // 隐藏当前步骤
        document.querySelectorAll('.setup-step').forEach(s => s.classList.remove('active'));
        document.querySelectorAll('.progress-step').forEach(s => s.classList.remove('active'));

        // 显示新步骤
        const stepElement = document.querySelector(`.setup-step[data-step="${step}"]`);
        if (stepElement) {
            stepElement.classList.add('active');
        }

        const progressStep = document.querySelector(`.progress-step[data-step="${step}"]`);
        if (progressStep) {
            progressStep.classList.add('active');
        }

        // 标记之前的步骤为完成
        for (let i = 1; i < step; i++) {
            const completedStep = document.querySelector(`.progress-step[data-step="${i}"]`);
            if (completedStep) {
                completedStep.classList.add('completed');
            }
        }

        // 更新进度条
        const progress = ((step - 1) / (totalSteps - 1)) * 100;
        document.getElementById('progress-fill').style.width = `${progress}%`;

        currentStep = step;
    }

    // 验证用户名
    function validateUsername(username) {
        if (!username) return { valid: false, message: '请输入用户名' };
        if (username.length < 3) return { valid: false, message: '用户名至少需要3个字符' };
        if (username.length > 50) return { valid: false, message: '用户名不能超过50个字符' };
        if (!/^[a-zA-Z0-9_]+$/.test(username)) {
            return { valid: false, message: '用户名只能包含字母、数字和下划线' };
        }
        return { valid: true };
    }

    // 验证邮箱
    function validateEmail(email) {
        if (!email) return { valid: false, message: '请输入邮箱地址' };
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) return { valid: false, message: '请输入有效的邮箱地址' };
        return { valid: true };
    }

    // 验证密码
    function validatePassword(password) {
        if (!password) return { valid: false, message: '请输入密码' };
        if (password.length < 8) return { valid: false, message: '密码至少需要8个字符' };
        if (!/[a-z]/.test(password)) return { valid: false, message: '密码必须包含至少一个小写字母' };
        if (!/[A-Z]/.test(password)) return { valid: false, message: '密码必须包含至少一个大写字母' };
        if (!/[0-9]/.test(password)) return { valid: false, message: '密码必须包含至少一个数字' };
        return { valid: true };
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

    // 更新密码强度指示器
    function updateStrengthIndicator(strength) {
        const fill = document.getElementById('strength-fill');
        const text = document.getElementById('strength-text');

        if (!fill || !text) return;

        fill.className = 'strength-fill';
        text.textContent = `密码强度：${strength.text}`;

        if (strength.score > 0) {
            fill.classList.add(strength.level);
        }
    }

    // 初始化第一步（欢迎）
    function initStep1() {
        const startBtn = document.getElementById('start-setup-btn');
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                goToStep(2);
            });
        }
    }

    // 初始化第二步（管理员账户）
    function initStep2() {
        const usernameInput = document.getElementById('admin-username');
        const emailInput = document.getElementById('admin-email');
        const passwordInput = document.getElementById('admin-password');
        const confirmPasswordInput = document.getElementById('admin-confirm-password');
        const toggleBtn = document.getElementById('toggle-admin-password');
        const form = document.getElementById('admin-form');

        // 密码显示切换
        if (toggleBtn && passwordInput) {
            toggleBtn.addEventListener('click', () => {
                const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
            });
        }

        // 密码强度检测
        if (passwordInput) {
            passwordInput.addEventListener('input', () => {
                const strength = checkPasswordStrength(passwordInput.value);
                updateStrengthIndicator(strength);
            });
        }

        // 返回按钮
        const backBtn = document.getElementById('back-to-welcome-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                goToStep(1);
            });
        }

        // 表单提交
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                // 验证表单
                const username = usernameInput.value.trim();
                const email = emailInput.value.trim();
                const password = passwordInput.value;
                const confirmPassword = confirmPasswordInput.value;

                // 验证用户名
                const usernameResult = validateUsername(username);
                if (!usernameResult.valid) {
                    showToast(usernameResult.message, 'error');
                    return;
                }

                // 验证邮箱
                const emailResult = validateEmail(email);
                if (!emailResult.valid) {
                    showToast(emailResult.message, 'error');
                    return;
                }

                // 验证密码
                const passwordResult = validatePassword(password);
                if (!passwordResult.valid) {
                    showToast(passwordResult.message, 'error');
                    return;
                }

                // 验证确认密码
                if (password !== confirmPassword) {
                    showToast('两次输入的密码不一致', 'error');
                    return;
                }

                // 保存管理员信息
                adminInfo = { username, email, password };

                // 检查用户名是否已存在
                try {
                    const checkResponse = await fetch('/api/auth/check-username', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username })
                    });

                    if (checkResponse.ok) {
                        const data = await checkResponse.json();
                        if (data.exists) {
                            showToast('用户名已存在，请选择其他用户名', 'error');
                            return;
                        }
                    }
                } catch (error) {
                    console.error('Username check error:', error);
                }

                // 进入下一步
                goToStep(3);
            });
        }
    }

    // 初始化第三步（系统设置）
    function initStep3() {
        const allowRegCheckbox = document.getElementById('allow-registration');
        const sessionTimeoutInput = document.getElementById('session-timeout');
        const maxAttemptsInput = document.getElementById('max-login-attempts');
        const form = document.getElementById('settings-form');

        // 返回按钮
        const backBtn = document.getElementById('back-to-admin-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                goToStep(2);
            });
        }

        // 表单提交
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                // 收集设置
                systemSettings = {
                    allow_registration: allowRegCheckbox.checked,
                    session_timeout: parseInt(sessionTimeoutInput.value) || 15,
                    max_login_attempts: parseInt(maxAttemptsInput.value) || 5
                };

                // 创建管理员账户
                try {
                    showToast('正在创建管理员账户...');

                    const createResponse = await fetch('/api/setup/create-admin', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            username: adminInfo.username,
                            email: adminInfo.email,
                            password: adminInfo.password,
                            settings: systemSettings
                        })
                    });

                    if (createResponse.ok) {
                        showToast('管理员账户创建成功');
                        // 显示完成页面
                        document.getElementById('setup-admin-username').textContent = adminInfo.username;
                        goToStep(4);
                    } else {
                        const data = await createResponse.json();
                        showToast(data.detail || '创建失败，请重试', 'error');
                    }
                } catch (error) {
                    console.error('Create admin error:', error);
                    showToast('网络错误，请检查连接', 'error');
                }
            });
        }
    }

    // 初始化第四步（完成）
    function initStep4() {
        const loginBtn = document.getElementById('go-to-login-btn');
        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                window.location.href = '/login';
            });
        }
    }

    // 页面初始化
    function init() {
        initStep1();
        initStep2();
        initStep3();
        initStep4();
    }

    // DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
