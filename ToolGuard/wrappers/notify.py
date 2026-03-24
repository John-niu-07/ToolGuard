#!/usr/bin/env python3
"""
ToolGuard Webchat 通知模块

在等待用户确认时，发送提示消息到 webchat 界面
"""

import subprocess
import sys

def send_webchat_notification(message):
    """发送通知到 webchat 界面"""
    try:
        subprocess.run([
            'openclaw', 'message', 'send',
            '--target', 'webchat',
            message
        ], capture_output=True, timeout=5, check=False)
        return True
    except Exception:
        return False

def notify_confirmation_needed(command, risk_level, web_url):
    """发送确认提醒通知"""
    message = (
        f"🛡️ ToolGuard 提醒：请您在 ToolGuard 管理界面确认工具的执行\n\n"
        f"操作：{command}\n"
        f"风险等级：{risk_level}\n\n"
        f"访问：{web_url}"
    )
    return send_webchat_notification(message)

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        result = send_webchat_notification(' '.join(sys.argv[1:]))
        print(f"通知发送：{'✅ 成功' if result else '❌ 失败'}")
    else:
        print("用法：python3 notify.py <消息内容>")
