/**
 * ToolGuard Web UI - JavaScript
 */

const API_BASE = '';

// 切换选项卡
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    document.querySelector(`.tab[onclick="switchTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    if (tabName === 'task-monitor') {
        loadTaskMonitor();
    } else if (tabName === 'tool-sets') {
        loadToolSets();
    } else if (tabName === 'pending') {
        loadPending();
    }
}

// 加载任务监控
async function loadTaskMonitor() {
    try {
        // 加载任务状态
        const taskRes = await fetch(`${API_BASE}/api/task/status`);
        const taskData = await taskRes.json();
        
        const taskContainer = document.getElementById('taskStatus');
        if (taskData.task_mode && taskData.current_task) {
            taskContainer.innerHTML = `
                <div class="status-bar">
                    <span class="status-indicator status-ok">📋 任务监控中</span>
                    <span><strong>当前任务：</strong>${taskData.current_task}</span>
                </div>
            `;
        } else {
            taskContainer.innerHTML = `
                <div class="empty-state">暂无监控任务</div>
            `;
        }
        
        // 加载工具集（与工具集管理页面保持一致）
        const toolsRes = await fetch(`${API_BASE}/api/tool-sets`);
        const toolsData = await toolsRes.json();
        
        // 渲染备选工具集
        const allowedContainer = document.getElementById('taskAllowedTools');
        allowedContainer.innerHTML = (toolsData.allowed_tools || []).map(tool => `
            <div class="tool-item">
                <span class="tool-name">✅ ${tool}</span>
            </div>
        `).join('');
        
        // 渲染禁止工具集
        const blockedContainer = document.getElementById('taskBlockedTools');
        blockedContainer.innerHTML = (toolsData.blocked_tools || []).map(tool => `
            <div class="tool-item blocked">
                <span class="tool-name">⛔ ${tool}</span>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('加载任务监控失败:', error);
    }
}

// 加载工具集
async function loadToolSets() {
    try {
        const res = await fetch(`${API_BASE}/api/tool-sets`);
        const data = await res.json();
        
        document.getElementById('allowedCount').textContent = data.allowed_count || 0;
        document.getElementById('blockedCount').textContent = data.blocked_count || 0;
        
        // 渲染备选工具集
        const allowedContainer = document.getElementById('allowedTools');
        allowedContainer.innerHTML = (data.allowed_tools || []).map(tool => `
            <div class="tool-item">
                <span class="tool-name">🔧 ${tool}</span>
                <div class="tool-actions">
                    <button class="btn btn-warning btn-small" onclick="moveToBlocked('${tool}')">
                        ⛔ 移至禁止集
                    </button>
                </div>
            </div>
        `).join('');
        
        // 渲染禁止工具集
        const blockedContainer = document.getElementById('blockedTools');
        blockedContainer.innerHTML = (data.blocked_tools || []).map(tool => `
            <div class="tool-item blocked">
                <span class="tool-name">⛔ ${tool}</span>
                <div class="tool-actions">
                    <button class="btn btn-success btn-small" onclick="moveToAllowed('${tool}')">
                        ✅ 移至备选集
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('加载工具集失败:', error);
    }
}

// 移动工具到禁止集
async function moveToBlocked(toolName) {
    if (!confirm(`确定要将 ${toolName} 移至禁止工具集吗？\n\n移动后，该工具调用需要用户确认。`)) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/tools/block`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tool_name: toolName })
        });
        
        const result = await res.json();
        if (result.success) {
            alert(`✅ ${toolName} 已移至禁止工具集`);
            // 同时更新两个页面
            loadToolSets();
            loadTaskMonitor();
            loadStats();
        } else {
            alert(`❌ 操作失败：${result.error}`);
        }
    } catch (error) {
        alert(`❌ 操作失败：${error.message}`);
    }
}

// 移动工具到备选集
async function moveToAllowed(toolName) {
    if (!confirm(`确定要将 ${toolName} 移至备选工具集吗？\n\n移动后，该工具调用将直接执行。`)) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/tools/allow`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tool_name: toolName })
        });
        
        const result = await res.json();
        if (result.success) {
            alert(`✅ ${toolName} 已移至备选工具集`);
            // 同时更新两个页面
            loadToolSets();
            loadTaskMonitor();
            loadStats();
        } else {
            alert(`❌ 操作失败：${result.error}`);
        }
    } catch (error) {
        alert(`❌ 操作失败：${error.message}`);
    }
}

// 加载待确认请求
async function loadPending() {
    try {
        const res = await fetch(`${API_BASE}/api/pending`);
        const pending = await res.json();
        
        document.getElementById('pendingCount').textContent = pending.length || 0;
        
        const container = document.getElementById('pendingList');
        
        if (pending.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无待确认请求</div>';
            return;
        }
        
        container.innerHTML = pending.map(item => {
            const riskClass = `risk-${item.risk_level}`;
            const riskText = {
                'low': '🟢 低风险',
                'medium': '🟡 中风险',
                'high': '🟠 高风险',
                'critical': '🔴 严重风险'
            }[item.risk_level] || item.risk_level;
            
            return `
                <div class="pending-item ${item.risk_level === 'critical' ? 'critical' : ''}">
                    <div class="pending-header">
                        <span class="pending-title">🔧 ${item.tool_name}.${item.action}</span>
                        <span class="risk-badge ${riskClass}">${riskText}</span>
                    </div>
                    <div class="pending-details">
                        <div><strong>原因：</strong>${item.reason}</div>
                        <div><strong>时间：</strong>${new Date(item.timestamp).toLocaleString()}</div>
                        <div><strong>过期：</strong>${new Date(item.expires_at).toLocaleString()}</div>
                        ${item.current_task ? `<div><strong>任务：</strong>${item.current_task}</div>` : ''}
                    </div>
                    <div class="pending-actions">
                        <button class="btn btn-success" onclick="respondConfirmation('${item.confirmation_id}', true)">
                            ✅ 确认
                        </button>
                        <button class="btn btn-danger" onclick="respondConfirmation('${item.confirmation_id}', false)">
                            ❌ 拒绝
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('加载待确认请求失败:', error);
    }
}

// 响应用户确认
async function respondConfirmation(confirmationId, approved) {
    try {
        const res = await fetch(`${API_BASE}/api/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                confirmation_id: confirmationId,
                approved: approved
            })
        });
        
        const result = await res.json();
        if (result.success) {
            alert(`✅ 已${approved ? '批准' : '拒绝'}确认请求`);
            loadPending();
            loadStats();
        } else {
            alert(`❌ 操作失败：${result.error}`);
        }
    } catch (error) {
        alert(`❌ 操作失败：${error.message}`);
    }
}

// 加载统计
async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/api/tool-sets`);
        const data = await res.json();
        document.getElementById('allowedCount').textContent = data.allowed_count || 0;
        document.getElementById('blockedCount').textContent = data.blocked_count || 0;
    } catch (error) {
        console.error('加载统计失败:', error);
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/pending`);
        const pending = await res.json();
        document.getElementById('pendingCount').textContent = pending.length || 0;
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadTaskMonitor();
    loadToolSets();
    loadStats();
    loadPending();
    
    // 每 10 秒刷新一次，确保两个页面数据同步
    setInterval(() => {
        loadStats();
        loadTaskMonitor();
        loadToolSets();
        loadPending();
    }, 10000);
});
