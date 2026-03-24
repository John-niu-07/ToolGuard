/**
 * ToolGuard Hook Handler
 * 
 * 在工具调用前拦截并请求用户确认
 * 处理 tool:call 和 message:received 事件
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const TOOLGUARD_HOST = '127.0.0.1';
const TOOLGUARD_PORT = 8767;
const TIMEOUT = 5000;

const log = (msg) => {
    console.log(`[toolguard] ${msg}`);
    // 同时写入独立日志文件
    const logFile = path.join(__dirname, '../../logs/hook_debug.log');
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    try {
        fs.appendFileSync(logFile, `${timestamp} | ${msg}\n`);
    } catch(e) {}
};
const error = (msg) => {
    console.error(`[toolguard] ${msg}`);
    const logFile = path.join(__dirname, '../../logs/hook_debug.log');
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    try {
        fs.appendFileSync(logFile, `${timestamp} | ERROR: ${msg}\n`);
    } catch(e) {}
};

/**
 * 通知 ToolGuard 服务更新当前任务
 */
function updateTask(content, channel) {
    const postData = JSON.stringify({
        task: content,
        channel: channel || 'unknown',
    });

    const options = {
        hostname: TOOLGUARD_HOST,
        port: TOOLGUARD_PORT,
        path: '/api/task/update',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData),
        },
        timeout: TIMEOUT,
    };

    const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
            try {
                log(`任务已更新：${content}`);
            } catch (e) {
                error(`解析响应失败：${e.message}`);
            }
        });
    });

    req.on('error', (e) => {
        error(`更新任务失败：${e.message}`);
    });

    req.on('timeout', () => {
        error('更新任务超时');
        req.destroy();
    });

    req.write(postData);
    req.end();
}

/**
 * 清理待确认请求 - 当用户输入新内容时调用
 */
function clearPendingConfirmations() {
    const options = {
        hostname: TOOLGUARD_HOST,
        port: TOOLGUARD_PORT,
        path: '/api/pending/clear',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        timeout: TIMEOUT,
    };

    const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
            try {
                const result = JSON.parse(data);
                if (result.cleared > 0) {
                    log(`✅ 已清理 ${result.cleared} 个待确认请求`);
                }
            } catch (e) {
                // 忽略
            }
        });
    });

    req.on('error', () => {
        // 忽略错误
    });

    req.on('timeout', () => {
        req.destroy();
    });

    req.end();
}

/**
 * 调用 ToolGuard 服务进行检查
 */
function checkToolCall(toolName, action, parameters) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify({
            tool_name: toolName,
            action: action || '*',
            parameters: parameters || {},
        });

        const options = {
            hostname: TOOLGUARD_HOST,
            port: TOOLGUARD_PORT,
            path: '/check',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData),
            },
            timeout: TIMEOUT,
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    reject(new Error(`解析响应失败：${e.message}`));
                }
            });
        });

        req.on('error', (e) => {
            error(`请求失败：${e.message}`);
            // Fail-open: 服务不可用时放行
            resolve({ need_confirmation: false });
        });

        req.on('timeout', () => {
            error('请求超时');
            req.destroy();
            // Fail-open: 超时放行
            resolve({ need_confirmation: false });
        });

        req.write(postData);
        req.end();
    });
}

/**
 * Hook 处理器
 * 
 * Gateway 传递的事件格式：
 * - before_tool_call: { toolName, action, params, toolCallId, runId, ... }
 * - message:received: { content, channel, ... }
 */
const handler = async (event) => {
    // 调试：记录所有事件
    log(`[DEBUG] 收到事件：${JSON.stringify(event)}`);
    
    // 检查是否是 message:received 事件
    const eventType = event.type || event.event || '';
    const eventAction = event.action || '';
    
    log(`[DEBUG] eventType=${eventType}, eventAction=${eventAction}, hasContent=${event.content !== undefined}, hasToolName=${event.toolName !== undefined}`);
    
    // 处理 message:received 事件 - 用户输入新消息时清理待确认请求
    // 支持多种事件格式：{type:'message',action:'received'} 或 {event:'message:received'}
    if ((eventType === 'message' && eventAction === 'received') || 
        eventType === 'message:received' ||
        (event.content !== undefined && !event.toolName && !event.tool_name)) {
        
        const content = event.content || event.command || '';
        const channel = event.channel || event.channelId || 'unknown';
        
        log(`[DEBUG] 收到消息 from=${channel}: ${content.substring(0, 50)}`);
        
        // 更新任务并清理待确认请求
        updateTask(content, channel);
        
        // 清理待确认请求和临时允许列表
        clearPendingConfirmations();
        
        return null;
    }
    
    // Gateway 直接传递工具调用参数，不是包装的事件对象
    // 检查是否有 toolName 字段来判断是否是工具调用
    const toolName = event.toolName || event.tool_name || '';
    
    // 如果是工具调用（有 toolName 字段）
    if (toolName) {
        const toolAction = event.action || '*';
        const parameters = event.params || event.parameters || {};
        
        log(`[DEBUG] 检查工具调用：${toolName}.${toolAction}`);

        try {
            const result = await checkToolCall(toolName, toolAction, parameters);

            if (result.need_confirmation) {
                log(`⚠️ 需要确认：${toolName}.${toolAction}`);
                
                // 返回确认请求 - Gateway 期望的格式
                return {
                    block: true,
                    blockReason: result.message || `需要确认：${toolName}.${toolAction}`,
                    confirmation_id: result.confirmation_id,
                };
            }

            log(`✅ 放行：${toolName}.${toolAction}`);
            return null;

        } catch (err) {
            error(`错误：${err.message}`);
            // Fail-closed: 出错时阻止
            return {
                block: true,
                blockReason: err.message || 'ToolGuard 错误',
            };
        }
    }
    
    // 非工具调用事件，放行
    log(`[DEBUG] 未知事件类型，放行`);
    return null;

    log(`检查工具调用：${toolName}.${toolAction}`);

    try {
        const result = await checkToolCall(toolName, toolAction, parameters);

        if (result.need_confirmation) {
            log(`⚠️ 需要确认：${toolName}.${toolAction} - ${result.reason}`);
            
            // 返回等待确认状态
            return {
                wait_for_confirmation: true,
                confirmation_id: result.confirmation_id,
                message: result.message || `⚠️ 危险工具调用：${toolName}.${toolAction}\n原因：${result.reason}\n请确认是否允许。`,
                tool_name: toolName,
                action: toolAction,
                parameters: parameters,
                risk_level: result.risk_level || 'medium',
            };
        }

        log(`✅ 放行：${toolName}.${toolAction}`);
        return null;

    } catch (err) {
        error(`错误：${err.message}`);
        // Fail-open: 出错时放行
        return null;
    }
};

module.exports = handler;

// CLI 测试
if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length >= 1) {
        const toolName = args[0];
        const action = args[1] || '*';
        const parameters = args[2] ? JSON.parse(args[2]) : {};
        
        console.log(`测试 ToolGuard: ${toolName}.${action}`);
        
        checkToolCall(toolName, action, parameters)
            .then(result => {
                console.log('结果:', JSON.stringify(result, null, 2));
                process.exit(result.need_confirmation ? 1 : 0);
            })
            .catch(err => {
                console.error('错误:', err.message);
                process.exit(1);
            });
    } else {
        console.log('ToolGuard Hook - 测试工具');
        console.log('用法：node handler.js <tool_name> [action] [parameters]');
        console.log('示例：node handler.js message send \'{"to":"test@example.com"}\'');
    }
}
