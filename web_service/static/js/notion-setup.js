/**
 * Notion 配置向导逻辑
 */

(function() {
    'use strict';

    let currentStep = 1;

    function showToast(message, type) {
        type = type || 'success';
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast ' + type;
        toast.innerHTML = '<div class="toast-content"><span class="toast-icon">' + (type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ') + '</span><span class="toast-message">' + message + '</span></div>';
        container.appendChild(toast);
        setTimeout(function() { toast.remove(); }, 3000);
    }

    function goToStep(step) {
        document.querySelectorAll('.setup-step').forEach(function(s) { s.classList.remove('active'); });
        document.querySelectorAll('.progress-step').forEach(function(s) { s.classList.remove('active'); });
        document.getElementById('step-' + step).classList.add('active');
        for (var i = 1; i <= 3; i++) {
            var stepEl = document.querySelector('.progress-step[data-step="' + i + '"]');
            if (stepEl) {
                if (i <= step) stepEl.classList.add('active');
                else stepEl.classList.remove('active');
            }
        }
        currentStep = step;
    }

    function bindEvents() {
        document.getElementById('start-setup-btn').addEventListener('click', function() { goToStep(2); });
        document.getElementById('skip-setup-btn').addEventListener('click', function() { window.location.href = '/bill-management'; });
        document.getElementById('back-step-1').addEventListener('click', function() { goToStep(1); });
        document.getElementById('skip-step-2').addEventListener('click', function() { window.location.href = '/bill-management'; });
        
        document.getElementById('toggle-api-key').addEventListener('click', function() {
            var input = document.getElementById('notion-api-key');
            input.type = input.type === 'password' ? 'text' : 'password';
        });

        document.getElementById('notion-setup-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            var btn = document.getElementById('verify-config-btn');
            var originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = '验证中...';

            var payload = {
                config_name: document.getElementById('config-name').value,
                notion_api_key: document.getElementById('notion-api-key').value,
                notion_income_database_id: document.getElementById('income-db-id').value,
                notion_expense_database_id: document.getElementById('expense-db-id').value
            };

            try {
                var response = await window.Auth.apiRequest('/api/user/notion-config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response && response.ok) {
                    showToast('配置保存成功!');
                    goToStep(3);
                } else {
                    var data = await response.json();
                    showToast(data.detail || '配置保存失败', 'error');
                }
            } catch (err) {
                showToast('网络错误，请重试', 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        });

        document.getElementById('go-to-dashboard-btn').addEventListener('click', function() { window.location.href = '/bill-management'; });
    }

    // 存储现有配置数据
    let existingConfigData = null;

    async function checkExistingConfig() {
        try {
            var response = await window.Auth.apiRequest('/api/user/notion-config');
            if (response && response.ok) {
                var data = await response.json();
                if (data.is_configured) {
                    existingConfigData = data;
                    // 显示配置更新选择对话框
                    showConfigUpdateDialog();
                }
            }
        } catch (err) {}
    }

    function showConfigUpdateDialog() {
        // 创建模态对话框
        var modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.id = 'config-update-modal';
        modal.innerHTML = '<div class="modal-content"><div class="modal-header"><h2>检测到已有Notion配置</h2><button class="modal-close" id="close-modal">&times;</button></div><div class="modal-body"><p>您已经配置过 Notion，是否要更新现有配置？</p><div class="existing-config-info"><p><strong>当前配置：</strong>' + (existingConfigData.config_name || '默认配置') + '</p><p><strong>API密钥：</strong>' + (existingConfigData.notion_api_key || '已设置') + '</p><p><strong>验证状态：</strong>' + (existingConfigData.is_verified ? '<span class="success">已验证</span>' : '<span class="warning">未验证</span>') + '</p></div></div><div class="modal-footer"><button class="btn btn-secondary" id="keep-config-btn">保持现有配置</button><button class="btn btn-primary" id="update-config-btn">更新配置</button></div></div>';
        document.body.appendChild(modal);

        // 绑定事件
        document.getElementById('close-modal').addEventListener('click', closeModal);
        document.getElementById('keep-config-btn').addEventListener('click', function() {
            closeModal();
            goToStep(3);
        });
        document.getElementById('update-config-btn').addEventListener('click', function() {
            closeModal();
            // 预填充现有配置并进入第2步（API密钥需要重新输入）
            if (existingConfigData) {
                document.getElementById('config-name').value = existingConfigData.config_name || '默认配置';
                // API密钥是脱敏的，显示提示让用户重新输入
                document.getElementById('notion-api-key').value = '';
                document.getElementById('notion-api-key').placeholder = '请重新输入API密钥';
                document.getElementById('income-db-id').value = existingConfigData.notion_income_database_id || '';
                document.getElementById('expense-db-id').value = existingConfigData.notion_expense_database_id || '';
            }
            goToStep(2);
        });

        // 点击遮罩关闭
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
                goToStep(3);
            }
        });
    }

    function closeModal() {
        var modal = document.getElementById('config-update-modal');
        if (modal) {
            modal.remove();
        }
    }

    function init() {
        if (!window.Auth.isLoggedIn()) {
            window.location.href = '/login';
            return;
        }
        bindEvents();
        checkExistingConfig();
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
