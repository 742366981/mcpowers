# start_dev.ps1
# PowerShell 版一键启动本地开发环境
#
# 用法：
#   .\start_dev.ps1                # 默认启动 dev 环境
#   .\start_dev.ps1 test           # 启动 test 环境
#   .\start_dev.ps1 prod           # 启动 prod 环境（慎用！）
#   .\start_dev.ps1 -Build         # 强制重新构建镜像
#   .\start_dev.ps1 -Down          # 停止并清理容器
#   .\start_dev.ps1 -Logs          # 仅查看日志
#
# 前置条件：已安装 Docker Desktop
#
# 统一启动命令：
#   - 默认（代码变更/容器重启）：up -d --force-recreate
#   - -Build（依赖变了）：         up -d --build --force-recreate
# 详见 开发环境规范.md §4.4 / Flask后端规范.md §21.5。

param(
    [ValidateSet('dev', 'test', 'prod')]
    [string]$EnvType = 'dev',
    [switch]$Build,
    [switch]$Down,
    [switch]$Logs,
    [switch]$Help
)

# 颜色函数
function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# 帮助
if ($Help) {
    Write-Host "用法: .\start_dev.ps1 [dev|test|prod] [-Build] [-Down] [-Logs]"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\start_dev.ps1              # 启动 dev 环境"
    Write-Host "  .\start_dev.ps1 -Build      # 强制重新构建镜像"
    Write-Host "  .\start_dev.ps1 -Down       # 停止并清理"
    Write-Host "  .\start_dev.ps1 -Logs       # 查看日志"
    exit 0
}

$ComposeFile = "docker-compose.$EnvType.yml"
Write-Info "环境类型: $EnvType"
Write-Info "Compose 文件: $ComposeFile"

# 前置检查
try {
    $null = docker --version
} catch {
    Write-Err "未检测到 docker，请先安装 Docker Desktop"
    exit 1
}

try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Err "docker daemon 未运行，请先启动 Docker Desktop"
    exit 1
}

try {
    $null = docker compose version 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Err "未检测到 docker compose v2，请升级 Docker Desktop"
    exit 1
}

if (-not (Test-Path $ComposeFile)) {
    Write-Err "未找到 $ComposeFile，请确认在项目根目录运行"
    exit 1
}

$ConfigFile = "config\config_$EnvType.ini"
if (-not (Test-Path $ConfigFile)) {
    $ExampleFile = "$ConfigFile.example"
    if (Test-Path $ExampleFile) {
        Write-Warn "$ConfigFile 不存在，但发现 $ExampleFile"
        $reply = Read-Host "是否复制 .example 初始化配置? [y/N]"
        if ($reply -eq 'y' -or $reply -eq 'Y') {
            Copy-Item $ExampleFile $ConfigFile
            Write-Info "已创建 $ConfigFile，请按需修改后重新运行"
            exit 0
        }
    }
    Write-Err "请先创建 $ConfigFile 后再启动"
    exit 1
}

# 执行动作
if ($Down) {
    Write-Info "停止 $EnvType 环境..."
    docker compose -f $ComposeFile down
    Write-Info "已停止"
} elseif ($Logs) {
    docker compose -f $ComposeFile logs -f
} else {
    Write-Info "启动 $EnvType 环境..."

    # 统一命令：--force-recreate 强制重建容器，确保新代码生效；
    # 仅在 -Build 时额外构建镜像（依赖变了才需要）。
    # 若未检测到镜像且未传 -Build，提示用户首次构建。
    $images = docker compose -f $ComposeFile images --quiet 2>&1
    $hasImages = $LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($images)

    if (-not $Build -and -not $hasImages) {
        Write-Err "未检测到已构建的镜像，请使用 -Build 参数首次构建（依赖层会缓存，后续很快）："
        Write-Err "  .\start_dev.ps1 $EnvType -Build"
        exit 1
    }

    $buildArg = if ($Build) { "--build" } else { "" }
    docker compose -f $ComposeFile up -d --force-recreate $buildArg

    Write-Host ""
    Write-Info "启动完成！"
    Write-Host ""
    Write-Host "  查看日志: .\start_dev.ps1 -Logs"
    Write-Host "  停止服务: .\start_dev.ps1 -Down"
    Write-Host "  访问应用: http://localhost:8000"
    Write-Host "  接口文档: http://localhost:8000/apidocs/  (Swagger UI)"
    Write-Host "  健康检查: http://localhost:8000/health"
    Write-Host ""

    Write-Info "等待服务就绪..."
    Start-Sleep -Seconds 5
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Info "健康检查通过"
        } else {
            Write-Warn "健康检查返回 $($response.StatusCode)"
        }
    } catch {
        Write-Warn "健康检查失败，请查看日志: .\start_dev.ps1 -Logs"
    }
}
