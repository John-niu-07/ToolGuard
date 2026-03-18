"""
OpenClaw Safety Guard - Audit Logger
审计日志模块：记录所有安全相关事件
"""

import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class SafetyAuditLogger:
    """安全审计日志记录器"""
    
    def __init__(
        self,
        log_file: str = "audit/safety_audit.log",
        log_level: str = "INFO",
        retention_days: int = 30
    ):
        self.base_path = Path(__file__).parent.parent
        self.log_path = self.base_path / log_file
        
        # 确保目录存在
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        self.logger = logging.getLogger("SafetyAudit")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # 文件处理器
        file_handler = logging.FileHandler(self.log_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 避免重复添加
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
        
        self.retention_days = retention_days
    
    def log_request(
        self,
        user_id: str,
        input_text: str,
        risk_score: float,
        decision: str,
        reason: Optional[str] = None,
        policy_id: Optional[str] = None
    ):
        """记录请求分析结果"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "request_analyzed",
            "user_id": user_id,
            "input_preview": input_text[:200] + "..." if len(input_text) > 200 else input_text,
            "risk_score": risk_score,
            "decision": decision,  # allowed, warned, blocked
            "reason": reason,
            "policy_id": policy_id
        }
        
        log_level = logging.WARNING if decision == "blocked" else logging.INFO
        self.logger.log(log_level, json.dumps(log_entry, ensure_ascii=False))
    
    def log_blocked(
        self,
        user_id: str,
        input_text: str,
        policy_id: str,
        risk_score: float,
        patterns_matched: list
    ):
        """记录被拦截的请求"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "request_blocked",
            "user_id": user_id,
            "input_preview": input_text[:200] + "..." if len(input_text) > 200 else input_text,
            "policy_id": policy_id,
            "risk_score": risk_score,
            "patterns_matched": patterns_matched
        }
        
        self.logger.warning(json.dumps(log_entry, ensure_ascii=False))
    
    def log_warning(
        self,
        user_id: str,
        input_text: str,
        policy_id: str,
        risk_score: float
    ):
        """记录警告请求"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "request_warned",
            "user_id": user_id,
            "input_preview": input_text[:200] + "..." if len(input_text) > 200 else input_text,
            "policy_id": policy_id,
            "risk_score": risk_score
        }
        
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def log_appeal(
        self,
        user_id: str,
        original_input: str,
        appeal_reason: str,
        outcome: Optional[str] = None
    ):
        """记录用户申诉"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "appeal_submitted",
            "user_id": user_id,
            "original_input_preview": original_input[:200],
            "appeal_reason": appeal_reason,
            "outcome": outcome  # approved, rejected, pending
        }
        
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """记录错误"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        self.logger.error(json.dumps(log_entry, ensure_ascii=False))
    
    def cleanup_old_logs(self):
        """清理过期日志"""
        # 简单实现：如果日志文件过大，可以轮转
        # 生产环境建议使用 logging.handlers.TimedRotatingFileHandler
        pass


# 全局实例
_audit_logger: Optional[SafetyAuditLogger] = None


def get_audit_logger(config: Optional[Dict] = None) -> SafetyAuditLogger:
    """获取审计日志器实例"""
    global _audit_logger
    
    if _audit_logger is None:
        if config:
            _audit_logger = SafetyAuditLogger(
                log_file=config.get("audit", {}).get("log_file", "audit/safety_audit.log"),
                log_level=config.get("audit", {}).get("log_level", "INFO"),
                retention_days=config.get("audit", {}).get("retention_days", 30)
            )
        else:
            _audit_logger = SafetyAuditLogger()
    
    return _audit_logger
