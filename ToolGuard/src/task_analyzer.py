#!/usr/bin/env python3
"""
ToolGuard 任务分析器

根据用户任务/指令确定备选工具集
"""

import yaml
from pathlib import Path
from typing import Dict, List, Set

# 预定义的任务 - 工具映射
DEFAULT_TASK_TOOL_MAPPING = {
    # 邮件相关任务
    'email': ['message', 'himalaya', 'gog', 'mail-send'],
    '邮件': ['message', 'himalaya', 'gog', 'mail-send'],
    'send email': ['message', 'himalaya', 'gog', 'mail-send'],
    
    # 文件操作任务
    'file': ['read', 'write', 'exec'],
    '文件': ['read', 'write', 'exec'],
    'delete': ['read', 'write', 'exec', 'rm', 'trash'],
    '删除': ['read', 'write', 'exec', 'rm', 'trash'],
    
    # 天气查询任务
    'weather': ['web_search', 'web_fetch', 'exec'],
    '天气': ['web_search', 'web_fetch', 'exec'],
    
    # 代码管理任务
    'git': ['git', 'exec', 'read', 'write'],
    'push': ['git', 'exec'],
    'commit': ['git', 'exec'],
    
    # 网络请求任务
    'curl': ['curl', 'exec'],
    'http': ['curl', 'web_fetch', 'exec'],
    'api': ['curl', 'web_fetch', 'exec'],
    
    # 远程连接任务
    'ssh': ['ssh', 'exec'],
    'remote': ['ssh', 'scp', 'rsync', 'exec'],
    'scp': ['scp', 'exec'],
    'rsync': ['rsync', 'exec'],
    
    # 浏览器任务
    'browser': ['browser'],
    '网页': ['browser', 'web_fetch'],
    'screenshot': ['browser'],
    
    # 飞书办公任务
    'feishu': ['feishu_doc', 'feishu_drive', 'feishu_bitable', 'feishu_chat'],
    '飞书': ['feishu_doc', 'feishu_drive', 'feishu_bitable', 'feishu_chat'],
    'doc': ['feishu_doc'],
    '文档': ['feishu_doc'],
    
    # 系统管理任务
    'system': ['exec', 'gateway', 'cron', 'nodes'],
    '配置': ['gateway', 'read', 'write'],
    '定时': ['cron', 'exec'],
    
    # 通用任务
    'search': ['web_search', 'memory_search'],
    '搜索': ['web_search', 'memory_search'],
    'read': ['read', 'web_fetch', 'memory_get'],
    '写': ['write', 'message', 'mail-send'],
}

class TaskAnalyzer:
    """任务分析器"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(
            Path.home() / ".openclaw/workspace/ToolGuard/config/task_tool_mapping.yaml"
        )
        self.task_tool_mapping = self._load_mapping()
        self.all_tools = self._get_all_tools()
        self.current_task = None
        self.allowed_tools: Set[str] = set()
    
    def _load_mapping(self) -> Dict:
        """加载任务 - 工具映射"""
        try:
            config_file = Path(self.config_path).expanduser()
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    custom_mapping = yaml.safe_load(f) or {}
                # 合并自定义和默认映射
                merged = DEFAULT_TASK_TOOL_MAPPING.copy()
                merged.update(custom_mapping)
                return merged
            else:
                return DEFAULT_TASK_TOOL_MAPPING
        except Exception as e:
            print(f"加载任务 - 工具映射失败：{e}")
            return DEFAULT_TASK_TOOL_MAPPING
    
    def _get_all_tools(self) -> Set[str]:
        """获取所有可用工具"""
        all_tools = set()
        for tools in DEFAULT_TASK_TOOL_MAPPING.values():
            all_tools.update(tools)
        # 添加 OpenClaw 内置工具
        all_tools.update([
            'read', 'write', 'edit', 'exec', 'process',
            'web_search', 'web_fetch', 'browser', 'canvas',
            'nodes', 'cron', 'message', 'tts', 'gateway',
            'memory_search', 'memory_get', 'sessions_list',
            'sessions_history', 'sessions_send', 'sessions_spawn',
            'subagents', 'session_status', 'agents_list',
            'feishu_doc', 'feishu_drive', 'feishu_wiki',
            'feishu_bitable', 'feishu_chat', 'feishu_app_scopes',
            'himalaya', 'gog', 'git', 'curl', 'ssh', 'scp',
            'rsync', 'trash', 'rm', 'mail-send'
        ])
        return all_tools
    
    def analyze_task(self, task: str) -> Set[str]:
        """
        分析任务，确定备选工具集
        
        参数：
            task: 用户任务/指令
            
        返回：
            备选工具集
        """
        self.current_task = task
        task_lower = task.lower()
        
        # 1. 关键词匹配
        matched_tools = set()
        for keyword, tools in self.task_tool_mapping.items():
            if keyword.lower() in task_lower:
                matched_tools.update(tools)
        
        # 2. 如果没有匹配到，使用默认工具集
        if not matched_tools:
            matched_tools = {'read', 'write', 'web_search', 'web_fetch', 'message'}
        
        self.allowed_tools = matched_tools
        return matched_tools
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        """
        检查工具是否在备选工具集中
        
        参数：
            tool_name: 工具名称
            
        返回：
            是否允许
        """
        return tool_name in self.allowed_tools
    
    def get_allowed_tools(self) -> Set[str]:
        """获取当前备选工具集"""
        return self.allowed_tools
    
    def add_allowed_tool(self, tool_name: str):
        """添加工具到备选集"""
        self.allowed_tools.add(tool_name)
    
    def reset(self):
        """重置分析器"""
        self.current_task = None
        self.allowed_tools = set()
    
    def save_mapping(self):
        """保存自定义映射"""
        try:
            config_file = Path(self.config_path).expanduser()
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump({}, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            print(f"保存映射失败：{e}")


# 全局实例
_analyzer = None

def get_analyzer() -> TaskAnalyzer:
    """获取分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = TaskAnalyzer()
    return _analyzer
