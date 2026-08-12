#!/usr/bin/env bash
# mcpowers swagger 栈探测(v2.31.0+)
#
# 探测当前项目是否真用了 swagger / OpenAPI 工具栈。
# 命中任一栈(flasgger/apispec/fastapi/springdoc/openapi-typescript/swagger-jsdoc)→ exit 0
# 都没装 → exit 1(让 hook 直接放行,不骚扰非 swagger 项目)
#
# 使用方式:
#   bash swagger-stack-detect.sh
#   # 无参数,自动读 ${CLAUDE_PROJECT_DIR:-$(pwd)} 下的依赖声明
#
# 退出码:
#   0 = 项目使用了 swagger 栈,后续 lint 应执行
#   1 = 项目未使用 swagger 栈,hook 应放行

set -e

WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$WORK_DIR" 2>/dev/null || exit 1

# 探测的依赖关键字(任一命中即视为 swagger 项目)
SWAGGER_KEYWORDS=(
    'flasgger'              # Flask Flasgger
    'apispec'               # apispec(Flask 底层)
    'fastapi'               # FastAPI(自带 OpenAPI)
    'springdoc'             # Spring Boot springdoc-openapi
    'springfox'             # Spring Boot springfox(旧)
    'openapi-typescript'    # 前端 TS 代码生成
    'swagger-ui-express'    # Express swagger-ui
    'swagger-jsdoc'         # Express swagger-jsdoc
    'gin-swagger'           # Go Gin swagger
)

# 大目录排除(避免扫 node_modules / .git / venv 等)
EXCLUDE_DIRS=(
    -path '*/.git' -prune -o
    -path '*/node_modules' -prune -o
    -path '*/__pycache__' -prune -o
    -path '*/venv' -prune -o
    -path '*/.venv' -prune -o
    -path '*/dist' -prune -o
    -path '*/build' -prune -o
    -path '*/target' -prune -o
    -path '*/.pytest_cache' -prune -o
    -path '*/.mypy_cache' -prune -o
    -path '*/.tox' -prune -o
    -path '*/.cache' -prune -o
)

# Step 1:扫描依赖声明文件(快速路径,~50ms)
# 命中 → exit 0;声明文件存在但都没命中 → 信任依赖声明,exit 1
HAS_MANIFEST=0
for kw in "${SWAGGER_KEYWORDS[@]}"; do
    if grep -lE -- "$kw" \
        requirements.txt pyproject.toml setup.py setup.cfg Pipfile \
        package.json pnpm-lock.yaml yarn.lock \
        go.mod go.sum \
        pom.xml build.gradle build.gradle.kts \
        2>/dev/null | head -1 | grep -q .; then
        exit 0
    fi
done

# 统计实际存在的声明文件数(>=1 说明项目有依赖声明体系 → 信任它)
for f in requirements.txt pyproject.toml setup.py setup.cfg Pipfile \
         package.json pnpm-lock.yaml yarn.lock \
         go.mod go.sum \
         pom.xml build.gradle build.gradle.kts; do
    [ -f "$f" ] && HAS_MANIFEST=1 && break
done

# Step 2:仅当项目完全无依赖声明文件(罕见纯脚本/示例项目)时才做兜底源码扫描,
#         且只跑一次(不是每 kw 一次),深度限定 3,排除大目录
#         关键:排除 .md / README / CHANGELOG 等纯文档文件(避免 mcpowers 自仓库的
#         "docs/API文档/swagger_template.md" / "docs/技术规范/接口契约规范.md"
#         等被误判为"项目用了 swagger")
if [ "$HAS_MANIFEST" = 0 ]; then
    for kw in "${SWAGGER_KEYWORDS[@]}"; do
        if find "$WORK_DIR" -maxdepth 3 \
            "${EXCLUDE_DIRS[@]}" \
            -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' \
                       -o -name '*.go' -o -name '*.java' -o -name '*.kt' \) \
            -print0 2>/dev/null \
            | xargs -0 grep -lE -- "$kw" 2>/dev/null \
            | head -1 | grep -q .; then
            exit 0
        fi
    done
fi

# 既无声明命中,也无源码兜底命中 → 不用 swagger
exit 1
