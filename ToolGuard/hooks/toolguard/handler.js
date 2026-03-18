/**
 * ToolGuard Hook Handler
 * 
 * 在工具调用前拦截并请求用户确认
 * 处理 tool:call 事件
 */

const http = require('http');

const TOOLGUARD_HOST = '127.0.0.1';
const TOOLGUARD_PORT = 8767;
const TIMEOUT = 5000;

const log = (msg) => console.log(`[toolguard] ${msg}`);
const error = (msg) => console.error(`[toolguard] ${msg}`);

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
 */
const handler = async (event) => {
    const { type, action, context } = event;
    
    // 只处理 before_tool_call 事件
    if (type !== 'tool' || action !== 'before_tool_call') {
        return null;
    }
    
    const toolName = context?.tool_name || context?.tool || '';
    const toolAction = context?.action || '*';
    const parameters = context?.parameters || {};
    
    if (!toolName) {
        return null;
    }

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
