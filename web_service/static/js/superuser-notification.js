/**
 * 超级管理员提升通知组件
 * 当用户被自动提升为超级管理员时显示友好的通知
 */

(function() {
    'use strict';

    // 本地存储键
    const DISMISSED_KEY = 'superuser_promotion_dismissed';
    const CHECKED_KEY = 'superuser_promotion_checked';

    /**
     * 检查是否应该显示通知
     */
    async function shouldShowNotification() {
        // 如果已经关闭过，不再显示
        if (localStorage.getItem(DISMISSED_KEY) === 'true') {
            return false;
        }

        // 如果已经检查过且不是超级管理员，不再检查
        if (localStorage.getItem(CHECKED_KEY) === 'true') {
            return false;
        }

        // 检查用户登录状态和角色
        try {
            const response = await fetch('/api/auth/me');
            if (response.ok) {
                const user = await response.json();
                // 如果是超级管理员，显示通知
                return user.is_superuser === true;
            }
        } catch (err) {
            console.error('Failed to check user status:', err);
        }

        return false;
    }

    /**
     * 创建通知横幅
     */
    function createNotificationBanner() {
        // 移除已存在的通知
        const existing = document.getElementById('superuser-promotion-banner');
        if (existing) {
            existing.remove();
        }

        // 创建通知元素
        const banner = document.createElement('div');
        banner.id = 'superuser-promotion-banner';
        banner.className = 'superuser-promotion-banner';

        banner.innerHTML = `
            <div class="banner-content">
                <div class="banner-icon">👑</div>
                <div class="banner-message">
                    <strong>恭喜！</strong> 您已成为系统的超级管理员
                </div>
                <div class="banner-actions">
                    <button class="banner-btn btn-primary" onclick="window.location.href='/admin/users'">
                        管理用户
                    </button>
                    <button class="banner-btn btn-text" id="dismiss-banner">
                        知道了
                    </button>
                </div>
            </div>
        `;

        // 添加到页面
        document.body.insertBefore(banner, document.body.firstChild);

        // 绑定关闭按钮事件
        const dismissBtn = document.getElementById('dismiss-banner');
        if (dismissBtn) {
            dismissBtn.addEventListener('click', dismissNotification);
        }

        // 添加样式
        addStyles();
    }

    /**
     * 关闭通知
     */
    function dismissNotification() {
        const banner = document.getElementById('superuser-promotion-banner');
        if (banner) {
            banner.classList.add('banner-hiding');
            setTimeout(function() {
                banner.remove();
            }, 300);
        }
        localStorage.setItem(DISMISSED_KEY, 'true');
    }

    /**
     * 添加样式
     */
    function addStyles() {
        // 检查样式是否已存在
        if (document.getElementById('superuser-notification-styles')) {
            return;
        }

        const style = document.createElement('style');
        style.id = 'superuser-notification-styles';
        style.textContent = `
            .superuser-promotion-banner {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 20px;
                z-index: 10000;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                animation: bannerSlideDown 0.3s ease-out;
            }

            .superuser-promotion-banner.banner-hiding {
                animation: bannerSlideUp 0.3s ease-in forwards;
            }

            @keyframes bannerSlideDown {
                from {
                    transform: translateY(-100%);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }

            @keyframes bannerSlideUp {
                from {
                    transform: translateY(0);
                    opacity: 1;
                }
                to {
                    transform: translateY(-100%);
                    opacity: 0;
                }
            }

            .banner-content {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 16px;
                max-width: 1200px;
                margin: 0 auto;
                flex-wrap: wrap;
            }

            .banner-icon {
                font-size: 24px;
            }

            .banner-message {
                font-size: 15px;
                flex: 1;
                min-width: 200px;
            }

            .banner-actions {
                display: flex;
                gap: 8px;
            }

            .banner-btn {
                padding: 6px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                border: none;
            }

            .banner-btn.btn-primary {
                background: rgba(255, 255, 255, 0.25);
                color: white;
            }

            .banner-btn.btn-primary:hover {
                background: rgba(255, 255, 255, 0.35);
            }

            .banner-btn.btn-text {
                background: transparent;
                color: rgba(255, 255, 255, 0.9);
            }

            .banner-btn.btn-text:hover {
                color: white;
                text-decoration: underline;
            }

            @media (max-width: 768px) {
                .banner-content {
                    flex-direction: column;
                    text-align: center;
                }

                .banner-message {
                    min-width: auto;
                }

                .banner-actions {
                    width: 100%;
                    justify-content: center;
                }
            }

            /* 为已有的顶部导航栏留出空间 */
            body.has-superuser-banner {
                padding-top: 60px;
            }
        `;

        document.head.appendChild(style);

        // 为body添加class
        document.body.classList.add('has-superuser-banner');
    }

    /**
     * 初始化通知
     */
    async function init() {
        // 只在登录用户页面显示
        const token = localStorage.getItem('access_token');
        if (!token) {
            return;
        }

        const shouldShow = await shouldShowNotification();
        if (shouldShow) {
            createNotificationBanner();
        }

        // 标记已检查
        localStorage.setItem(CHECKED_KEY, 'true');
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
