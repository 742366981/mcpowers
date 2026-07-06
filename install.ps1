# mcpowers 一键安装脚本（Windows PowerShell，参考 superpowers）
#
# 设计原则：
#   - 用 Junction（Windows 软链等效）引用源文件，编辑源文件后立即生效
#   - 升级 = git pull（无需重装）
#   - 幂等：重复运行结果一致
#   - 自动检测并替换旧安装
#
# 用法：
#   .\install.ps1           # 默认 symlink (Junction) 模式
#   .\install.ps1 -Copy     # 复制模式（无 symlink 权限时使用）
#
# Windows 执行策略提示：
#   首次运行若被拦截，先执行：Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#   或绕过：powershell -ExecutionPolicy Bypass -File install.ps1
#
# 仓库地址：git@github.com:742366981/mcpowers.git

[CmdletBinding()]
param(
    [switch]$Copy
)

$ErrorActionPreference = 'Stop'

# ============== 解析模式 ==============
$Mode = if ($Copy) { 'copy' } else { 'symlink' }

# ============== 定位源和目标 ==============
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir = Join-Path $env:USERPROFILE '.claude\skills'

# ============== 预检 ==============
$ClaudeDir = Split-Path $SkillsDir
if (-not (Test-Path $ClaudeDir)) {
    Write-Host "✗ $ClaudeDir 不存在，请先安装 Claude Code" -ForegroundColor Red
    exit 1
}
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

# ============== 打印头部 ==============
Write-Host '=== mcpowers 安装 ===' -ForegroundColor Cyan
Write-Host "源:   $RepoDir"
Write-Host "目标: $SkillsDir"
Write-Host "模式: $Mode"
Write-Host ''

# ============== 通用安装函数 ==============
function Install-Item {
    param(
        [string]$Src,
        [string]$Dst,
        [string]$Name
    )

    # 已存在且已正确链接 → 跳过
    if (Test-Path $Dst) {
        $item = Get-Item $Dst -Force
        $isReparse = ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
        if ($isReparse) {
            $target = (Get-Item $Dst -Force).Target
            if ($target -eq $Src) {
                Write-Host "  ✓ $Name (已链接)" -ForegroundColor Green
                return
            }
            Write-Host "  ⚠ $Name 已存在（旧链接 $target），替换中..." -ForegroundColor Yellow
        } else {
            Write-Host "  ⚠ $Name 已存在（目录），替换中..." -ForegroundColor Yellow
        }
        Remove-Item -Recurse -Force $Dst
    }

    if ($Mode -eq 'symlink') {
        # Junction 模式：Windows 软链等效，目录用 Junction（无需管理员）
        try {
            New-Item -ItemType Junction -Path $Dst -Target $Src | Out-Null
            Write-Host "  ✓ $Name → $Src" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ $Name 创建 Junction 失败: $_" -ForegroundColor Red
            Write-Host "    提示: Windows 7+ 支持 Junction，无需管理员权限"
            throw
        }
    } else {
        Copy-Item -Recurse $Src $Dst
        Write-Host "  ✓ $Name (copied)" -ForegroundColor Green
    }
}

# ============== 1. 主入口 ==============
Write-Host '[1/3] 安装主入口 mcpowers/' -ForegroundColor Cyan
Install-Item -Src "$RepoDir\mcpowers" -Dst "$SkillsDir\mcpowers" -Name "mcpowers"

# ============== 2. 18 个技能（扁平化） ==============
Write-Host '[2/3] 安装技能（scene + method，共 18 个）' -ForegroundColor Cyan
$skillDirs = @()
$skillDirs += Get-ChildItem "$RepoDir\skills\scene" -Directory
$skillDirs += Get-ChildItem "$RepoDir\skills\method" -Directory
foreach ($skillDir in $skillDirs) {
    $name = $skillDir.Name
    Install-Item -Src $skillDir.FullName -Dst "$SkillsDir\$name" -Name $name
}

# ============== 3. 规范库 ==============
Write-Host '[3/3] 安装规范库 mcpowers-shared/' -ForegroundColor Cyan
Install-Item -Src "$RepoDir\mcpowers-shared" -Dst "$SkillsDir\mcpowers-shared" -Name "mcpowers-shared"

# ============== 收尾 ==============
Write-Host ''
Write-Host '=== 安装完成 ===' -ForegroundColor Green
$skillCount = (Get-ChildItem $SkillsDir -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'mcpowers*' }).Count
Write-Host "  技能数: $skillCount（含 1 个路由器 + 18 个技能 + 1 个规范库）"
Write-Host ''
if ($Mode -eq 'symlink') {
    Write-Host '✓ symlink (Junction) 模式已启用：' -ForegroundColor Green
    Write-Host '  - 编辑源文件后无需重装，重启 Claude Code 即可生效'
    Write-Host "  - 升级: cd $RepoDir && git pull"
} else {
    Write-Host '✓ copy 模式已启用：' -ForegroundColor Green
    Write-Host '  - 编辑源文件后需重新运行 install.ps1 才生效'
    Write-Host "  - 升级: cd $RepoDir && git pull && .\install.ps1 -Copy"
}
Write-Host ''
Write-Host '请重启 Claude Code 使技能生效。' -ForegroundColor Yellow
Write-Host '验证: 在任意项目说"加个功能"，看 AI 是否自动调 mcpowers-feat'
