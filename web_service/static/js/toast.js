/**
 * Notion Bill Importer - Toast Notification System
 * 版本: 2.0
 *
 * 统一的Toast通知系统，支持多种类型和自定义配置
 */

class ToastSystem {
    constructor(options = {}) {
        this.options = {
            containerClass: 'toast-container',
            defaultDuration: 4000,
            position: 'bottom-right',
            maxToasts: 5,
            showProgress: false,
            ...options
        };

        this.container = null;
        this.toasts = new Map();
        this.toastCounter = 0;

        this.init();
    }

    /**
     * 初始化Toast容器
     */
    init() {
        // 查找或创建容器
        this.container = document.querySelector(`.${this.options.containerClass}`);

        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = this.options.containerClass;
            document.body.appendChild(this.container);
        }

        // 设置容器位置
        this.setPosition(this.options.position);
    }

    /**
     * 设置容器位置
     * @param {string} position - 位置
     */
    setPosition(position) {
        this.container.className = this.options.containerClass;
        this.container.style.cssText = '';

        const positions = {
            'top-right': 'top: 24px; right: 24px;',
            'top-left': 'top: 24px; left: 24px;',
            'top-center': 'top: 24px; left: 50%; transform: translateX(-50%);',
            'bottom-right': 'bottom: 24px; right: 24px;',
            'bottom-left': 'bottom: 24px; left: 24px;',
            'bottom-center': 'bottom: 24px; left: 50%; transform: translateX(-50%);'
        };

        if (positions[position]) {
            this.container.style.cssText = positions[position];
        }
    }

    /**
     * 显示Toast
     * @param {Object} options - Toast配置
     * @returns {string} Toast ID
     */
    show(options) {
        const toast = this.createToast(options);
        const id = `toast-${++this.toastCounter}`;

        // 设置Toast ID
        toast.id = id;
        toast.dataset.id = id;

        // 添加到容器
        this.container.appendChild(toast);

        // 存储Toast引用
        this.toasts.set(id, {
            element: toast,
            timer: null,
            startTime: Date.now()
        });

        // 自动关闭
        if (options.duration !== 0) {
            const duration = options.duration ?? this.options.defaultDuration;
            this.startTimer(id, duration);
        }

        // 显示进度条
        if (options.showProgress ?? this.options.showProgress) {
            this.addProgressBar(toast, duration);
        }

        // 限制最大数量
        this.enforceMaxToasts();

        return id;
    }

    /**
     * 创建Toast元素
     * @param {Object} options
     * @returns {HTMLElement}
     */
    createToast(options) {
        const {
            type = 'info',
            title = '',
            message = '',
            icon = null,
            closable = true,
            actions = []
        } = options;

        // 创建Toast元素
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        // 获取图标
        const iconSvg = icon || this.getDefaultIcon(type);

        // 构建HTML
        let html = `
            <div class="toast-icon">${iconSvg}</div>
            <div class="toast-content">
        `;

        if (title) {
            html += `<div class="toast-title">${this.escapeHtml(title)}</div>`;
        }

        if (message) {
            html += `<div class="toast-message">${this.escapeHtml(message)}</div>`;
        }

        // 添加操作按钮
        if (actions.length > 0) {
            html += '<div class="toast-actions">';
            actions.forEach(action => {
                const buttonClass = action.primary ? 'btn btn-primary btn-xs' : 'btn btn-ghost btn-xs';
                html += `<button class="${buttonClass}" data-action="${action.label}">${action.label}</button>`;
            });
            html += '</div>';
        }

        html += '</div>';

        // 添加关闭按钮
        if (closable) {
            html += `
                <button class="toast-close" aria-label="关闭">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            `;
        }

        toast.innerHTML = html;

        // 绑定事件
        this.bindToastEvents(toast, options);

        return toast;
    }

    /**
     * 绑定Toast事件
     * @param {HTMLElement} toast
     * @param {Object} options
     */
    bindToastEvents(toast, options) {
        // 关闭按钮
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.dismiss(toast.id);
            });
        }

        // 操作按钮
        const actionButtons = toast.querySelectorAll('.toast-actions button');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const actionLabel = e.target.dataset.action;
                const action = options.actions.find(a => a.label === actionLabel);
                if (action && action.handler) {
                    action.handler();
                }
                this.dismiss(toast.id);
            });
        });

        // 鼠标悬停暂停计时
        toast.addEventListener('mouseenter', () => {
            this.pauseTimer(toast.id);
        });

        toast.addEventListener('mouseleave', () => {
            this.resumeTimer(toast.id);
        });
    }

    /**
     * 添加进度条
     * @param {HTMLElement} toast
     * @param {number} duration
     */
    addProgressBar(toast, duration) {
        const progressBar = document.createElement('div');
        progressBar.className = 'toast-progress';
        progressBar.style.cssText = `
            position: absolute;
            bottom: 0;
            left: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--color-primary-500), var(--color-primary-600));
            transition: width linear;
        `;

        toast.appendChild(progressBar);

        // 设置动画
        requestAnimationFrame(() => {
            progressBar.style.transition = `width ${duration}ms linear`;
            requestAnimationFrame(() => {
                progressBar.style.width = '100%';
            });
        });
    }

    /**
     * 开始计时器
     * @param {string} id
     * @param {number} duration
     */
    startTimer(id, duration) {
        const toastData = this.toasts.get(id);
        if (!toastData) return;

        toastData.timer = setTimeout(() => {
            this.dismiss(id);
        }, duration);
    }

    /**
     * 暂停计时器
     * @param {string} id
     */
    pauseTimer(id) {
        const toastData = this.toasts.get(id);
        if (!toastData || !toastData.timer) return;

        clearTimeout(toastData.timer);
        toastData.remainingTime = toastData.remainingTime ||
            (toastData.duration || this.options.defaultDuration) -
            (Date.now() - toastData.startTime);
    }

    /**
     * 恢复计时器
     * @param {string} id
     */
    resumeTimer(id) {
        const toastData = this.toasts.get(id);
        if (!toastData) return;

        const remainingTime = toastData.remainingTime ||
            (toastData.duration || this.options.defaultDuration);

        if (remainingTime > 0) {
            this.startTimer(id, remainingTime);
        }
    }

    /**
     * 关闭Toast
     * @param {string} id
     */
    dismiss(id) {
        const toastData = this.toasts.get(id);
        if (!toastData) return;

        const { element, timer } = toastData;

        // 清除计时器
        if (timer) {
            clearTimeout(timer);
        }

        // 添加隐藏动画
        element.classList.add('hiding');

        // 移除元素
        setTimeout(() => {
            element.remove();
            this.toasts.delete(id);
        }, 200);
    }

    /**
     * 清空所有Toast
     */
    clear() {
        this.toasts.forEach((_, id) => {
            this.dismiss(id);
        });
    }

    /**
     * 强制执行最大Toast数量限制
     */
    enforceMaxToasts() {
        if (this.toasts.size > this.options.maxToasts) {
            const oldestId = this.toasts.keys().next().value;
            this.dismiss(oldestId);
        }
    }

    /**
     * 获取默认图标
     * @param {string} type
     * @returns {string}
     */
    getDefaultIcon(type) {
        const icons = {
            success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>`,
            error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>`,
            warning: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>`,
            info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>`
        };

        return icons[type] || icons.info;
    }

    /**
     * HTML转义
     * @param {string} text
     * @returns {string}
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 便捷方法

    /**
     * 显示成功消息
     */
    success(message, options = {}) {
        return this.show({
            type: 'success',
            message,
            ...options
        });
    }

    /**
     * 显示错误消息
     */
    error(message, options = {}) {
        return this.show({
            type: 'error',
            message,
            ...options
        });
    }

    /**
     * 显示警告消息
     */
    warning(message, options = {}) {
        return this.show({
            type: 'warning',
            message,
            ...options
        });
    }

    /**
     * 显示信息消息
     */
    info(message, options = {}) {
        return this.show({
            type: 'info',
            message,
            ...options
        });
    }

    /**
     * 显示带标题的消息
     */
    showWithTitle(title, message, type = 'info', options = {}) {
        return this.show({
            type,
            title,
            message,
            ...options
        });
    }
}

/**
 * 创建全局Toast实例
 */
let globalToast = null;

/**
 * 获取全局Toast实例
 * @returns {ToastSystem}
 */
function getToast() {
    if (!globalToast) {
        globalToast = new ToastSystem();
    }
    return globalToast;
}

/**
 * 简化的Toast API
 */
const toast = {
    success: (message, options) => getToast().success(message, options),
    error: (message, options) => getToast().error(message, options),
    warning: (message, options) => getToast().warning(message, options),
    info: (message, options) => getToast().info(message, options),
    show: (options) => getToast().show(options),
    dismiss: (id) => getToast().dismiss(id),
    clear: () => getToast().clear()
};

// 导出到全局
if (typeof window !== 'undefined') {
    window.ToastSystem = ToastSystem;
    window.toast = toast;

    // 提供更简洁的全局API
    window.showToast = toast.info;
    window.showSuccess = toast.success;
    window.showError = toast.error;
    window.showWarning = toast.warning;
}
