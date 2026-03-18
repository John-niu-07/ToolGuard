#!/usr/bin/env python3
"""
OpenClaw Safety Guard - Audit Log Viewer

查看和分析安全审计日志。

用法:
    python safety_log.py [options]
    
选项:
    --limit N       显示最近 N 条记录 (默认：10)
    --filter TYPE   过滤类型 (blocked|warned|allowed)
    --follow        实时跟踪日志 (类似 tail -f)
    --json          输出 JSON 格式
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime


def get_log_path():
    """获取日志文件路径"""
    return Path(__file__).parent.parent / "audit" / "safety_audit.log"


def parse_log_line(line):
    """解析日志行"""
    try:
        # 格式：timestamp | level | json_data
        parts = line.strip().split(' | ', 2)
        if len(parts) != 3:
            return None
        
        timestamp_str, level, json_str = parts
        data = json.loads(json_str)
        data['_timestamp'] = timestamp_str
        data['_level'] = level
        return data
    except (json.JSONDecodeError, ValueError):
        return None


def read_logs(limit=10, filter_type=None):
    """读取日志"""
    log_path = get_log_path()
    
    if not log_path.exists():
        return []
    
    logs = []
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            data = parse_log_line(line)
            if data is None:
                continue
            
            # 过滤
            if filter_type:
                event_type = data.get('event', '')
                if filter_type == 'blocked' and 'blocked' not in event_type:
                    continue
                elif filter_type == 'warned' and 'warned' not in event_type:
                    continue
                elif filter_type == 'allowed' and 'allowed' not in event_type:
                    continue
            
            logs.append(data)
    
    # 返回最近的 N 条
    return logs[-limit:] if limit > 0 else logs


def format_log_entry(data):
    """格式化日志条目"""
    timestamp = data.get('_timestamp', 'N/A')
    event = data.get('event', 'unknown')
    user_id = data.get('user_id', 'anonymous')
    risk_score = data.get('risk_score', 0)
    preview = data.get('input_preview', '')[:50]
    
    # 根据事件类型添加图标
    icon = "📝"
    if 'blocked' in event:
        icon = "🚫"
    elif 'warned' in event:
        icon = "⚠️"
    elif 'allowed' in event:
        icon = "✅"
    
    return f"{icon} [{timestamp}] {event} user={user_id} risk={risk_score:.2f} preview=\"{preview}\""


def show_logs(limit=10, filter_type=None, as_json=False):
    """显示日志"""
    logs = read_logs(limit, filter_type)
    
    if not logs:
        if as_json:
            print(json.dumps({"logs": [], "count": 0}, ensure_ascii=False))
        else:
            print("📭 没有找到日志记录")
        return
    
    if as_json:
        # 移除内部字段
        clean_logs = []
        for log in logs:
            clean_log = {k: v for k, v in log.items() if not k.startswith('_')}
            clean_logs.append(clean_log)
        
        print(json.dumps({"logs": clean_logs, "count": len(clean_logs)}, ensure_ascii=False, indent=2))
    else:
        print(f"📊 最近 {len(logs)} 条安全日志:\n")
        for log in logs:
            print(format_log_entry(log))


def follow_logs(filter_type=None):
    """实时跟踪日志"""
    log_path = get_log_path()
    
    if not log_path.exists():
        print(f"⏳ 等待日志文件创建... ({log_path})")
        while not log_path.exists():
            time.sleep(1)
    
    print(f"👁️  实时跟踪日志 (Ctrl+C 退出):\n")
    
    with open(log_path, 'r', encoding='utf-8') as f:
        # 移动到文件末尾
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if line:
                data = parse_log_line(line)
                if data:
                    # 过滤
                    if filter_type:
                        event_type = data.get('event', '')
                        if filter_type == 'blocked' and 'blocked' not in event_type:
                            continue
                        elif filter_type == 'warned' and 'warned' not in event_type:
                            continue
                        elif filter_type == 'allowed' and 'allowed' not in event_type:
                            continue
                    
                    print(format_log_entry(data))
            else:
                time.sleep(0.5)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenClaw Safety Guard - Audit Log Viewer')
    parser.add_argument('--limit', '-n', type=int, default=10, help='显示最近 N 条记录')
    parser.add_argument('--filter', '-f', choices=['blocked', 'warned', 'allowed'], help='过滤类型')
    parser.add_argument('--follow', action='store_true', help='实时跟踪日志')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    
    args = parser.parse_args()
    
    if args.follow:
        follow_logs(args.filter)
    else:
        show_logs(args.limit, args.filter, args.json)


if __name__ == "__main__":
    main()
