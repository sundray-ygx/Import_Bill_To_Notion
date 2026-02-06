/**
 * 注册页面逻辑
 * 使用新的表单验证器和Toast通知系统
 */

document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');
    const registerBtn = document.getElementById('register-btn');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const strengthFill = document.getElementById('strength-fill');
    const strengthText = document.getElementById('strength-text');

    if (!registerForm) return;

    // 初始化表单验证器
    const validator = new FormValidator(registerForm, {
        validateOnBlur: true,
        validateOnChange: false,
        showErrorMessages: true
    });

    // 添加验证规则
    validator.addFields({
        username: [
            { type: 'required', message: '请输入用户名' },
            { type: 'minLength', min: 3, message: '用户名至少需要3个字符' },
            { type: 'maxLength', max: 50, message: '用户名不能超过50个字符' },
            {
                type: 'pattern',
                regex: /^[a-zA-Z0-9_-]+$/,
                message: '用户名只能包含字母、数字、下划线和连字符'
            }
        ],
        email: [
            { type: 'required', message: '请输入电子邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' }
        ],
        password: [
            { type: 'required', message: '请输入密码' },
            { type: 'minLength', min: 8, message: '密码至少需要8个字符' },
            {
                type: 'pattern',
                regex: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                message: '密码必须包含大小写字母和数字'
            }
        ],
        confirm_password: [
            { type: 'required', message: '请确认密码' },
            { type: 'match', field: 'password', message: '两次输入的密码不一致' }
        ]
    });

    // 密码可见性切换
    const togglePassword = document.getElementById('toggle-password');

    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', () => {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';

            // 切换图标
            const showIcon = togglePassword.querySelector('.icon-show');
            const hideIcon = togglePassword.querySelector('.icon-hide');

            if (showIcon && hideIcon) {
                showIcon.style.display = isPassword ? 'none' : 'block';
                hideIcon.style.display = isPassword ? 'block' : 'none';
            }

            // 更新ARIA标签
            togglePassword.setAttribute('aria-label', isPassword ? '显示密码' : '隐藏密码');
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

    // 检查密码强度
    function checkPasswordStrength(password) {
        if (!password) return { score: 0, text: '未输入', valid: false };

        let score = 0;

        // 长度检查
        if (password.length >= 8) score++;
        if (password.length >= 12) score++;

        // 字符类型检查
        if (/[a-z]/.test(password)) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/[0-9]/.test(password)) score++;
        if (/[^a-zA-Z0-9]/.test(password)) score++;

        // 验证是否符合后端要求
        const hasRequiredLength = password.length >= 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasDigit = /[0-9]/.test(password);
        const valid = hasRequiredLength && hasUpperCase && hasLowerCase && hasDigit;

        if (score <= 2) return { score, level: 'weak', text: '弱', valid };
        if (score <= 4) return { score, level: 'medium', text: '中等', valid };
        return { score, level: 'strong', text: '强', valid };
    }

    // 更新强度指示器
    function updateStrengthIndicator(strength) {
        if (!strengthFill || !strengthText) return;

        strengthFill.className = 'strength-fill';
        strengthText.textContent = `密码强度：${strength.text}`;

        if (strength.score > 0) {
            strengthFill.classList.add(strength.level);
        }

        // 如果密码不符合要求，添加警告样式
        if (strength.text !== '未输入' && !strength.valid) {
            strengthText.textContent += ' （必须包含大小写字母和数字）';
            strengthText.style.color = 'var(--color-error-600)';
        } else if (strength.valid) {
            strengthText.style.color = 'var(--color-success-600)';
        } else {
            strengthText.style.color = '';
        }
    }

    // 表单提交处理
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 验证表单
        if (!validator.validate()) {
            // 聚焦到第一个错误字段
            const firstError = registerForm.querySelector('.input-error');
            if (firstError) {
                firstError.focus();
            }
            return;
        }

        // 获取表单数据
        const formData = new FormData(registerForm);
        const username = formData.get('username');
        const email = formData.get('email');
        const password = formData.get('password');
        const terms = formData.get('terms');

        // 验证服务条款
        if (!terms) {
            toast.error('请同意服务条款和隐私政策');
            return;
        }

        // 设置加载状态
        setButtonLoading(registerBtn, true);

        try {
            // 发送注册请求
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok) {
                // 保存认证信息
                saveAuth({
                    access_token: data.access_token,
                    refresh_token: data.refresh_token
                }, data.user);

                // 根据用户角色决定跳转目标
                const isSuperuser = data.user?.is_superuser || false;

                if (isSuperuser) {
                    toast.success('注册成功！您是系统管理员，正在前往设置页面...');
                    setTimeout(() => {
                        window.location.href = '/settings';
                    }, 1500);
                } else {
                    toast.success('注册成功！正在前往首页...');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1500);
                }
            } else {
                // 注册失败
                const errorMsg = data.detail || '注册失败，请稍后重试';
                toast.error(errorMsg);
            }
        } catch (error) {
            console.error('Register error:', error);
            toast.error('网络错误，请稍后重试');
        } finally {
            setButtonLoading(registerBtn, false);
        }
    });

    // 实时验证用户名（防抖）
    let usernameTimeout;
    const usernameInput = document.getElementById('username');
    if (usernameInput) {
        usernameInput.addEventListener('input', () => {
            clearTimeout(usernameTimeout);
            usernameTimeout = setTimeout(async () => {
                const username = usernameInput.value.trim();
                if (username.length >= 3) {
                    // 这里可以添加用户名可用性检查
                    // 暂时不实现，避免频繁请求
                }
            }, 500);
        });
    }
});

/**
 * 设置按钮加载状态
 * @param {HTMLButtonElement} btn
 * @param {boolean} loading
 */
function setButtonLoading(btn, loading) {
    if (!btn) return;

    if (loading) {
        btn.classList.add('loading');
        btn.disabled = true;
    } else {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}
