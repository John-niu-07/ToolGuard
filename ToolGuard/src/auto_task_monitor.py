#!/usr/bin/env python3
"""
ToolGuard 自动任务监控 Hook

在 OpenClaw 收到用户消息时，自动分析并启动任务监控
"""

import http.client
import json
import re

TOOLGUARD_HOST = '127.0.0.1'
TOOLGUARD_PORT = 8767
TIMEOUT = 3

# 任务关键词模式
TASK_PATTERNS = [
    r'发送.*邮件',
    r'给.*发邮件',
    r'查询.*天气',
    r'查看.*天气',
    r'删除.*文件',
    r'创建.*文件',
    r'写入.*文件',
    r'推送.*代码',
    r'提交.*代码',
    r'拉取.*代码',
    r'下载.*文件',
    r'上传.*文件',
    r'同步.*文件',
    r'搜索.*',
    r'查找.*',
    r'阅读.*邮件',
    r'查阅.*邮件',
    r'回复.*邮件',
    r'转发.*邮件',
    r'打开.*网页',
    r'访问.*网站',
    r'截图.*',
    r'连接.*ssh',
    r'ssh.*',
    r'复制.*到.*',
    r'scp.*',
    r'rsync.*',
    r'配置.*',
    r'设置.*',
    r'定时.*',
    r'cron.*',
]

def is_task_instruction(message: str) -> bool:
    """
    判断消息是否是任务指令
    
    参数：
        message: 用户消息
        
    返回：
        是否是任务指令
    """
    # 太短的消息不是任务
    if len(message.strip()) < 4:
        return False
    
    # 检查是否包含任务关键词
    for pattern in TASK_PATTERNS:
        if re.search(pattern, message):
            return True
    
    # 检查是否包含动词（简单判断）
    task_verbs = ['发送', '查询', '查看', '删除', '创建', '写入', '推送', '提交', 
                  '拉取', '下载', '上传', '同步', '搜索', '查找', '阅读', '查阅',
                  '回复', '转发', '打开', '访问', '截图', '连接', '复制', '配置', '设置',
                  '执行', '运行', '测试', '安装', '卸载', '备份', '恢复']
    
    for verb in task_verbs:
        if verb in message:
            return True
    
    return False

def start_task_monitoring(task: str) -> bool:
    """
    启动任务监控
    
    参数：
        task: 任务描述
        
    返回：
        是否成功启动
    """
    try:
        conn = http.client.HTTPConnection(TOOLGUARD_HOST, TOOLGUARD_PORT, timeout=TIMEOUT)
        conn.request('POST', '/api/task/start', json.dumps({
            'task': task
        }), {'Content-Type': 'application/json'})
        
        response = conn.getresponse()
        data = json.loads(response.read().decode())
        conn.close()
        
        if data.get('success'):
            print(f"📋 ToolGuard 自动任务监控已启动：{task}")
            print(f"   备选工具集：{', '.join(data.get('allowed_tools', []))}")
            return True
        else:
            print(f"⚠️ ToolGuard 任务监控启动失败：{data.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"⚠️ ToolGuard 连接失败：{e}")
        return False

def check_task_status() -> dict:
    """
    检查当前任务状态
    
    返回：
        任务状态字典
    """
    try:
        conn = http.client.HTTPConnection(TOOLGUARD_HOST, TOOLGUARD_PORT, timeout=TIMEOUT)
        conn.request('GET', '/api/task/status')
        
        response = conn.getresponse()
        data = json.loads(response.read().decode())
        conn.close()
        
        return data
        
    except Exception as e:
        return {'error': str(e)}

def stop_task_monitoring() -> bool:
    """
    停止任务监控
    
    返回：
        是否成功停止
    """
    try:
        conn = http.client.HTTPConnection(TOOLGUARD_HOST, TOOLGUARD_PORT, timeout=TIMEOUT)
        conn.request('POST', '/api/task/stop')
        
        response = conn.getresponse()
        data = json.loads(response.read().decode())
        conn.close()
        
        if data.get('success'):
            print("⏹️ ToolGuard 任务监控已停止")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"⚠️ ToolGuard 连接失败：{e}")
        return False

# Hook 处理器
async def handler(event):
    """
    OpenClaw Hook 处理器
    
    监听 message:received 事件，自动启动任务监控
    """
    event_type = event.get('type', '')
    action = event.get('action', '')
    
    # 只处理消息接收事件
    if event_type != 'message' or action != 'received':
        return None
    
    # 获取消息内容
    message = event.get('content', '')
    if not message:
        return None
    
    # 检查是否已经是任务监控模式
    status = check_task_status()
    if status.get('task_mode'):
        # 已经在监控中，不重复启动
        return None
    
    # 判断是否是任务指令
    if is_task_instruction(message):
        # 自动启动任务监控
        start_task_monitoring(message)
    
    return None

if __name__ == '__main__':
    # 测试
    import sys
    
    if len(sys.argv) < 2:
        print("用法：python3 auto_task_monitor.py <消息内容>")
        print("")
        print("示例：")
        print("  python3 auto_task_monitor.py '发送天气预报邮件到 test@example.com'")
        print("  python3 auto_task_monitor.py '查询北京天气'")
        sys.exit(0)
    
    message = ' '.join(sys.argv[1:])
    
    print(f"测试消息：{message}")
    print(f"是否任务指令：{'是' if is_task_instruction(message) else '否'}")
    
    if is_task_instruction(message):
        print("")
        start_task_monitoring(message)
