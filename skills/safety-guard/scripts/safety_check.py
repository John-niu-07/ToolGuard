#!/usr/bin/env python3
"""
OpenClaw Safety Guard - Safety Check Command

检查用户输入的安全性，返回风险评级和建议操作。

用法:
    python safety_check.py "用户输入"
    
输出:
    JSON 格式的安全检查结果
"""

import sys
import json
import os
from pathlib import Path

# 添加护栏核心模块路径 (优先使用 Skill 目录内的副本)
SKILL_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_PATH))

# 备用路径：独立的 openclaw-safety-guard 目录
BACKUP_GUARD_PATH = Path(__file__).parent.parent.parent.parent / "openclaw-safety-guard"
if BACKUP_GUARD_PATH.exists():
    sys.path.insert(1, str(BACKUP_GUARD_PATH))

try:
    from guardrail import SafetyGuardrail
except ImportError as e:
    print(json.dumps({
        "error": f"Safety guard module not found: {str(e)}",
        "install_hint": "Run: pip3 install PyYAML"
    }, ensure_ascii=False))
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "No input provided",
            "usage": "safety_check.py <message>"
        }, ensure_ascii=False))
        sys.exit(1)
    
    # 获取用户输入
    user_input = " ".join(sys.argv[1:])
    
    if not user_input.strip():
        print(json.dumps({
            "error": "Empty input",
            "allowed": True,
            "action": "allow"
        }, ensure_ascii=False))
        sys.exit(0)
    
    # 初始化护栏
    try:
        guard = SafetyGuardrail()
    except Exception as e:
        print(json.dumps({
            "error": f"Failed to initialize safety guard: {str(e)}",
            "allowed": True,  # Fail-open
            "action": "allow"
        }, ensure_ascii=False))
        sys.exit(0)
    
    # 执行安全检查
    try:
        result = guard.analyze(user_input, user_id="openclaw-user")
        
        # 构建输出
        output = {
            "input_preview": user_input[:100] + "..." if len(user_input) > 100 else user_input,
            "allowed": result.allowed,
            "blocked": result.blocked,
            "warn": result.warn,
            "risk_score": round(result.risk_score, 2),
            "risk_level": result.risk_level,
            "reasons": result.reasons[:3] if result.reasons else [],
            "patterns_matched": result.patterns_matched[:5] if result.patterns_matched else []
        }
        
        # 确定建议操作
        if result.blocked:
            output["action"] = "block"
            output["message"] = result.response_message
        elif result.warn:
            output["action"] = "warn"
            output["message"] = result.response_message
        else:
            output["action"] = "allow"
            output["message"] = ""
        
        # 输出 JSON
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        # Fail-open: 出错时放行
        print(json.dumps({
            "error": f"Safety check failed: {str(e)}",
            "allowed": True,
            "action": "allow",
            "fallback": True
        }, ensure_ascii=False))
        sys.exit(0)


if __name__ == "__main__":
    main()
