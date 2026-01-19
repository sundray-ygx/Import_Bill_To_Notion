/**
 * 认证通用功能模块
 */

// API 基础路径
const API_BASE = '/api/auth';

// 本地存储键
const STORAGE_KEYS = {
    ACCESS_TOKEN: 'access_token',
    REFRESH_TOKEN: 'refresh_token',
    USER_INFO: 'user'
};

/**
 * 显示消息提示
 */
function showAlert(message, type = 'info') {
    const container = document.getElementById('alert-container');
    if (!container) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;

    container.innerHTML = '';
    container.appendChild(alert);

    // 3秒后自动隐藏
    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

/**
 * 清除消息提示
 */
function clearAlert() {
    const container = document.getElementById('alert-container');
    if (container) {
        container.innerHTML = '';
    }
}

/**
 * 切换密码显示/隐藏
 */
function setupPasswordToggle() {
    const toggleBtn = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('password');

    if (toggleBtn && passwordInput) {
        toggleBtn.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            toggleBtn.textContent = type === 'password' ? '👁️' : '🙈';
        });
    }
}

/**
 * 保存认证信息到本地存储
 */
function saveAuth(tokens, user) {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);
    localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(user));
}

/**
 * 从本地存储清除认证信息
 */
function clearAuth() {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER_INFO);
}

/**
 * 获取访问令牌
 */
function getAccessToken() {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
}

/**
 * 获取刷新令牌
 */
function getRefreshToken() {
    return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
}

/**
 * 获取用户信息
 */
function getUserInfo() {
    const userInfo = localStorage.getItem(STORAGE_KEYS.USER_INFO);
    return userInfo ? JSON.parse(userInfo) : null;
}

/**
 * 检查用户是否已登录
 */
function isLoggedIn() {
    return !!getAccessToken();
}

/**
 * 设置按钮加载状态
 */
function setButtonLoading(btn, loading) {
    if (loading) {
        btn.classList.add('loading');
        btn.disabled = true;
    } else {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

/**
 * API 请求封装
 */
async function apiRequest(url, options = {}) {
    const token = getAccessToken();

    // 构建请求头
    const headers = {
        ...options.headers
    };

    // 添加认证令牌
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // 只有当 body 不是 FormData 时才设置 Content-Type
    // FormData 需要浏览器自动设置 Content-Type 和 boundary
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = options.headers?.['Content-Type'] || 'application/json';
    }

    const response = await fetch(url, {
        ...options,
        headers
    });

    // 处理 401 未授权
    if (response.status === 401) {
        clearAuth();
        window.location.href = '/login';
        return null;
    }

    return response;
}

/**
 * 刷新访问令牌
 */
async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        return false;
    }

    try {
        const response = await fetch(`${API_BASE}/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            saveAuth({
                access_token: data.access_token,
                refresh_token: data.refresh_token
            }, data.user);
            return true;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
    }

    clearAuth();
    return false;
}

/**
 * 登出
 */
async function logout(refreshToken = null) {
    try {
        const token = refreshToken || getRefreshToken();
        if (token) {
            await fetch(`${API_BASE}/logout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAccessToken()}`
                },
                body: JSON.stringify({ refresh_token: token })
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        clearAuth();
        window.location.href = '/login';
    }
}

/**
 * 页面初始化
 */
document.addEventListener('DOMContentLoaded', async () => {
    // 设置密码切换
    setupPasswordToggle();

    // 如果已登录且在登录/注册页面，跳转到首页
    if (isLoggedIn() && (window.location.pathname === '/login' || window.location.pathname === '/register')) {
        window.location.href = '/';
        return;
    }
});

// 导出到全局
window.Auth = {
    showAlert,
    clearAlert,
    setButtonLoading,
    saveAuth,
    clearAuth,
    getAccessToken,
    getRefreshToken,
    getUserInfo,
    isLoggedIn,
    logout,
    apiRequest
};
