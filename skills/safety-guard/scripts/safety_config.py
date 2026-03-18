#!/usr/bin/env python3
"""
OpenClaw Safety Guard - Configuration Command

查看和修改安全配置。

用法:
    python safety_config.py show                    # 显示配置
    python safety_config.py set <key> <value>       # 设置配置项
    python safety_config.py add pattern <pattern>   # 添加风险模式
"""

import sys
import json
import yaml
from pathlib import Path


def get_config_path():
    """获取配置文件路径"""
    return Path(__file__).parent.parent / "config" / "safety_config.yaml"


def get_patterns_path():
    """获取模式文件路径"""
    return Path(__file__).parent.parent / "rules" / "patterns.yaml"


def load_yaml(path):
    """加载 YAML 文件"""
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def save_yaml(path, data):
    """保存 YAML 文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


def show_config():
    """显示当前配置"""
    config_path = get_config_path()
    
    if not config_path.exists():
        print(json.dumps({
            "error": "Config file not found",
            "path": str(config_path)
        }, ensure_ascii=False))
        return
    
    config = load_yaml(config_path)
    
    output = {
        "config_file": str(config_path),
        "thresholds": config.get("thresholds", {}),
        "detectors": list(config.get("detectors", {}).keys()),
        "audit_enabled": config.get("audit", {}).get("enabled", True)
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


def set_config(key, value):
    """设置配置项"""
    config_path = get_config_path()
    config = load_yaml(config_path)
    
    # 解析键路径 (如：thresholds.medium_risk)
    keys = key.split('.')
    
    # 导航到目标位置
    current = config
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    # 设置值
    current[keys[-1]] = value
    
    # 保存
    save_yaml(config_path, config)
    
    print(json.dumps({
        "success": True,
        "message": f"Set {key} = {value}",
        "config_file": str(config_path)
    }, ensure_ascii=False))


def add_pattern(pattern, category="custom"):
    """添加风险模式"""
    patterns_path = get_patterns_path()
    patterns = load_yaml(patterns_path)
    
    # 添加到指定类别
    if category not in patterns:
        patterns[category] = []
    
    if isinstance(patterns[category], list):
        if pattern not in patterns[category]:
            patterns[category].append(pattern)
            save_yaml(patterns_path, patterns)
            
            print(json.dumps({
                "success": True,
                "message": f"Added pattern '{pattern}' to category '{category}'",
                "patterns_file": str(patterns_path)
            }, ensure_ascii=False))
        else:
            print(json.dumps({
                "success": False,
                "message": f"Pattern '{pattern}' already exists in '{category}'"
            }, ensure_ascii=False))
    else:
        print(json.dumps({
            "error": f"Category '{category}' is not a list"
        }, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "No command provided",
            "usage": "safety_config.py <command> [args]",
            "commands": ["show", "set", "add"]
        }, ensure_ascii=False))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "show":
        show_config()
    
    elif command == "set":
        if len(sys.argv) < 4:
            print(json.dumps({
                "error": "Usage: safety_config.py set <key> <value>"
            }, ensure_ascii=False))
            sys.exit(1)
        
        key = sys.argv[2]
        value = sys.argv[3]
        
        # 尝试转换为数字
        try:
            value = float(value)
        except ValueError:
            pass
        
        set_config(key, value)
    
    elif command == "add":
        if len(sys.argv) < 5 or sys.argv[2] != "pattern":
            print(json.dumps({
                "error": "Usage: safety_config.py add pattern <pattern> [category]"
            }, ensure_ascii=False))
            sys.exit(1)
        
        pattern = sys.argv[3]
        category = sys.argv[4] if len(sys.argv) > 4 else "custom"
        
        add_pattern(pattern, category)
    
    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "valid_commands": ["show", "set", "add"]
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
