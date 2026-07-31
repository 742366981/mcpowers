#!/usr/bin/env bash
# start_dev.sh - 一键启动本地开发环境
# 用法：bash start_dev.sh [dev|test|prod] [--build] [--stop|--down] [--logs]
#
# 统一启动命令：
#   - 默认（代码变更/容器重启）：up -d --force-recreate
#   - --build（依赖变了）：        up -d --build（compose 自动检测镜像变化重建容器）
#   - --stop（停止，容器仍在）：    stop
#   - --down（停止+删除容器/网络）：down
# 详见 开发环境规范.md §4.4 / Flask后端规范.md §21.5。

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

ENV_TYPE="dev"; COMPOSE_FILE="docker-compose.${ENV_TYPE}.yml"; ACTION="up"; BUILD_FLAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        dev|test|prod) ENV_TYPE=$1; COMPOSE_FILE="docker-compose.${ENV_TYPE}.yml"; shift ;;
        --build) BUILD_FLAG="--build"; shift ;;
        --stop) ACTION="stop"; shift ;;
        --down) ACTION="down"; shift ;;
        --logs) ACTION="logs"; shift ;;
        --help|-h) echo "用法: bash start_dev.sh [dev|test|prod] [--build] [--stop|--down] [--logs]"; exit 0 ;;
        *) error "未知参数: $1"; exit 1 ;;
    esac
done

info "环境类型: ${ENV_TYPE}"; info "Compose 文件: ${COMPOSE_FILE}"
command -v docker &>/dev/null || { error "未检测到 docker"; exit 1; }
docker info &>/dev/null || { error "docker daemon 未运行"; exit 1; }
docker compose version &>/dev/null || { error "未检测到 docker compose v2"; exit 1; }
[[ -f "${COMPOSE_FILE}" ]] || { error "未找到 ${COMPOSE_FILE}"; exit 1; }

CONFIG_FILE="config/config_${ENV_TYPE}.ini"
[[ -f "${CONFIG_FILE}" ]] || { error "请先创建 ${CONFIG_FILE}"; exit 1; }

case "${ACTION}" in
    up)
        info "启动 ${ENV_TYPE} 环境..."
        if [[ -n "${BUILD_FLAG}" ]]; then
            # 依赖变了：重新构建镜像，compose 会自动检测到镜像变化并重建容器
            docker compose -f "${COMPOSE_FILE}" up -d --build
        else
            # 默认：强制重建容器，确保代码通过 volume 挂载的更新生效
            # 首次启动（无镜像）必须加 --build
            if ! docker compose -f "${COMPOSE_FILE}" images --quiet 2>/dev/null | grep -q .; then
                error "未检测到已构建的镜像，请使用 --build 参数首次构建："
                error "  bash start_dev.sh ${ENV_TYPE} --build"
                exit 1
            fi
            docker compose -f "${COMPOSE_FILE}" up -d --force-recreate
        fi
        echo ""
        info "✅ 启动完成！"
        echo "  查看日志: bash start_dev.sh --logs"
        echo "  停止服务(容器保留): bash start_dev.sh --stop"
        echo "  停止并清理: bash start_dev.sh --down"
        echo "  访问应用: http://localhost:8000"
        echo "  接口文档: http://localhost:8000/apidocs/"
        echo "  健康检查: http://localhost:8000/health"
        sleep 5
        if command -v curl &>/dev/null; then
            curl -sf http://localhost:8000/health >/dev/null 2>&1 && info "✅ 健康检查通过" || warn "健康检查失败"
        fi
        ;;
    stop) info "停止 ${ENV_TYPE}（容器保留）..."; docker compose -f "${COMPOSE_FILE}" stop; info "✅ 已停止" ;;
    down) info "停止并清理 ${ENV_TYPE}..."; docker compose -f "${COMPOSE_FILE}" down; info "✅ 已清理" ;;
    logs) docker compose -f "${COMPOSE_FILE}" logs -f ;;
    *) error "未知动作: ${ACTION}"; exit 1 ;;
esac