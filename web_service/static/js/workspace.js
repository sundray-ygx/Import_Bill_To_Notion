/**
 * ============================================
 * 财务工作空间 - 完整版应用逻辑
 * SPA架构，整合所有功能模块
 * ============================================
 */

(function() {
    'use strict';

    // ============================================
    // 应用状态管理
    // ============================================

    const AppState = {
        currentView: 'dashboard',
        user: null,
        isLoading: false,
        sidebarCollapsed: false,
        data: {
            stats: null,
            activity: [],
            bills: [],
            reviews: [],
            history: [],
            uploadedFiles: []
        }
    };

    // ============================================
    // DOM 元素缓存（优化性能）
    // ============================================

    const DOM = {
        // 容器
        viewsContainer: null,
        toastContainer: null,
        modalContainer: null,

        // 仪表板
        statsElements: {},
        activityList: null,

        // 账单上传
        uploadForm: null,
        fileInput: null,
        uploadArea: null,
        fileListBody: null,
        bulkActionsBar: null,

        // 历史记录
        historyItems: null,
        historyFilters: {},

        // 复盘
        reviewPreview: null,
        reviewList: null
    };

    // ============================================
    // 工具函数
    // ============================================

    const Utils = {
        // 显示 Toast 消息
        showToast(message, type = 'success', duration = 3000) {
            const container = DOM.toastContainer || document.getElementById('toast-container');
            if (!container) return;

            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `
                <div class="toast-content">
                    <span class="toast-icon">${this.getToastIcon(type)}</span>
                    <span class="toast-message">${this.escapeHtml(message)}</span>
                </div>
            `;

            container.appendChild(toast);

            // 自动移除
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100px)';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        },

        getToastIcon(type) {
            const icons = {
                success: '✓',
                error: '✕',
                warning: '⚠',
                info: 'ℹ'
            };
            return icons[type] || icons.info;
        },

        // HTML 转义
        escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        // 格式化货币
        formatCurrency(amount) {
            if (amount === null || amount === undefined) return '¥0.00';
            return new Intl.NumberFormat('zh-CN', {
                style: 'currency',
                currency: 'CNY',
                minimumFractionDigits: 2
            }).format(amount);
        },

        // 格式化文件大小
        formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        },

        // 格式化日期（使用 DateTimeUtils 如果可用）
        formatDate(dateStr) {
            return window.DateTimeUtils ?
                window.DateTimeUtils.formatDate(dateStr) :
                dateStr || '-';
        },

        formatDateTime(dateStr) {
            return window.DateTimeUtils ?
                window.DateTimeUtils.formatDateTime(dateStr) :
                dateStr || '-';
        },

        formatFullDateTime(dateStr) {
            return window.DateTimeUtils ?
                window.DateTimeUtils.formatFullDateTime(dateStr) :
                dateStr || '-';
        },

        // 获取平台图标
        getPlatformIcon(platform) {
            const icons = {
                alipay: '💰',
                wechat: '💚',
                unionpay: '💳'
            };
            return icons[platform] || '📄';
        },

        // 获取平台标签
        getPlatformLabel(platform) {
            const labels = {
                alipay: '支付宝',
                wechat: '微信支付',
                unionpay: '银联'
            };
            return labels[platform] || platform || '未知';
        },

        // 获取状态标签
        getStatusLabel(status) {
            const labels = {
                pending: '待处理',
                processing: '处理中',
                success: '成功',
                completed: '已完成',
                failed: '失败'
            };
            return labels[status] || status || '未知';
        },

        // 获取状态图标
        getStatusIcon(status) {
            const icons = {
                success: '✅',
                completed: '✅',
                failed: '❌',
                pending: '⏳',
                processing: '⏳'
            };
            return icons[status] || '📌';
        },

        // 防抖函数（性能优化）
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // 显示加载状态
        showLoading(container, message = '加载中...') {
            if (typeof container === 'string') {
                container = document.getElementById(container);
            }
            if (!container) return;

            container.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>${message}</p>
                </div>
            `;
        },

        // 显示空状态
        showEmpty(container, message, icon = '📭', action = null) {
            if (typeof container === 'string') {
                container = document.getElementById(container);
            }
            if (!container) return;

            let actionHtml = '';
            if (action) {
                actionHtml = `<button class="empty-action-btn" data-action="${action.action}">${action.label}</button>`;
            }

            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">${icon}</div>
                    <p>${message}</p>
                    ${actionHtml}
                </div>
            `;
        },

        // 显示错误状态
        showError(container, message, hint = null) {
            if (typeof container === 'string') {
                container = document.getElementById(container);
            }
            if (!container) return;

            container.innerHTML = `
                <div class="error-state">
                    <div class="error-state-icon">⚠️</div>
                    <p>${message}</p>
                    ${hint ? `<p class="error-hint">${hint}</p>` : ''}
                </div>
            `;
        }
    };

    // ============================================
    // 账单上传模块 (Bills)
    // ============================================

    const BillsModule = {
        selectedFileIds: new Set(),
        currentFilters: {
            status: '',
            platform: ''
        },

        // 初始化
        init() {
            // 先注入HTML内容
            this.injectContent();
            // 然后初始化各个模块
            this.initUploadForm();
            this.initFilters();
            this.initBulkActions();
            this.loadFiles();
        },

        // 注入HTML内容
        injectContent() {
            const viewContainer = document.getElementById('view-bills');
            if (!viewContainer) return;

            // 如果内容已经注入过，就跳过
            if (viewContainer.querySelector('.upload-section')) return;

            viewContainer.innerHTML = `
                <div class="bills-view-container">
                    <!-- 上传区域 -->
                    <div class="upload-section">
                        <div class="upload-card">
                            <div class="upload-card-header">
                                <h2>上传账单</h2>
                            </div>
                            <form id="upload-form" enctype="multipart/form-data">
                                <div class="upload-form-content">
                                    <div class="form-group">
                                        <label for="file" class="form-label required">选择账单文件</label>
                                        <div class="file-input-wrapper">
                                            <input type="file" id="file" name="file" accept=".csv,.txt,.xls,.xlsx" required>
                                            <div class="file-input-label" id="file-label" tabindex="0">
                                                <svg class="file-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                                    <polyline points="14 2 14 8 20 8"/>
                                                    <line x1="16" y1="13" x2="8" y2="13"/>
                                                    <line x1="16" y1="17" x2="8" y2="17"/>
                                                    <polyline points="10 9 9 9 8 9"/>
                                                </svg>
                                                <span class="file-text">点击选择或拖拽文件到这里</span>
                                            </div>
                                        </div>
                                        <div class="form-hint">支持格式：CSV, TXT, XLS, XLSX（最大50MB）</div>
                                    </div>

                                    <div class="form-group">
                                        <label for="platform" class="form-label">账单平台（可选）</label>
                                        <select id="platform" name="platform" class="form-input">
                                            <option value="">自动检测</option>
                                            <option value="alipay">支付宝</option>
                                            <option value="wechat">微信支付</option>
                                            <option value="unionpay">银联</option>
                                        </select>
                                    </div>

                                    <button type="submit" class="btn btn-primary" id="upload-btn">
                                        <span class="btn-text">上传账单</span>
                                    </button>
                                </div>

                                <div id="progress" class="upload-progress" style="display: none;">
                                    <div class="progress-bar-bg">
                                        <div class="progress-bar-fill" style="width: 0%;"></div>
                                    </div>
                                    <div class="progress-text">正在处理... 0%</div>
                                </div>

                                <div id="result" class="upload-result" style="display: none;"></div>
                            </form>
                        </div>
                    </div>

                    <!-- 文件列表区域 -->
                    <div class="files-section">
                        <div class="section-header">
                            <h3>已上传文件</h3>
                            <div class="section-actions">
                                <button class="btn btn-secondary btn-sm" id="refresh-files-btn">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0118.8-4.3M22 12.5a10 10 0 01-18.8 4.2"/>
                                    </svg>
                                    刷新
                                </button>
                            </div>
                        </div>

                        <div id="files-loading" class="loading-state" style="display: none;">
                            <div class="loading-spinner"></div>
                            <p>加载文件列表中...</p>
                        </div>

                        <div id="files-list" class="files-list">
                            <!-- 文件列表将在这里动态加载 -->
                        </div>

                        <div id="files-empty" class="empty-state" style="display: none;">
                            <div class="empty-icon">📁</div>
                            <h3>还没有上传文件</h3>
                            <p>上传您的第一个账单文件开始使用</p>
                        </div>
                    </div>
                </div>
            `;
        },

        // 初始化上传表单
        initUploadForm() {
            const form = document.getElementById('upload-form');
            const fileInput = document.getElementById('file');
            const fileLabel = document.getElementById('file-label');
            const uploadArea = document.getElementById('upload-area');

            if (!form) return;

            // 拖拽上传
            if (uploadArea) {
                ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                    uploadArea.addEventListener(eventName, (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                    });
                });

                ['dragenter', 'dragover'].forEach(eventName => {
                    uploadArea.addEventListener(eventName, () => {
                        uploadArea.classList.add('drag-over');
                    });
                });

                ['dragleave', 'drop'].forEach(eventName => {
                    uploadArea.addEventListener(eventName, () => {
                        uploadArea.classList.remove('drag-over');
                    });
                });

                uploadArea.addEventListener('drop', (e) => {
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        fileInput.files = files;
                        this.handleFileSelect(files[0]);
                    }
                });
            }

            // 文件选择
            if (fileInput) {
                fileInput.addEventListener('change', () => {
                    if (fileInput.files.length > 0) {
                        this.handleFileSelect(fileInput.files[0]);
                    }
                });
            }

            // 点击文件标签触发文件选择
            if (fileLabel && fileInput) {
                fileLabel.addEventListener('click', () => {
                    fileInput.click();
                });
            }

            // 表单提交
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleUpload();
            });
        },

        // 处理文件选择
        handleFileSelect(file) {
            const fileLabel = document.getElementById('file-label');
            if (fileLabel) {
                fileLabel.innerHTML = `
                    <span class="file-icon">📄</span>
                    <span class="file-text">${Utils.escapeHtml(file.name)}</span>
                `;
            }
        },

        // 处理上传
        async handleUpload() {
            const fileInput = document.getElementById('file');
            const platformSelect = document.getElementById('platform');
            const uploadBtn = document.getElementById('upload-btn');
            const progress = document.getElementById('progress');
            const result = document.getElementById('result');

            const file = fileInput.files[0];
            if (!file) {
                Utils.showToast('请选择文件', 'error');
                return;
            }

            // 验证文件大小（50MB）
            if (file.size > 50 * 1024 * 1024) {
                Utils.showToast('文件大小不能超过 50MB', 'error');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('platform', platformSelect.value);

            // 显示加载状态
            uploadBtn.disabled = true;
            uploadBtn.querySelector('.btn-text').style.display = 'none';
            uploadBtn.querySelector('.btn-loading').style.display = 'inline';
            progress.style.display = 'block';
            result.style.display = 'none';

            try {
                const response = await window.Auth.apiRequest('/api/bills/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                progress.style.display = 'none';
                result.style.display = 'block';

                if (response.ok) {
                    result.className = 'upload-result success';
                    result.innerHTML = `
                        <div class="result-icon">✓</div>
                        <div class="result-message">${Utils.escapeHtml(data.message || '上传成功')}</div>
                    `;
                    Utils.showToast('账单上传成功！');
                    this.loadFiles();

                    // 清空表单
                    fileInput.value = '';
                    document.getElementById('file-label').innerHTML = `
                        <span class="file-icon">📄</span>
                        <span class="file-text">点击选择或拖拽文件到这里</span>
                    `;
                } else {
                    result.className = 'upload-result error';
                    result.innerHTML = `
                        <div class="result-icon">✕</div>
                        <div class="result-message">${Utils.escapeHtml(data.detail || '上传失败')}</div>
                    `;
                    Utils.showToast(data.detail || '上传失败', 'error');
                }
            } catch (error) {
                console.error('Upload error:', error);
                progress.style.display = 'none';
                result.style.display = 'block';
                result.className = 'upload-result error';
                result.innerHTML = `
                    <div class="result-icon">✕</div>
                    <div class="result-message">网络错误，请检查连接</div>
                `;
                Utils.showToast('网络错误', 'error');
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.querySelector('.btn-text').style.display = 'inline';
                uploadBtn.querySelector('.btn-loading').style.display = 'none';
            }
        },

        // 加载文件列表
        async loadFiles() {
            const tableBody = document.getElementById('file-list-body');
            if (!tableBody) return;

            Utils.showLoading(tableBody, '加载文件列表...');

            try {
                const response = await window.Auth.apiRequest('/api/bills/uploads');

                if (response.ok) {
                    const data = await response.json();
                    AppState.data.uploadedFiles = data.files || [];
                    this.renderFileList();
                } else if (response.status === 401) {
                    window.location.href = '/login';
                } else {
                    throw new Error('加载失败');
                }
            } catch (error) {
                console.error('Failed to load files:', error);
                Utils.showError(tableBody, '加载失败', '请检查网络连接或刷新页面重试');
            }
        },

        // 渲染文件列表
        renderFileList() {
            const tableBody = document.getElementById('file-list-body');
            if (!tableBody) return;

            let files = AppState.data.uploadedFiles;

            // 应用过滤
            files = files.filter(file => {
                const matchStatus = !this.currentFilters.status || file.status === this.currentFilters.status;
                const matchPlatform = !this.currentFilters.platform || file.platform === this.currentFilters.platform;
                return matchStatus && matchPlatform;
            });

            if (files.length === 0) {
                Utils.showEmpty(tableBody, '还没有上传任何账单', '📭', {
                    action: 'upload',
                    label: '上传第一个账单'
                });
                this.clearSelection();
                return;
            }

            tableBody.innerHTML = files.map(file => {
                const isPendingOrFailed = file.status === 'pending' || file.status === 'failed';
                const importButton = isPendingOrFailed ? `
                    <button class="btn-action btn-import" data-action="import" data-file-id="${file.id}" title="导入到Notion">
                        <span class="action-icon">📥</span>
                        <span class="action-text">导入</span>
                    </button>
                ` : '';

                return `
                <tr class="file-row" data-file-id="${file.id}">
                    <td class="col-select">
                        <input type="checkbox" class="file-select-checkbox" data-file-id="${file.id}">
                    </td>
                    <td class="col-platform">
                        <span class="platform-badge ${file.platform}">
                            <span class="platform-icon">${Utils.getPlatformIcon(file.platform)}</span>
                            <span class="platform-name">${Utils.getPlatformLabel(file.platform)}</span>
                        </span>
                    </td>
                    <td class="col-filename">
                        <div class="filename-cell" title="${Utils.escapeHtml(file.file_name)}">
                            <span class="filename-text">${Utils.escapeHtml(file.file_name)}</span>
                        </div>
                    </td>
                    <td class="col-original-name">
                        <div class="filename-cell" title="${Utils.escapeHtml(file.original_file_name)}">
                            <span class="filename-text filename-original">${Utils.escapeHtml(file.original_file_name)}</span>
                        </div>
                    </td>
                    <td class="col-size">
                        <span class="size-text">${Utils.formatFileSize(file.file_size)}</span>
                    </td>
                    <td class="col-status">
                        <span class="status-badge ${file.status}">
                            ${Utils.getStatusLabel(file.status)}
                        </span>
                    </td>
                    <td class="col-created">
                        <span class="date-text">${Utils.formatDateTime(file.created_at)}</span>
                    </td>
                    <td class="col-actions">
                        <div class="action-buttons">
                            ${importButton}
                            <button class="btn-action btn-view" data-action="view" data-file-id="${file.id}" title="查看详情">
                                <span class="action-icon">👁</span>
                            </button>
                            <button class="btn-action btn-content" data-action="content" data-file-id="${file.id}" title="查看内容">
                                <span class="action-icon">📋</span>
                            </button>
                            <button class="btn-action btn-delete" data-action="delete" data-file-id="${file.id}" title="删除">
                                <span class="action-icon">🗑</span>
                            </button>
                        </div>
                    </td>
                </tr>
                `;
            }).join('');

            this.bindActionButtons();
            this.bindCheckboxEvents();
        },

        // 绑定操作按钮事件
        bindActionButtons() {
            document.querySelectorAll('.btn-action[data-action]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const fileId = parseInt(btn.dataset.fileId);
                    const action = btn.dataset.action;

                    switch (action) {
                        case 'view':
                            await this.showFileDetail(fileId);
                            break;
                        case 'content':
                            await this.showFileContent(fileId);
                            break;
                        case 'import':
                            await this.importFile(fileId);
                            break;
                        case 'delete':
                            await this.deleteFile(fileId);
                            break;
                    }
                });
            });
        },

        // 显示文件详情
        async showFileDetail(fileId) {
            try {
                const response = await window.Auth.apiRequest(`/api/bills/uploads/${fileId}`);

                if (response.ok) {
                    const data = await response.json();
                    Modal.showDetail(data);
                } else {
                    Utils.showToast('加载详情失败', 'error');
                }
            } catch (error) {
                console.error('Failed to load file detail:', error);
                Utils.showToast('加载详情失败', 'error');
            }
        },

        // 显示文件内容（CSV预览）
        async showFileContent(fileId) {
            try {
                const response = await window.Auth.apiRequest(`/api/bills/uploads/${fileId}/preview?max_rows=500`);

                if (response.ok) {
                    const data = await response.json();
                    Modal.showContentPreview(data);
                } else {
                    Utils.showToast('加载内容失败', 'error');
                }
            } catch (error) {
                console.error('Failed to load file content:', error);
                Utils.showToast('加载内容失败', 'error');
            }
        },

        // 导入文件到Notion
        async importFile(fileId) {
            const confirm = window.confirm('确定要将此账单导入到 Notion 吗？');
            if (!confirm) return;

            try {
                const response = await window.Auth.apiRequest(`/api/bills/uploads/${fileId}/import`, {
                    method: 'POST'
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.status === 'already_imported') {
                        Utils.showToast('此文件已经导入过了', 'warning');
                    } else if (data.success) {
                        Utils.showToast(`导入成功！共导入 ${data.imported || 0} 条记录`);
                        this.showReviewBanner();
                    } else {
                        Utils.showToast(data.message || '导入失败', 'error');
                    }
                    this.loadFiles();
                } else {
                    const data = await response.json();
                    Utils.showToast(data.detail || '导入失败', 'error');
                }
            } catch (error) {
                console.error('Import error:', error);
                Utils.showToast('网络错误', 'error');
            }
        },

        // 删除文件
        async deleteFile(fileId) {
            const confirm = window.confirm('确定要删除这个文件吗？此操作不可撤销！');
            if (!confirm) return;

            try {
                const response = await window.Auth.apiRequest(`/api/bills/uploads/${fileId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    Utils.showToast('文件已删除');
                    this.loadFiles();
                } else {
                    const data = await response.json();
                    Utils.showToast(data.detail || '删除失败', 'error');
                }
            } catch (error) {
                console.error('Failed to delete file:', error);
                Utils.showToast('网络错误', 'error');
            }
        },

        // 初始化过滤器
        initFilters() {
            const statusFilter = document.getElementById('status-filter-select');
            const platformFilter = document.getElementById('platform-filter-select');
            const clearFiltersBtn = document.getElementById('clear-filters-btn');

            const debouncedRender = Utils.debounce(() => this.renderFileList(), 100);

            if (statusFilter) {
                statusFilter.addEventListener('change', () => {
                    this.currentFilters.status = statusFilter.value;
                    debouncedRender();
                });
            }

            if (platformFilter) {
                platformFilter.addEventListener('change', () => {
                    this.currentFilters.platform = platformFilter.value;
                    debouncedRender();
                });
            }

            if (clearFiltersBtn) {
                clearFiltersBtn.addEventListener('click', () => {
                    this.currentFilters = { status: '', platform: '' };
                    if (statusFilter) statusFilter.value = '';
                    if (platformFilter) platformFilter.value = '';
                    this.renderFileList();
                });
            }
        },

        // 绑定复选框事件
        bindCheckboxEvents() {
            document.querySelectorAll('.file-select-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    const fileId = parseInt(e.target.dataset.fileId);
                    if (e.target.checked) {
                        this.selectedFileIds.add(fileId);
                    } else {
                        this.selectedFileIds.delete(fileId);
                    }
                    this.updateBulkActionsBar();
                    this.updateSelectAllCheckbox();
                });
            });
        },

        // 更新批量操作栏
        updateBulkActionsBar() {
            const bulkActionsBar = document.getElementById('bulk-actions-bar');
            const selectedCount = document.getElementById('selected-count');

            if (this.selectedFileIds.size > 0) {
                bulkActionsBar.style.display = 'flex';
                selectedCount.textContent = this.selectedFileIds.size;
            } else {
                bulkActionsBar.style.display = 'none';
            }
        },

        // 更新全选复选框
        updateSelectAllCheckbox() {
            const selectAllCheckbox = document.getElementById('select-all-checkbox');
            const tableSelectAll = document.getElementById('table-select-all');
            const visibleCheckboxes = document.querySelectorAll('.file-select-checkbox');
            const checkedCount = document.querySelectorAll('.file-select-checkbox:checked').length;

            const state = checkedCount === 0 ? 'unchecked' :
                          checkedCount === visibleCheckboxes.length ? 'checked' : 'indeterminate';

            [selectAllCheckbox, tableSelectAll].forEach(checkbox => {
                if (checkbox) {
                    checkbox.checked = state === 'checked';
                    checkbox.indeterminate = state === 'indeterminate';
                }
            });
        },

        // 清空选择
        clearSelection() {
            this.selectedFileIds.clear();
            document.querySelectorAll('.file-select-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
            this.updateBulkActionsBar();
            this.updateSelectAllCheckbox();
        },

        // 初始化批量操作
        initBulkActions() {
            const selectAllCheckbox = document.getElementById('select-all-checkbox');
            const tableSelectAll = document.getElementById('table-select-all');
            const bulkImportBtn = document.getElementById('bulk-import-btn');
            const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
            const cancelSelectionBtn = document.getElementById('cancel-selection-btn');

            const toggleHandler = () => {
                const visibleCheckboxes = document.querySelectorAll('.file-select-checkbox');
                const selectAll = selectAllCheckbox || tableSelectAll;

                visibleCheckboxes.forEach(checkbox => {
                    checkbox.checked = selectAll.checked;
                    const fileId = parseInt(checkbox.dataset.fileId);
                    if (selectAll.checked) {
                        this.selectedFileIds.add(fileId);
                    } else {
                        this.selectedFileIds.delete(fileId);
                    }
                });
                this.updateBulkActionsBar();
            };

            if (selectAllCheckbox) selectAllCheckbox.addEventListener('change', toggleHandler);
            if (tableSelectAll) tableSelectAll.addEventListener('change', toggleHandler);

            if (bulkImportBtn) {
                bulkImportBtn.addEventListener('click', () => this.bulkImportFiles());
            }

            if (bulkDeleteBtn) {
                bulkDeleteBtn.addEventListener('click', () => this.bulkDeleteFiles());
            }

            if (cancelSelectionBtn) {
                cancelSelectionBtn.addEventListener('click', () => this.clearSelection());
            }
        },

        // 批量导入
        async bulkImportFiles() {
            if (this.selectedFileIds.size === 0) {
                Utils.showToast('请先选择要导入的文件', 'warning');
                return;
            }

            const selectedFiles = AppState.data.uploadedFiles.filter(f =>
                this.selectedFileIds.has(f.id) && f.status === 'pending'
            );

            if (selectedFiles.length === 0) {
                Utils.showToast('选中的文件中没有待处理的文件', 'warning');
                return;
            }

            const count = selectedFiles.length;
            if (!confirm(`确定要批量导入 ${count} 个文件吗？`)) return;

            Utils.showToast(`开始批量导入 ${count} 个文件，请稍候...`);

            let successCount = 0;
            let failCount = 0;

            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                Utils.showToast(`正在导入 (${i + 1}/${count}): ${file.original_file_name || file.file_name}`);

                try {
                    const response = await window.Auth.apiRequest(`/api/bills/uploads/${file.id}/import`, {
                        method: 'POST'
                    });

                    if (response && response.ok) {
                        successCount++;
                    } else {
                        failCount++;
                    }
                } catch (error) {
                    failCount++;
                }

                await new Promise(resolve => setTimeout(resolve, 500));
            }

            this.clearSelection();
            await this.loadFiles();

            const resultMsg = `批量导入完成！成功: ${successCount} 个，失败: ${failCount} 个`;
            if (failCount === 0) {
                Utils.showToast(resultMsg, 'success');
            } else if (successCount === 0) {
                Utils.showToast(resultMsg, 'error');
            } else {
                Utils.showToast(resultMsg, 'warning');
            }
        },

        // 批量删除
        async bulkDeleteFiles() {
            if (this.selectedFileIds.size === 0) {
                Utils.showToast('请先选择要删除的文件', 'warning');
                return;
            }

            const count = this.selectedFileIds.size;
            if (!confirm(`确定要删除选中的 ${count} 个文件吗？此操作不可撤销！`)) return;

            try {
                const response = await window.Auth.apiRequest('/api/bills/uploads/batch-delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ upload_ids: Array.from(this.selectedFileIds) })
                });

                if (response.ok) {
                    const data = await response.json();
                    Utils.showToast(data.message || `成功删除 ${count} 个文件`);
                    this.clearSelection();
                    this.loadFiles();
                } else {
                    const data = await response.json();
                    Utils.showToast(data.detail || '批量删除失败', 'error');
                }
            } catch (error) {
                console.error('Bulk delete error:', error);
                Utils.showToast('网络错误', 'error');
            }
        },

        // 显示复盘Banner
        showReviewBanner() {
            const banner = document.getElementById('review-banner');
            if (banner) {
                banner.style.display = 'block';
                banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
    };

    // ============================================
    // 历史记录模块 (History)
    // ============================================

    const HistoryModule = {
        currentPage: 1,
        pageSize: 10,
        totalItems: 0,
        totalPages: 0,
        currentFilters: {
            search: '',
            status: '',
            platform: '',
            start_date: '',
            end_date: ''
        },
        selectedHistoryIds: new Set(),
        allHistory: [],

        // 初始化
        init() {
            // 先注入HTML内容
            this.injectContent();
            // 然后初始化各个模块
            this.initSearch();
            this.initFilters();
            this.initPagination();
            this.initBulkActions();
            this.loadStats();
            this.loadHistory();
        },

        // 注入HTML内容
        injectContent() {
            const viewContainer = document.getElementById('view-history');
            if (!viewContainer) return;

            // 如果内容已经注入过，就跳过
            if (viewContainer.querySelector('.history-view-container')) return;

            viewContainer.innerHTML = `
                <div class="history-view-container">
                    <!-- 统计卡片 -->
                    <div class="history-stats-grid">
                        <div class="stat-card">
                            <div class="stat-card__header">
                                <h3 class="stat-card__title">总导入次数</h3>
                                <span class="stat-card__icon">📊</span>
                            </div>
                            <div class="stat-card__value" id="stat-total">0</div>
                            <div class="stat-card__footer">
                                <span class="stat-card__label">累计导入</span>
                            </div>
                        </div>

                        <div class="stat-card">
                            <div class="stat-card__header">
                                <h3 class="stat-card__title">成功导入</h3>
                                <span class="stat-card__icon success">✓</span>
                            </div>
                            <div class="stat-card__value" id="stat-success">0</div>
                            <div class="stat-card__footer">
                                <span class="stat-card__label">成功次数</span>
                            </div>
                        </div>

                        <div class="stat-card">
                            <div class="stat-card__header">
                                <h3 class="stat-card__title">失败次数</h3>
                                <span class="stat-card__icon error">✕</span>
                            </div>
                            <div class="stat-card__value" id="stat-failed">0</div>
                            <div class="stat-card__footer">
                                <span class="stat-card__label">失败次数</span>
                            </div>
                        </div>

                        <div class="stat-card">
                            <div class="stat-card__header">
                                <h3 class="stat-card__title">总记录数</h3>
                                <span class="stat-card__icon">📝</span>
                            </div>
                            <div class="stat-card__value" id="stat-records">0</div>
                            <div class="stat-card__footer">
                                <span class="stat-card__label">成功记录</span>
                            </div>
                        </div>
                    </div>

                    <!-- 过滤器 -->
                    <div class="history-filters">
                        <div class="filter-row">
                            <input type="text" id="search-input" class="form-input" placeholder="搜索文件名...">
                            <select id="status-filter" class="form-input">
                                <option value="">全部状态</option>
                                <option value="success">成功</option>
                                <option value="failed">失败</option>
                                <option value="partial">部分成功</option>
                            </select>
                            <select id="platform-filter" class="form-input">
                                <option value="">全部平台</option>
                                <option value="alipay">支付宝</option>
                                <option value="wechat">微信支付</option>
                                <option value="unionpay">银联</option>
                            </select>
                        </div>
                        <div class="filter-row">
                            <input type="date" id="start-date" class="form-input" placeholder="开始日期">
                            <input type="date" id="end-date" class="form-input" placeholder="结束日期">
                            <button id="clear-date-filter" class="btn btn-secondary btn-sm">清除日期</button>
                            <button id="clear-all-filters" class="btn btn-secondary btn-sm">清除全部</button>
                        </div>
                    </div>

                    <!-- 历史记录表格 -->
                    <div class="history-table-wrapper">
                        <div id="history-loading" class="loading-state" style="display: none;">
                            <div class="loading-spinner"></div>
                            <p>加载中...</p>
                        </div>

                        <table class="table" id="history-table" style="display: none;">
                            <thead>
                                <tr>
                                    <th><input type="checkbox" id="select-all-history"></th>
                                    <th>文件名</th>
                                    <th>平台</th>
                                    <th>状态</th>
                                    <th>记录数</th>
                                    <th>时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="history-tbody">
                                <!-- 历史记录将在这里动态加载 -->
                            </tbody>
                        </table>

                        <div id="history-empty" class="empty-state" style="display: none;">
                            <div class="empty-icon">📋</div>
                            <h3>暂无导入记录</h3>
                            <p>上传您的第一个账单文件开始使用</p>
                        </div>
                    </div>

                    <!-- 分页 -->
                    <div class="pagination-wrapper">
                        <div class="pagination-info">
                            <span id="pagination-info">显示 0-0 共 0 条</span>
                        </div>
                        <div class="pagination-controls">
                            <button class="btn btn-secondary btn-sm" id="prev-page" ${'disabled'}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="15 18 9 12 15 6"/>
                                    <polyline points="9 18 3 12 9 6"/>
                                </svg>
                                上一页
                            </button>
                            <span id="page-numbers" class="page-numbers"></span>
                            <button class="btn btn-secondary btn-sm" id="next-page" ${'disabled'}>
                                下一页
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="9 18 15 12 9 6"/>
                                    <polyline points="3 18 9 12 3 6"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        },

        // 初始化搜索
        initSearch() {
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                const debouncedSearch = Utils.debounce(() => {
                    this.currentFilters.search = searchInput.value;
                    this.renderHistory();
                }, 300);

                searchInput.addEventListener('input', debouncedSearch);
            }
        },

        // 初始化过滤器
        initFilters() {
            const statusFilter = document.getElementById('status-filter');
            const platformFilter = document.getElementById('platform-filter');
            const startDateInput = document.getElementById('start-date');
            const endDateInput = document.getElementById('end-date');
            const clearDateBtn = document.getElementById('clear-date-filter');
            const clearAllBtn = document.getElementById('clear-all-filters');

            if (statusFilter) {
                statusFilter.addEventListener('change', () => {
                    this.currentFilters.status = statusFilter.value;
                    this.renderHistory();
                });
            }

            if (platformFilter) {
                platformFilter.addEventListener('change', () => {
                    this.currentFilters.platform = platformFilter.value;
                    this.renderHistory();
                });
            }

            if (startDateInput) {
                startDateInput.addEventListener('change', () => {
                    this.currentFilters.start_date = startDateInput.value;
                    this.currentPage = 1;
                    this.loadHistory();
                });
            }

            if (endDateInput) {
                endDateInput.addEventListener('change', () => {
                    this.currentFilters.end_date = endDateInput.value;
                    this.currentPage = 1;
                    this.loadHistory();
                });
            }

            if (clearDateBtn) {
                clearDateBtn.addEventListener('click', () => {
                    if (startDateInput) startDateInput.value = '';
                    if (endDateInput) endDateInput.value = '';
                    this.currentFilters.start_date = '';
                    this.currentFilters.end_date = '';
                    this.currentPage = 1;
                    this.loadHistory();
                });
            }

            if (clearAllBtn) {
                clearAllBtn.addEventListener('click', () => {
                    this.currentFilters = {
                        search: '', status: '', platform: '', start_date: '', end_date: ''
                    };
                    if (statusFilter) statusFilter.value = '';
                    if (platformFilter) platformFilter.value = '';
                    if (startDateInput) startDateInput.value = '';
                    if (endDateInput) endDateInput.value = '';
                    const searchInput = document.getElementById('search-input');
                    if (searchInput) searchInput.value = '';
                    this.currentPage = 1;
                    this.loadHistory();
                });
            }
        },

        // 初始化分页
        initPagination() {
            const prevPageBtn = document.getElementById('prev-page');
            const nextPageBtn = document.getElementById('next-page');

            if (prevPageBtn) {
                prevPageBtn.addEventListener('click', () => {
                    if (this.currentPage > 1) {
                        this.currentPage--;
                        this.loadHistory();
                    }
                });
            }

            if (nextPageBtn) {
                nextPageBtn.addEventListener('click', () => {
                    if (this.currentPage < this.totalPages) {
                        this.currentPage++;
                        this.loadHistory();
                    }
                });
            }
        },

        // 初始化批量操作
        initBulkActions() {
            const selectAllCheckbox = document.getElementById('select-all-checkbox');
            const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
            const cancelSelectionBtn = document.getElementById('cancel-selection-btn');

            if (selectAllCheckbox) {
                selectAllCheckbox.addEventListener('change', () => {
                    const visibleCheckboxes = document.querySelectorAll('.history-select-checkbox');
                    visibleCheckboxes.forEach(checkbox => {
                        checkbox.checked = selectAllCheckbox.checked;
                        const historyId = parseInt(checkbox.dataset.historyId);
                        if (selectAllCheckbox.checked) {
                            this.selectedHistoryIds.add(historyId);
                        } else {
                            this.selectedHistoryIds.delete(historyId);
                        }
                    });
                    this.updateBulkActionsBar();
                });
            }

            if (bulkDeleteBtn) {
                bulkDeleteBtn.addEventListener('click', () => this.bulkDeleteHistory());
            }

            if (cancelSelectionBtn) {
                cancelSelectionBtn.addEventListener('click', () => this.clearSelection());
            }
        },

        // 加载统计数据
        async loadStats() {
            try {
                const response = await window.Auth.apiRequest('/api/bills/history/stats');
                if (response.ok) {
                    const stats = await response.json();

                    const totalImports = document.getElementById('total-imports');
                    const successfulImports = document.getElementById('successful-imports');
                    const totalRecords = document.getElementById('total-records');
                    const avgDuration = document.getElementById('avg-duration');

                    if (totalImports) totalImports.textContent = stats.total || 0;
                    if (successfulImports) successfulImports.textContent = stats.successful || 0;
                    if (totalRecords) totalRecords.textContent = stats.total_records || 0;
                    if (avgDuration) avgDuration.textContent = stats.avg_duration ?
                        `${Math.round(stats.avg_duration)}秒` : '-';
                }
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        },

        // 加载历史记录
        async loadHistory() {
            const historyItems = document.getElementById('history-items');
            if (!historyItems) return;

            Utils.showLoading(historyItems, '加载历史记录...');

            try {
                const params = new URLSearchParams({
                    page: this.currentPage,
                    page_size: this.pageSize
                });

                if (this.currentFilters.start_date) {
                    params.append('start_date', this.currentFilters.start_date);
                }
                if (this.currentFilters.end_date) {
                    params.append('end_date', this.currentFilters.end_date);
                }

                const response = await window.Auth.apiRequest(`/api/bills/history?${params}`);

                if (response.ok) {
                    const data = await response.json();
                    this.allHistory = data.history || [];
                    this.totalItems = data.total || 0;
                    this.totalPages = Math.ceil(this.totalItems / this.pageSize);

                    this.renderHistory();
                    this.updatePagination();
                } else if (response.status === 401) {
                    window.location.href = '/login';
                } else {
                    throw new Error('加载失败');
                }
            } catch (error) {
                console.error('Failed to load history:', error);
                Utils.showError(historyItems, '加载失败，请刷新页面重试');
            }
        },

        // 渲染历史记录
        renderHistory() {
            const historyItems = document.getElementById('history-items');
            if (!historyItems) return;

            // 应用筛选
            let filteredHistory = this.allHistory.filter(item => {
                const fileName = item.original_file_name || item.file_name || '';
                const matchSearch = !this.currentFilters.search ||
                    fileName.toLowerCase().includes(this.currentFilters.search.toLowerCase()) ||
                    item.platform?.toLowerCase().includes(this.currentFilters.search.toLowerCase());

                const matchStatus = !this.currentFilters.status || item.status === this.currentFilters.status;
                const matchPlatform = !this.currentFilters.platform || item.platform === this.currentFilters.platform;

                return matchSearch && matchStatus && matchPlatform;
            });

            if (filteredHistory.length === 0) {
                Utils.showEmpty(historyItems, '暂无导入记录');
                this.clearSelection();
                return;
            }

            historyItems.innerHTML = filteredHistory.map(item => `
                <div class="history-item" data-history-id="${item.id}">
                    <div class="history-checkbox">
                        <input type="checkbox" class="history-select-checkbox" data-history-id="${item.id}">
                    </div>
                    <div class="history-item-icon ${item.platform}">
                        ${Utils.getPlatformIcon(item.platform)}
                    </div>
                    <div class="history-item-content">
                        <div class="history-item-title">${Utils.escapeHtml(item.original_file_name || item.file_name || '未知文件')}</div>
                        <div class="history-item-meta">
                            <span class="history-item-meta-item">📅 ${Utils.formatDate(item.started_at)}</span>
                            <span class="history-item-meta-item">⏱ ${item.duration_seconds ? item.duration_seconds + '秒' : '-'}</span>
                        </div>
                    </div>
                    <div class="history-item-status">
                        <span class="status-badge ${item.status}">
                            ${Utils.getStatusLabel(item.status)}
                        </span>
                        <div class="history-item-stats">
                            <span>${item.imported_records || 0}/${item.total_records || 0} 条</span>
                        </div>
                    </div>
                    <div class="history-item-actions">
                        <button class="action-btn action-btn-view" data-action="view" data-history-id="${item.id}" title="查看详情">
                            <span>👁</span>
                        </button>
                        <button class="action-btn action-btn-delete" data-action="delete" data-history-id="${item.id}" title="删除">
                            <span>🗑</span>
                        </button>
                    </div>
                </div>
            `).join('');

            this.bindHistoryItemEvents();
        },

        // 绑定历史记录项事件
        bindHistoryItemEvents() {
            const historyItems = document.getElementById('history-items');
            if (!historyItems) return;

            historyItems.addEventListener('change', (e) => {
                if (e.target.classList.contains('history-select-checkbox')) {
                    const historyId = parseInt(e.target.dataset.historyId);
                    if (e.target.checked) {
                        this.selectedHistoryIds.add(historyId);
                    } else {
                        this.selectedHistoryIds.delete(historyId);
                    }
                    this.updateBulkActionsBar();
                    this.updateSelectAllCheckbox();
                    e.stopPropagation();
                }
            });

            historyItems.addEventListener('click', (e) => {
                const actionBtn = e.target.closest('.action-btn');
                if (actionBtn) {
                    e.stopPropagation();
                    const historyId = parseInt(actionBtn.dataset.historyId);
                    const action = actionBtn.dataset.action;

                    if (action === 'view') {
                        this.showDetail(historyId);
                    } else if (action === 'delete') {
                        this.deleteHistoryItem(historyId);
                    }
                    return;
                }

                const historyItem = e.target.closest('.history-item');
                if (historyItem && !e.target.closest('.history-checkbox') && !e.target.closest('.history-item-actions')) {
                    const historyId = parseInt(historyItem.dataset.historyId);
                    this.showDetail(historyId);
                }
            });
        },

        // 显示详情
        showDetail(historyId) {
            const item = this.allHistory.find(h => h.id === historyId);
            if (!item) return;

            const detailHtml = `
                <div class="detail-section">
                    <h3>基本信息</h3>
                    <div class="detail-row">
                        <span class="detail-label">文件名：</span>
                        <span class="detail-value">${Utils.escapeHtml(item.original_file_name || item.file_name || '-')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">平台：</span>
                        <span class="detail-value">${Utils.getPlatformLabel(item.platform)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">状态：</span>
                        <span class="detail-value">
                            <span class="status-badge ${item.status}">
                                ${Utils.getStatusLabel(item.status)}
                            </span>
                        </span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">开始时间：</span>
                        <span class="detail-value">${Utils.formatFullDateTime(item.started_at)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">完成时间：</span>
                        <span class="detail-value">${item.completed_at ? Utils.formatFullDateTime(item.completed_at) : '-'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">耗时：</span>
                        <span class="detail-value">${item.duration_seconds ? item.duration_seconds + ' 秒' : '-'}</span>
                    </div>
                </div>

                <div class="detail-section">
                    <h3>导入统计</h3>
                    <div class="detail-stat-grid">
                        <div class="detail-stat-card">
                            <div class="detail-stat-value">${item.total_records || 0}</div>
                            <div class="detail-stat-label">总记录数</div>
                        </div>
                        <div class="detail-stat-card">
                            <div class="detail-stat-value">${item.imported_records || 0}</div>
                            <div class="detail-stat-label">成功导入</div>
                        </div>
                        <div class="detail-stat-card">
                            <div class="detail-stat-value">${item.skipped_records || 0}</div>
                            <div class="detail-stat-label">跳过记录</div>
                        </div>
                        <div class="detail-stat-card">
                            <div class="detail-stat-value">${item.failed_records || 0}</div>
                            <div class="detail-stat-label">失败记录</div>
                        </div>
                    </div>
                </div>

                ${item.error_message ? `
                <div class="detail-section">
                    <h3>错误信息</h3>
                    <div class="error-message">${Utils.escapeHtml(item.error_message)}</div>
                </div>
                ` : ''}
            `;

            Modal.show('导入详情', detailHtml);
        },

        // 删除单条记录
        async deleteHistoryItem(historyId) {
            const confirm = window.confirm('确定要删除这条记录吗？此操作不可撤销！');
            if (!confirm) return;

            try {
                const response = await window.Auth.apiRequest(`/api/bills/history/${historyId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    Utils.showToast('记录已删除');
                    this.loadHistory();
                    this.loadStats();
                } else {
                    const data = await response.json();
                    Utils.showToast(data.detail || '删除失败', 'error');
                }
            } catch (error) {
                console.error('Delete error:', error);
                Utils.showToast('网络错误', 'error');
            }
        },

        // 批量删除
        async bulkDeleteHistory() {
            if (this.selectedHistoryIds.size === 0) {
                Utils.showToast('请先选择要删除的记录', 'warning');
                return;
            }

            const count = this.selectedHistoryIds.size;
            if (!confirm(`确定要删除选中的 ${count} 条记录吗？此操作不可撤销！`)) return;

            try {
                const response = await window.Auth.apiRequest('/api/bills/history/batch-delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ history_ids: Array.from(this.selectedHistoryIds) })
                });

                if (response.ok) {
                    const data = await response.json();
                    Utils.showToast(data.message || `成功删除 ${count} 条记录`);
                    this.clearSelection();
                    this.loadHistory();
                    this.loadStats();
                } else {
                    const data = await response.json();
                    Utils.showToast(data.detail || '批量删除失败', 'error');
                }
            } catch (error) {
                console.error('Bulk delete error:', error);
                Utils.showToast('网络错误', 'error');
            }
        },

        // 更新批量操作栏
        updateBulkActionsBar() {
            const bulkActionsBar = document.getElementById('bulk-actions-bar');
            const selectedCount = document.getElementById('selected-count');

            if (this.selectedHistoryIds.size > 0) {
                bulkActionsBar.style.display = 'flex';
                selectedCount.textContent = this.selectedHistoryIds.size;
            } else {
                bulkActionsBar.style.display = 'none';
            }
        },

        // 更新全选复选框
        updateSelectAllCheckbox() {
            const selectAllCheckbox = document.getElementById('select-all-checkbox');
            const visibleCheckboxes = document.querySelectorAll('.history-select-checkbox');
            const checkedCount = document.querySelectorAll('.history-select-checkbox:checked').length;

            if (visibleCheckboxes.length > 0 && checkedCount === visibleCheckboxes.length) {
                selectAllCheckbox.checked = true;
                selectAllCheckbox.indeterminate = false;
            } else if (checkedCount > 0) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = true;
            } else {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
            }
        },

        // 清空选择
        clearSelection() {
            this.selectedHistoryIds.clear();
            document.querySelectorAll('.history-select-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
            this.updateBulkActionsBar();
            this.updateSelectAllCheckbox();
        },

        // 更新分页
        updatePagination() {
            const prevPageBtn = document.getElementById('prev-page');
            const nextPageBtn = document.getElementById('next-page');
            const paginationPages = document.getElementById('pagination-pages');

            if (prevPageBtn) prevPageBtn.disabled = this.currentPage <= 1;
            if (nextPageBtn) nextPageBtn.disabled = this.currentPage >= this.totalPages;

            if (!paginationPages) return;

            let pages = [];
            pages.push(1);

            const start = Math.max(2, this.currentPage - 1);
            const end = Math.min(this.totalPages - 1, this.currentPage + 1);

            if (start > 2) pages.push('...');

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            if (end < this.totalPages - 1) pages.push('...');

            if (this.totalPages > 1) pages.push(this.totalPages);

            paginationPages.innerHTML = pages.map(p => {
                if (p === '...') {
                    return '<span class="pagination-ellipsis">...</span>';
                }
                return `
                    <button class="pagination-page ${p === this.currentPage ? 'active' : ''}" data-page="${p}">
                        ${p}
                    </button>
                `;
            }).join('');

            paginationPages.querySelectorAll('.pagination-page[data-page]').forEach(btn => {
                btn.addEventListener('click', () => {
                    this.currentPage = parseInt(btn.dataset.page);
                    this.loadHistory();
                });
            });
        }
    };

    // ============================================
    // 复盘模块 (Review)
    // ============================================

    const ReviewModule = {
        currentPreview: null,
        reviewType: 'monthly',

        // 注入HTML内容
        injectContent() {
            const viewContainer = document.getElementById('view-review');
            if (!viewContainer) return;
            if (viewContainer.querySelector('.review-view-container')) return;

            viewContainer.innerHTML = `
                <div class="review-view-container">
                    <!-- Notion 连接状态仪表板 -->
                    <div class="connection-dashboard" id="connection-dashboard">
                        <!-- 左侧：核心状态面板 -->
                        <div class="status-core-panel">
                            <div class="status-indicator-wrapper" id="status-indicator-wrapper">
                                <div class="status-ring">
                                    <svg class="status-pulse" id="status-pulse" width="60" height="60" viewBox="0 0 80 80">
                                        <circle cx="40" cy="40" r="36" fill="none" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                                        <circle class="pulse-ring" cx="40" cy="40" r="36" fill="none" stroke="currentColor" stroke-width="2"/>
                                        <circle class="status-dot" cx="40" cy="40" r="8" fill="currentColor"/>
                                    </svg>
                                </div>
                            </div>
                            <div class="status-core-info">
                                <h2 class="status-core-title">Notion 连接</h2>
                                <p class="status-core-status" id="status-core-status">检查中...</p>
                            </div>
                        </div>

                        <!-- 中间：数据库配置网格 -->
                        <div class="databases-grid">
                            <div class="database-section">
                                <div class="database-section-header">
                                    <h3 class="database-section-title">账单数据库</h3>
                                </div>
                                <div class="database-items" id="income-database-status">
                                    <div class="database-item">
                                        <span class="database-label">收入数据库</span>
                                        <span class="database-status-badge checking">检查中...</span>
                                    </div>
                                    <div class="database-item">
                                        <span class="database-label">支出数据库</span>
                                        <span class="database-status-badge checking">检查中...</span>
                                    </div>
                                </div>
                            </div>

                            <div class="database-section">
                                <div class="database-section-header">
                                    <h3 class="database-section-title">复盘数据库</h3>
                                </div>
                                <div class="database-items" id="review-databases-status">
                                    <div class="database-item">
                                        <span class="database-label">月度复盘</span>
                                        <span class="database-status-badge checking">检查中...</span>
                                    </div>
                                    <div class="database-item">
                                        <span class="database-label">季度复盘</span>
                                        <span class="database-status-badge checking">检查中...</span>
                                    </div>
                                    <div class="database-item">
                                        <span class="database-label">年度复盘</span>
                                        <span class="database-status-badge checking">检查中...</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 右侧：操作面板 -->
                        <div class="status-actions-panel">
                            <button class="action-btn" id="test-connection-btn" disabled>
                                <span>测试连接</span>
                            </button>
                        </div>
                    </div>

                    <!-- 复盘创建区域 -->
                    <div class="create-review-section">
                        <div class="section-header">
                            <h2 class="section-title">创建复盘报告</h2>
                            <p class="section-subtitle">选择时间周期和复盘类型，智能生成分析报告</p>
                        </div>

                        <div class="create-form-card">
                            <div class="form-grid">
                                <!-- 复盘类型 -->
                                <div class="form-field-group">
                                    <label class="form-label">
                                        复盘类型
                                        <span class="required">*</span>
                                    </label>
                                    <div class="type-selector" id="review-type-selector">
                                        <button class="type-option active" data-type="monthly">
                                            <span class="type-name">月度复盘</span>
                                        </button>
                                        <button class="type-option" data-type="quarterly">
                                            <span class="type-name">季度复盘</span>
                                        </button>
                                        <button class="type-option" data-type="yearly">
                                            <span class="type-name">年度复盘</span>
                                        </button>
                                        <button class="type-option" data-type="custom">
                                            <span class="type-name">自定义</span>
                                        </button>
                                    </div>
                                    <input type="hidden" id="review-type" value="monthly">
                                </div>

                                <!-- 复盘标题和状态 -->
                                <div class="form-row">
                                    <div class="form-field">
                                        <label class="form-label" for="review-title">
                                            复盘标题
                                            <span class="optional">(可选)</span>
                                        </label>
                                        <input type="text" id="review-title" class="form-input" placeholder="留空自动生成">
                                    </div>
                                    <div class="form-field">
                                        <label class="form-label" for="review-status">
                                            状态
                                        </label>
                                        <select id="review-status" class="form-select">
                                            <option value="计划中">计划中</option>
                                            <option value="进行中">进行中</option>
                                            <option value="完成">完成</option>
                                        </select>
                                    </div>
                                </div>

                                <!-- 日期范围 -->
                                <div class="form-field-group date-range-group">
                                    <label class="form-label">
                                        时间周期
                                        <span class="required">*</span>
                                    </label>
                                    <div class="date-range-inputs">
                                        <div class="date-field">
                                            <label class="date-label">开始日期</label>
                                            <input type="date" id="start-date" class="form-input date-input" required>
                                        </div>
                                        <div class="date-separator">→</div>
                                        <div class="date-field">
                                            <label class="date-label">结束日期</label>
                                            <input type="date" id="end-date" class="form-input date-input" required>
                                        </div>
                                    </div>
                                </div>

                                <!-- 生成按钮 -->
                                <div class="form-actions">
                                    <button class="btn-generate" id="generate-preview-btn">
                                        <span class="btn-text">生成预览</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 进度条模态框 -->
                    <div class="progress-modal" id="progress-modal" style="display: none;">
                        <div class="progress-backdrop"></div>
                        <div class="progress-container">
                            <div class="progress-content">
                                <div class="progress-spinner">
                                    <svg class="spinner" width="48" height="48" viewBox="0 0 48 48">
                                        <circle cx="24" cy="24" r="20" fill="none" stroke="currentColor" stroke-width="3" opacity="0.2"/>
                                        <circle cx="24" cy="24" r="20" fill="none" stroke="url(#spinner-gradient)" stroke-width="3" stroke-dasharray="125.6" stroke-dashoffset="31.4">
                                            <animateTransform attributeName="transform" type="rotate" from="0 24 24" to="360 24 24" dur="1.5s" repeatCount="indefinite"/>
                                        </circle>
                                        <defs>
                                            <linearGradient id="spinner-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                                <stop offset="0%" stop-color="#667eea"/>
                                                <stop offset="100%" stop-color="#764ba2"/>
                                            </linearGradient>
                                        </defs>
                                    </svg>
                                </div>
                                <h3 class="progress-title" id="progress-title">正在生成预览...</h3>
                                <p class="progress-description" id="progress-description">请稍候，正在处理您的数据</p>

                                <!-- 进度步骤 -->
                                <div class="progress-steps">
                                    <div class="progress-step" id="step-fetch">
                                        <div class="step-indicator">
                                            <div class="step-icon">📥</div>
                                        </div>
                                        <div class="step-content">
                                            <span class="step-title">查询交易数据</span>
                                            <span class="step-status">等待中...</span>
                                        </div>
                                    </div>

                                    <div class="progress-step" id="step-calculate">
                                        <div class="step-indicator">
                                            <div class="step-icon">📊</div>
                                        </div>
                                        <div class="step-content">
                                            <span class="step-title">计算统计分析</span>
                                            <span class="step-status">等待中...</span>
                                        </div>
                                    </div>

                                    <div class="progress-step" id="step-generate">
                                        <div class="step-indicator">
                                            <div class="step-icon">📝</div>
                                        </div>
                                        <div class="step-content">
                                            <span class="step-title">生成复盘内容</span>
                                            <span class="step-status">等待中...</span>
                                        </div>
                                    </div>

                                    <div class="progress-step" id="step-complete">
                                        <div class="step-indicator">
                                            <div class="step-icon">✓</div>
                                        </div>
                                        <div class="step-content">
                                            <span class="step-title">完成</span>
                                            <span class="step-status">等待中...</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 预览编辑区域 -->
                    <div class="preview-section" id="preview-section" style="display: none;">
                        <div class="preview-header">
                            <div class="preview-header-left">
                                <h2 class="preview-title">复盘预览</h2>
                                <p class="preview-subtitle">您可以在提交前编辑以下内容</p>
                            </div>
                            <button class="btn-close-preview" id="close-preview-btn">
                                ✕ 关闭预览
                            </button>
                        </div>

                        <div class="preview-layout">
                            <!-- 左侧：属性编辑面板 -->
                            <div class="attributes-panel">
                                <div class="panel-header">
                                    <h3 class="panel-title">页面属性</h3>
                                    <span class="panel-badge">可编辑</span>
                                </div>

                                <div class="attributes-list">
                                    <!-- 基本属性 -->
                                    <div class="attributes-section">
                                        <div class="attributes-section-title">基本信息</div>

                                        <div class="attribute-group">
                                            <label class="attribute-label">标题 *</label>
                                            <input type="text" id="attr-title" class="attribute-input" placeholder="复盘报告标题">
                                        </div>

                                        <div class="attribute-row">
                                            <div class="attribute-group half">
                                                <label class="attribute-label">开始日期 *</label>
                                                <input type="date" id="attr-start-date" class="attribute-input">
                                            </div>
                                            <div class="attribute-group half">
                                                <label class="attribute-label">结束日期 *</label>
                                                <input type="date" id="attr-end-date" class="attribute-input">
                                            </div>
                                        </div>

                                        <div class="attribute-group">
                                            <label class="attribute-label">状态</label>
                                            <select id="attr-status" class="attribute-select">
                                                <option value="计划中">计划中</option>
                                                <option value="进行中">进行中</option>
                                                <option value="完成">完成</option>
                                            </select>
                                        </div>

                                        <div class="attribute-group">
                                            <label class="attribute-label">周期 (Period)</label>
                                            <input type="text" id="attr-period" class="attribute-input" placeholder="如：2026-01">
                                        </div>
                                    </div>

                                    <!-- 财务数据卡片 -->
                                    <div class="attributes-section">
                                        <div class="attributes-section-title">财务数据</div>

                                        <div class="finance-summary">
                                            <div class="finance-item income">
                                                <div class="finance-label">总收入</div>
                                                <div class="finance-value">¥<span id="attr-total-income">0.00</span></div>
                                            </div>

                                            <div class="finance-item expense">
                                                <div class="finance-label">总支出</div>
                                                <div class="finance-value">¥<span id="attr-total-expense">0.00</span></div>
                                            </div>

                                            <div class="finance-item" id="net-balance-item">
                                                <div class="finance-label">净收益</div>
                                                <div class="finance-value">¥<span id="attr-net-balance">0.00</span></div>
                                            </div>

                                            <div class="finance-item transactions">
                                                <div class="finance-label">交易笔数</div>
                                                <div class="finance-value"><span id="attr-transaction-count">0</span> 笔</div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- 可选属性 -->
                                    <div class="attributes-section">
                                        <div class="attributes-section-title">附加信息（可选）</div>

                                        <div class="attribute-group">
                                            <label class="attribute-label">摘要 (Summary)</label>
                                            <textarea id="attr-summary" class="attribute-textarea" rows="2" placeholder="复盘摘要..."></textarea>
                                        </div>

                                        <div class="attribute-group">
                                            <label class="attribute-label">分类 (Categories)</label>
                                            <textarea id="attr-categories" class="attribute-textarea" rows="2" placeholder="分类信息..."></textarea>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 右侧：Markdown 编辑器 -->
                            <div class="markdown-panel">
                                <div class="panel-header">
                                    <h3 class="panel-title">复盘内容</h3>
                                    <span class="panel-hint">Markdown 格式</span>
                                </div>
                                <div class="markdown-editor-wrapper">
                                    <textarea id="markdown-editor" class="markdown-editor" spellcheck="false"
                                        placeholder="复盘内容将在此处显示..."></textarea>
                                </div>
                            </div>
                        </div>

                        <div class="preview-actions">
                            <button class="btn btn-secondary" id="preview-cancel-btn">
                                ✕ 取消
                            </button>
                            <button class="btn btn-success" id="submit-to-notion-btn">
                                ✓ 提交到 Notion
                            </button>
                        </div>
                    </div>
                </div>
            `;
        },

        // 初始化
        init() {
            this.injectContent();
            this.initDateInputs();
            this.initEventListeners();
            this.initTypeSelector();
            this.loadReviewHistory();
            this.checkNotionConnection();
        },

        // 初始化日期输入
        initDateInputs() {
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

            const startDateInput = document.getElementById('start-date');
            const endDateInput = document.getElementById('end-date');

            if (startDateInput) startDateInput.value = this.formatDateForInput(firstDay);
            if (endDateInput) endDateInput.value = this.formatDateForInput(lastDay);
        },

        // 初始化事件监听
        initEventListeners() {
            const generatePreviewBtn = document.getElementById('generate-preview-btn');
            const submitToNotionBtn = document.getElementById('submit-to-notion-btn');
            const closePreviewBtn = document.getElementById('close-preview-btn');
            const previewCancelBtn = document.getElementById('preview-cancel-btn');

            if (generatePreviewBtn) {
                generatePreviewBtn.addEventListener('click', () => this.generatePreview());
            }

            if (submitToNotionBtn) {
                submitToNotionBtn.addEventListener('click', () => this.submitToNotion());
            }

            if (closePreviewBtn) {
                closePreviewBtn.addEventListener('click', () => this.closePreview());
            }

            if (previewCancelBtn) {
                previewCancelBtn.addEventListener('click', () => this.closePreview());
            }
        },

        // 初始化类型选择器
        initTypeSelector() {
            const typeOptions = document.querySelectorAll('.type-option');
            const hiddenInput = document.getElementById('review-type');

            typeOptions.forEach(option => {
                option.addEventListener('click', () => {
                    typeOptions.forEach(opt => opt.classList.remove('active'));
                    option.classList.add('active');
                    hiddenInput.value = option.dataset.type;
                    this.onReviewTypeChange(option.dataset.type);
                });
            });
        },

        // 复盘类型变更
        onReviewTypeChange(reviewType) {
            this.reviewType = reviewType;

            const today = new Date();
            let startDate, endDate;

            switch (reviewType) {
                case 'monthly':
                    startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                    endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
                    break;
                case 'quarterly':
                    const currentQuarter = Math.floor(today.getMonth() / 3);
                    startDate = new Date(today.getFullYear(), currentQuarter * 3, 1);
                    endDate = new Date(today.getFullYear(), currentQuarter * 3 + 3, 0);
                    break;
                case 'yearly':
                    startDate = new Date(today.getFullYear(), 0, 1);
                    endDate = new Date(today.getFullYear(), 11, 31);
                    break;
                case 'custom':
                    return;
            }

            const startDateInput = document.getElementById('start-date');
            const endDateInput = document.getElementById('end-date');

            if (startDateInput) startDateInput.value = this.formatDateForInput(startDate);
            if (endDateInput) endDateInput.value = this.formatDateForInput(endDate);
        },

        // 检查 Notion 连接
        async checkNotionConnection() {
            const statusIndicator = document.getElementById('status-indicator-wrapper');
            const statusCoreStatus = document.getElementById('status-core-status');
            const testBtn = document.getElementById('test-connection-btn');

            if (!statusIndicator || !statusCoreStatus) return;

            statusIndicator.className = 'status-indicator-wrapper checking';
            statusCoreStatus.textContent = '检查中...';
            if (testBtn) testBtn.disabled = true;

            try {
                const response = await window.Auth.apiRequest('/api/review/test-connection');

                if (response.ok) {
                    const data = await response.json();
                    this.updateConnectionStatus(data);
                } else {
                    statusIndicator.className = 'status-indicator-wrapper error';
                    statusCoreStatus.textContent = '连接失败';
                    if (testBtn) testBtn.disabled = false;
                }
            } catch (error) {
                console.error('Connection check failed:', error);
                statusIndicator.className = 'status-indicator-wrapper error';
                statusCoreStatus.textContent = '连接失败';
                if (testBtn) testBtn.disabled = false;
            }
        },

        // 更新连接状态
        updateConnectionStatus(data) {
            const statusIndicator = document.getElementById('status-indicator-wrapper');
            const statusCoreStatus = document.getElementById('status-core-status');
            const testBtn = document.getElementById('test-connection-btn');

            if (!statusIndicator || !statusCoreStatus) return;

            if (data.api_key_valid === true) {
                statusIndicator.className = 'status-indicator-wrapper success';
                statusCoreStatus.textContent = '已连接';
                if (testBtn) testBtn.disabled = false;

                // 更新数据库状态
                this.updateDatabaseBadge('income-database-status', 0, data.income_db_valid, null, '已连接');
                this.updateDatabaseBadge('income-database-status', 1, data.expense_db_valid, null, '已连接');
                this.updateDatabaseBadge('review-databases-status', 0, data.monthly_review_db_valid, null, '已配置');
                this.updateDatabaseBadge('review-databases-status', 1, data.quarterly_review_db_valid, null, '已配置');
                this.updateDatabaseBadge('review-databases-status', 2, data.yearly_review_db_valid, null, '已配置');
            } else {
                statusIndicator.className = 'status-indicator-wrapper error';
                statusCoreStatus.textContent = '未连接';
                if (testBtn) testBtn.disabled = false;
            }
        },

        // 更新数据库徽章
        updateDatabaseBadge(containerId, index, isValid, errorMsg, defaultText) {
            const container = document.getElementById(containerId);
            if (!container) return;

            const items = container.querySelectorAll('.database-item');
            if (!items[index]) return;

            const badge = items[index].querySelector('.database-status-badge');

            if (isValid === true) {
                badge.className = 'database-status-badge valid';
                badge.textContent = defaultText || '已配置';
            } else if (isValid === false) {
                badge.className = 'database-status-badge invalid';
                badge.textContent = errorMsg || '未配置';
            } else {
                badge.className = 'database-status-badge';
                badge.textContent = '未配置';
            }
        },

        // 生成预览
        async generatePreview() {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            const reviewTitle = document.getElementById('review-title').value.trim();

            if (!startDate || !endDate) {
                Utils.showToast('请选择开始日期和结束日期', 'error');
                return;
            }

            if (new Date(startDate) > new Date(endDate)) {
                Utils.showToast('开始日期不能晚于结束日期', 'error');
                return;
            }

            // 显示进度
            this.showProgressModal();
            this.updateProgressStep('step-fetch', 'active', '正在查询交易数据...');

            try {
                let url = `/api/review/preview?start_date=${startDate}&end_date=${endDate}`;
                if (reviewTitle) {
                    url += `&review_title=${encodeURIComponent(reviewTitle)}`;
                }

                const response = await window.Auth.apiRequest(url);

                if (response.ok) {
                    this.updateProgressStep('step-fetch', 'completed', '查询完成');
                    this.updateProgressStep('step-calculate', 'active', '正在计算统计数据...');

                    await new Promise(resolve => setTimeout(resolve, 500));
                    this.updateProgressStep('step-calculate', 'completed', '计算完成');
                    this.updateProgressStep('step-generate', 'active', '正在生成复盘内容...');

                    const data = await response.json();

                    await new Promise(resolve => setTimeout(resolve, 500));
                    this.updateProgressStep('step-generate', 'completed', '生成完成');
                    this.updateProgressStep('step-complete', 'completed', '完成');

                    await new Promise(resolve => setTimeout(resolve, 500));
                    this.hideProgressModal();

                    if (data.success) {
                        this.currentPreview = data;
                        this.displayPreview(data);
                        Utils.showToast('预览生成成功', 'success');
                    } else {
                        Utils.showToast('生成预览失败: ' + (data.error || '未知错误'), 'error');
                    }
                } else {
                    this.hideProgressModal();
                    Utils.showToast('生成预览失败: ' + (response?.statusText || '网络错误'), 'error');
                }
            } catch (error) {
                console.error('Preview error:', error);
                this.hideProgressModal();
                Utils.showToast('生成预览失败: ' + error.message, 'error');
            }
        },

        // 显示预览
        displayPreview(data) {
            const { attributes, markdown_content } = data;

            if (!attributes || !markdown_content) {
                Utils.showToast('预览数据格式错误', 'error');
                return;
            }

            // 填充基本属性
            document.getElementById('attr-title').value = attributes.title || '';
            document.getElementById('attr-start-date').value = attributes.start_date || '';
            document.getElementById('attr-end-date').value = attributes.end_date || '';
            document.getElementById('attr-status').value = attributes.status || '计划中';

            const startDate = new Date(attributes.start_date);
            const period = `${startDate.getFullYear()}-${String(startDate.getMonth() + 1).padStart(2, '0')}`;
            document.getElementById('attr-period').value = period;

            document.getElementById('attr-total-income').textContent = Utils.formatCurrency(attributes.total_income);
            document.getElementById('attr-total-expense').textContent = Utils.formatCurrency(attributes.total_expense);
            document.getElementById('attr-net-balance').textContent = Utils.formatCurrency(attributes.net_balance);
            document.getElementById('attr-transaction-count').textContent = attributes.transaction_count || 0;

            const netBalanceItem = document.getElementById('net-balance-item');
            if (netBalanceItem) {
                netBalanceItem.classList.remove('positive', 'negative');
                if (attributes.net_balance >= 0) {
                    netBalanceItem.classList.add('positive');
                } else {
                    netBalanceItem.classList.add('negative');
                }
            }

            if (attributes.summary) {
                document.getElementById('attr-summary').value = attributes.summary;
            }
            if (attributes.categories) {
                document.getElementById('attr-categories').value = attributes.categories;
            }

            // 填充 Markdown
            const markdownEditor = document.getElementById('markdown-editor');
            if (markdownEditor) {
                markdownEditor.value = markdown_content;
            }

            // 显示预览区域
            const previewSection = document.getElementById('preview-section');
            if (previewSection) {
                previewSection.style.display = 'block';
                previewSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        },

        // 关闭预览
        closePreview() {
            const previewSection = document.getElementById('preview-section');
            if (previewSection) {
                previewSection.style.display = 'none';
            }
            this.currentPreview = null;
        },

        // 提交到 Notion
        async submitToNotion() {
            if (!this.currentPreview) {
                Utils.showToast('请先生成预览', 'error');
                return;
            }

            const attributes = {
                title: document.getElementById('attr-title').value,
                start_date: document.getElementById('attr-start-date').value,
                end_date: document.getElementById('attr-end-date').value,
                status: document.getElementById('attr-status').value,
                total_income: this.currentPreview.attributes.total_income,
                total_expense: this.currentPreview.attributes.total_expense,
                net_balance: this.currentPreview.attributes.net_balance,
                transaction_count: this.currentPreview.attributes.transaction_count
            };

            const markdownContent = document.getElementById('markdown-editor').value;

            // 显示提交模态框
            this.showSubmittingModal();
            this.resetSubmitProgress();

            try {
                this.updateSubmitProgressStep('submit-step-validate', 'active', '正在验证数据...');
                await new Promise(resolve => setTimeout(resolve, 200));

                if (!attributes.title || !attributes.start_date || !attributes.end_date) {
                    this.updateSubmitProgressStep('submit-step-validate', 'error', '数据验证失败');
                    Utils.showToast('请填写完整的必填字段', 'error');
                    await new Promise(resolve => setTimeout(resolve, 500));
                    this.hideSubmittingModal();
                    return;
                }

                this.updateSubmitProgressStep('submit-step-validate', 'completed', '验证完成');
                this.updateSubmitProgressStep('submit-step-create', 'active', '正在连接 Notion...');

                const submitData = {
                    review_type: this.reviewType,
                    attributes: attributes,
                    markdown_content: markdownContent
                };

                const response = await window.Auth.apiRequest('/api/review/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(submitData)
                }, 60000);

                if (!response) {
                    this.updateSubmitProgressStep('submit-step-create', 'error', '请求失败');
                    Utils.showToast('请求失败，请检查网络连接', 'error');
                    await new Promise(resolve => setTimeout(resolve, 500));
                    this.hideSubmittingModal();
                    return;
                }

                if (!response.ok) {
                    this.updateSubmitProgressStep('submit-step-create', 'error', '创建失败');
                    let errorText = response.statusText || '网络错误';
                    try {
                        const errorData = await response.json();
                        errorText = errorData.detail || errorData.error || errorText;
                    } catch (e) {}
                    Utils.showToast('提交失败: ' + errorText, 'error');
                    await new Promise(resolve => setTimeout(resolve, 500));
                    this.hideSubmittingModal();
                    return;
                }

                this.updateSubmitProgressStep('submit-step-create', 'completed', '页面创建完成');
                this.updateSubmitProgressStep('submit-step-content', 'active', '正在添加内容...');

                await new Promise(resolve => setTimeout(resolve, 300));
                this.updateSubmitProgressStep('submit-step-content', 'completed', '内容添加完成');
                this.updateSubmitProgressStep('submit-step-finalize', 'active', '正在完成...');

                const data = await response.json();

                await new Promise(resolve => setTimeout(resolve, 200));
                this.updateSubmitProgressStep('submit-step-finalize', 'completed', '完成');

                if (data.success) {
                    await new Promise(resolve => setTimeout(resolve, 300));
                    this.hideSubmittingModal();
                    this.showSuccessModal(attributes, data.url);
                    this.loadReviewHistory();
                } else {
                    this.updateSubmitProgressStep('submit-step-finalize', 'error', '失败');
                    Utils.showToast('提交失败: ' + (data.error || '未知错误'), 'error');
                    await new Promise(resolve => setTimeout(resolve, 500));
                    this.hideSubmittingModal();
                }
            } catch (error) {
                console.error('Submit error:', error);

                const activeStep = document.querySelector('.submit-progress-step.active');
                if (activeStep) {
                    this.updateSubmitProgressStep(activeStep.id, 'error', '请求失败');
                }

                let errorMsg = '未知错误';
                if (error.name === 'AbortError') {
                    errorMsg = '请求超时，请检查网络连接或稍后重试';
                } else if (error.message) {
                    errorMsg = error.message;
                }

                Utils.showToast('提交失败: ' + errorMsg, 'error');
                await new Promise(resolve => setTimeout(resolve, 1000));
                this.hideSubmittingModal();
            }
        },

        // 加载复盘历史
        async loadReviewHistory() {
            const reviewList = document.getElementById('review-history-list');
            if (!reviewList) return;

            Utils.showLoading(reviewList, '加载复盘历史...');

            try {
                const response = await window.Auth.apiRequest('/api/review/history');

                if (response.ok) {
                    const data = await response.json();
                    this.renderReviewHistory(data.reviews || []);
                } else {
                    Utils.showError(reviewList, '加载失败');
                }
            } catch (error) {
                console.error('Failed to load review history:', error);
                Utils.showError(reviewList, '加载失败');
            }
        },

        // 渲染复盘历史
        renderReviewHistory(reviews) {
            const reviewList = document.getElementById('review-history-list');
            if (!reviewList) return;

            if (reviews.length === 0) {
                Utils.showEmpty(reviewList, '暂无复盘记录', '📊', {
                    action: 'generate-review',
                    label: '生成第一个复盘'
                });
                return;
            }

            reviewList.innerHTML = reviews.map(item => `
                <div class="review-history-item">
                    <div class="review-history-icon">${this.getTypeIcon(item.type)}</div>
                    <div class="review-history-content">
                        <div class="review-history-title">${Utils.escapeHtml(item.name)}</div>
                        <div class="review-history-meta">
                            <span>📅 ${item.period}</span>
                            <span>💰 ${Utils.formatCurrency(item.total_income - item.total_expense)}</span>
                        </div>
                    </div>
                    <button class="review-history-btn" data-review-id="${item.id}" data-url="${item.url || ''}">
                        查看
                    </button>
                </div>
            `).join('');

            // 绑定查看按钮事件
            reviewList.querySelectorAll('.review-history-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const url = btn.dataset.url;
                    if (url) {
                        window.open(url, '_blank');
                    } else {
                        Utils.showToast('暂无链接', 'warning');
                    }
                });
            });
        },

        // 获取类型图标
        getTypeIcon(type) {
            const icons = {
                monthly: '📅',
                quarterly: '📊',
                yearly: '🎯'
            };
            return icons[type] || '📄';
        },

        // 显示进度模态框
        showProgressModal() {
            const modal = document.getElementById('progress-modal');
            if (modal) {
                modal.style.display = 'flex';
                this.resetProgressSteps();
            }
        },

        // 隐藏进度模态框
        hideProgressModal() {
            const modal = document.getElementById('progress-modal');
            if (modal) {
                modal.style.display = 'none';
            }
        },

        // 重置进度步骤
        resetProgressSteps() {
            const steps = ['step-fetch', 'step-calculate', 'step-generate', 'step-complete'];
            steps.forEach((stepId) => {
                const step = document.getElementById(stepId);
                if (step) {
                    step.classList.remove('active', 'completed');
                    step.querySelector('.step-status').textContent = '等待中...';
                }
            });
        },

        // 更新进度步骤
        updateProgressStep(stepId, status, statusText) {
            const step = document.getElementById(stepId);
            if (!step) return;

            step.classList.remove('active', 'completed');

            if (status === 'active') {
                step.classList.add('active');
                step.querySelector('.step-status').textContent = statusText || '处理中...';
            } else if (status === 'completed') {
                step.classList.add('completed');
                step.querySelector('.step-status').textContent = statusText || '完成';
            } else {
                step.querySelector('.step-status').textContent = statusText || '等待中...';
            }
        },

        // 显示提交中模态框
        showSubmittingModal() {
            const modal = document.getElementById('submitting-modal');
            if (modal) {
                modal.style.display = 'flex';
            }
        },

        // 隐藏提交中模态框
        hideSubmittingModal() {
            const modal = document.getElementById('submitting-modal');
            if (modal) {
                modal.style.display = 'none';
            }
        },

        // 重置提交进度
        resetSubmitProgress() {
            const steps = ['submit-step-validate', 'submit-step-create', 'submit-step-content', 'submit-step-finalize'];
            steps.forEach(stepId => {
                const step = document.getElementById(stepId);
                if (step) {
                    step.classList.remove('active', 'completed', 'error');
                    step.querySelector('.step-status').textContent = '等待中...';
                }
            });
        },

        // 更新提交进度步骤
        updateSubmitProgressStep(stepId, status, statusText) {
            const step = document.getElementById(stepId);
            if (!step) return;

            step.classList.remove('active', 'completed', 'error');

            if (status === 'active') {
                step.classList.add('active');
                step.querySelector('.step-status').textContent = statusText || '处理中...';
            } else if (status === 'completed') {
                step.classList.add('completed');
                step.querySelector('.step-status').textContent = statusText || '完成';
            } else if (status === 'error') {
                step.classList.add('error');
                step.querySelector('.step-status').textContent = statusText || '失败';
            } else {
                step.querySelector('.step-status').textContent = statusText || '等待中...';
            }
        },

        // 显示成功模态框
        showSuccessModal(attributes, notionPageUrl) {
            const detailsHtml = `
                <div class="result-item">
                    <span class="label">标题</span>
                    <span class="value">${Utils.escapeHtml(attributes.title)}</span>
                </div>
                <div class="result-item">
                    <span class="label">周期</span>
                    <span class="value">${attributes.start_date} 至 ${attributes.end_date}</span>
                </div>
                <div class="result-item">
                    <span class="label">收入</span>
                    <span class="value income">¥${Utils.formatCurrency(attributes.total_income)}</span>
                </div>
                <div class="result-item">
                    <span class="label">支出</span>
                    <span class="value expense">¥${Utils.formatCurrency(attributes.total_expense)}</span>
                </div>
                <div class="result-item">
                    <span class="label">净收益</span>
                    <span class="value ${attributes.net_balance >= 0 ? 'income' : 'expense'}">
                        ¥${Utils.formatCurrency(attributes.net_balance)}
                    </span>
                </div>
            `;

            const successDetails = document.getElementById('success-details');
            if (successDetails) {
                successDetails.innerHTML = detailsHtml;
            }

            const successModal = document.getElementById('success-modal');
            if (successModal) {
                successModal.style.display = 'flex';

                // 绑定查看按钮
                const successViewBtn = document.getElementById('success-view-btn');
                if (successViewBtn && notionPageUrl) {
                    successViewBtn.onclick = () => {
                        window.open(notionPageUrl, '_blank');
                    };
                }
            }
        },

        // 格式化日期为输入框格式
        formatDateForInput(date) {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        }
    };

    // ============================================
    // 设置模块 (Settings)
    // ============================================

    const SettingsModule = {
        currentSection: 'notion',

        // 初始化
        init() {
            this.initSidebarNav();
            this.loadSettingsSection('notion');
        },

        // 初始化侧边栏导航
        initSidebarNav() {
            document.querySelectorAll('.settings-nav-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const section = item.dataset.settingsTab;
                    if (section) {
                        this.loadSettingsSection(section);
                    }
                });
            });
        },

        // 加载设置部分
        async loadSettingsSection(sectionId) {
            this.currentSection = sectionId;

            // 更新导航高亮
            document.querySelectorAll('.settings-nav-item').forEach(item => {
                item.classList.remove('active');
                if (item.dataset.settingsTab === sectionId) {
                    item.classList.add('active');
                }
            });

            const contentContainer = document.getElementById('settings-content');
            if (!contentContainer) return;

            // 显示加载状态
            Utils.showLoading(contentContainer, '加载设置...');

            try {
                switch (sectionId) {
                    case 'notion':
                        await this.loadNotionSettings(contentContainer);
                        break;
                    case 'account':
                        await this.loadAccountSettings(contentContainer);
                        break;
                    case 'review':
                        await this.loadReviewSettings(contentContainer);
                        break;
                    default:
                        contentContainer.innerHTML = '<p>未知设置</p>';
                }
            } catch (error) {
                console.error('Failed to load settings section:', error);
                Utils.showError(contentContainer, '加载失败');
            }
        },

        // 加载 Notion 设置
        async loadNotionSettings(container) {
            try {
                const response = await window.Auth.apiRequest('/api/user/notion-config');

                if (response.ok) {
                    const config = await response.json();

                    container.innerHTML = `
                        <div class="settings-section">
                            <h3>Notion 集成配置</h3>

                            <div class="config-status-card">
                                <div class="status-indicator-wrapper ${config.is_verified ? 'success' : 'error'}">
                                    <div class="status-core-indicator">
                                        <div class="status-core-status">${config.is_verified ? '已验证' : '未验证'}</div>
                                    </div>
                                </div>
                                <div class="config-status-text">
                                    ${config.is_verified ? '您的 Notion 配置已验证通过' : '配置已保存，请验证配置'}
                                </div>
                                ${!config.is_verified ? '<button class="btn btn-primary" id="verify-config-btn">验证配置</button>' : ''}
                            </div>

                            <form id="notion-config-form">
                                <div class="form-group">
                                    <label for="config-name">配置名称</label>
                                    <input type="text" id="config-name" class="form-input" value="${config.config_name || '默认配置'}">
                                </div>

                                <div class="form-group">
                                    <label for="notion-api-key">Notion API 密钥</label>
                                    <div class="password-input-wrapper">
                                        <input type="password" id="notion-api-key" class="form-input"
                                            placeholder="${config.is_configured && config.notion_api_key ? '已配置密钥（留空则保持不变）' : '请输入Notion API密钥'}">
                                        <button type="button" class="toggle-password" id="toggle-api-key">👁</button>
                                    </div>
                                </div>

                                <div class="form-group">
                                    <label for="income-db-id">收入数据库 ID</label>
                                    <input type="text" id="income-db-id" class="form-input" value="${config.notion_income_database_id || ''}">
                                </div>

                                <div class="form-group">
                                    <label for="expense-db-id">支出数据库 ID</label>
                                    <input type="text" id="expense-db-id" class="form-input" value="${config.notion_expense_database_id || ''}">
                                </div>

                                <button type="submit" class="btn btn-primary">保存配置</button>
                            </form>
                        </div>
                    `;

                    this.initNotionConfigForm();
                } else {
                    throw new Error('加载配置失败');
                }
            } catch (error) {
                console.error('Failed to load Notion config:', error);
                Utils.showError(container, '加载配置失败');
            }
        },

        // 初始化 Notion 配置表单
        initNotionConfigForm() {
            const form = document.getElementById('notion-config-form');
            const toggleBtn = document.getElementById('toggle-api-key');
            const apiKeyInput = document.getElementById('notion-api-key');
            const verifyBtn = document.getElementById('verify-config-btn');

            if (toggleBtn && apiKeyInput) {
                toggleBtn.addEventListener('click', () => {
                    const type = apiKeyInput.getAttribute('type') === 'password' ? 'text' : 'password';
                    apiKeyInput.setAttribute('type', type);
                });
            }

            if (form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();

                    const apiKeyValue = apiKeyInput.value.trim();
                    const configData = {
                        notion_income_database_id: document.getElementById('income-db-id').value,
                        notion_expense_database_id: document.getElementById('expense-db-id').value,
                        config_name: document.getElementById('config-name').value
                    };

                    if (apiKeyValue) {
                        configData.notion_api_key = apiKeyValue;
                    }

                    try {
                        const response = await window.Auth.apiRequest('/api/user/notion-config', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(configData)
                        });

                        if (response.ok) {
                            Utils.showToast('配置已保存');
                            this.loadSettingsSection('notion');
                        } else {
                            const data = await response.json();
                            Utils.showToast(data.detail || '保存失败', 'error');
                        }
                    } catch (error) {
                        console.error('Config save error:', error);
                        Utils.showToast('网络错误', 'error');
                    }
                });
            }

            if (verifyBtn) {
                verifyBtn.addEventListener('click', async () => {
                    try {
                        verifyBtn.disabled = true;
                        verifyBtn.textContent = '验证中...';

                        const response = await window.Auth.apiRequest('/api/user/notion-config/verify', {
                            method: 'POST'
                        });

                        const data = await response.json();

                        if (data.success) {
                            Utils.showToast('配置验证成功');
                            this.loadSettingsSection('notion');
                        } else {
                            Utils.showToast(data.message || '配置验证失败', 'error');
                        }
                    } catch (error) {
                        console.error('Config verify error:', error);
                        Utils.showToast('网络错误', 'error');
                    } finally {
                        verifyBtn.disabled = false;
                        verifyBtn.textContent = '验证配置';
                    }
                });
            }
        },

        // 加载账户设置
        async loadAccountSettings(container) {
            try {
                const response = await window.Auth.apiRequest('/api/user/profile');

                if (response.ok) {
                    const profile = await response.json();

                    container.innerHTML = `
                        <div class="settings-section">
                            <h3>个人资料</h3>

                            <form id="profile-form">
                                <div class="form-group">
                                    <label for="profile-username">用户名</label>
                                    <input type="text" id="profile-username" class="form-input" value="${Utils.escapeHtml(profile.username)}" disabled>
                                    <small>用户名不能修改</small>
                                </div>

                                <div class="form-group">
                                    <label for="profile-email">邮箱</label>
                                    <input type="email" id="profile-email" class="form-input" value="${Utils.escapeHtml(profile.email || '')}">
                                </div>

                                <button type="submit" class="btn btn-primary">保存资料</button>
                            </form>

                            <div class="settings-divider"></div>

                            <h3>修改密码</h3>

                            <form id="password-form">
                                <div class="form-group">
                                    <label for="current-password">当前密码</label>
                                    <input type="password" id="current-password" class="form-input" required>
                                </div>

                                <div class="form-group">
                                    <label for="new-password">新密码</label>
                                    <div class="password-input-wrapper">
                                        <input type="password" id="new-password" class="form-input" required>
                                        <button type="button" class="toggle-password" data-target="new-password">👁</button>
                                    </div>
                                </div>

                                <div class="form-group">
                                    <label for="confirm-new-password">确认新密码</label>
                                    <input type="password" id="confirm-new-password" class="form-input" required>
                                </div>

                                <button type="submit" class="btn btn-primary">修改密码</button>
                            </form>

                            <div class="settings-divider"></div>

                            <h3>统计信息</h3>

                            <div class="stats-grid">
                                <div class="stat-item">
                                    <div class="stat-value">${profile.total_uploads || 0}</div>
                                    <div class="stat-label">上传次数</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">${profile.total_imports || 0}</div>
                                    <div class="stat-label">导入记录</div>
                                </div>
                            </div>
                        </div>
                    `;

                    this.initProfileForms();
                } else {
                    throw new Error('加载资料失败');
                }
            } catch (error) {
                console.error('Failed to load profile:', error);
                Utils.showError(container, '加载资料失败');
            }
        },

        // 初始化个人资料表单
        initProfileForms() {
            // 个人资料表单
            const profileForm = document.getElementById('profile-form');
            if (profileForm) {
                profileForm.addEventListener('submit', async (e) => {
                    e.preventDefault();

                    const email = document.getElementById('profile-email').value;

                    try {
                        const response = await window.Auth.apiRequest('/api/user/profile', {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email })
                        });

                        if (response.ok) {
                            Utils.showToast('资料已更新');
                        } else {
                            const data = await response.json();
                            Utils.showToast(data.detail || '更新失败', 'error');
                        }
                    } catch (error) {
                        console.error('Update error:', error);
                        Utils.showToast('网络错误', 'error');
                    }
                });
            }

            // 密码表单
            const passwordForm = document.getElementById('password-form');
            if (passwordForm) {
                passwordForm.addEventListener('submit', async (e) => {
                    e.preventDefault();

                    const currentPassword = document.getElementById('current-password').value;
                    const newPassword = document.getElementById('new-password').value;
                    const confirmPassword = document.getElementById('confirm-new-password').value;

                    if (newPassword !== confirmPassword) {
                        Utils.showToast('两次输入的密码不一致', 'error');
                        return;
                    }

                    try {
                        const response = await window.Auth.apiRequest('/api/auth/change-password', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                current_password: currentPassword,
                                new_password: newPassword
                            })
                        });

                        if (response.ok) {
                            Utils.showToast('密码已修改，请重新登录');
                            setTimeout(() => {
                                window.Auth.logout();
                            }, 1500);
                        } else {
                            const data = await response.json();
                            Utils.showToast(data.detail || '修改失败', 'error');
                        }
                    } catch (error) {
                        console.error('Password change error:', error);
                        Utils.showToast('网络错误', 'error');
                    }
                });
            }

            // 密码切换按钮
            document.querySelectorAll('.toggle-password').forEach(btn => {
                btn.addEventListener('click', () => {
                    const targetId = btn.dataset.target;
                    const input = document.getElementById(targetId);
                    if (input) {
                        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                        input.setAttribute('type', type);
                    }
                });
            });
        },

        // 加载复盘设置
        async loadReviewSettings(container) {
            try {
                const response = await window.Auth.apiRequest('/api/review/config');

                if (response.ok) {
                    const config = await response.json();

                    container.innerHTML = `
                        <div class="settings-section">
                            <h3>复盘配置</h3>

                            <form id="review-config-form">
                                <div class="form-group">
                                    <label for="monthly-review-db">月度复盘数据库 ID</label>
                                    <input type="text" id="monthly-review-db" class="form-input" value="${config.monthly_review_db || ''}">
                                </div>

                                <div class="form-group">
                                    <label for="monthly-template-id">月度复盘模板 ID（可选）</label>
                                    <input type="text" id="monthly-template-id" class="form-input" value="${config.monthly_template_id || ''}">
                                </div>

                                <div class="form-group">
                                    <label for="quarterly-review-db">季度复盘数据库 ID</label>
                                    <input type="text" id="quarterly-review-db" class="form-input" value="${config.quarterly_review_db || ''}">
                                </div>

                                <div class="form-group">
                                    <label for="quarterly-template-id">季度复盘模板 ID（可选）</label>
                                    <input type="text" id="quarterly-template-id" class="form-input" value="${config.quarterly_template_id || ''}">
                                </div>

                                <div class="form-group">
                                    <label for="yearly-review-db">年度复盘数据库 ID</label>
                                    <input type="text" id="yearly-review-db" class="form-input" value="${config.yearly_review_db || ''}">
                                </div>

                                <div class="form-group">
                                    <label for="yearly-template-id">年度复盘模板 ID（可选）</label>
                                    <input type="text" id="yearly-template-id" class="form-input" value="${config.yearly_template_id || ''}">
                                </div>

                                <button type="submit" class="btn btn-primary">保存配置</button>
                            </form>
                        </div>
                    `;

                    this.initReviewConfigForm();
                } else {
                    throw new Error('加载配置失败');
                }
            } catch (error) {
                console.error('Failed to load review config:', error);
                Utils.showError(container, '加载配置失败');
            }
        },

        // 初始化复盘配置表单
        initReviewConfigForm() {
            const form = document.getElementById('review-config-form');
            if (form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();

                    const configData = {
                        notion_monthly_review_db: document.getElementById('monthly-review-db').value,
                        notion_monthly_template_id: document.getElementById('monthly-template-id').value,
                        notion_quarterly_review_db: document.getElementById('quarterly-review-db').value,
                        notion_quarterly_template_id: document.getElementById('quarterly-template-id').value,
                        notion_yearly_review_db: document.getElementById('yearly-review-db').value,
                        notion_yearly_template_id: document.getElementById('yearly-template-id').value
                    };

                    try {
                        const response = await window.Auth.apiRequest('/api/review/config', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(configData)
                        });

                        if (response.ok) {
                            const data = await response.json();
                            Utils.showToast(data.message || '复盘配置已保存');
                        } else {
                            const data = await response.json();
                            Utils.showToast(data.detail || '保存失败', 'error');
                        }
                    } catch (error) {
                        console.error('Review config save error:', error);
                        Utils.showToast('网络错误', 'error');
                    }
                });
            }
        }
    };

    // ============================================
    // 模态框管理
    // ============================================

    const Modal = {
        show(title, content) {
            const modal = document.getElementById('detail-modal');
            const modalTitle = document.getElementById('modal-title');
            const modalBody = document.getElementById('modal-body-content');
            const modalClose = document.getElementById('modal-close');
            const modalOk = document.getElementById('modal-ok');
            const modalBackdrop = document.getElementById('modal-backdrop');

            if (!modal || !modalBody) return;

            if (modalTitle) modalTitle.textContent = title;
            modalBody.innerHTML = content;
            modal.style.display = 'flex';

            // 绑定关闭按钮
            const closeHandler = () => this.close();
            if (modalClose) modalClose.onclick = closeHandler;
            if (modalOk) modalOk.onclick = closeHandler;
            if (modalBackdrop) modalBackdrop.onclick = closeHandler;
        },

        showDetail(data) {
            const content = `
                <div class="detail-section">
                    <h3>文件信息</h3>
                    <div class="detail-row">
                        <span class="detail-label">文件名：</span>
                        <span class="detail-value">${Utils.escapeHtml(data.file_name)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">平台：</span>
                        <span class="detail-value">${Utils.getPlatformLabel(data.platform)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">状态：</span>
                        <span class="detail-value">
                            <span class="status-badge ${data.status}">
                                ${Utils.getStatusLabel(data.status)}
                            </span>
                        </span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">上传时间：</span>
                        <span class="detail-value">${Utils.formatDateTime(data.created_at)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">文件大小：</span>
                        <span class="detail-value">${Utils.formatFileSize(data.file_size)}</span>
                    </div>
                </div>
            `;

            this.show('账单详情', content);
        },

        showContentPreview(data) {
            let tableHtml = '';

            if (data.data && data.data.length > 0) {
                const columns = data.columns || [];
                tableHtml = `
                    <div class="preview-header">
                        <div class="preview-stats">
                            <span class="stat-item">
                                <span class="stat-icon">📊</span>
                                <span class="stat-text">共 ${data.total_records} 条记录</span>
                            </span>
                            <span class="stat-item">
                                <span class="stat-icon">🔍</span>
                                <span class="stat-text">显示前 ${data.preview_records} 条</span>
                            </span>
                            <span class="stat-item">
                                <span class="stat-icon">${Utils.getPlatformIcon(data.detected_platform || data.platform)}</span>
                                <span class="stat-text">${Utils.getPlatformLabel(data.detected_platform || data.platform)}</span>
                            </span>
                        </div>
                    </div>
                    <div class="table-container">
                        <table class="bill-table">
                            <thead>
                                <tr>
                                    <th class="col-index">#</th>
                                    ${columns.map(col => `<th>${Utils.escapeHtml(String(col))}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${data.data.map((record, index) => `
                                    <tr class="${index % 2 === 0 ? 'even-row' : 'odd-row'}">
                                        <td class="col-index">${index + 1}</td>
                                        ${columns.map(col => `
                                            <td>${Utils.escapeHtml(String(record[col] !== undefined && record[col] !== null ? record[col] : '-'))}</td>
                                        `).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            } else {
                tableHtml = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <p>暂无账单数据</p>
                    </div>
                `;
            }

            const content = `
                <div class="bill-preview-content">
                    <div class="preview-title">
                        <h3>账单内容预览</h3>
                        <p class="preview-filename">${Utils.escapeHtml(data.file_name || '未知文件')}</p>
                    </div>
                    ${tableHtml}
                </div>
            `;

            // 使用宽模态框显示预览
            const modal = document.getElementById('detail-modal');
            if (modal) {
                modal.classList.add('content-preview-modal');
            }

            this.show('账单内容预览', content);
        },

        close() {
            const modal = document.getElementById('detail-modal');
            if (modal) {
                modal.style.display = 'none';
                modal.classList.remove('content-preview-modal');
            }
        }
    };

    // ============================================
    // 主工作空间对象
    // ============================================

    const Workspace = {
        // 初始化
        async init() {
            console.log('初始化工作空间...');

            // 检查登录状态
            if (!window.Auth || !window.Auth.isLoggedIn()) {
                window.location.href = '/login';
                return;
            }

            // 初始化 DOM 缓存
            DOM.toastContainer = document.getElementById('toast-container');
            DOM.viewsContainer = document.getElementById('views-container');

            // 加载用户信息
            await this.loadUser();

            // 初始化导航
            this.initNavigation();

            // 加载默认视图
            this.navigateTo('dashboard');

            console.log('工作空间初始化完成');
        },

        // 加载用户信息
        async loadUser() {
            try {
                const response = await window.Auth.apiRequest('/api/user/profile');
                if (response.ok) {
                    const profile = await response.json();
                    AppState.user = profile;
                    this.updateUserDisplay();
                }
            } catch (error) {
                console.error('Failed to load user:', error);
            }
        },

        // 更新用户显示
        updateUserDisplay() {
            const user = AppState.user;
            if (!user) return;

            // 更新用户名显示
            const userNameDisplays = document.querySelectorAll('.user-name-display');
            userNameDisplays.forEach(el => {
                el.textContent = user.username || '用户';
            });

            // 更新用户首字母
            const userInitials = document.querySelectorAll('.user-initial');
            userInitials.forEach(el => {
                el.textContent = (user.username || 'U').charAt(0).toUpperCase();
            });
        },

        // 初始化导航
        initNavigation() {
            // 侧边栏导航
            document.querySelectorAll('.nav-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const view = item.dataset.view;
                    if (view) {
                        this.navigateTo(view);
                    }
                });
            });

            // 侧边栏折叠
            const sidebarToggle = document.getElementById('sidebar-toggle');
            if (sidebarToggle) {
                sidebarToggle.addEventListener('click', () => {
                    const sidebar = document.getElementById('sidebar');
                    if (sidebar) {
                        sidebar.classList.toggle('collapsed');
                        AppState.sidebarCollapsed = sidebar.classList.contains('collapsed');
                    }
                });
            }

            // 刷新按钮
            const refreshBtn = document.getElementById('refresh-btn');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => {
                    this.refreshCurrentView();
                });
            }

            // 快速上传按钮
            const quickUploadBtn = document.getElementById('quick-upload-btn');
            if (quickUploadBtn) {
                quickUploadBtn.addEventListener('click', () => {
                    this.navigateTo('bills');
                });
            }

            // 用户菜单
            const userMenuBtn = document.getElementById('user-menu-btn');
            if (userMenuBtn) {
                userMenuBtn.addEventListener('click', () => {
                    this.navigateTo('settings');
                });
            }
        },

        // 导航到指定视图
        navigateTo(viewName) {
            // 清理当前视图（如果需要）
            const previousView = AppState.currentView;
            if (previousView && previousView !== viewName) {
                this.cleanupView(previousView);
            }

            // 更新当前视图
            AppState.currentView = viewName;

            // 更新导航激活状态
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
                if (item.dataset.view === viewName) {
                    item.classList.add('active');
                }
            });

            // 隐藏所有视图
            document.querySelectorAll('.view').forEach(view => {
                view.classList.remove('active');
            });

            // 查找或创建视图容器
            let viewElement = document.getElementById(`view-${viewName}`);
            if (!viewElement) {
                viewElement = document.createElement('div');
                viewElement.id = `view-${viewName}`;
                viewElement.className = 'view';
                if (DOM.viewsContainer) {
                    DOM.viewsContainer.appendChild(viewElement);
                }
            }

            // 渲染视图内容
            viewElement.innerHTML = this.getViewTemplate(viewName);
            viewElement.classList.add('active');

            // 初始化视图
            this.initView(viewName);

            // 更新页面标题
            const titles = {
                dashboard: ['仪表板', '您的财务概览'],
                bills: ['账单上传', '上传您的账单文件'],
                history: ['导入历史', '查看所有导入记录'],
                review: ['财务复盘', '生成财务分析报告'],
                settings: ['系统设置', '配置您的偏好']
            };
            const [title, subtitle] = titles[viewName] || ['页面', ''];
            this.updatePageTitle(title, subtitle);
        },

        // 清理视图资源
        cleanupView(viewName) {
            switch (viewName) {
                case 'dashboard':
                    // 清理Dashboard视图的自动刷新定时器
                    if (window.DashboardView && window.DashboardView.stopAutoRefresh) {
                        window.DashboardView.stopAutoRefresh();
                    }
                    break;
                // 其他视图的清理逻辑（如果需要）
                default:
                    break;
            }
        },

        // 获取视图模板
        getViewTemplate(viewName) {
            const templates = {
                dashboard: () => this.getDashboardTemplate(),
                bills: () => this.getBillsTemplate(),
                history: () => this.getHistoryTemplate(),
                review: () => this.getReviewTemplate(),
                settings: () => this.getSettingsTemplate()
            };

            return templates[viewName] ? templates[viewName]() : '<p>未知视图</p>';
        },

        // 仪表板模板（简化版，由DashboardView模块动态渲染）
        getDashboardTemplate() {
            // Dashboard内容由DashboardView模块动态加载
            return `
                <div class="dashboard-container">
                    <div class="loading-state">
                        <div class="loading-spinner"></div>
                        <p>加载仪表板数据...</p>
                    </div>
                </div>
            `;
        },

        // 账单上传模板
        getBillsTemplate() {
            return `
                <div class="bills-container">
                    <!-- 主上传区域 - 突出显示 -->
                    <div class="bills-hero-section">
                        <div class="upload-zone-card">
                            <div class="upload-zone-header">
                                <div class="upload-zone-title">
                                    <div class="upload-zone-icon">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                                            <polyline points="17 8 12 3 7 8"/>
                                            <line x1="12" y1="3" x2="12" y2="15"/>
                                        </svg>
                                    </div>
                                    <div>
                                        <h2>上传账单文件</h2>
                                        <p>支持支付宝、微信支付、银联账单</p>
                                    </div>
                                </div>
                                <div class="upload-zone-badges">
                                    <span class="platform-badge alipay">支付宝</span>
                                    <span class="platform-badge wechat">微信支付</span>
                                    <span class="platform-badge unionpay">银联</span>
                                </div>
                            </div>

                            <div class="upload-drop-area" id="upload-area">
                                <input type="file" id="file" accept=".csv,.xlsx,.xls" style="display: none;">
                                <div class="upload-drop-content">
                                    <div class="upload-drop-icon">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                                            <path d="M14 2v6h6"/>
                                            <path d="M12 18v-6"/>
                                            <path d="M9 15l3 3 3-3"/>
                                        </svg>
                                    </div>
                                    <h3>拖放文件到此处</h3>
                                    <p>或点击选择文件（最大 50MB）</p>
                                    <div class="upload-formats">支持 CSV, XLSX, XLS 格式</div>
                                </div>
                            </div>

                            <div class="upload-controls">
                                <div class="upload-platform-select">
                                    <label for="platform">检测平台</label>
                                    <select id="platform" class="neon-select">
                                        <option value="auto">自动检测</option>
                                        <option value="alipay">支付宝</option>
                                        <option value="wechat">微信支付</option>
                                        <option value="unionpay">银联</option>
                                    </select>
                                </div>
                                <button class="neon-btn-primary" id="upload-btn">
                                    <span class="btn-text">开始上传</span>
                                    <span class="btn-loading" style="display: none;">
                                        <span class="btn-spinner"></span> 上传中...
                                    </span>
                                </button>
                            </div>

                            <div class="upload-progress-area" id="progress" style="display: none;">
                                <div class="progress-bar">
                                    <div class="progress-fill" id="progress-fill"></div>
                                </div>
                                <div class="progress-text" id="progress-text">正在上传...</div>
                            </div>

                            <div class="upload-result-area" id="result" style="display: none;"></div>
                        </div>
                    </div>

                    <!-- 功能快速入口 -->
                    <div class="bills-quick-actions">
                        <div class="quick-action-grid">
                            <div class="quick-action-item" onclick="BillsModule.showImportHistory()">
                                <div class="quick-action-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="12" cy="12" r="10"/>
                                        <polyline points="12 6 12 12 16 14"/>
                                    </svg>
                                </div>
                                <div class="quick-action-content">
                                    <h4>导入历史</h4>
                                    <p>查看所有导入记录</p>
                                </div>
                            </div>
                            <div class="quick-action-item" onclick="BillsModule.showTemplates()">
                                <div class="quick-action-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                                        <path d="M14 2v6h6"/>
                                        <path d="M16 13H8"/>
                                        <path d="M16 17H8"/>
                                        <path d="M10 9H8"/>
                                    </svg>
                                </div>
                                <div class="quick-action-content">
                                    <h4>账单模板</h4>
                                    <p>下载官方模板</p>
                                </div>
                            </div>
                            <div class="quick-action-item" onclick="BillsModule.showHelp()">
                                <div class="quick-action-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="12" cy="12" r="10"/>
                                        <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
                                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                                    </svg>
                                </div>
                                <div class="quick-action-content">
                                    <h4>使用帮助</h4>
                                    <p>查看操作指南</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 已上传文件列表 - 可折叠 -->
                    <div class="bills-files-section">
                        <div class="section-header-collapsible">
                            <div class="section-header-left">
                                <h3>已上传文件</h3>
                                <span class="file-count-badge" id="file-count-badge">0</span>
                            </div>
                            <div class="section-header-actions">
                                <button class="icon-btn" onclick="BillsModule.loadFiles()" title="刷新">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0118.8-4.3M22 12.5a10 10 0 01-18.8 4.2"/>
                                    </svg>
                                </button>
                                <button class="icon-btn" onclick="BillsModule.toggleFilters()" title="筛选">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <!-- 筛选栏 - 默认隐藏 -->
                        <div class="filters-panel" id="filters-panel" style="display: none;">
                            <div class="filter-chips">
                                <button class="filter-chip active" data-filter="all">全部</button>
                                <button class="filter-chip" data-filter="pending">待处理</button>
                                <button class="filter-chip" data-filter="completed">已完成</button>
                                <button class="filter-chip" data-filter="failed">失败</button>
                                <div class="filter-divider"></div>
                                <button class="filter-chip" data-platform="alipay">支付宝</button>
                                <button class="filter-chip" data-platform="wechat">微信</button>
                                <button class="filter-chip" data-platform="unionpay">银联</button>
                            </div>
                        </div>

                        <!-- 批量操作栏 -->
                        <div class="bulk-actions-panel" id="bulk-actions-panel" style="display: none;">
                            <div class="bulk-info">
                                <span class="bulk-count">已选择 <strong id="selected-count">0</strong> 项</span>
                            </div>
                            <div class="bulk-buttons">
                                <button class="bulk-btn bulk-btn-primary" id="bulk-import-btn">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                                        <polyline points="17 8 12 3 7 8"/>
                                        <line x1="12" y1="3" x2="12" y2="15"/>
                                    </svg>
                                    批量导入
                                </button>
                                <button class="bulk-btn bulk-btn-danger" id="bulk-delete-btn">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"/>
                                        <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                                    </svg>
                                    批量删除
                                </button>
                                <button class="bulk-btn bulk-btn-secondary" id="cancel-selection-btn">取消选择</button>
                            </div>
                        </div>

                        <!-- 文件列表 - 卡片网格布局 -->
                        <div class="files-grid" id="files-grid">
                            <div class="files-loading">
                                <div class="loading-spinner-large"></div>
                                <p>加载文件列表...</p>
                            </div>
                        </div>
                    </div>

                    <!-- 复盘建议横幅 -->
                    <div id="review-banner" class="review-banner" style="display: none;">
                        <div class="review-banner-content">
                            <div class="review-banner-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M3 3v18h18"/>
                                    <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"/>
                                </svg>
                            </div>
                            <div class="review-banner-text">
                                <h4>账单导入成功！</h4>
                                <p>检测到您本月已导入多笔账单，是否生成财务复盘报告？</p>
                            </div>
                            <div class="review-banner-actions">
                                <button class="neon-btn-primary neon-btn-sm" onclick="Workspace.navigateTo('review')">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M3 3v18h18"/>
                                        <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"/>
                                    </svg>
                                    生成复盘
                                </button>
                                <button class="neon-btn-secondary neon-btn-sm" onclick="BillsModule.hideReviewBanner()">稍后</button>
                            </div>
                            <button class="review-banner-close" onclick="BillsModule.hideReviewBanner()">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="18" y1="6" x2="6" y2="18"/>
                                    <line x1="6" y1="6" x2="18" y2="18"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        },

        // 历史记录模板
        getHistoryTemplate() {
            return `
                <div class="history-container">
                    <div class="history-stats">
                        <div class="stat-card">
                            <div class="stat-card-header">
                                <span class="stat-card-label">总导入</span>
                                <div class="stat-card-icon">📊</div>
                            </div>
                            <div class="stat-card-value" id="total-imports">0</div>
                        </div>

                        <div class="stat-card">
                            <div class="stat-card-header">
                                <span class="stat-card-label">成功</span>
                                <div class="stat-card-icon success">✅</div>
                            </div>
                            <div class="stat-card-value" id="successful-imports">0</div>
                        </div>

                        <div class="stat-card">
                            <div class="stat-card-header">
                                <span class="stat-card-label">总记录数</span>
                                <div class="stat-card-icon">📝</div>
                            </div>
                            <div class="stat-card-value" id="total-records">0</div>
                        </div>

                        <div class="stat-card">
                            <div class="stat-card-header">
                                <span class="stat-card-label">平均耗时</span>
                                <div class="stat-card-icon">⏱</div>
                            </div>
                            <div class="stat-card-value" id="avg-duration">-</div>
                        </div>
                    </div>

                    <div class="history-filters">
                        <div class="filter-group">
                            <input type="text" id="search-input" class="search-input" placeholder="搜索文件名或平台...">
                        </div>
                        <div class="filter-group">
                            <select id="status-filter" class="filter-select">
                                <option value="">全部状态</option>
                                <option value="success">成功</option>
                                <option value="failed">失败</option>
                                <option value="processing">处理中</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <select id="platform-filter" class="filter-select">
                                <option value="">全部平台</option>
                                <option value="alipay">支付宝</option>
                                <option value="wechat">微信支付</option>
                                <option value="unionpay">银联</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <input type="date" id="start-date" class="date-input" placeholder="开始日期">
                        </div>
                        <div class="filter-group">
                            <input type="date" id="end-date" class="date-input" placeholder="结束日期">
                        </div>
                        <div class="filter-group">
                            <button class="btn btn-secondary btn-sm" id="clear-date-filter">清除日期</button>
                        </div>
                        <div class="filter-group">
                            <button class="btn btn-secondary btn-sm" id="clear-all-filters">清除全部</button>
                        </div>
                    </div>

                    <div class="bulk-actions-bar" id="bulk-actions-bar" style="display: none;">
                        <div class="bulk-actions-left">
                            <input type="checkbox" id="select-all-checkbox" class="select-all-checkbox">
                            <label for="select-all-checkbox" class="select-all-label">
                                已选择 <span id="selected-count">0</span> 项
                            </label>
                        </div>
                        <div class="bulk-actions-right">
                            <button class="btn btn-danger btn-sm" id="bulk-delete-btn">
                                <span>🗑</span> 批量删除
                            </button>
                            <button class="btn btn-secondary btn-sm" id="cancel-selection-btn">
                                取消选择
                            </button>
                        </div>
                    </div>

                    <div class="history-list" id="history-items">
                        <div class="loading-state">
                            <div class="loading-spinner"></div>
                            <p>加载中...</p>
                        </div>
                    </div>

                    <div class="pagination" id="pagination">
                        <button class="pagination-btn" id="prev-page">
                            <span>←</span> 上一页
                        </button>
                        <div class="pagination-pages" id="pagination-pages"></div>
                        <button class="pagination-btn" id="next-page">
                            下一页 <span>→</span>
                        </button>
                    </div>
                </div>
            `;
        },

        // 复盘模板
        getReviewTemplate() {
            return `
                <div class="review-container">
                    <!-- 连接状态 -->
                    <div class="connection-status-card">
                        <div id="status-indicator-wrapper" class="status-indicator-wrapper">
                            <div class="status-core-indicator">
                                <div id="status-core-status" class="status-core-status">检查中...</div>
                            </div>
                        </div>
                        <button class="btn btn-secondary btn-sm" id="test-connection-btn">测试连接</button>
                    </div>

                    <!-- 快速生成区域 -->
                    <div class="review-quick-section">
                        <h3>快速生成复盘</h3>
                        <div class="review-cards">
                            <div class="review-card" data-type="monthly">
                                <div class="review-card-icon">📅</div>
                                <h4>月度复盘</h4>
                                <p>生成本月财务分析报告</p>
                                <button class="review-card-btn" onclick="ReviewModule.generate('monthly')">立即生成</button>
                            </div>
                            <div class="review-card" data-type="quarterly">
                                <div class="review-card-icon">📊</div>
                                <h4>季度复盘</h4>
                                <p>生成本季度财务分析报告</p>
                                <button class="review-card-btn" onclick="ReviewModule.generate('quarterly')">立即生成</button>
                            </div>
                            <div class="review-card" data-type="yearly">
                                <div class="review-card-icon">🎯</div>
                                <h4>年度复盘</h4>
                                <p>生成年度财务分析报告</p>
                                <button class="review-card-btn" onclick="ReviewModule.generate('yearly')">立即生成</button>
                            </div>
                        </div>
                    </div>

                    <!-- 自定义生成区域 -->
                    <div class="review-custom-section">
                        <h3>自定义复盘</h3>
                        <div class="review-form">
                            <div class="form-group">
                                <label>复盘类型</label>
                                <div class="type-selector">
                                    <div class="type-option active" data-type="monthly">
                                        <span class="type-icon">📅</span>
                                        <span class="type-label">月度复盘</span>
                                    </div>
                                    <div class="type-option" data-type="quarterly">
                                        <span class="type-icon">📊</span>
                                        <span class="type-label">季度复盘</span>
                                    </div>
                                    <div class="type-option" data-type="yearly">
                                        <span class="type-icon">🎯</span>
                                        <span class="type-label">年度复盘</span>
                                    </div>
                                    <div class="type-option" data-type="custom">
                                        <span class="type-icon">⚙</span>
                                        <span class="type-label">自定义</span>
                                    </div>
                                    <input type="hidden" id="review-type" value="monthly">
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>复盘标题</label>
                                    <input type="text" id="review-title" class="form-input" placeholder="例如：2024年1月账单复盘">
                                </div>
                                <div class="form-group">
                                    <label>状态</label>
                                    <select id="review-status" class="form-select">
                                        <option value="计划中">计划中</option>
                                        <option value="进行中">进行中</option>
                                        <option value="已完成">已完成</option>
                                    </select>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>开始日期</label>
                                    <input type="date" id="start-date" class="form-input">
                                </div>
                                <div class="form-group">
                                    <label>结束日期</label>
                                    <input type="date" id="end-date" class="form-input">
                                </div>
                            </div>
                            <button class="btn btn-primary btn-large" id="generate-preview-btn">
                                <span>📊</span> 生成预览
                            </button>
                        </div>
                    </div>

                    <!-- 预览区域 -->
                    <div id="preview-section" class="preview-section" style="display: none;">
                        <div class="preview-header">
                            <h3>预览结果</h3>
                            <div class="preview-actions">
                                <button class="btn btn-secondary btn-sm" id="close-preview-btn">关闭预览</button>
                                <button class="btn btn-primary btn-sm" id="preview-cancel-btn">取消</button>
                                <button class="btn btn-primary btn-sm" id="submit-to-notion-btn">
                                    <span>📤</span> 提交到 Notion
                                </button>
                            </div>
                        </div>

                        <div class="preview-content">
                            <!-- 基本属性 -->
                            <div class="preview-attributes">
                                <h4>基本属性</h4>
                                <div class="form-row">
                                    <div class="form-group">
                                        <label>标题</label>
                                        <input type="text" id="attr-title" class="form-input">
                                    </div>
                                    <div class="form-group">
                                        <label>周期</label>
                                        <input type="text" id="attr-period" class="form-input" readonly>
                                    </div>
                                </div>
                                <div class="form-row">
                                    <div class="form-group">
                                        <label>开始日期</label>
                                        <input type="date" id="attr-start-date" class="form-input">
                                    </div>
                                    <div class="form-group">
                                        <label>结束日期</label>
                                        <input type="date" id="attr-end-date" class="form-input">
                                    </div>
                                </div>
                                <div class="form-row">
                                    <div class="form-group">
                                        <label>状态</label>
                                        <select id="attr-status" class="form-select">
                                            <option value="计划中">计划中</option>
                                            <option value="进行中">进行中</option>
                                            <option value="已完成">已完成</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label>交易笔数</label>
                                        <input type="text" id="attr-transaction-count" class="form-input" readonly>
                                    </div>
                                </div>
                            </div>

                            <!-- 财务数据 -->
                            <div class="preview-financial">
                                <h4>财务数据</h4>
                                <div class="financial-grid">
                                    <div class="financial-item">
                                        <div class="financial-label">总收入</div>
                                        <div class="financial-value income" id="attr-total-income">¥0.00</div>
                                    </div>
                                    <div class="financial-item">
                                        <div class="financial-label">总支出</div>
                                        <div class="financial-value expense" id="attr-total-expense">¥0.00</div>
                                    </div>
                                    <div class="financial-item" id="net-balance-item">
                                        <div class="financial-label">净收益</div>
                                        <div class="financial-value" id="attr-net-balance">¥0.00</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Markdown 编辑器 -->
                            <div class="markdown-editor-section">
                                <h4>复盘内容</h4>
                                <div class="markdown-editor-wrapper">
                                    <div class="line-numbers" id="line-numbers"></div>
                                    <textarea id="markdown-editor" class="markdown-editor" spellcheck="false"></textarea>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 复盘历史 -->
                    <div class="review-history-section">
                        <h3>复盘历史</h3>
                        <div class="review-history-list" id="review-history-list">
                            <div class="loading-state">
                                <div class="loading-spinner"></div>
                                <p>加载中...</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 进度模态框 -->
                <div id="progress-modal" class="progress-modal" style="display: none;">
                    <div class="progress-modal-content">
                        <h3>生成复盘报告</h3>
                        <div class="progress-steps">
                            <div class="progress-step" id="step-fetch">
                                <div class="step-indicator"></div>
                                <div class="step-content">
                                    <div class="step-title">查询交易数据</div>
                                    <div class="step-status">等待中...</div>
                                </div>
                            </div>
                            <div class="progress-step" id="step-calculate">
                                <div class="step-indicator"></div>
                                <div class="step-content">
                                    <div class="step-title">计算统计数据</div>
                                    <div class="step-status">等待中...</div>
                                </div>
                            </div>
                            <div class="progress-step" id="step-generate">
                                <div class="step-indicator"></div>
                                <div class="step-content">
                                    <div class="step-title">生成复盘内容</div>
                                    <div class="step-status">等待中...</div>
                                </div>
                            </div>
                            <div class="progress-step" id="step-complete">
                                <div class="step-indicator"></div>
                                <div class="step-content">
                                    <div class="step-title">完成</div>
                                    <div class="step-status">等待中...</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 提交模态框 -->
                <div id="submitting-modal" class="progress-modal" style="display: none;">
                    <div class="progress-modal-content">
                        <h3>提交到 Notion</h3>
                        <div class="progress-steps">
                            <div class="submit-progress-step" id="submit-step-validate">
                                <div class="step-indicator"></div>
                                <div class="step-content">
                                    <div class="step-title">验证数据</div>
                                    <div class="step-status">等待中...</div>
                                </div>
                            </div>
                            <div class="submit-progress-step" id="submit-step-create">
                                <div class="step-indicator"></div>
                                <div class="step-content">
                                    <div class="step-title">创建页面</div>
                                    <div class="step-status">等待中...</div>
                                </div>
                            </div>
                            <div class="submit-progress-step" id="submit-step-content">
                                <div class="step-indicator"></div>
                                <div class="step-content">
                                    <div class="step-title">添加内容</div>
                                    <div class="step-status">等待中...</div>
                                </div>
                            </div>
                            <div class="submit-progress-step" id="submit-step-finalize">
                                <div class="step-indicator"></div>
                                <div class="step-content">
                                    <div class="step-title">完成</div>
                                    <div class="step-status">等待中...</div>
                                </div>
                            </div>
                        </div>
                        <button class="btn btn-secondary" id="submit-modal-close-btn">关闭（可离开页面）</button>
                    </div>
                </div>

                <!-- 成功模态框 -->
                <div id="success-modal" class="modal" style="display: none;">
                    <div class="modal-backdrop"></div>
                    <div class="modal-container">
                        <div class="modal-header">
                            <h2>✅ 提交成功</h2>
                        </div>
                        <div class="modal-body">
                            <p>复盘报告已成功提交到 Notion！</p>
                            <div id="success-details" class="success-details"></div>
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-secondary" id="success-close-btn">关闭</button>
                            <button class="btn btn-primary" id="success-view-btn">查看 Notion 页面</button>
                        </div>
                    </div>
                </div>
            `;
        },

        // 设置模板
        getSettingsTemplate() {
            return `
                <div class="settings-container">
                    <div class="settings-nav">
                        <a href="#" class="settings-nav-item active" data-settings-tab="notion">Notion配置</a>
                        <a href="#" class="settings-nav-item" data-settings-tab="account">账户设置</a>
                        <a href="#" class="settings-nav-item" data-settings-tab="review">复盘配置</a>
                    </div>

                    <div class="settings-content" id="settings-content">
                        <!-- 动态加载设置内容 -->
                        <div class="loading-state">
                            <div class="loading-spinner"></div>
                            <p>加载中...</p>
                        </div>
                    </div>
                </div>
            `;
        },

        // 初始化视图
        initView(viewName) {
            switch (viewName) {
                case 'dashboard':
                    // 初始化仪表板视图
                    if (window.DashboardView) {
                        window.DashboardView.init();
                    }
                    break;
                case 'bills':
                    BillsModule.init();
                    break;
                case 'history':
                    HistoryModule.init();
                    break;
                case 'review':
                    ReviewModule.init();
                    break;
                case 'settings':
                    SettingsModule.init();
                    break;
            }
        },

        // 更新页面标题
        updatePageTitle(title, subtitle) {
            const titleElement = document.getElementById('page-title');
            const subtitleElement = document.getElementById('page-subtitle');

            if (titleElement) titleElement.textContent = title;
            if (subtitleElement) subtitleElement.textContent = subtitle;
        },

        // 刷新当前视图
        refreshCurrentView() {
            const viewName = AppState.currentView;
            this.initView(viewName);
            Utils.showToast('数据已刷新', 'success');
        }
    };

    // ============================================
    // 导出到全局
    // ============================================

    window.Workspace = Workspace;
    window.WorkspaceApp = Workspace; // 添加别名，便于其他模块调用
    window.BillsModule = BillsModule;
    window.HistoryModule = HistoryModule;
    window.ReviewModule = ReviewModule;
    window.SettingsModule = SettingsModule;
    window.Modal = Modal;
    window.Utils = Utils;

    // ============================================
    // DOM加载完成后初始化
    // ============================================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => Workspace.init());
    } else {
        Workspace.init();
    }

})();
