#!/usr/bin/env python3
"""
ToolGuard 任务分析器

根据用户任务/指令确定备选工具集
从 Risk Tools 管理中的"安全工具"列表选取备选工具
"""

import json
from pathlib import Path
from typing import Dict, List, Set

# 预定义的任务 - 工具映射（用于识别任务类型）
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
        self.risk_tool_list_path = str(
            Path.home() / ".openclaw/workspace/ToolGuard/config/risk_tool_list.json"
        )
        self.task_tool_mapping = self._load_mapping()
        self.safe_tools = self._load_safe_tools()
        self.current_task = None
        self.allowed_tools: Set[str] = set()
    
    def _load_mapping(self) -> Dict:
        """加载任务 - 工具映射"""
        try:
            config_file = Path(self.config_path).expanduser()
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    custom_mapping = json.load(f) or {}
                # 合并自定义和默认映射
                merged = DEFAULT_TASK_TOOL_MAPPING.copy()
                merged.update(custom_mapping)
                return merged
            else:
                return DEFAULT_TASK_TOOL_MAPPING
        except Exception as e:
            print(f"加载任务 - 工具映射失败：{e}")
            return DEFAULT_TASK_TOOL_MAPPING
    
    def _load_safe_tools(self) -> Set[str]:
        """从 risk_tool_list.json 加载安全工具列表"""
        try:
            risk_tool_file = Path(self.risk_tool_list_path).expanduser()
            if risk_tool_file.exists():
                with open(risk_tool_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                safe_tools = set()
                for tool in data.get('safe_tools', []):
                    tool_name = tool.get('tool_name', '')
                    if tool_name:
                        safe_tools.add(tool_name)
                
                print(f"✅ 加载安全工具列表：{len(safe_tools)} 个工具")
                return safe_tools
            else:
                print(f"⚠️  Risk tool list 不存在，使用默认安全工具")
                return {'read', 'web_search', 'web_fetch', 'memory_search', 'memory_get'}
        except Exception as e:
            print(f"加载安全工具列表失败：{e}")
            return {'read', 'web_search', 'web_fetch', 'memory_search', 'memory_get'}
    
    def analyze_task(self, task: str) -> Set[str]:
        """
        分析任务，从安全工具列表中确定备选工具集
        
        参数：
            task: 用户任务/指令
            
        返回：
            备选工具集（仅包含安全工具列表中的工具）
        """
        # 每次分析任务时都重新加载安全工具列表（确保使用最新配置）
        self.safe_tools = self._load_safe_tools()
        
        self.current_task = task
        task_lower = task.lower()
        
        # 1. 关键词匹配
        matched_tools = set()
        for keyword, tools in self.task_tool_mapping.items():
            if keyword.lower() in task_lower:
                matched_tools.update(tools)
        
        # 2. 从安全工具列表中过滤
        allowed_tools = matched_tools.intersection(self.safe_tools)
        
        # 3. 如果没有匹配到，使用安全工具列表中的默认工具集
        if not allowed_tools:
            # 从安全工具列表中选择通用的只读工具
            allowed_tools = self.safe_tools.intersection({
                'read', 'web_search', 'web_fetch', 
                'memory_search', 'memory_get', 'browser'
            })
            # 如果还是没有，就使用所有安全工具
            if not allowed_tools:
                allowed_tools = self.safe_tools.copy()
        
        self.allowed_tools = allowed_tools
        print(f"📋 任务：{task}")
        print(f"✅ 备选工具集：{', '.join(sorted(allowed_tools))}")
        return allowed_tools
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        """
        检查工具是否在备选工具集中
        
        参数：
            tool_name: 工具名称
            
        返回：
            是否允许
        """
        # 首先检查是否在安全工具列表中
        if tool_name not in self.safe_tools:
            print(f"❌ 工具 {tool_name} 不在安全工具列表中")
            return False
        
        # 然后检查是否在当前任务的备选工具集中
        return tool_name in self.allowed_tools
    
    def get_allowed_tools(self) -> Set[str]:
        """获取当前备选工具集"""
        return self.allowed_tools
    
    def add_allowed_tool(self, tool_name: str):
        """添加工具到备选集"""
        if tool_name in self.safe_tools:
            self.allowed_tools.add(tool_name)
            print(f"✅ 添加工具 {tool_name} 到备选集")
        else:
            print(f"❌ 工具 {tool_name} 不在安全工具列表中，无法添加")
    
    def reset(self):
        """重置分析器"""
        self.current_task = None
        self.allowed_tools = set()
    
    def reload_safe_tools(self):
        """重新加载安全工具列表"""
        self.safe_tools = self._load_safe_tools()
        print(f"✅ 安全工具列表已重新加载：{len(self.safe_tools)} 个工具")


# 全局实例
_analyzer = None

def get_analyzer() -> TaskAnalyzer:
    """获取分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = TaskAnalyzer()
    return _analyzer
