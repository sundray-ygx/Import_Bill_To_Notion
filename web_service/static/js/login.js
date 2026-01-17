/**
 * 登录页面逻辑
 */

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');

    if (!loginForm) return;

    // 表单提交处理
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAlert();

        // 获取表单数据
        const formData = new FormData(loginForm);
        const username = formData.get('username');
        const password = formData.get('password');

        // 验证输入
        if (!username || !password) {
            showAlert('请输入用户名和密码', 'error');
            return;
        }

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
                // 保存认证信息
                saveAuth({
                    access_token: data.access_token,
                    refresh_token: data.refresh_token
                }, data.user);

                showAlert('登录成功！正在跳转...', 'success');

                // 延迟跳转
                setTimeout(() => {
                    // 检查是否有重定向地址
                    const redirectUrl = new URLSearchParams(window.location.search).get('redirect');
                    window.location.href = redirectUrl || '/';
                }, 500);
            } else {
                // 登录失败
                const errorMsg = data.detail || '登录失败，请检查用户名和密码';
                showAlert(errorMsg, 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            showAlert('网络错误，请稍后重试', 'error');
        } finally {
            setButtonLoading(loginBtn, false);
        }
    });

    // Enter 键提交
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loginForm.dispatchEvent(new Event('submit'));
            }
        });
    }
});
