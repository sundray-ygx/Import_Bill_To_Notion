/**
 * 导航栏功能模块
 */

(function() {
    'use strict';

    const navbar = {
        init: function() {
            this.setupUserMenu();
            this.setupMobileToggle();
            this.setupLogout();
            this.updateAuthState();
        },

        /**
         * 设置用户菜单
         */
        setupUserMenu: function() {
            const toggle = document.getElementById('user-menu-toggle');
            const dropdown = document.getElementById('user-dropdown');

            if (!toggle || !dropdown) return;

            // 点击切换下拉菜单
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const isVisible = dropdown.style.display !== 'none';
                dropdown.style.display = isVisible ? 'none' : 'block';
            });

            // 点击外部关闭下拉菜单
            document.addEventListener('click', (e) => {
                if (!toggle.contains(e.target) && !dropdown.contains(e.target)) {
                    dropdown.style.display = 'none';
                }
            });
        },

        /**
         * 设置移动端菜单切换
         */
        setupMobileToggle: function() {
            const toggle = document.getElementById('navbar-toggle');
            const navbar = document.getElementById('navbar');

            if (!toggle || !navbar) return;

            toggle.addEventListener('click', () => {
                navbar.classList.toggle('mobile-open');
            });
        },

        /**
         * 设置登出功能
         */
        setupLogout: function() {
            const logoutBtn = document.getElementById('logout-btn');

            if (!logoutBtn) return;

            logoutBtn.addEventListener('click', async () => {
                if (confirm('确定要退出登录吗？')) {
                    await window.Auth?.logout();
                }
            });
        },

        /**
         * 更新认证状态显示
         */
        updateAuthState: function() {
            const isLoggedIn = window.Auth?.isLoggedIn();
            const userInfo = window.Auth?.getUserInfo();

            const mainNav = document.getElementById('main-nav');
            const guestNav = document.getElementById('guest-nav');
            const userMenu = document.getElementById('user-menu-container');
            const authButtons = document.getElementById('auth-buttons');
            const adminMenu = document.getElementById('admin-menu');

            if (isLoggedIn) {
                // 已登录状态
                if (mainNav) mainNav.style.display = 'flex';
                if (guestNav) guestNav.style.display = 'none';
                if (userMenu) userMenu.style.display = 'block';
                if (authButtons) authButtons.style.display = 'none';

                // 更新用户信息
                if (userInfo) {
                    const navbarUsername = document.getElementById('navbar-username');
                    const dropdownUsername = document.getElementById('dropdown-username');
                    const dropdownEmail = document.getElementById('dropdown-email');

                    if (navbarUsername) navbarUsername.textContent = userInfo.username;
                    if (dropdownUsername) dropdownUsername.textContent = userInfo.username;
                    if (dropdownEmail) dropdownEmail.textContent = userInfo.email;
                }

                // 显示管理员菜单（超级管理员专属）
                if (userInfo && userInfo.is_superuser && adminMenu) {
                    adminMenu.style.display = 'block';
                }
            } else {
                // 未登录状态
                if (mainNav) mainNav.style.display = 'none';
                if (guestNav) guestNav.style.display = 'flex';
                if (userMenu) userMenu.style.display = 'none';
                if (authButtons) authButtons.style.display = 'flex';
            }
        }
    };

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => navbar.init());
    } else {
        navbar.init();
    }

    // 导出到全局
    window.Navbar = navbar;
})();
