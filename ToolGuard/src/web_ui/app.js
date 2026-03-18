// ToolGuard Web UI - 前端逻辑

const API_BASE = window.location.origin;

// 页面加载时获取数据
document.addEventListener('DOMContentLoaded', () => {
    checkServiceStatus();
    loadPendingConfirmations();
    loadRiskTools();
    loadAuditLog();
    
    // 每 10 秒自动刷新待确认
    setInterval(() => {
        loadPendingConfirmations();
    }, 10000);
});

// 切换选项卡
function switchTab(tabName) {
    // 更新选项卡样式
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 激活当前选项卡
    event.target.classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // 加载对应数据
    if (tabName === 'risk-tools') {
        loadRiskTools();
    } else if (tabName === 'audit') {
        loadAuditLog();
    }
}

// 检查服务状态
async function checkServiceStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        if (data.status === 'ok') {
            document.getElementById('statusIndicator').className = 'status-indicator status-ok';
            document.getElementById('statusText').textContent = '服务运行中';
        } else {
            throw new Error('Service not ok');
        }
    } catch (error) {
        document.getElementById('statusIndicator').className = 'status-indicator';
        document.getElementById('statusIndicator').style.background = '#ef4444';
        document.getElementById('statusIndicator').style.color = 'white';
        document.getElementById('statusText').textContent = '服务离线';
    }
}

// 加载待处理确认
async function loadPendingConfirmations() {
    try {
        const response = await fetch(`${API_BASE}/api/pending`);
        const pending = await response.json();
        
        const pendingList = document.getElementById('pendingList');
        
        if (pending.length === 0) {
            pendingList.innerHTML = `
                <div class="empty-state">
                    <p>✅ 暂无待确认请求</p>
                </div>
            `;
            return;
        }
        
        pendingList.innerHTML = pending.map(conf => {
            const riskClass = `risk-${conf.risk_level}`;
            const itemClass = conf.risk_level === 'critical' ? 'critical' : 
                             conf.risk_level === 'high' ? 'high' : 'medium';
            
            return `
                <div class="pending-item ${itemClass}">
                    <div class="pending-header">
                        <span class="pending-title">
                            ${conf.tool_name}.${conf.action}
                        </span>
                        <span class="risk-badge ${riskClass}">
                            ${getRiskLevelText(conf.risk_level)}
                        </span>
                    </div>
                    <div class="pending-details">
                        <p><strong>原因：</strong>${conf.reason}</p>
                        <p><strong>时间：</strong>${formatTime(conf.timestamp)}</p>
                        <p><strong>过期：</strong>${formatTime(conf.expires_at)}</p>
                        ${conf.parameters ? `<p><strong>参数：</strong><pre style="background:#f0f0f0;padding:8px;border-radius:4px;margin-top:4px;">${JSON.stringify(conf.parameters, null, 2)}</pre></p>` : ''}
                    </div>
                    <div class="pending-actions">
                        <button class="btn btn-approve" onclick="approveConfirmation('${conf.confirmation_id}')">
                            ✅ 允许
                        </button>
                        <button class="btn btn-deny" onclick="denyConfirmation('${conf.confirmation_id}')">
                            ❌ 拒绝
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('加载待处理确认失败:', error);
        document.getElementById('pendingList').innerHTML = `
            <div class="empty-state">
                <p>❌ 加载失败</p>
            </div>
        `;
    }
}

// 加载 Risk Tools
async function loadRiskTools() {
    try {
        const response = await fetch(`${API_BASE}/api/risk-tools`);
        const data = await response.json();
        
        const riskToolsList = document.getElementById('riskToolsList');
        const riskTools = data.risk_tools || [];
        const safeTools = data.safe_tools || [];
        
        if (riskTools.length === 0 && safeTools.length === 0) {
            riskToolsList.innerHTML = `
                <div class="empty-state">
                    <p>暂无配置</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        // 危险工具表格
        if (riskTools.length > 0) {
            html += `
                <h4 style="margin: 20px 0 12px; color: #333;">🔴 危险工具 (${riskTools.length})</h4>
                <table class="tools-table">
                    <thead>
                        <tr>
                            <th>工具</th>
                            <th>动作</th>
                            <th>风险等级</th>
                            <th>原因</th>
                            <th>确认</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${riskTools.map(tool => `
                            <tr>
                                <td><code>${tool.tool_name}</code></td>
                                <td><code>${tool.action}</code></td>
                                <td><span class="risk-badge risk-${tool.risk_level}">${getRiskLevelText(tool.risk_level)}</span></td>
                                <td>${tool.reason}</td>
                                <td>${tool.require_confirmation ? '✅' : '⚪'}</td>
                                <td class="actions">
                                    <button class="btn btn-edit btn-small" onclick="editRiskTool('${tool.tool_name}', '${tool.action}')">✏️</button>
                                    <button class="btn btn-danger btn-small" onclick="deleteRiskTool('${tool.tool_name}', '${tool.action}')">🗑️</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
        
        // 安全工具表格
        if (safeTools.length > 0) {
            html += `
                <h4 style="margin: 20px 0 12px; color: #333;">🟢 安全工具 (${safeTools.length})</h4>
                <table class="tools-table">
                    <thead>
                        <tr>
                            <th>工具</th>
                            <th>动作</th>
                            <th>说明</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${safeTools.map(tool => `
                            <tr>
                                <td><code>${tool.tool_name}</code></td>
                                <td><code>${tool.action || '*'}</code></td>
                                <td>${tool.reason}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
        
        riskToolsList.innerHTML = html;
        
    } catch (error) {
        console.error('加载 Risk Tools 失败:', error);
        document.getElementById('riskToolsList').innerHTML = `
            <div class="empty-state">
                <p>❌ 加载失败</p>
            </div>
        `;
    }
}

// 加载审计日志
async function loadAuditLog() {
    try {
        const response = await fetch(`${API_BASE}/api/audit`);
        const logs = await response.json();
        
        const auditLog = document.getElementById('auditLog');
        
        if (logs.length === 0) {
            auditLog.innerHTML = `
                <div class="empty-state">
                    <p>暂无审计日志</p>
                </div>
            `;
            return;
        }
        
        auditLog.innerHTML = logs.map(log => `
            <div class="log-item">
                <span class="log-icon">${getLogIcon(log)}</span>
                <div class="log-content">
                    <div style="font-weight: 500;">
                        ${log.tool_name}.${log.action}
                        ${log.confirmed ? (log.approved ? ' ✅ 允许' : ' ❌ 拒绝') : ''}
                    </div>
                    <div style="color: #999; font-size: 12px;">
                        ${log.confirmation_id ? `ID: ${log.confirmation_id.substring(0, 8)}...` : ''} | 
                        ${formatTime(log.timestamp)}
                    </div>
                </div>
                <span class="log-time">${formatTime(log.timestamp)}</span>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('加载审计日志失败:', error);
        document.getElementById('auditLog').innerHTML = `
            <div class="empty-state">
                <p>❌ 加载失败</p>
            </div>
        `;
    }
}

// 允许确认
async function approveConfirmation(confirmation_id) {
    try {
        const response = await fetch(`${API_BASE}/api/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ confirmation_id, approved: true })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('✅ 已允许工具调用', 'success');
            loadPendingConfirmations();
            loadAuditLog();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('允许失败:', error);
        showNotification('❌ 操作失败：' + error.message, 'error');
    }
}

// 拒绝确认
async function denyConfirmation(confirmation_id) {
    try {
        const response = await fetch(`${API_BASE}/api/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ confirmation_id, approved: false })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('❌ 已拒绝工具调用', 'success');
            loadPendingConfirmations();
            loadAuditLog();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('拒绝失败:', error);
        showNotification('❌ 操作失败：' + error.message, 'error');
    }
}

// 打开添加模态框
function openAddModal() {
    document.getElementById('modalTitle').textContent = '添加 Risk Tool';
    document.getElementById('riskToolForm').reset();
    document.getElementById('editOldToolName').value = '';
    document.getElementById('editOldAction').value = '';
    document.getElementById('riskToolModal').classList.add('active');
}

// 编辑 Risk Tool
function editRiskTool(toolName, action) {
    fetch(`${API_BASE}/api/risk-tools`)
        .then(res => res.json())
        .then(data => {
            const tool = (data.risk_tools || []).find(
                t => t.tool_name === toolName && t.action === action
            );
            
            if (!tool) {
                showNotification('❌ 未找到工具', 'error');
                return;
            }
            
            document.getElementById('modalTitle').textContent = '编辑 Risk Tool';
            document.getElementById('toolName').value = tool.tool_name;
            document.getElementById('toolAction').value = tool.action;
            document.getElementById('riskLevel').value = tool.risk_level;
            document.getElementById('requireConfirmation').checked = tool.require_confirmation !== false;
            document.getElementById('reason').value = tool.reason;
            document.getElementById('examples').value = (tool.examples || []).join('\n');
            document.getElementById('editOldToolName').value = tool.tool_name;
            document.getElementById('editOldAction').value = tool.action;
            
            document.getElementById('riskToolModal').classList.add('active');
        })
        .catch(err => {
            console.error('加载工具信息失败:', err);
            showNotification('❌ 加载失败', 'error');
        });
}

// 删除 Risk Tool
async function deleteRiskTool(toolName, action) {
    if (!confirm(`确定要删除 ${toolName}.${action} 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/risk-tools/remove`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tool_name: toolName, action: action })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('✅ 已删除', 'success');
            loadRiskTools();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('删除失败:', error);
        showNotification('❌ 操作失败：' + error.message, 'error');
    }
}

// 保存 Risk Tool
async function saveRiskTool(event) {
    event.preventDefault();
    
    const oldToolName = document.getElementById('editOldToolName').value;
    const oldAction = document.getElementById('editOldAction').value;
    
    const examplesText = document.getElementById('examples').value;
    const examples = examplesText.split('\n').filter(e => e.trim());
    
    const toolData = {
        tool_name: document.getElementById('toolName').value,
        action: document.getElementById('toolAction').value,
        risk_level: document.getElementById('riskLevel').value,
        reason: document.getElementById('reason').value,
        require_confirmation: document.getElementById('requireConfirmation').checked,
        examples: examples
    };
    
    try {
        let response;
        
        if (oldToolName && oldAction) {
            // 更新
            response = await fetch(`${API_BASE}/api/risk-tools/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    old_tool_name: oldToolName,
                    old_action: oldAction,
                    new_config: toolData
                })
            });
        } else {
            // 添加
            response = await fetch(`${API_BASE}/api/risk-tools/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(toolData)
            });
        }
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('✅ 已保存', 'success');
            closeModal();
            loadRiskTools();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('保存失败:', error);
        showNotification('❌ 操作失败：' + error.message, 'error');
    }
}

// 关闭模态框
function closeModal() {
    document.getElementById('riskToolModal').classList.remove('active');
}

// 刷新所有数据
function refreshAll() {
    checkServiceStatus();
    loadPendingConfirmations();
    loadAuditLog();
    showNotification('🔄 已刷新', 'success');
}

// 获取风险等级文本
function getRiskLevelText(level) {
    const texts = {
        'low': '🟢 Low',
        'medium': '🟡 Medium',
        'high': '🟠 High',
        'critical': '🔴 Critical'
    };
    return texts[level] || level;
}

// 获取日志图标
function getLogIcon(log) {
    if (!log.confirmed) return '⚪';
    if (log.approved) return '✅';
    if (log.approved === false) return '❌';
    return '⚪';
}

// 格式化时间
function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 显示通知
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transform: translateX(400px);
        transition: transform 0.3s;
        z-index: 1000;
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(400px)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}
