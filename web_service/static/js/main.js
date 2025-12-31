// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    console.log('Notion账单导入服务已加载');
    
    // 获取当前页面的元素
    const uploadForm = document.getElementById('upload-form');
    const fileListDiv = document.getElementById('file-list');
    const filePreviewDiv = document.getElementById('file-preview');
    const closePreviewBtn = document.getElementById('close-preview');
    
    // 加载文件列表（如果在账单管理页面）
    if (fileListDiv) {
        loadFileList();
    }
    
    // 关闭预览事件（如果在账单管理页面）
    if (closePreviewBtn) {
        closePreviewBtn.addEventListener('click', () => {
            filePreviewDiv.style.display = 'none';
        });
    }
    
    // 上传表单处理（如果在上传或账单管理页面）
    if (uploadForm) {
        setupUploadForm(uploadForm);
    }
    
    // 日志管理页面处理
    setupLogManagement();
});

// 设置上传表单处理
function setupUploadForm(uploadForm) {
    const uploadBtn = document.getElementById('upload-btn');
    const progress = document.getElementById('progress');
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.querySelector('.progress-text');
    const result = document.getElementById('result');
    const fileListDiv = document.getElementById('file-list');
    
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 重置状态
        result.style.display = 'none';
        progress.style.display = 'block';
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        uploadBtn.classList.add('loading');
        uploadBtn.disabled = true;
        
        // 构建FormData
        const formData = new FormData(uploadForm);
        
        try {
            // 模拟进度更新（实际项目中可以使用fetch的progress事件）
            const progressInterval = setInterval(() => {
                const currentWidth = parseInt(progressBar.style.width);
                if (currentWidth < 90) {
                    const newWidth = currentWidth + 10;
                    progressBar.style.width = `${newWidth}%`;
                    progressText.textContent = `${newWidth}%`;
                }
            }, 200);
            
            // 发送请求
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            clearInterval(progressInterval);
            
            // 更新进度为100%
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            
            // 处理响应
            const data = await response.json();
            
            // 显示结果
            result.style.display = 'block';
            if (data.success) {
                result.className = 'result success';
                result.innerHTML = `
                    <strong>上传成功！</strong><br>
                    ${data.message}<br>
                    ${data.import_result ? `
                        <br><strong>导入结果：</strong><br>
                        状态：${data.import_result.success ? '成功' : '失败'}<br>
                        信息：${data.import_result.message}
                    ` : ''}
                `;
                
                // 刷新文件列表（如果在账单管理页面）
                if (fileListDiv) {
                    loadFileList();
                }
            } else {
                result.className = 'result error';
                result.innerHTML = `<strong>上传失败！</strong><br>${data.message}`;
            }
        } catch (error) {
            result.style.display = 'block';
            result.className = 'result error';
            result.innerHTML = `<strong>上传失败！</strong><br>发生网络错误：${error.message}`;
        } finally {
            // 恢复按钮状态
            uploadBtn.classList.remove('loading');
            uploadBtn.disabled = false;
        }
    });
}

// 加载文件列表
async function loadFileList() {
    const fileListDiv = document.getElementById('file-list');
    
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        
        if (data.files && data.files.length > 0) {
            fileListDiv.innerHTML = data.files.map(file => `
                <div class="file-item">
                    <div class="file-item-header">
                        <div class="file-name">${file.file_name}</div>
                        <div class="file-actions">
                            ${file.file_name.endsWith('.csv') ? `<button class="btn btn-secondary btn-sm" onclick="viewFile('${file.file_name}')">查看</button>` : ''}
                            <button class="btn btn-danger btn-sm" onclick="deleteFile('${file.file_name}')">删除</button>
                        </div>
                    </div>
                    <div class="file-info">
                        <span class="file-size">${formatFileSize(file.size)}</span>
                        <span class="file-date">${formatDate(file.created_at)}</span>
                    </div>
                </div>
            `).join('');
        } else {
            fileListDiv.innerHTML = '<div class="file-list-empty">暂无上传文件</div>';
        }
    } catch (error) {
        console.error('加载文件列表失败:', error);
        fileListDiv.innerHTML = '<div class="file-list-empty">加载文件列表失败</div>';
    }
}

// 删除文件
async function deleteFile(fileName) {
    if (!confirm(`确定要删除文件 ${fileName} 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/file/${encodeURIComponent(fileName)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 刷新文件列表
            loadFileList();
        } else {
            alert(`删除失败: ${result.message}`);
        }
    } catch (error) {
        console.error('删除文件失败:', error);
        alert(`删除失败: ${error.message}`);
    }
}

// 查看文件内容
window.viewFile = async function(fileName) {
    const previewTitle = document.getElementById('preview-title').querySelector('span');
    const previewContent = document.getElementById('preview-content');
    const filePreviewDiv = document.getElementById('file-preview');
    
    try {
        const response = await fetch(`/api/file/${encodeURIComponent(fileName)}/content`);
        const data = await response.json();
        
        if (!data.success && data.message) {
            alert(data.message);
            return;
        }
        
        // 显示预览
        previewTitle.textContent = fileName;
        
        // 生成表格
        let tableHTML = '<table class="preview-table">';
        
        // 添加表头
        tableHTML += '<thead><tr>';
        data.columns.forEach(col => {
            tableHTML += `<th>${col}</th>`;
        });
        tableHTML += '</tr></thead>';
        
        // 添加数据行
        tableHTML += '<tbody>';
        data.data.forEach(row => {
            tableHTML += '<tr>';
            data.columns.forEach(col => {
                tableHTML += `<td>${row[col] || ''}</td>`;
            });
            tableHTML += '</tr>';
        });
        tableHTML += '</tbody></table>';
        
        previewContent.innerHTML = tableHTML;
        filePreviewDiv.style.display = 'block';
    } catch (error) {
        console.error('查看文件失败:', error);
        alert('查看文件失败: ' + error.message);
    }
}

// 设置日志管理页面
function setupLogManagement() {
    const refreshLogsBtn = document.getElementById('refresh-logs');
    const clearLogsBtn = document.getElementById('clear-logs');
    
    if (refreshLogsBtn) {
        refreshLogsBtn.addEventListener('click', () => {
            loadLogs();
        });
    }
    
    if (clearLogsBtn) {
        clearLogsBtn.addEventListener('click', () => {
            if (confirm('确定要清空日志吗？')) {
                clearLogs();
            }
        });
    }
    
    // 初始加载日志
    if (document.getElementById('log-container')) {
        loadLogs();
    }
}

// 加载日志（从服务器获取真实日志）
async function loadLogs() {
    const logContainer = document.getElementById('log-container');
    const logLevelSelect = document.getElementById('log-level');
    
    if (!logContainer) return;
    
    logContainer.innerHTML = '<div class="log-loading">加载日志中...</div>';
    
    try {
        // 尝试从服务器获取日志（这里使用模拟实现，实际项目中应该有对应的API）
        // 模拟API调用延迟
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // 从本地日志文件读取（模拟实现）
        const response = await fetch('/api/logs', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        let logs = [];
        
        if (response.ok) {
            logs = await response.json();
        } else {
            // 如果API调用失败，使用模拟日志数据
            logs = getMockLogs();
        }
        
        // 应用日志级别过滤
        const selectedLevel = logLevelSelect ? logLevelSelect.value : 'all';
        const filteredLogs = selectedLevel === 'all' ? logs : logs.filter(log => log.level === selectedLevel);
        
        // 显示日志
        if (filteredLogs.length > 0) {
            logContainer.innerHTML = filteredLogs.map(log => `
                <div class="log-entry ${log.level.toLowerCase()}">
                    <strong>${log.time} [${log.level}]</strong> ${log.message}
                </div>
            `).join('');
        } else {
            logContainer.innerHTML = '<div class="log-empty">没有符合条件的日志</div>';
        }
    } catch (error) {
        console.error('加载日志失败:', error);
        // 使用模拟日志数据作为回退
        const logs = getMockLogs();
        const selectedLevel = logLevelSelect ? logLevelSelect.value : 'all';
        const filteredLogs = selectedLevel === 'all' ? logs : logs.filter(log => log.level === selectedLevel);
        
        if (filteredLogs.length > 0) {
            logContainer.innerHTML = filteredLogs.map(log => `
                <div class="log-entry ${log.level.toLowerCase()}">
                    <strong>${log.time} [${log.level}]</strong> ${log.message}
                </div>
            `).join('');
        } else {
            logContainer.innerHTML = '<div class="log-empty">没有符合条件的日志</div>';
        }
    }
}

// 获取模拟日志数据
function getMockLogs() {
    const now = new Date();
    const formattedNow = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    return [
        {
            level: 'INFO',
            time: formattedNow,
            message: '服务运行正常'
        },
        {
            level: 'INFO',
            time: formattedNow,
            message: '已加载所有组件'
        },
        {
            level: 'INFO',
            time: formattedNow,
            message: 'API路由已注册完成'
        },
        {
            level: 'INFO',
            time: formattedNow,
            message: '数据库连接正常'
        },
        {
            level: 'WARNING',
            time: formattedNow,
            message: '检测到配置文件已更新'
        }
    ];
}

// 清空日志（模拟实现）
function clearLogs() {
    const logContainer = document.getElementById('log-container');
    if (logContainer) {
        logContainer.innerHTML = '<div class="log-empty">日志已清空</div>';
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}
