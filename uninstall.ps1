# mcpowers 卸载脚本（Windows PowerShell）
#
# 用法：
#   .\uninstall.ps1           # 交互式
#   .\uninstall.ps1 -Yes      # 跳过确认
#
# 安全：只删 mcpowers* 前缀的目录，不碰其他技能

[CmdletBinding()]
param(
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'

$SkillsDir = Join-Path $env:USERPROFILE '.claude\skills'

Write-Host '=== mcpowers 卸载 ===' -ForegroundColor Cyan
Write-Host ''

# ============== 收集待删目标 ==============
$targets = @()

if (Test-Path "$SkillsDir\mcpowers") {
    $targets += "$SkillsDir\mcpowers"
}
if (Test-Path "$SkillsDir\mcpowers-shared") {
    $targets += "$SkillsDir\mcpowers-shared"
}
Get-ChildItem "$SkillsDir\mcpowers-*" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Name -eq 'mcpowers' -or $_.Name -eq 'mcpowers-shared') { return }
    $targets += $_.FullName
}

if ($targets.Count -eq 0) {
    Write-Host '✓ 没有找到 mcpowers 相关的安装，无需卸载' -ForegroundColor Green
    exit 0
}

Write-Host "将删除以下 $($targets.Count) 项："
foreach ($t in $targets) {
    $item = Get-Item $t -Force -ErrorAction SilentlyContinue
    $isReparse = $item -and ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
    if ($isReparse) {
        Write-Host "  - $t (junction → $($item.Target))" -ForegroundColor Yellow
    } else {
        Write-Host "  - $t"
    }
}
Write-Host ''

# ============== 确认 ==============
if (-not $Yes) {
    $answer = Read-Host '确认删除？[y/N]'
    if ($answer -notmatch '^[yY]([eE][sS])?$') {
        Write-Host '已取消' -ForegroundColor Yellow
        exit 0
    }
}

# ============== 执行删除 ==============
foreach ($t in $targets) {
    Remove-Item -Recurse -Force $t
    Write-Host "  ✓ 删除 $t" -ForegroundColor Green
}

Write-Host ''
Write-Host '=== 卸载完成 ===' -ForegroundColor Green
Write-Host '  （不影响 find-skills、skill-creator 等其他技能）'
Write-Host ''
Write-Host '如需重装: .\install.ps1'
