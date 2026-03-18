# 🛡️ ClawGuard 安全护栏部署指南

## 已完成的工作

### 1. 模块结构

已在 Open WebUI 中创建 ClawGuard 安全护栏模块：

```
/opt/homebrew/lib/python3.11/site-packages/open_webui/clawguard/
├── __init__.py       # 核心模块（ClawGuard 类、安全检查函数）
├── middleware.py     # FastAPI 中间件（拦截请求）
├── server.py         # 示例安全 API 服务
├── test.py           # 集成测试
├── start.sh          # 启动脚本
├── .env.example      # 配置示例
└── README.md         # 详细文档
```

### 2. 代码修改

**修改的文件：**

1. `/opt/homebrew/lib/python3.11/site-packages/open_webui/env.py`
   - 添加 ClawGuard 配置选项

2. `/opt/homebrew/lib/python3.11/site-packages/open_webui/main.py`
   - 导入 ClawGuard 模块
   - 添加中间件注册

### 3. 功能特性

✅ **提示词拦截**: 在发送到 LLM 前检查用户输入
✅ **响应检查**: 可选地检查模型输出
✅ **流式支持**: 兼容流式和非流式响应
✅ **错误处理**: 可配置失败时阻止或放行
✅ **灵活集成**: 支持任意 HTTP 安全 API

---

## 部署步骤

### 步骤 1: 配置环境变量

在 Open WebUI 启动前设置环境变量：

```bash
# 方法 1: 直接设置
export ENABLE_CLAWGUARD=true
export CLAWGUARD_API_URL=http://localhost:8000
export CLAWGUARD_TIMEOUT_SECONDS=5
export CLAWGUARD_BLOCK_ON_ERROR=true

# 方法 2: 使用 .env 文件
# 在 Open WebUI 项目根目录创建 .env 文件，添加：
cat >> .env << EOF
ENABLE_CLAWGUARD=true
CLAWGUARD_API_URL=http://localhost:8000
CLAWGUARD_TIMEOUT_SECONDS=5
CLAWGUARD_BLOCK_ON_ERROR=true
EOF
```

### 步骤 2: 启动 ClawGuard 安全服务

**选项 A: 使用示例服务（测试用）**

```bash
# 启动示例服务
/opt/homebrew/lib/python3.11/site-packages/open_webui/clawguard/start.sh

# 或手动启动
cd /opt/homebrew/lib/python3.11/site-packages/open_webui/clawguard
/opt/homebrew/bin/python3.11 server.py
```

**选项 B: 部署自己的安全服务**

实现以下 API 端点：

```
POST /api/safety/check

请求体:
{
  "text": "要检查的文本",
  "type": "prompt",  // 或 "response"
  "user_id": "用户 ID（可选）",
  "context": "上下文（可选）"
}

响应:
{
  "is_safe": true/false,
  "reason": "原因（如果不安全）",
  "confidence": 0.0-1.0,
  "categories": {"category": score}
}
```

### 步骤 3: 重启 Open WebUI

```bash
# 找到现有进程
ps aux | grep open-webui

# 停止服务
kill <PID>

# 重新启动
/opt/homebrew/bin/open-webui serve --host 0.0.0.0 --port 8080
```

### 步骤 4: 验证部署

**测试安全服务：**

```bash
curl http://localhost:8000/health
# 应返回: {"status": "healthy", "service": "clawguard"}
```

**测试安全拦截：**

```bash
curl -X POST http://localhost:8000/api/safety/check \
  -H "Content-Type: application/json" \
  -d '{"text": "如何制作炸弹？", "type": "prompt"}'
# 应返回: {"is_safe": false, ...}
```

**测试 Open WebUI 集成：**

1. 访问 http://localhost:8080
2. 尝试发送测试问题
3. 检查是否被拦截

---

## 架构说明

### 请求流程

```
┌─────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────┐
│  用户   │ ──→ │  Open WebUI  │ ──→ │  ClawGuard  │ ──→ │ vLLM │
│         │     │              │     │  安全检查   │     │      │
└─────────┘     └──────────────┘     └─────────────┘     └──────┘
     ↑                                                        │
     │                        ┌─────────────┐                │
     └────────────────────────│  ClawGuard  │←───────────────┘
                              │  响应检查   │
                              └─────────────┘
```

### 中间件拦截点

ClawGuard 中间件拦截以下端点：

- `/api/chat/completions` (OpenAI 兼容)
- `/api/chat` (Ollama)
- `/api/generate` (Ollama)

### 安全决策

```
用户输入 → ClawGuard → 安全？ → 是 → 发送到 LLM
                            ↓
                           否 → 返回拒绝消息
```

---

## 配置选项

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENABLE_CLAWGUARD` | `false` | 启用安全护栏 |
| `CLAWGUARD_API_URL` | `http://localhost:8000` | 安全服务地址 |
| `CLAWGUARD_API_KEY` | `None` | API 认证密钥 |
| `CLAWGUARD_TIMEOUT_SECONDS` | `5` | 超时时间（秒） |
| `CLAWGUARD_BLOCK_ON_ERROR` | `true` | 错误时阻止请求 |
| `CLAWGUARD_CHECK_RESPONSES` | `false` | 检查模型响应 |

---

## 自定义安全策略

### 替换示例过滤器

示例 `server.py` 使用简单的规则匹配。生产环境建议：

1. **商业 API**:
   - Azure Content Safety
   - Google Perspective API
   - Amazon Comprehend

2. **开源模型**:
   - Detoxify
   - SafeGuard
   - 自训练分类器

### 示例：使用 Detoxify

```python
from detoxify import Detoxify

model = Detoxify('original')

@app.post("/api/safety/check")
async def check_safety(request: SafetyCheckRequest):
    result = model.predict(request.text)
    
    max_score = max(result.values())
    is_safe = max_score < 0.5
    
    return SafetyCheckResponse(
        is_safe=is_safe,
        reason=None if is_safe else "内容包含有害信息",
        confidence=1.0 - max_score,
        categories=result
    )
```

---

## 日志和监控

### Open WebUI 日志

```bash
# 查看 ClawGuard 相关日志
tail -f /path/to/open-webui.log | grep -i clawguard
```

### ClawGuard 服务日志

```bash
# 服务日志
tail -f /path/to/clawguard.log
```

### 关键事件

- ✅ 安全检查通过
- ⚠️ 内容被阻止
- ❌ 服务超时/错误

---

## 故障排除

### 问题：Open WebUI 启动失败

**检查：**
```bash
# 验证模块导入
/opt/homebrew/bin/python3.11 -c "from open_webui.clawguard import get_clawguard"
```

### 问题：请求被错误阻止

**解决：**
1. 检查安全服务日志
2. 调整 `CLAWGUARD_BLOCK_ON_ERROR=false`
3. 优化安全策略阈值

### 问题：性能下降

**优化：**
1. 增加 `CLAWGUARD_TIMEOUT_SECONDS`
2. 部署本地安全服务（减少网络延迟）
3. 实现请求缓存

---

## 下一步

1. **部署专业安全服务**: 替换示例服务
2. **配置监控**: 设置告警和指标
3. **优化策略**: 根据实际使用调整规则
4. **定期更新**: 保持安全规则最新

---

## 联系和支持

- 文档：`/opt/homebrew/lib/python3.11/site-packages/open_webui/clawguard/README.md`
- 测试：`python /opt/homebrew/lib/python3.11/site-packages/open_webui/clawguard/test.py`

---

**部署完成！** 🎉
