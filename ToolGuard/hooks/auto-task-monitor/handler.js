/**
 * ToolGuard 自动任务监控 Hook Handler
 * 
 * 在用户输入任务指令时，自动启动 ToolGuard 任务监控
 */

const { spawn } = require('child_process');
const path = require('path');

const log = (msg) => console.log(`[auto-task-monitor] ${msg}`);
const error = (msg) => console.error(`[auto-task-monitor] ${msg}`);

/**
 * 调用 Python 脚本进行任务监控
 */
function startTaskMonitoring(message) {
    return new Promise((resolve, reject) => {
        const scriptPath = path.join(__dirname, '../../src/auto_task_monitor.py');
        
        const python = spawn('python3', [scriptPath, message]);
        
        let output = '';
        let errorOutput = '';
        
        python.stdout.on('data', (data) => {
            output += data.toString();
            log(data.toString().trim());
        });
        
        python.stderr.on('data', (data) => {
            errorOutput += data.toString();
            if (errorOutput.trim()) {
                error(data.toString().trim());
            }
        });
        
        python.on('close', (code) => {
            if (code === 0) {
                resolve({ success: true, output });
            } else {
                reject(new Error(`Python script exited with code ${code}`));
            }
        });
        
        python.on('error', (err) => {
            error(`Spawn error: ${err.message}`);
            reject(err);
        });
    });
}

/**
 * Hook 处理器
 */
const handler = async (event) => {
    const { type, action, content, from } = event;
    
    // 只处理 message:received 事件
    if (type !== 'message' || action !== 'received') {
        return null;
    }
    
    // 忽略空消息
    if (!content || content.trim().length === 0) {
        return null;
    }
    
    // 忽略来自自己的消息
    if (from === 'system' || from === 'assistant') {
        return null;
    }
    
    log(`收到消息：${content.substring(0, 50)}...`);
    
    try {
        // 调用 Python 脚本进行任务监控
        await startTaskMonitoring(content);
    } catch (err) {
        error(`任务监控启动失败：${err.message}`);
    }
    
    return null;
};

module.exports = handler;

// CLI 测试
if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length >= 1) {
        const message = args.join(' ');
        console.log(`测试自动任务监控：${message}`);
        console.log('');
        
        startTaskMonitoring(message)
            .then(result => {
                console.log('✅ 测试完成');
                process.exit(0);
            })
            .catch(err => {
                console.error('❌ 测试失败:', err.message);
                process.exit(1);
            });
    } else {
        console.log('ToolGuard 自动任务监控 - 测试工具');
        console.log('用法：node handler.js <消息内容>');
        console.log('示例：node handler.js "发送天气预报邮件到 test@example.com"');
    }
}
