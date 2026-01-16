/**
 * 注册页面逻辑
 */

document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');
    const registerBtn = document.getElementById('register-btn');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const strengthFill = document.getElementById('strength-fill');
    const strengthText = document.getElementById('strength-text');
    const passwordMatchHint = document.getElementById('password-match-hint');

    if (!registerForm) return;

    // 密码强度检测
    if (passwordInput) {
        passwordInput.addEventListener('input', () => {
            const password = passwordInput.value;
            const strength = checkPasswordStrength(password);
            updateStrengthIndicator(strength);
            checkPasswordMatch();
        });
    }

    // 确认密码匹配检测
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', checkPasswordMatch);
    }

    // 检查密码强度（与后端验证一致）
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

        // 验证是否符合后端要求：至少8个字符，包含大小写字母和数字
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
            strengthText.style.color = '#ef4444';
        } else if (strength.valid) {
            strengthText.style.color = '#10b981';
        } else {
            strengthText.style.color = '';
        }
    }

    // 检查密码是否匹配
    function checkPasswordMatch() {
        if (!confirmPasswordInput || !passwordMatchHint) return;

        const password = passwordInput ? passwordInput.value : '';
        const confirmPassword = confirmPasswordInput.value;

        if (!confirmPassword) {
            passwordMatchHint.textContent = '';
            passwordMatchHint.style.color = '';
            return false;
        }

        if (password === confirmPassword) {
            passwordMatchHint.textContent = '✓ 密码匹配';
            passwordMatchHint.style.color = '#10b981';
            return true;
        } else {
            passwordMatchHint.textContent = '✗ 密码不匹配';
            passwordMatchHint.style.color = '#ef4444';
            return false;
        }
    }

    // 表单提交处理
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAlert();

        // 获取表单数据
        const formData = new FormData(registerForm);
        const username = formData.get('username');
        const email = formData.get('email');
        const password = formData.get('password');
        const confirmPassword = formData.get('confirm_password');
        const terms = formData.get('terms');

        // 验证输入
        if (!username || !email || !password || !confirmPassword) {
            showAlert('请填写所有必填项', 'error');
            return;
        }

        if (username.length < 3 || username.length > 50) {
            showAlert('用户名长度必须在3-50个字符之间', 'error');
            return;
        }

        if (password !== confirmPassword) {
            showAlert('两次输入的密码不一致', 'error');
            return;
        }

        // 验证密码强度
        const strengthResult = checkPasswordStrength(password);
        if (!strengthResult.valid) {
            showAlert('密码必须至少8个字符，包含大小写字母和数字', 'error');
            return;
        }

        if (!terms) {
            showAlert('请同意服务条款和隐私政策', 'error');
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
                showAlert('注册成功！正在进入配置向导...', 'success');

                // 保存认证信息到本地存储
                if (window.Auth && window.Auth.saveAuth) {
                    window.Auth.saveAuth({
                        access_token: data.access_token,
                        refresh_token: data.refresh_token
                    }, data.user);
                }

                // 延迟跳转到配置向导
                setTimeout(() => {
                    window.location.href = '/setup';
                }, 1500);
            } else {
                // 注册失败
                const errorMsg = data.detail || '注册失败，请稍后重试';
                showAlert(errorMsg, 'error');
            }
        } catch (error) {
            console.error('Register error:', error);
            showAlert('网络错误，请稍后重试', 'error');
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
