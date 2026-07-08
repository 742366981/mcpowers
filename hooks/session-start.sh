#!/usr/bin/env bash
# mcpowers SessionStart hook
# 每次 Claude Code 启动时执行，输出路由器铁律摘要到 stdout
# 退出码 0 = 注入信息（不阻断）

set -e

cat <<'EOF'
[mcpowers] 会话启动 → 路由器已激活
[mcpowers] 路由表: ~/.claude/skills/mcpowers/SKILL.md
[mcpowers] 铁律摘要:
[mcpowers]   1. 改前确认影响范围
[mcpowers]   2. TDD 先行：没失败的测试不写生产代码
[mcpowers]   3. 改完即 commit（不攒 commit）
[mcpowers]   4. 代码 + 文档同 commit
[mcpowers]   5. 临时文件放 temp/ 目录
[mcpowers] 反模式详见各技能的 "反模式（禁止）" 段
EOF

exit 0
