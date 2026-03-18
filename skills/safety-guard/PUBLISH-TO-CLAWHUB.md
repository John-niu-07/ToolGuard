# 📦 发布到 ClawHub 指南

**版本**: 1.0.0  
**最后更新**: 2026-03-14

---

## 🎯 目标

将 Safety Guard Skill 发布到 ClawHub.com，让其他 OpenClaw 用户可以轻松安装。

---

## ✅ 准备工作

### 1. 确认 ClawHub CLI 已安装

```bash
clawhub --version
# 应该显示：clawhub@0.7.0 或类似版本
```

如果未安装：
```bash
npm install -g clawhub
```

### 2. 登录 ClawHub

```bash
clawhub login
```

**流程**:
1. 运行命令后，会打开浏览器
2. 登录 clawhub.com 账号（没有则注册）
3. 授权 CLI 访问
4. 返回终端，应该显示登录成功

**验证登录**:
```bash
clawhub whoami
# 应该显示你的用户名
```

### 3. 准备发布文件

已创建的文件：
- ✅ `clawhub.json` - ClawHub 配置（包元数据）
- ✅ `.gitignore` - 排除不需要发布的文件
- ✅ `SKILL.md` - Skill 主文档
- ✅ 所有代码和文档

---

## 🚀 发布流程

### 步骤 1: 导航到 Skill 目录

```bash
cd ~/.openclaw/workspace/skills/safety-guard
```

### 步骤 2: 验证配置

```bash
# 检查 clawhub.json
cat clawhub.json
```

**应该包含**:
```json
{
  "name": "safety-guard",
  "displayName": "OpenClaw Safety Guard",
  "version": "1.0.0",
  "description": "Security guard skill...",
  "author": "John-niu-07",
  "license": "MIT"
}
```

### 步骤 3: 执行发布命令

```bash
clawhub publish . \
  --slug safety-guard \
  --name "OpenClaw Safety Guard" \
  --version 1.0.0 \
  --changelog "Initial release: Core safety guard functionality with prompt injection detection, harmful content filtering, dangerous command blocking, and audit logging"
```

**命令解析**:
- `.` - 当前目录
- `--slug safety-guard` - ClawHub 上的唯一标识符
- `--name "..."` - 显示名称
- `--version 1.0.0` - 版本号
- `--changelog "..."` - 更新日志

### 步骤 4: 等待发布完成

**预期输出**:
```
✓ Packaging skill...
✓ Uploading to ClawHub...
✓ Publishing safety-guard@1.0.0...
✓ Published successfully!

View at: https://clawhub.com/skills/safety-guard
```

### 步骤 5: 验证发布

```bash
# 搜索你的 Skill
clawhub search "safety-guard"

# 查看 Skill 详情
clawhub info safety-guard
```

---

## 📋 发布后检查

### 1. 访问 ClawHub 页面

打开：https://clawhub.com/skills/safety-guard

**检查项**:
- ✅ 显示名称和描述正确
- ✅ 版本号显示 1.0.0
- ✅ 作者信息正确
- ✅ 安装说明清晰
- ✅ GitHub 链接有效

### 2. 测试安装

```bash
# 在另一个 OpenClaw 实例测试
clawhub install safety-guard
```

### 3. 分享链接

**分享 URL**:
```
https://clawhub.com/skills/safety-guard
```

**社交媒体文案**:
```
🛡️ 发布了 OpenClaw Safety Guard Skill 到 @ClawHub!

在调用大模型前分析用户输入，检测有害内容、风险指令和安全威胁。

安装：clawhub install safety-guard
查看：https://clawhub.com/skills/safety-guard

#OpenClaw #AI #Security #ClawHub
```

---

## 🔄 更新发布

### 发布新版本

1. **更新版本号**

编辑 `clawhub.json`:
```json
{
  "version": "1.0.1"  // 递增版本号
}
```

2. **更新 changelog**

```bash
git commit -am "Bump version to 1.0.1"
```

3. **重新发布**

```bash
clawhub publish . \
  --slug safety-guard \
  --version 1.0.1 \
  --changelog "Fix bug in pattern matching + add new detection rules"
```

### 版本命名规范

| 版本 | 说明 | 示例 |
|------|------|------|
| **主版本** | 重大变更，不兼容 | 1.0.0 → 2.0.0 |
| **次版本** | 新功能，向后兼容 | 1.0.0 → 1.1.0 |
| **补丁** | Bug 修复 | 1.0.0 → 1.0.1 |

---

## 🐛 故障排除

### 问题 1: "Not logged in"

**错误**:
```
Error: Not logged in. Run: clawhub login
```

**解决**:
```bash
clawhub login
```

### 问题 2: "Slug already taken"

**错误**:
```
Error: Slug 'safety-guard' is already taken
```

**解决**:
- 使用不同的 slug，如 `safety-guard-skill` 或 `openclaw-safety-guard`
- 或联系 ClawHub 支持（如果是你的）

### 问题 3: "Missing required fields"

**错误**:
```
Error: Missing required fields: name, version
```

**解决**:
- 检查 `clawhub.json` 是否包含所有必需字段
- 必需字段：`name`, `version`, `description`

### 问题 4: 发布超时

**错误**:
```
Error: Upload timeout
```

**解决**:
```bash
# 检查网络连接
ping clawhub.com

# 重试发布
clawhub publish . --slug safety-guard --version 1.0.0
```

### 问题 5: 文件大小超限

**错误**:
```
Error: Package size exceeds limit (50MB)
```

**解决**:
- 检查 `.gitignore` 是否排除了 `venv/`, `__pycache__/` 等
- 删除大文件（日志、测试数据等）

---

## 📊 ClawHub 配置说明

### clawhub.json 字段详解

```json
{
  "name": "safety-guard",              // ⭐ 必需：唯一标识符
  "displayName": "OpenClaw Safety Guard", // 显示名称
  "version": "1.0.0",                  // ⭐ 必需：语义化版本
  "description": "...",                // ⭐ 必需：简短描述
  "author": "John-niu-07",             // 作者
  "license": "MIT",                    // 许可证
  "homepage": "...",                   // 项目主页
  "keywords": ["security", "safety"],  // 搜索关键词
  "main": "SKILL.md",                  // 主文档
  "bin": ["safety-check", ...],        // 可执行命令
  "files": [...],                      // 包含的文件
  "engines": {                         // 依赖环境
    "openclaw": ">=2026.3.0",
    "python": ">=3.10"
  },
  "dependencies": {                    // 依赖包
    "python_packages": ["PyYAML"]
  },
  "repository": {                      // 代码仓库
    "url": "https://github.com/..."
  },
  "bugs": {                            // 问题反馈
    "url": "https://github.com/.../issues"
  },
  "changelog": "..."                   // 更新日志
}
```

### 必需字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `name` | 唯一标识符 | `safety-guard` |
| `version` | 语义化版本 | `1.0.0` |
| `description` | 简短描述 | "Security guard skill..." |

### 推荐字段

| 字段 | 说明 |
|------|------|
| `author` | 作者信息 |
| `license` | 开源许可证 |
| `keywords` | 搜索关键词 |
| `repository` | GitHub 仓库 |

---

## 📈 发布后推广

### 1. 社交媒体

- **Twitter/X**: 分享链接和截图
- **Discord**: OpenClaw 官方服务器
- **Reddit**: r/LocalLLaMA, r/OpenClaw

### 2. 文档更新

在 README.md 添加：
```markdown
## 安装

```bash
# 从 ClawHub 安装
clawhub install safety-guard
```
```

### 3. 收集反馈

- 监控 GitHub Issues
- 回复 ClawHub 评论
- 根据反馈改进

---

## 🎯 完整发布命令（复制粘贴）

```bash
# 1. 登录
clawhub login

# 2. 验证登录
clawhub whoami

# 3. 进入目录
cd ~/.openclaw/workspace/skills/safety-guard

# 4. 发布
clawhub publish . \
  --slug safety-guard \
  --name "OpenClaw Safety Guard" \
  --version 1.0.0 \
  --changelog "Initial release: Core safety guard functionality"

# 5. 验证
clawhub search "safety-guard"

# 6. 推送 Git 更新
git push origin main
```

---

## 🔗 相关资源

| 资源 | 链接 |
|------|------|
| **ClawHub 官网** | https://clawhub.com |
| **ClawHub 文档** | https://clawhub.com/docs |
| **你的 Skill** | https://clawhub.com/skills/safety-guard |
| **GitHub 仓库** | https://github.com/John-niu-07/openclaw-safety-guard-skill |

---

## ✅ 发布清单

发布前检查：

- [ ] 已登录 ClawHub (`clawhub whoami`)
- [ ] `clawhub.json` 配置正确
- [ ] 版本号为 `1.0.0`
- [ ] `.gitignore` 排除不必要文件
- [ ] 所有文件已提交到 Git
- [ ] README.md 包含安装说明
- [ ] SKILL.md 文档完整

发布后检查：

- [ ] ClawHub 页面显示正常
- [ ] 安装命令测试通过
- [ ] GitHub 仓库已更新
- [ ] 分享了发布消息

---

**祝发布顺利！** 🚀

*最后更新：2026-03-14*
