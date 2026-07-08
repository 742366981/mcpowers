#!/usr/bin/env bash
# mcpowers SessionStart hook — 注入完整铁律到 system context
# 每次 Claude Code 启动时执行，输出铁律到 stdout
# 退出码 0 = 注入信息（不阻断）

set -e

cat <<'EOF'
[mcpowers] 会话启动 → 路由器已激活（~/.claude/skills/mcpowers/SKILL.md）
[mcpowers] 路由表: ~/.claude/skills/mcpowers/SKILL.md

[mcpowers] 铁律（7 条必须做 + 6 条禁止做）：

  必须做：
  1. 修改前先分析影响、询问用户确认
  2. 修改时遵守 代码同步修改规范（mcpowers-shared/docs/技术规范/代码同步修改规范.md）
  3. 完成时立即 commit（禁止多个独立任务后才 commit）
  4. 接口开发先写 docstring，再写实现
  5. 代码注释完整（函数 docstring + 类注释 + 复杂逻辑注释）
  6. 临时文件放 temp/ 目录，用完即删
  7. 改完同步更新 README / 文档（代码和文档必须同 commit）

  禁止做：
  1. 未经用户确认直接修改任何代码/文档
  2. 先写代码后补文档
  3. 只 commit 代码不 commit 文档
  4. 多处重复定义同一内容
  5. 在项目根目录创建临时文件
  6. 违反 SOLID/KISS/DRY/YAGNI 原则

  完整规范见 mcpowers-shared/docs/AI操作规范.md（按需 Read）
[mcpowers] 反模式详见各技能的 "反模式（禁止）" 段
EOF

exit 0
