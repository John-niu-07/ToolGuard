#!/usr/bin/env python3
"""
ToolGuard - OpenClaw 工具调用监控系统

核心逻辑：
- 备选工具集：初始化时包含所有工具，工具调用直接执行
- 禁止工具集：初始化时为空，工具调用需要确认
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

# 所有可用工具列表
ALL_TOOLS = {
    'exec', 'read', 'write', 'edit', 'browser', 'canvas', 'nodes',
    'web_search', 'web_fetch', 'memory_search', 'memory_get',
    'message', 'tts', 'gateway', 'feishu_doc', 'feishu_drive',
    'feishu_wiki', 'feishu_bitable', 'feishu_chat', 'himalaya',
    'gog', 'git', 'curl', 'ssh', 'scp', 'rsync', 'trash'
}

class ToolGuard:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(
            Path.home() / ".openclaw/workspace/ToolGuard/config/toolguard_config.json"
        )
        self.risk_tools_path = Path.home() / ".openclaw/workspace/ToolGuard/config/risk_tool_list.json"
        self.pending_path = Path.home() / ".openclaw/workspace/ToolGuard/storage/pending_confirmations.json"
        
        # 加载配置
        self.config = self._load_config()
        self.risk_tools = self._load_risk_tools()
        self.pending_confirmations = self._load_pending_confirmations()
        
        # 初始化备选工具集和禁止工具集
        self.allowed_tools: Set[str] = set(self.config.get('allowed_tools', ALL_TOOLS))
        self.blocked_tools: Set[str] = set(self.config.get('blocked_tools', []))
        
        # 临时允许列表（确认后 5 分钟内不需要再次确认）
        self.temp_allowed: Dict[str, datetime] = {}  # tool_name -> expires_at
        
        # 任务监控
        self.task_mode = False
        self.current_task = None
        
        self._log("ToolGuard 初始化完成")
        self._log(f"备选工具集：{len(self.allowed_tools)} 个工具")
        self._log(f"禁止工具集：{len(self.blocked_tools)} 个工具")
    
    def _load_config(self) -> Dict:
        """加载 ToolGuard 配置"""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_config(self):
        """保存 ToolGuard 配置"""
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            'allowed_tools': list(self.allowed_tools),
            'blocked_tools': list(self.blocked_tools),
            'task_mode': self.task_mode,
            'current_task': self.current_task
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def _load_risk_tools(self) -> Dict:
        """加载风险工具列表"""
        if self.risk_tools_path.exists():
            with open(self.risk_tools_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'safe_tools': [], 'risk_tools': []}
    
    def _load_pending_confirmations(self) -> Dict:
        """加载待确认请求"""
        if self.pending_path.exists():
            with open(self.pending_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if 'pending' in data else {'pending': []}
        return {'pending': []}
    
    def _save_pending_confirmations(self):
        """保存待确认请求"""
        self.pending_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.pending_path, 'w', encoding='utf-8') as f:
            json.dump(self.pending_confirmations, f, ensure_ascii=False, indent=2)
    
    def _log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"{timestamp} | {message}\n"
        print(log_line.strip())
        
        # 写入日志文件
        log_file = Path.home() / ".openclaw/workspace/ToolGuard/logs/toolguard.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line)
    
    def check_tool_call(self, tool_name: str, action: str = "*", parameters: Dict = None) -> Tuple[bool, str, str]:
        """
        检查工具调用是否需要确认
        
        新逻辑：
        - 如果工具在备选工具集中 → 直接放行
        - 如果工具在临时允许列表中 → 直接放行
        - 如果工具在禁止工具集中 → 需要确认
        
        返回：
            (need_confirmation, reason, risk_level)
        """
        parameters = parameters or {}
        
        # 清理过期的临时允许
        self._cleanup_temp_allowed()
        
        self._log(f"检查工具调用：{tool_name}.{action}")
        
        # 检查是否在备选工具集中
        if tool_name in self.allowed_tools:
            self._log(f"✅ 工具 {tool_name} 在备选工具集中，直接放行")
            return False, "", "low"
        
        # 检查是否在临时允许列表中
        if tool_name in self.temp_allowed:
            expires_at = self.temp_allowed[tool_name]
            self._log(f"✅ 工具 {tool_name} 在临时允许列表中（过期：{expires_at}），直接放行")
            return False, "", "low"
        
        # 检查是否在禁止工具集中
        if tool_name in self.blocked_tools:
            reason = f"工具 {tool_name} 在禁止工具集中，需要用户确认"
            self._log(f"⚠️ {reason}")
            return True, reason, "medium"
        
        # 未知工具（不在任何集合中）- 默认需要确认
        reason = f"未知工具 {tool_name}，需要用户确认"
        self._log(f"⚠️ {reason}")
        return True, reason, "medium"
    
    def _cleanup_temp_allowed(self):
        """清理过期的临时允许"""
        now = datetime.now()
        expired = [tool for tool, expires_at in self.temp_allowed.items() if expires_at < now]
        for tool in expired:
            del self.temp_allowed[tool]
            self._log(f"临时允许已过期：{tool}")
    
    def add_temp_allowed(self, tool_name: str, duration_seconds: int = 120):
        """添加临时允许"""
        expires_at = datetime.now() + timedelta(seconds=duration_seconds)
        self.temp_allowed[tool_name] = expires_at
        self._log(f"✅ 工具 {tool_name} 已临时允许（{duration_seconds}秒={duration_seconds//60}分钟，过期：{expires_at}）")
    
    def request_confirmation(self, tool_name: str, action: str, parameters: Dict, 
                           reason: str, risk_level: str = "medium") -> str:
        """请求用户确认"""
        confirmation_id = str(uuid.uuid4())
        
        # 获取超时配置
        timeout = self.config.get('confirmation', {}).get('default_timeout', 300)
        
        confirmation = {
            'confirmation_id': confirmation_id,
            'tool_name': tool_name,
            'action': action,
            'parameters': parameters,
            'reason': reason,
            'risk_level': risk_level,
            'timestamp': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=timeout)).isoformat(),
            'status': 'pending',
            'response_time': None,
            'user_id': 'unknown',
            'task_mode': self.task_mode,
            'current_task': self.current_task
        }
        
        self.pending_confirmations['pending'].append(confirmation)
        self._save_pending_confirmations()
        
        self._log(f"创建待确认请求：{confirmation_id} ({tool_name}.{action})")
        
        # 发送 WebChat 提示
        self._send_webchat_notification(tool_name, action, confirmation_id)
        
        return confirmation_id
    
    def _send_webchat_notification(self, tool_name: str, action: str, confirmation_id: str):
        """发送 WebChat 通知"""
        try:
            # 使用 OpenClaw 的 sessions_send 发送 WebChat 消息
            import subprocess
            message = f"⚠️ 工具调用需要确认\n\n工具：{tool_name}.{action}\n\n请前往 Web UI 的「待确认请求」页面查看并确认。\n\nWeb UI 地址：http://127.0.0.1:8767"
            
            # 记录日志
            self._log(f"📢 WebChat 通知：{message}")
            
            # 注意：这里无法直接发送 WebChat 消息，因为 ToolGuard 是独立服务
            # 实际项目中可以通过以下方式实现：
            # 1. 调用 OpenClaw Gateway API
            # 2. 使用 sessions_send 工具
            # 3. 通过 webhook 通知
            
        except Exception as e:
            self._log(f"发送 WebChat 通知失败：{e}")
    
    def respond_confirmation(self, confirmation_id: str, approved: bool, user_id: str = 'unknown') -> bool:
        """响应用户确认"""
        for confirmation in self.pending_confirmations['pending']:
            if confirmation['confirmation_id'] == confirmation_id:
                if confirmation['status'] != 'pending':
                    self._log(f"确认请求已处理：{confirmation_id}")
                    return False
                
                confirmation['status'] = 'approved' if approved else 'denied'
                confirmation['response_time'] = datetime.now().isoformat()
                confirmation['user_id'] = user_id
                
                self._save_pending_confirmations()
                
                if approved:
                    # 添加临时允许（2 分钟）
                    tool_name = confirmation['tool_name']
                    self.add_temp_allowed(tool_name, duration_seconds=120)
                    self._log(f"✅ 已批准确认请求：{confirmation_id}，工具 {tool_name} 临时允许 2 分钟")
                else:
                    # 拒绝时清理临时允许列表，确保工具不会被执行
                    tool_name = confirmation['tool_name']
                    if tool_name in self.temp_allowed:
                        del self.temp_allowed[tool_name]
                    self._log(f"❌ 已拒绝确认请求：{confirmation_id}，工具 {tool_name} 已被拒绝")
                
                return True
        
        self._log(f"未找到确认请求：{confirmation_id}")
        return False
    
    def move_tool_to_blocked(self, tool_name: str):
        """将工具从备选工具集移至禁止工具集"""
        if tool_name in self.allowed_tools:
            self.allowed_tools.remove(tool_name)
            self.blocked_tools.add(tool_name)
            self._save_config()
            self._log(f"工具 {tool_name} 已移至禁止工具集")
            return True
        return False
    
    def move_tool_to_allowed(self, tool_name: str):
        """将工具从禁止工具集移至备选工具集"""
        if tool_name in self.blocked_tools:
            self.blocked_tools.remove(tool_name)
            self.allowed_tools.add(tool_name)
            self._save_config()
            self._log(f"工具 {tool_name} 已移至备选工具集")
            return True
        return False
    
    def get_tool_sets(self) -> Dict:
        """获取工具集信息"""
        return {
            'all_tools': list(ALL_TOOLS),
            'allowed_tools': list(self.allowed_tools),
            'blocked_tools': list(self.blocked_tools),
            'allowed_count': len(self.allowed_tools),
            'blocked_count': len(self.blocked_tools)
        }
    
    def get_pending_confirmations(self) -> List[Dict]:
        """获取待确认请求列表"""
        # 清理过期的确认请求
        now = datetime.now()
        self.pending_confirmations['pending'] = [
            c for c in self.pending_confirmations['pending']
            if datetime.fromisoformat(c['expires_at']) > now and c['status'] == 'pending'
        ]
        self._save_pending_confirmations()
        
        return self.pending_confirmations['pending']
    
    def update_current_task(self, task: str, channel: str = 'unknown'):
        """更新当前任务"""
        self.current_task = task
        self.task_mode = True
        self._log(f"更新当前任务 from {channel}: {task}")
        self._save_config()
    
    def clear_pending_confirmations(self) -> int:
        """清理所有待确认请求 - 当用户输入新内容时调用"""
        pending_count = len(self.pending_confirmations.get('pending', []))
        
        if pending_count > 0:
            # 真正从 pending 列表中删除所有待确认请求（不只是标记为 cancelled）
            self.pending_confirmations['pending'] = []
            
            self._save_pending_confirmations()
            self._log(f"已清理 {pending_count} 个待确认请求（用户输入新内容）")
        
        # 同时清理临时允许列表 - 防止工具被意外放行
        if self.temp_allowed:
            cleared_count = len(self.temp_allowed)
            self.temp_allowed.clear()
            self._log(f"已清理 {cleared_count} 个临时允许（用户输入新内容）")
        
        return pending_count
    
    def update_current_task(self, task: str, channel: str = 'unknown'):
        """更新当前任务 - 不清理临时允许列表"""
        # 注意：这里不清理临时允许列表
        # 临时允许列表只在超时后过期，或者有待确认请求且用户输入新内容时才清理
        self.current_task = task
        self.task_mode = True
        self._log(f"更新当前任务 from {channel}: {task}")
        self._save_config()
