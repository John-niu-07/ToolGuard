#!/usr/bin/env python3
"""
ToolGuard Server - Web 服务和 API

提供：
1. 工具调用检查 API
2. 确认状态查询 API
3. 用户确认响应 API
4. Web 管理界面
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys

# 导入 ToolGuard
sys.path.insert(0, str(Path(__file__).parent))
from toolguard import ToolGuard

# ============================================================================
# 配置
# ============================================================================

CONFIG = {
    "host": "127.0.0.1",
    "port": 8767,
    "log_file": str(Path.home() / ".openclaw/workspace/ToolGuard/logs/server.log"),
}

# 初始化 ToolGuard
guard = None

# ============================================================================
# HTTP 处理器
# ============================================================================

class ToolGuardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logging.info(f"HTTP: {args[0]}")
    
    def send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_html(self, content: str, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        global guard
        
        # 重新加载待处理确认（确保与 CLI 共享数据）
        guard._load_pending_confirmations()
        
        # Web UI
        if self.path == '/':
            web_ui_file = Path(__file__).parent / "web_ui" / "index.html"
            if web_ui_file.exists():
                with open(web_ui_file, 'r', encoding='utf-8') as f:
                    self.send_html(f.read())
            else:
                self.send_json({"error": "Web UI not found"}, 404)
        
        # Web UI 静态文件
        elif self.path == '/app.js':
            js_file = Path(__file__).parent / "web_ui" / "app.js"
            if js_file.exists():
                with open(js_file, 'r', encoding='utf-8') as f:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/javascript')
                    self.end_headers()
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.send_json({"error": "File not found"}, 404)
        
        # 健康检查
        elif self.path == '/health':
            self.send_json({
                "status": "ok",
                "service": "ToolGuard",
                "version": "1.0.0",
            })
        
        # 获取待处理确认
        elif self.path == '/api/pending':
            pending = guard.get_pending_confirmations()
            self.send_json(pending)
        
        # 获取确认状态
        elif self.path.startswith('/api/confirmation/'):
            confirmation_id = self.path.split('/')[-1]
            status = guard.get_confirmation_status(confirmation_id)
            if status:
                self.send_json(status)
            else:
                self.send_json({"error": "Confirmation not found"}, 404)
        
        # 获取审计日志
        elif self.path == '/api/audit':
            audit_file = Path.home() / ".openclaw/workspace/ToolGuard/logs/audit.jsonl"
            audit_file = audit_file.expanduser()
            
            if audit_file.exists():
                logs = []
                with open(audit_file, 'r', encoding='utf-8') as f:
                    for line in f.readlines()[-50:]:  # 最近 50 条
                        try:
                            logs.append(json.loads(line))
                        except:
                            pass
                self.send_json(logs)
            else:
                self.send_json([])
        
        # 获取 Risk Tools 配置
        elif self.path == '/api/risk-tools':
            self.send_json(guard.risk_tools)
        
        # 获取任务状态
        elif self.path == '/api/task/status':
            self.send_json(guard.get_task_state())
        
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        global guard
        
        # 重新加载待处理确认（确保与 CLI 共享数据）
        guard._load_pending_confirmations()
        
        # 检查工具调用
        if self.path == '/check':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON"}, 400)
                return
            
            tool_name = data.get('tool_name', '')
            action = data.get('action', '*')
            parameters = data.get('parameters', {})
            
            # 检查是否需要确认
            need_confirmation, reason, risk_level = guard.check_tool_call(tool_name, action, parameters)
            
            if need_confirmation:
                # 请求确认
                confirmation_id = guard.request_confirmation(tool_name, action, parameters, reason, risk_level)
                
                self.send_json({
                    "need_confirmation": True,
                    "confirmation_id": confirmation_id,
                    "message": f"⚠️ 危险工具调用：{tool_name}.{action}\n原因：{reason}\n风险等级：{risk_level}\n请确认是否允许。",
                    "tool_name": tool_name,
                    "action": action,
                    "risk_level": risk_level,
                })
            else:
                self.send_json({
                    "need_confirmation": False,
                })
        
        # 设置确认响应
        elif self.path == '/api/confirm':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON"}, 400)
                return
            
            confirmation_id = data.get('confirmation_id')
            approved = data.get('approved', False)
            
            if not confirmation_id:
                self.send_json({"error": "confirmation_id required"}, 400)
                return
            
            success = guard.set_confirmation_response(confirmation_id, approved)
            
            if success:
                self.send_json({
                    "success": True,
                    "approved": approved,
                })
            else:
                self.send_json({
                    "success": False,
                    "error": "Confirmation not found or already processed",
                }, 400)
        
        # 重新加载 risk tool 列表
        elif self.path == '/api/reload':
            guard.reload_risk_tools()
            self.send_json({
                "success": True,
                "message": "Risk tool list reloaded",
            })
        
        # 添加 Risk Tool
        elif self.path == '/api/risk-tools/add':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON"}, 400)
                return
            
            # 必填字段
            required = ['tool_name', 'action', 'risk_level', 'reason']
            for field in required:
                if field not in data:
                    self.send_json({"error": f"Missing required field: {field}"}, 400)
                    return
            
            # 设置默认值
            if 'require_confirmation' not in data:
                data['require_confirmation'] = True
            if 'examples' not in data:
                data['examples'] = []
            
            success = guard.add_risk_tool(data)
            
            if success:
                self.send_json({"success": True, "message": "Risk tool added"})
            else:
                self.send_json({"success": False, "error": "Tool already exists or save failed"}, 400)
        
        # 删除 Risk Tool
        elif self.path == '/api/risk-tools/remove':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON"}, 400)
                return
            
            tool_name = data.get('tool_name')
            action = data.get('action')
            
            if not tool_name or not action:
                self.send_json({"error": "tool_name and action required"}, 400)
                return
            
            success = guard.remove_risk_tool(tool_name, action)
            
            if success:
                self.send_json({"success": True, "message": "Risk tool removed"})
            else:
                self.send_json({"success": False, "error": "Tool not found or save failed"}, 400)
        
        # 更新 Risk Tool
        elif self.path == '/api/risk-tools/update':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON"}, 400)
                return
            
            old_tool_name = data.get('old_tool_name')
            old_action = data.get('old_action')
            new_config = data.get('new_config', {})
            
            if not old_tool_name or not old_action:
                self.send_json({"error": "old_tool_name and old_action required"}, 400)
                return
            
            success = guard.update_risk_tool(old_tool_name, old_action, new_config)
            
            if success:
                self.send_json({"success": True, "message": "Risk tool updated"})
            else:
                self.send_json({"success": False, "error": "Tool not found or save failed"}, 400)
        
        # 保存完整配置
        elif self.path == '/api/risk-tools/save':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON"}, 400)
                return
            
            success = guard.save_risk_tools(data)
            
            if success:
                self.send_json({"success": True, "message": "Configuration saved"})
            else:
                self.send_json({"success": False, "error": "Save failed"}, 400)
        
        # 启动任务监控
        elif self.path == '/api/task/start':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON"}, 400)
                return
            
            task = data.get('task', '')
            if not task:
                self.send_json({"error": "task required"}, 400)
                return
            
            allowed_tools = guard.start_task_monitoring(task)
            
            self.send_json({
                "success": True,
                "message": "Task monitoring started",
                "task": task,
                "allowed_tools": list(allowed_tools)
            })
        
        # 停止任务监控
        elif self.path == '/api/task/stop':
            guard.stop_task_monitoring()
            self.send_json({
                "success": True,
                "message": "Task monitoring stopped"
            })
        
        else:
            self.send_json({"error": "Not found"}, 404)

# ============================================================================
# 主程序
# ============================================================================

def main():
    global guard
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(CONFIG["log_file"], encoding='utf-8')
        ]
    )
    
    # 初始化 ToolGuard
    guard = ToolGuard()
    
    # 启动服务器
    host = CONFIG["host"]
    port = CONFIG["port"]
    
    server = HTTPServer((host, port), ToolGuardHandler)
    
    logging.info(f"ToolGuard Server 启动在 http://{host}:{port}")
    logging.info(f"健康检查：http://{host}:{port}/health")
    logging.info(f"工具检查：POST http://{host}:{port}/check")
    logging.info(f"Web 界面：http://{host}:{port}")
    
    print(f"\n🛡️  ToolGuard Server 已启动")
    print(f"   地址：http://{host}:{port}")
    print(f"   Web 界面：http://{host}:{port}")
    print(f"   健康检查：http://{host}:{port}/health")
    print(f"   按 Ctrl+C 停止\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("ToolGuard Server 停止中...")
        server.shutdown()
        logging.info("ToolGuard Server 已停止")

if __name__ == '__main__':
    main()
