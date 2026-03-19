#!/usr/bin/env python3
"""
ToolGuard - OpenClaw 工具调用监控系统 v3.0.0

新增功能：
- 任务级工具集监控
- 备选工具集管理
- 异常工具调用拦截
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import yaml

# 导入任务分析器
from task_analyzer import get_analyzer, TaskAnalyzer

# ============================================================================
# 配置
# ============================================================================

DEFAULT_CONFIG_PATH = str(Path.home() / ".openclaw/workspace/ToolGuard/config/toolguard_config.yaml")
DEFAULT_RISK_TOOL_LIST_PATH = str(Path.home() / ".openclaw/workspace/ToolGuard/config/risk_tool_list.json")

# ============================================================================
# ToolGuard 核心类
# ============================================================================

class ToolGuard:
    """ToolGuard 核心类 v3.0.0"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        self.risk_tools = self._load_risk_tools()
        self.pending_confirmations: Dict[str, Dict] = {}
        self.task_analyzer = get_analyzer()
        
        # 任务级监控
        self.task_mode = False
        self.current_task = None
        self.allowed_tools: Set[str] = set()
        
        self._setup_logging()
        self._setup_storage()
        self._load_pending_confirmations()
        self._log("ToolGuard v3.0.0 初始化完成")
    
    def _setup_storage(self):
        """设置文件存储"""
        storage_dir = Path.home() / ".openclaw/workspace/ToolGuard/storage"
        storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = storage_dir / "pending_confirmations.json"
        self.task_storage_file = storage_dir / "task_state.json"
        
        if not self.storage_file.exists():
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def _load_pending_confirmations(self):
        """从文件加载待处理确认"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.pending_confirmations = json.load(f)
                self.cleanup_expired()
                self._save_pending_confirmations()
        except Exception as e:
            self._log(f"加载待处理确认失败：{e}", "ERROR")
            self.pending_confirmations = {}
    
    def _save_pending_confirmations(self):
        """保存待处理确认到文件"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.pending_confirmations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"保存待处理确认失败：{e}", "ERROR")
    
    def _save_task_state(self):
        """保存任务状态"""
        try:
            task_state = {
                'task_mode': self.task_mode,
                'current_task': self.current_task,
                'allowed_tools': list(self.allowed_tools),
                'timestamp': datetime.now().isoformat()
            }
            with open(self.task_storage_file, 'w', encoding='utf-8') as f:
                json.dump(task_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"保存任务状态失败：{e}", "ERROR")
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            config_file = Path(self.config_path).expanduser()
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                return {}
        except Exception as e:
            logging.error(f"加载配置文件失败：{e}")
            return {}
    
    def _load_risk_tools(self) -> Dict:
        """加载危险工具列表"""
        risk_tool_path = self.config.get('risk_tools', {}).get('config_file', DEFAULT_RISK_TOOL_LIST_PATH)
        try:
            risk_tool_file = Path(risk_tool_path).expanduser()
            if risk_tool_file.exists():
                with open(risk_tool_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"risk_tools": [], "safe_tools": []}
        except Exception as e:
            logging.error(f"加载 risk tool 列表失败：{e}")
            return {"risk_tools": [], "safe_tools": []}
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path.home() / ".openclaw/workspace/ToolGuard/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = self.config.get('general', {}).get('log_file', str(log_dir / "toolguard.log"))
        log_file = Path(log_file).expanduser()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        log_level = self.config.get('general', {}).get('log_level', 'INFO')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s | %(levelname)s | %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file, encoding='utf-8')
            ]
        )
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} | {level} | {message}\n"
        logging.log(getattr(logging, level), message)
    
    # ========================================================================
    # 任务级监控功能 (v3.0.0 新增)
    # ========================================================================
    
    def start_task_monitoring(self, task: str) -> Set[str]:
        """
        开始任务监控
        
        参数：
            task: 用户任务/指令
            
        返回：
            备选工具集
        """
        self.task_mode = True
        self.current_task = task
        
        # 分析任务，确定备选工具集
        self.allowed_tools = self.task_analyzer.analyze_task(task)
        
        self._log(f"开始任务监控：{task}")
        self._log(f"备选工具集：{', '.join(self.allowed_tools)}")
        
        # 保存任务状态
        self._save_task_state()
        
        return self.allowed_tools
    
    def check_tool_in_task(self, tool_name: str, action: str = "*") -> Tuple[bool, str]:
        """
        在任务模式下检查工具调用
        
        参数：
            tool_name: 工具名称
            action: 动作
            
        返回：
            (need_confirmation, reason)
        """
        if not self.task_mode:
            return False, ""
        
        # 检查是否在备选工具集中
        if self.task_analyzer.is_tool_allowed(tool_name):
            self._log(f"✅ 工具 {tool_name} 在备选集中，允许执行")
            return False, ""
        else:
            reason = f"工具 {tool_name} 不在当前任务的备选工具集中"
            self._log(f"⚠️ {reason}")
            return True, reason
    
    def stop_task_monitoring(self):
        """停止任务监控"""
        self.task_mode = False
        self.current_task = None
        self.allowed_tools = set()
        self.task_analyzer.reset()
        self._log("停止任务监控")
    
    def add_to_allowed_tools(self, tool_name: str):
        """添加工具到备选集"""
        self.allowed_tools.add(tool_name)
        self.task_analyzer.add_allowed_tool(tool_name)
        self._save_task_state()
        self._log(f"添加工具到备选集：{tool_name}")
    
    def get_task_state(self) -> Dict:
        """获取任务状态"""
        return {
            'task_mode': self.task_mode,
            'current_task': self.current_task,
            'allowed_tools': list(self.allowed_tools)
        }
    
    # ========================================================================
    # 原有功能（风险工具检查）
    # ========================================================================
    
    def check_tool_call(self, tool_name: str, action: str = "*", parameters: Dict = None) -> Tuple[bool, str, str]:
        """
        检查工具调用是否需要确认
        
        返回：
            (need_confirmation, reason, risk_level)
        """
        parameters = parameters or {}
        
        # 任务模式下优先检查
        if self.task_mode:
            need_confirm, reason = self.check_tool_in_task(tool_name, action)
            if need_confirm:
                return True, reason, 'high'
        
        # 检查是否在 risk tool 列表中
        for risk_tool in self.risk_tools.get("risk_tools", []):
            if risk_tool["tool_name"].lower() != tool_name.lower():
                continue
            if risk_tool["action"] != "*" and risk_tool["action"].lower() != action.lower():
                continue
            if risk_tool.get("require_confirmation", False):
                return (
                    True,
                    risk_tool.get("reason", "危险工具调用"),
                    risk_tool.get("risk_level", "medium")
                )
        
        # 检查是否在 safe tool 列表中
        for safe_tool in self.risk_tools.get("safe_tools", []):
            if safe_tool["tool_name"].lower() != tool_name.lower():
                continue
            if "action" in safe_tool:
                if safe_tool["action"].lower() != action.lower():
                    continue
            return False, "", "low"
        
        return False, "", "low"
    
    def request_confirmation(self, tool_name: str, action: str, parameters: Dict, 
                           reason: str, risk_level: str = "medium") -> str:
        """请求用户确认"""
        confirmation_id = str(uuid.uuid4())
        
        timeout = self.config.get('confirmation', {}).get('default_timeout', 300)
        risk_levels = self.risk_tools.get('risk_levels', {})
        if risk_level in risk_levels:
            timeout = risk_levels[risk_level].get('timeout', timeout)
        
        self.pending_confirmations[confirmation_id] = {
            "confirmation_id": confirmation_id,
            "tool_name": tool_name,
            "action": action,
            "parameters": {k: str(v)[:200] for k, v in parameters.items()},
            "reason": reason,
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=timeout)).isoformat(),
            "status": "pending",
            "response_time": None,
            "user_id": "unknown",
            "task_mode": self.task_mode,
            "current_task": self.current_task
        }
        
        self._log(f"等待用户确认：{confirmation_id} - {tool_name}.{action} (风险等级：{risk_level})")
        self._save_pending_confirmations()
        
        return confirmation_id
    
    def get_confirmation_status(self, confirmation_id: str) -> Optional[Dict]:
        """获取确认状态"""
        conf = self.pending_confirmations.get(confirmation_id)
        if not conf:
            return None
        
        if conf["status"] == "pending":
            expires_at = datetime.fromisoformat(conf["expires_at"])
            if datetime.now() > expires_at:
                conf["status"] = "expired"
                self._log(f"确认超时：{confirmation_id}", "WARNING")
        
        return conf
    
    def set_confirmation_response(self, confirmation_id: str, approved: bool, 
                                  user_id: str = "unknown", add_to_allowed: bool = False) -> bool:
        """设置用户响应"""
        conf = self.pending_confirmations.get(confirmation_id)
        if not conf:
            self._log(f"确认 ID 不存在：{confirmation_id}", "ERROR")
            return False
        
        if conf["status"] != "pending":
            self._log(f"确认已处理：{confirmation_id} - {conf['status']}", "WARNING")
            return False
        
        conf["status"] = "approved" if approved else "denied"
        conf["response_time"] = datetime.now().isoformat()
        conf["user_id"] = user_id
        
        # 如果用户确认且选择添加到备选集
        if approved and add_to_allowed and self.task_mode:
            self.add_to_allowed_tools(conf["tool_name"])
            self._log(f"工具 {conf['tool_name']} 已添加到备选集")
        
        self._log(f"用户响应：{confirmation_id} - {'✅ 允许' if approved else '❌ 拒绝'}")
        self._audit_log(
            tool_name=conf["tool_name"],
            action=conf["action"],
            parameters=conf["parameters"],
            confirmed=True,
            approved=approved,
            confirmation_id=confirmation_id
        )
        self._save_pending_confirmations()
        
        return True
    
    def _audit_log(self, tool_name: str, action: str, parameters: Dict, 
                   confirmed: bool, approved: bool = None, confirmation_id: str = None):
        """记录审计日志"""
        audit_enabled = self.config.get('audit', {}).get('log_confirmations', True)
        if not audit_enabled:
            return
        
        audit_file = self.config.get('general', {}).get('audit_file', 
                    str(Path.home() / ".openclaw/workspace/ToolGuard/logs/audit.jsonl"))
        audit_file = Path(audit_file).expanduser()
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "confirmation_id": confirmation_id,
            "tool_name": tool_name,
            "action": action,
            "parameters": parameters,
            "confirmed": confirmed,
            "approved": approved,
            "task_mode": self.task_mode,
            "current_task": self.current_task
        }
        
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def cleanup_expired(self) -> int:
        """清理超时的确认请求"""
        now = datetime.now()
        expired_count = 0
        
        for conf_id, conf in list(self.pending_confirmations.items()):
            if conf["status"] == "pending":
                expires_at = datetime.fromisoformat(conf["expires_at"])
                if now > expires_at:
                    conf["status"] = "expired"
                    expired_count += 1
                    self._log(f"确认超时：{conf_id}", "WARNING")
                    self._audit_log(
                        tool_name=conf["tool_name"],
                        action=conf["action"],
                        parameters=conf["parameters"],
                        confirmed=True,
                        approved=False,
                        confirmation_id=conf_id
                    )
        
        if expired_count > 0:
            self._log(f"清理了 {expired_count} 个超时的确认请求")
        
        return expired_count
    
    def get_pending_confirmations(self) -> List[Dict]:
        """获取所有待处理的确认请求"""
        return [
            conf for conf in self.pending_confirmations.values()
            if conf["status"] == "pending"
        ]
    
    def reload_risk_tools(self):
        """重新加载 risk tool 列表"""
        self.risk_tools = self._load_risk_tools()
        self._log("重新加载 risk tool 列表完成")
    
    def save_risk_tools(self, risk_tools_data: Dict) -> bool:
        """保存 risk tool 列表"""
        risk_tool_path = self.config.get('risk_tools', {}).get('config_file', DEFAULT_RISK_TOOL_LIST_PATH)
        try:
            risk_tool_file = Path(risk_tool_path).expanduser()
            risk_tool_file.parent.mkdir(parents=True, exist_ok=True)
            
            existing = {}
            if risk_tool_file.exists():
                with open(risk_tool_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            
            existing.update(risk_tools_data)
            existing['last_updated'] = datetime.now().strftime("%Y-%m-%d")
            
            with open(risk_tool_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            
            self.risk_tools = existing
            self._log("Risk tool 列表已保存")
            return True
        except Exception as e:
            self._log(f"保存 risk tool 列表失败：{e}", "ERROR")
            return False


# ============================================================================
# OpenClaw Hook 接口
# ============================================================================

_guard = None

def get_guard() -> ToolGuard:
    """获取 ToolGuard 实例"""
    global _guard
    if _guard is None:
        _guard = ToolGuard()
    return _guard


async def on_tool_call(event: dict) -> dict:
    """OpenClaw tool call hook"""
    guard = get_guard()
    
    tool_name = event.get("tool_name", "")
    action = event.get("action", "*")
    parameters = event.get("parameters", {})
    
    need_confirmation, reason, risk_level = guard.check_tool_call(tool_name, action, parameters)
    
    if not need_confirmation:
        return None
    
    confirmation_id = guard.request_confirmation(tool_name, action, parameters, reason, risk_level)
    
    return {
        "wait_for_confirmation": True,
        "confirmation_id": confirmation_id,
        "message": f"⚠️ 危险工具调用：{tool_name}.{action}\n原因：{reason}\n风险等级：{risk_level}\n请确认是否允许。",
        "tool_name": tool_name,
        "action": action,
        "parameters": parameters,
        "risk_level": risk_level,
    }


# ============================================================================
# CLI 接口
# ============================================================================

if __name__ == "__main__":
    import sys
    
    guard = ToolGuard()
    
    if len(sys.argv) < 2:
        print("ToolGuard v3.0.0 - OpenClaw 工具调用监控系统")
        print("")
        print("用法：")
        print("  python3 toolguard.py check <tool_name> [action] [parameters]")
        print("  python3 toolguard.py task <task_description>")
        print("  python3 toolguard.py status [confirmation_id]")
        print("  python3 toolguard.py pending")
        print("")
        print("示例：")
        print("  python3 toolguard.py check message send '{\"to\":\"test@example.com\"}'")
        print("  python3 toolguard.py task '发送天气预报邮件'")
        print("  python3 toolguard.py pending")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "check":
        if len(sys.argv) < 3:
            print("用法：python3 toolguard.py check <tool_name> [action] [parameters]")
            sys.exit(1)
        
        tool_name = sys.argv[2]
        action = sys.argv[3] if len(sys.argv) > 3 else "*"
        parameters = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        
        need_confirmation, reason, risk_level = guard.check_tool_call(tool_name, action, parameters)
        
        if need_confirmation:
            confirmation_id = guard.request_confirmation(tool_name, action, parameters, reason, risk_level)
            
            print(f"⚠️  需要确认")
            print(f"   工具：{tool_name}.{action}")
            print(f"   原因：{reason}")
            print(f"   风险等级：{risk_level}")
            print(f"   确认 ID: {confirmation_id}")
            print(f"")
            print(f"请在 Web 界面确认：http://127.0.0.1:8767")
        else:
            print(f"✅ 安全工具，可以直接执行")
    
    elif command == "task":
        if len(sys.argv) < 3:
            print("用法：python3 toolguard.py task <task_description>")
            sys.exit(1)
        
        task = ' '.join(sys.argv[2:])
        allowed_tools = guard.start_task_monitoring(task)
        
        print(f"📋 任务监控已启动")
        print(f"   任务：{task}")
        print(f"   备选工具集：{', '.join(allowed_tools)}")
        print(f"   任务模式：{'✅ 启用' if guard.task_mode else '❌ 禁用'}")
    
    elif command == "status":
        if len(sys.argv) < 3:
            print("用法：python3 toolguard.py status <confirmation_id>")
            sys.exit(1)
        
        confirmation_id = sys.argv[2]
        status = guard.get_confirmation_status(confirmation_id)
        
        if status:
            print(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 确认 ID 不存在：{confirmation_id}")
    
    elif command == "pending":
        pending = guard.get_pending_confirmations()
        
        if pending:
            print(f"待处理的确认请求：{len(pending)}")
            print("")
            for conf in pending:
                print(f"ID: {conf['confirmation_id']}")
                print(f"   工具：{conf['tool_name']}.{conf['action']}")
                print(f"   原因：{conf['reason']}")
                print(f"   风险等级：{conf['risk_level']}")
                print(f"   时间：{conf['timestamp']}")
                if conf.get('task_mode'):
                    print(f"   任务模式：是")
                    print(f"   当前任务：{conf.get('current_task', 'N/A')}")
                print("")
        else:
            print("✅ 暂无待处理的确认请求")
    
    else:
        print(f"未知命令：{command}")
        sys.exit(1)
