/**
 * ============================================
 * Dashboard视图模块
 * 财务概览、统计卡片、活动时间线
 * ============================================
 */

(function() {
    'use strict';

    // ============================================
    // Dashboard视图模块
    // ============================================

    window.DashboardView = {
        // 状态
        isLoading: false,
        lastRefreshTime: null,
        refreshInterval: 60000, // 60秒自动刷新
        autoRefreshTimer: null,

        // 初始化
        init() {
            console.log('[DashboardView] Initializing...');
            this.cacheDOM();
            this.bindEvents();
            this.loadData();
            this.startAutoRefresh();
        },

        // 缓存DOM元素
        cacheDOM() {
            this.container = document.getElementById('view-dashboard');
            this.refreshBtn = document.getElementById('refresh-btn');
        },

        // 绑定事件
        bindEvents() {
            // 刷新按钮
            if (this.refreshBtn) {
                this.refreshBtn.addEventListener('click', () => this.handleManualRefresh());
            }
        },

        // 加载所有数据
        async loadData() {
            if (this.isLoading) return;
            this.isLoading = true;

            this.renderLoading();

            try {
                // 并行加载统计数据和活动记录
                const [statsResponse, activityResponse] = await Promise.all([
                    window.Auth.apiRequest('/api/dashboard/stats'),
                    window.Auth.apiRequest('/api/dashboard/activity?limit=10')
                ]);

                const statsData = statsResponse.ok ? await statsResponse.json() : null;
                const activityData = activityResponse.ok ? await activityResponse.json() : null;

                // 渲染数据
                this.renderDashboard(statsData?.data, activityData?.data);
                this.lastRefreshTime = new Date();
            } catch (error) {
                console.error('[DashboardView] Failed to load data:', error);
                this.renderError('加载数据失败', '请检查网络连接后重试');
            } finally {
                this.isLoading = false;
            }
        },

        // 渲染加载状态
        renderLoading() {
            if (!this.container) return;
            this.container.innerHTML = `
                <div class="dashboard-container">
                    <div class="loading-state">
                        <div class="loading-spinner"></div>
                        <p>加载仪表板数据...</p>
                    </div>
                </div>
            `;
        },

        // 渲染错误状态
        renderError(message, hint) {
            if (!this.container) return;
            this.container.innerHTML = `
                <div class="dashboard-container">
                    <div class="error-state">
                        <div class="error-state-icon">⚠️</div>
                        <p>${message}</p>
                        ${hint ? `<p class="error-hint">${hint}</p>` : ''}
                        <button class="retry-btn" onclick="window.DashboardView.loadData()">
                            重试
                        </button>
                    </div>
                </div>
            `;
        },

        // 渲染仪表板
        renderDashboard(stats, activities) {
            if (!this.container) return;

            // 格式化数据
            const formattedStats = this.formatStats(stats || {});
            const formattedActivities = this.formatActivities(activities || []);

            // 生成HTML
            this.container.innerHTML = `
                <div class="dashboard-container">
                    <!-- 统计卡片区域 -->
                    <section class="stats-section">
                        <div class="stats-grid">
                            ${this.renderStatCard({
                                label: '本月收入',
                                value: formattedStats.monthlyIncome,
                                icon: '💰',
                                iconClass: 'income',
                                trend: formattedStats.incomeTrend,
                                trendLabel: '较上月'
                            })}
                            ${this.renderStatCard({
                                label: '本月支出',
                                value: formattedStats.monthlyExpense,
                                icon: '💸',
                                iconClass: 'expense',
                                trend: formattedStats.expenseTrend,
                                trendLabel: '较上月'
                            })}
                            ${this.renderStatCard({
                                label: '净余额',
                                value: formattedStats.netBalance,
                                icon: '⚖️',
                                iconClass: 'balance',
                                isPositive: formattedStats.netBalance >= 0
                            })}
                            ${this.renderStatCard({
                                label: '交易笔数',
                                value: formattedStats.transactionCount,
                                icon: '📊',
                                iconClass: 'count'
                            })}
                        </div>
                    </section>

                    <!-- 活动时间线区域 -->
                    <section class="activity-section">
                        <div class="section-header">
                            <div>
                                <h3>最近活动</h3>
                                <p class="section-subtitle">您的最近账单操作记录</p>
                            </div>
                        </div>

                        ${this.renderActivityTimeline(formattedActivities)}
                    </section>
                </div>
            `;
        },

        // 渲染统计卡片
        renderStatCard(config) {
            const { label, value, icon, iconClass, trend, trendLabel, isPositive } = config;

            // 趋势指示器
            let trendHtml = '';
            if (trend !== null && trend !== undefined) {
                const isTrendPositive = trend >= 0;
                const trendIcon = isTrendPositive ? '↑' : '↓';
                const trendClass = isTrendPositive ? 'positive' : 'negative';
                const trendPercent = Math.abs((trend * 100).toFixed(1));

                trendHtml = `
                    <div class="stat-card-trend ${trendClass}">
                        <span>${trendIcon} ${trendPercent}%</span>
                        <span>${trendLabel}</span>
                    </div>
                `;
            }

            // 余额特殊处理
            const valueClass = iconClass === 'balance' ? (isPositive ? 'positive' : 'negative') : '';
            const formattedValue = iconClass === 'balance' && !isPositive
                ? `-${this.formatCurrency(Math.abs(value))}`
                : this.formatCurrency(value);

            return `
                <div class="stat-card">
                    <div class="stat-card-header">
                        <span class="stat-card-label">${label}</span>
                        <div class="stat-card-icon ${iconClass}">${icon}</div>
                    </div>
                    <div class="stat-card-value ${valueClass}">${formattedValue}</div>
                    ${trendHtml}
                </div>
            `;
        },

        // 渲染活动时间线
        renderActivityTimeline(activities) {
            if (!activities || activities.length === 0) {
                return `
                    <div class="activity-empty">
                        <div class="activity-empty-icon">📭</div>
                        <p>还没有任何活动记录</p>
                        <p class="activity-empty-hint">上传您的第一个账单开始使用</p>
                        <button class="activity-empty-btn" onclick="window.Workspace.navigateTo('bills')">
                            上传账单
                        </button>
                    </div>
                `;
            }

            return `
                <div class="activity-list">
                    ${activities.map(activity => this.renderActivityItem(activity)).join('')}
                </div>
            `;
        },

        // 渲染单个活动项
        renderActivityItem(activity) {
            const { type, title, description, time, status } = activity;

            const iconMap = {
                import: '📥',
                review: '📊',
                error: '❌',
                info: 'ℹ️'
            };

            const icon = iconMap[type] || '📌';
            const statusClass = status || 'info';
            const iconClass = type === 'error' ? 'error' : (type === 'review' ? 'review' : 'import');

            return `
                <div class="activity-item">
                    <div class="activity-item-icon ${iconClass}">${icon}</div>
                    <div class="activity-item-content">
                        <div class="activity-item-title">${this.escapeHtml(title)}</div>
                        <div class="activity-item-meta">
                            <span>${this.escapeHtml(description)}</span>
                            <span>•</span>
                            <span>${time}</span>
                            ${status && status !== 'info' ? `
                                <span class="activity-item-status ${statusClass}">
                                    ${this.getStatusLabel(status)}
                                </span>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        },

        // 格式化统计数据
        formatStats(stats) {
            return {
                monthlyIncome: stats.monthlyIncome || 0,
                monthlyExpense: stats.monthlyExpense || 0,
                netBalance: stats.netBalance || 0,
                transactionCount: stats.transactionCount || 0,
                incomeTrend: stats.incomeTrend !== null ? stats.incomeTrend / stats.monthlyIncome || 0 : null,
                expenseTrend: stats.expenseTrend !== null ? stats.expenseTrend / stats.monthlyExpense || 0 : null
            };
        },

        // 格式化活动数据
        formatActivities(activities) {
            return activities.map(activity => ({
                type: activity.type || 'info',
                title: activity.title || '未知活动',
                description: activity.description || '',
                time: activity.time || '刚刚',
                status: activity.status || 'info'
            }));
        },

        // 手动刷新
        async handleManualRefresh() {
            if (this.isLoading) return;

            // 添加旋转动画
            this.refreshBtn?.classList.add('refreshing');

            try {
                await this.loadData();
                this.showToast('数据已刷新', 'success');
            } catch (error) {
                this.showToast('刷新失败', 'error');
            } finally {
                setTimeout(() => {
                    this.refreshBtn?.classList.remove('refreshing');
                }, 500);
            }
        },

        // 自动刷新
        startAutoRefresh() {
            // 清除现有的定时器
            if (this.autoRefreshTimer) {
                clearInterval(this.autoRefreshTimer);
            }

            // 设置新的定时器
            this.autoRefreshTimer = setInterval(() => {
                // 仅当页面可见时自动刷新
                if (!document.hidden) {
                    console.log('[DashboardView] Auto refreshing...');
                    this.loadData().catch(error => {
                        console.error('[DashboardView] Auto refresh failed:', error);
                    });
                }
            }, this.refreshInterval);
        },

        // 停止自动刷新
        stopAutoRefresh() {
            if (this.autoRefreshTimer) {
                clearInterval(this.autoRefreshTimer);
                this.autoRefreshTimer = null;
            }
        },

        // 销毁
        destroy() {
            console.log('[DashboardView] Destroying...');
            this.stopAutoRefresh();
            if (this.container) {
                this.container.innerHTML = '';
            }
        },

        // ============================================
        // 工具方法
        // ============================================

        // 格式化货币
        formatCurrency(amount) {
            if (amount === null || amount === undefined || isNaN(amount)) return '¥0.00';
            return new Intl.NumberFormat('zh-CN', {
                style: 'currency',
                currency: 'CNY',
                minimumFractionDigits: 2
            }).format(amount);
        },

        // HTML转义
        escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        // 获取状态标签
        getStatusLabel(status) {
            const labels = {
                success: '成功',
                error: '失败',
                pending: '处理中',
                info: ''
            };
            return labels[status] || '';
        },

        // 显示Toast
        showToast(message, type = 'success') {
            if (window.Utils && window.Utils.showToast) {
                window.Utils.showToast(message, type);
            } else {
                console.log(`[Toast] ${type}: ${message}`);
            }
        }
    };

    // ============================================
    // 导出
    // ============================================

    console.log('[DashboardView] Module loaded');
})();
