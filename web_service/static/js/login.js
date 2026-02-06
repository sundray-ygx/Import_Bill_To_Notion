/**
 * 登录页面逻辑
 * 使用新的表单验证器和Toast通知系统
 */

/**
 * 设置 access_token 到 Cookie
 * 用于服务端页面级别的认证检查
 */
function setAccessTokenCookie(token) {
    const expires = new Date();
    // 7天后过期（与 access_token 过期时间匹配）
    expires.setTime(expires.getTime() + 7 * 24 * 60 * 60 * 1000);

    // 设置 Cookie，path=/ 确保全站可用
    // SameSite=Lax 允许同站点导航时携带 Cookie
    document.cookie = `access_token=${token}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`;
}

/**
 * 清除 Cookie 中的 access_token
 */
function clearAccessTokenCookie() {
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Lax';
}

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');

    if (!loginForm) return;

    // 初始化表单验证器
    const validator = new FormValidator(loginForm, {
        validateOnBlur: true,
        validateOnChange: false,
        showErrorMessages: true
    });

    // 添加验证规则
    validator.addFields({
        username: [
            { type: 'required', message: '请输入用户名' }
        ],
        password: [
            { type: 'required', message: '请输入密码' }
        ]
    });

    // 密码可见性切换
    const togglePassword = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('password');

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

    // 表单提交处理
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 验证表单
        if (!validator.validate()) {
            // 聚焦到第一个错误字段
            const firstError = loginForm.querySelector('.input-error');
            if (firstError) {
                firstError.focus();
            }
            return;
        }

        // 获取表单数据
        const formData = new FormData(loginForm);
        const username = formData.get('username');
        const password = formData.get('password');

        // 设置加载状态
        setButtonLoading(loginBtn, true);

        try {
            // 发送登录请求
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    username: username,
                    password: password,
                    grant_type: 'password'
                })
            });

            const data = await response.json();

            if (response.ok) {
                // 保存认证信息到 localStorage
                saveAuth({
                    access_token: data.access_token,
                    refresh_token: data.refresh_token
                }, data.user);

                // 同时设置 Cookie，供服务端页面认证使用
                setAccessTokenCookie(data.access_token);

                // 显示成功提示
                toast.success('登录成功！正在跳转...');

                // 延迟跳转
                setTimeout(() => {
                    // 检查是否有重定向地址
                    const redirectUrl = new URLSearchParams(window.location.search).get('redirect');
                    window.location.href = redirectUrl || '/';
                }, 500);
            } else {
                // 登录失败
                const errorMsg = data.detail || '登录失败，请检查用户名和密码';
                toast.error(errorMsg);

                // 聚焦到密码输入框
                if (passwordInput) {
                    passwordInput.focus();
                    passwordInput.select();
                }
            }
        } catch (error) {
            console.error('Login error:', error);
            toast.error('网络错误，请稍后重试');
        } finally {
            setButtonLoading(loginBtn, false);
        }
    });
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
