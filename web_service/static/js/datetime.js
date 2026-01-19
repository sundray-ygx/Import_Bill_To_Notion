/**
 * 日期时间工具函数
 * 统一处理北京时间（UTC+8）的显示
 */

(function(global) {
    'use strict';

    const DateTimeUtils = {
        /**
         * 将ISO时间字符串转换为北京时间（UTC+8）并格式化
         * @param {string} dateStr - ISO格式的日期时间字符串
         * @param {object} options - 格式化选项
         * @returns {string} 格式化后的北京时间字符串
         */
        formatBeijingTime: function(dateStr, options = {}) {
            if (!dateStr) return '-';

            const defaultOptions = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            };

            const date = new Date(dateStr);
            // 计算北京时间偏移（UTC+8）
            const beijingTime = new Date(date.getTime() + (8 * 60 * 60 * 1000) + (date.getTimezoneOffset() * 60 * 1000));

            return beijingTime.toLocaleString('zh-CN', { ...defaultOptions, ...options });
        },

        /**
         * 格式化日期（不包含时间）
         * @param {string} dateStr - ISO格式的日期字符串
         * @returns {string} 格式化后的日期字符串
         */
        formatDate: function(dateStr) {
            return this.formatBeijingTime(dateStr, {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        },

        /**
         * 格式化完整日期时间（年/月/日 时:分）
         * @param {string} dateStr - ISO格式的日期时间字符串
         * @returns {string} 格式化后的日期时间字符串
         */
        formatDateTime: function(dateStr) {
            return this.formatBeijingTime(dateStr, {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        /**
         * 格式化完整日期时间（年/月/日 时:分:秒）
         * @param {string} dateStr - ISO格式的日期时间字符串
         * @returns {string} 格式化后的日期时间字符串
         */
        formatFullDateTime: function(dateStr) {
            return this.formatBeijingTime(dateStr, {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        },

        /**
         * 格式化时间（时:分:秒）
         * @param {string} dateStr - ISO格式的日期时间字符串
         * @returns {string} 格式化后的时间字符串
         */
        formatTime: function(dateStr) {
            return this.formatBeijingTime(dateStr, {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        },

        /**
         * 计算相对时间（如：3分钟前）
         * @param {string} dateStr - ISO格式的日期时间字符串
         * @returns {string} 相对时间字符串
         */
        formatRelativeTime: function(dateStr) {
            if (!dateStr) return '-';

            const date = new Date(dateStr);
            const beijingTime = new Date(date.getTime() + (8 * 60 * 60 * 1000) + (date.getTimezoneOffset() * 60 * 1000));
            const now = new Date();
            const nowBeijing = new Date(now.getTime() + (8 * 60 * 60 * 1000) + (now.getTimezoneOffset() * 60 * 1000));

            const diffMs = nowBeijing - beijingTime;
            const diffSecs = Math.floor(diffMs / 1000);
            const diffMins = Math.floor(diffSecs / 60);
            const diffHours = Math.floor(diffMins / 60);
            const diffDays = Math.floor(diffHours / 24);

            if (diffSecs < 60) {
                return '刚刚';
            } else if (diffMins < 60) {
                return `${diffMins}分钟前`;
            } else if (diffHours < 24) {
                return `${diffHours}小时前`;
            } else if (diffDays < 7) {
                return `${diffDays}天前`;
            } else {
                return this.formatDate(dateStr);
            }
        }
    };

    // 导出模块
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = DateTimeUtils;
    } else {
        global.DateTimeUtils = DateTimeUtils;
    }
})(typeof window !== 'undefined' ? window : global);
