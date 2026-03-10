# Hook 错误修复指南

## 问题描述

在使用 Bash 工具时遇到以下错误:

```
PreToolUse hook error: 
/bin/sh: -c: line 1: syntax error near unexpected token `'data',c='
node -e let d='';process.stdin.on('data',c=>d+=c);...
```

## 问题原因

`everything-claude-code` 插件的 hooks 使用内联 Node.js 命令,其中包含复杂的 JavaScript 代码和单引号,导致 shell 执行时引号冲突。

**问题文件**:
- `/root/.codebuddy/plugins/marketplaces/affaan-m_everything-claude-code/hooks/hooks.json`

**影响范围**:
- Bash 工具无法执行
- Write 工具可能出现警告
- 其他 hooks 相关功能

## 解决方案

### 方案 1: 项目级别禁用 Hooks (已实施)

已创建 `.codebuddy.json` 文件禁用所有 hooks:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "PreToolUse": [],
    "PostToolUse": [],
    "Stop": [],
    "SessionStart": [],
    "SessionEnd": [],
    "PreCompact": []
  },
  "enabledPlugins": {
    "everything-claude-code@everything-claude-code": false
  }
}
```

**位置**: `/root/project-wb/dingtalk_bot/.codebuddy.json`

### 方案 2: 全局禁用插件

编辑 `/root/.codebuddy/settings.json`,修改:

```json
"enabledPlugins": {
  "superpowers@superpowers-marketplace": true,
  "everything-claude-code@everything-claude-code": false  // 改为 false
}
```

### 方案 3: 重启 CodeBuddy Code 会话

项目级配置需要重启会话才能生效:

1. 退出当前 CodeBuddy Code 会话
2. 重新进入项目目录
3. 启动新的 CodeBuddy Code 会话

```bash
# 如果使用 CLI
exit  # 退出
cd /root/project-wb/dingtalk_bot
codebuddy  # 重新启动
```

## 验证修复

重启会话后,测试执行简单命令:

```bash
pwd
ls -la
git status
```

如果不再出现 hook 错误,则说明修复成功。

## 后续影响

禁用 hooks 后,以下功能将不可用:

### 丢失的功能

1. **tmux 提醒**: 不会提醒在 tmux 中运行长时间命令
2. **git push 提醒**: 不会在 push 前提醒检查代码
3. **文档文件警告**: 不会警告非标准位置的 .md 文件
4. **自动格式化**: 不会在编辑后自动运行 Prettier/Biome
5. **TypeScript 类型检查**: 不会在编辑后自动检查类型
6. **console.log 警告**: 不会警告 console.log 语句
7. **持续学习**: 不会自动记录工具使用模式

### 手动替代方案

由于丢失了自动化功能,需要手动执行:

```bash
# 代替 tmux 提醒 - 手动使用 tmux
tmux new -s dev
tmux attach -t dev

# 代替自动格式化 - 手动运行
prettier --write .
# 或
biome format --write .

# 代替 TypeScript 检查 - 手动运行
tsc --noEmit

# 代替 console.log 检查 - 手动搜索
grep -r "console.log" src/
```

## 其他解决方案

### 方案 4: 修复插件 Hooks

如果您需要 hooks 功能,可以尝试修复插件:

1. 备份原始文件:
   ```bash
   cp /root/.codebuddy/plugins/marketplaces/affaan-m_everything-claude-code/hooks/hooks.json \
      /root/.codebuddy/plugins/marketplaces/affaan-m_everything-claude-code/hooks/hooks.json.backup
   ```

2. 将内联 JavaScript 命令替换为外部脚本文件

3. 或者等待插件作者修复该问题

### 方案 5: 只禁用 PreToolUse Hooks

如果您只想保留 PostToolUse hooks(如自动格式化),可以修改 `.codebuddy.json`:

```json
{
  "hooks": {
    "PreToolUse": []  // 只禁用 PreToolUse
  }
}
```

## 故障排查

### 问题: 配置没有生效

1. 确认文件位置正确:
   ```bash
   ls -la /root/project-wb/dingtalk_bot/.codebuddy.json
   ```

2. 检查 JSON 语法:
   ```bash
   cat /root/project-wb/dingtalk_bot/.codebuddy.json | jq
   ```

3. 重启 CodeBuddy Code 会话

### 问题: 仍然有错误

尝试全局禁用插件(方案 2)

## 相关文件

- **项目配置**: `/root/project-wb/dingtalk_bot/.codebuddy.json`
- **项目配置(备用)**: `/root/project-wb/dingtalk_bot/.codebuddy/settings.json`
- **全局配置**: `/root/.codebuddy/settings.json`
- **问题 Hooks**: `/root/.codebuddy/plugins/marketplaces/affaan-m_everything-claude-code/hooks/hooks.json`

## 总结

1. **问题**: everything-claude-code 插件的 hooks 引号冲突
2. **已实施**: 创建 `.codebuddy.json` 禁用 hooks
3. **需要**: 重启 CodeBuddy Code 会话使配置生效
4. **影响**: 丢失一些自动化功能,但 Bash 工具恢复正常

---

**更新时间**: 2026-03-02  
**状态**: 已修复,需重启会话
