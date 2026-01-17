/**
 * 用户表单页面逻辑
 * 用于创建和编辑用户
 */

(function() {
    'use strict';

    // 页面状态
    let pageState = {
        mode: 'create',
        userId: null,
        isLoading: false
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
            toast.style.transform = 'translateX(100px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // 从 URL 获取参数
    function getUrlParams() {
        const params = new URLSearchParams(window.location.search);
        return {
            mode: params.get('mode') || 'create',
            user_id: params.get('user_id') ? parseInt(params.get('user_id')) : null
        };
    }

    // 密码强度检测
    function checkPasswordStrength(password) {
        let strength = 0;
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        if (/[a-z]/.test(password)) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^a-zA-Z0-9]/.test(password)) strength++;
        if (strength <= 2) return 'weak';
        if (strength <= 4) return 'medium';
        return 'strong';
    }

    // 更新密码强度指示器
    function updatePasswordStrength() {
        const passwordInput = document.getElementById('password');
        const strengthFill = document.getElementById('strength-fill');
        const strengthText = document.getElementById('strength-text');
        if (!passwordInput || !strengthFill || !strengthText) return;
        const password = passwordInput.value;
        if (!password) {
            strengthFill.className = 'strength-fill';
            strengthFill.style.width = '0%';
            strengthText.textContent = '请输入密码';
            return;
        }
        const strength = checkPasswordStrength(password);
        const strengthMap = {
            'weak': { width: '33%', text: '弱' },
            'medium': { width: '66%', text: '中等' },
            'strong': { width: '100%', text: '强' }
        };
        strengthFill.className = `strength-fill ${strength}`;
        strengthFill.style.width = strengthMap[strength].width;
        strengthText.textContent = strengthMap[strength].text;
    }

    // 初始化密码输入框
    function initPasswordInputs() {
        const passwordInput = document.getElementById('password');
        if (passwordInput) {
            passwordInput.addEventListener('input', updatePasswordStrength);
        }
        const toggleButtons = document.querySelectorAll('.password-toggle');
        toggleButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const input = btn.previousElementSibling;
                if (input && input.type === 'password') {
                    input.type = 'text';
                    btn.querySelector('span').textContent = '🙈';
                } else if (input) {
                    input.type = 'password';
                    btn.querySelector('span').textContent = '👁';
                }
            });
        });
    }

    // 加载用户数据（编辑模式）
    async function loadUserData(userId) {
        if (pageState.isLoading) return;
        pageState.isLoading = true;
        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                fillForm(data.user);
            } else if (response.status === 401) {
                showToast('登录已过期，请重新登录', 'error');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 1500);
            } else {
                throw new Error('加载失败');
            }
        } catch (error) {
            console.error('Failed to load user:', error);
            showToast('加载用户数据失败', 'error');
            setTimeout(() => {
                window.location.href = '/admin/users';
            }, 2000);
        } finally {
            pageState.isLoading = false;
        }
    }

    // 填充表单（编辑模式）
    function fillForm(user) {
        document.getElementById('username').value = user.username;
        document.getElementById('email').value = user.email;
        const superuserRadio = document.querySelector(`input[name="is_superuser"][value="${user.is_superuser}"]`);
        if (superuserRadio) {
            superuserRadio.checked = true;
        }
        const activeCheckbox = document.querySelector('input[name="is_active"]');
        if (activeCheckbox) {
            activeCheckbox.checked = user.is_active;
        }
    }

    // 验证表单
    function validateForm(formData) {
        const errors = [];
        if (!formData.username || formData.username.length < 3) {
            errors.push('用户名至少需要3个字符');
        }
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!formData.email || !emailRegex.test(formData.email)) {
            errors.push('请输入有效的邮箱地址');
        }
        if (pageState.mode === 'create') {
            if (!formData.password || formData.password.length < 8) {
                errors.push('密码至少需要8个字符');
            } else {
                if (!/[a-z]/.test(formData.password)) {
                    errors.push('密码必须包含小写字母');
                }
                if (!/[A-Z]/.test(formData.password)) {
                    errors.push('密码必须包含大写字母');
                }
                if (!/[0-9]/.test(formData.password)) {
                    errors.push('密码必须包含数字');
                }
            }
        }
        return errors;
    }

    // 提交表单
    async function submitForm(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const data = {
            username: formData.get('username'),
            email: formData.get('email'),
            is_superuser: formData.get('is_superuser') === 'true',
            is_active: formData.get('is_active') === 'on'
        };
        if (pageState.mode === 'create') {
            data.password = formData.get('password');
        }
        const errors = validateForm(data);
        if (errors.length > 0) {
            showToast(errors[0], 'error');
            return;
        }
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = true;
        submitBtn.querySelector('.btn-text').textContent = pageState.mode === 'create' ? '创建中...' : '保存中...';
        try {
            let url, method;
            if (pageState.mode === 'create') {
                url = '/api/admin/users';
                method = 'POST';
            } else {
                url = `/api/admin/users/${pageState.userId}`;
                method = 'PUT';
            }
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            if (response.ok) {
                showToast(pageState.mode === 'create' ? '用户创建成功' : '用户更新成功');
                setTimeout(() => {
                    window.location.href = '/admin/users';
                }, 1000);
            } else {
                const result = await response.json();
                showToast(result.detail || '操作失败', 'error');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            showToast('网络错误，请重试', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.querySelector('.btn-text').textContent = pageState.mode === 'create' ? '创建用户' : '保存更改';
        }
    }

    // 重置密码
    async function resetPassword() {
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        if (!newPassword || newPassword.length < 8) {
            showToast('密码至少需要8个字符', 'error');
            return;
        }
        if (newPassword !== confirmPassword) {
            showToast('两次输入的密码不一致', 'error');
            return;
        }
        const errors = [];
        if (!/[a-z]/.test(newPassword)) errors.push('密码必须包含小写字母');
        if (!/[A-Z]/.test(newPassword)) errors.push('密码必须包含大写字母');
        if (!/[0-9]/.test(newPassword)) errors.push('密码必须包含数字');
        if (errors.length > 0) {
            showToast(errors[0], 'error');
            return;
        }
        const submitBtn = document.getElementById('password-submit');
        submitBtn.disabled = true;
        submitBtn.textContent = '重置中...';
        try {
            const response = await fetch(`/api/admin/users/${pageState.userId}/reset-password`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ new_password: newPassword })
            });
            if (response.ok) {
                showToast('密码重置成功');
                closeModal('password-modal');
                document.getElementById('password-reset-form').reset();
            } else {
                const result = await response.json();
                showToast(result.detail || '重置失败', 'error');
            }
        } catch (error) {
            console.error('Password reset error:', error);
            showToast('网络错误，请重试', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = '重置密码';
        }
    }

    // 删除用户
    async function deleteUser() {
        const confirmModal = document.getElementById('confirm-modal');
        closeModal('confirm-modal');
        try {
            const response = await fetch(`/api/admin/users/${pageState.userId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            if (response.ok) {
                showToast('用户已删除');
                setTimeout(() => {
                    window.location.href = '/admin/users';
                }, 1000);
            } else {
                const result = await response.json();
                showToast(result.detail || '删除失败', 'error');
            }
        } catch (error) {
            console.error('Delete user error:', error);
            showToast('网络错误，请重试', 'error');
        }
    }

    // 打开模态框
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    // 关闭模态框
    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // 初始化模态框
    function initModals() {
        const confirmOkBtn = document.getElementById('confirm-ok');
        const confirmCancelBtn = document.getElementById('confirm-cancel');
        const confirmCloseBtn = document.getElementById('confirm-close');
        const confirmBackdrop = document.querySelector('#confirm-modal .modal-backdrop');
        if (confirmOkBtn) confirmOkBtn.addEventListener('click', deleteUser);
        if (confirmCancelBtn) confirmCancelBtn.addEventListener('click', () => closeModal('confirm-modal'));
        if (confirmCloseBtn) confirmCloseBtn.addEventListener('click', () => closeModal('confirm-modal'));
        if (confirmBackdrop) confirmBackdrop.addEventListener('click', () => closeModal('confirm-modal'));

        const resetPasswordBtn = document.getElementById('reset-password-btn');
        const passwordCloseBtn = document.getElementById('password-close');
        const passwordCancelBtn = document.getElementById('password-cancel');
        const passwordSubmitBtn = document.getElementById('password-submit');
        const passwordBackdrop = document.querySelector('#password-modal .modal-backdrop');
        if (resetPasswordBtn) resetPasswordBtn.addEventListener('click', () => openModal('password-modal'));
        if (passwordCloseBtn) passwordCloseBtn.addEventListener('click', () => closeModal('password-modal'));
        if (passwordCancelBtn) passwordCancelBtn.addEventListener('click', () => closeModal('password-modal'));
        if (passwordBackdrop) passwordBackdrop.addEventListener('click', () => closeModal('password-modal'));
        if (passwordSubmitBtn) passwordSubmitBtn.addEventListener('click', (e) => {
            e.preventDefault();
            resetPassword();
        });

        const deleteUserBtn = document.getElementById('delete-user-btn');
        if (deleteUserBtn) {
            deleteUserBtn.addEventListener('click', () => {
                document.getElementById('confirm-title').textContent = '确认删除用户';
                document.getElementById('confirm-message').textContent = '确定要删除该用户吗？此操作不可撤销！';
                openModal('confirm-modal');
            });
        }
    }

    // 初始化表单
    function initForm() {
        const form = document.getElementById('user-form');
        if (form) {
            form.addEventListener('submit', submitForm);
        }
        const cancelBtn = document.getElementById('cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                window.location.href = '/admin/users';
            });
        }
    }

    // 检查权限
    function checkPermission() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
            return false;
        }
        const userStr = localStorage.getItem('user');
        if (userStr) {
            const user = JSON.parse(userStr);
            if (!user.is_superuser) {
                showToast('您没有权限访问此页面', 'error');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
                return false;
            }
        }
        return true;
    }

    // 页面初始化
    function init() {
        if (!checkPermission()) return;
        const params = getUrlParams();
        pageState.mode = params.mode;
        pageState.userId = params.user_id;
        const titleEl = document.getElementById('form-title');
        const badgeEl = document.getElementById('form-mode-badge');
        if (titleEl) {
            titleEl.textContent = pageState.mode === 'edit' ? '编辑用户' : '添加用户';
        }
        if (badgeEl) {
            badgeEl.textContent = pageState.mode === 'edit' ? '编辑' : '新增';
        }
        initPasswordInputs();
        initForm();
        initModals();
        if (pageState.mode === 'edit' && pageState.userId) {
            loadUserData(pageState.userId);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
