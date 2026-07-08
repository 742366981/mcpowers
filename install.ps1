# mcpowers 一键安装脚本（Windows PowerShell，参考 superpowers）
#
# 设计原则：
#   - 用 Junction（Windows 软链等效）引用源文件，编辑源文件后立即生效
#   - 升级 = git pull（无需重装）
#   - 幂等：重复运行结果一致
#   - 自动检测并替换旧安装
#
# 用法：
#   .\install.ps1                # 默认 symlink (Junction) 模式（含 hooks 注册）
#   .\install.ps1 -Copy          # 复制模式（无 symlink 权限时使用）
#   .\install.ps1 -NoHooks       # 跳过 hooks 注册（仅安装 skills）
#   .\install.ps1 -Copy -NoHooks # 组合使用
#
# Windows 执行策略提示：
#   首次运行若被拦截，先执行：Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#   或绕过：powershell -ExecutionPolicy Bypass -File install.ps1
#
# 仓库地址：git@github.com:742366981/mcpowers.git

[CmdletBinding()]
param(
    [switch]$Copy,
    [switch]$NoHooks
)

$ErrorActionPreference = 'Stop'

# ============== 解析模式 ==============
$Mode = if ($Copy) { 'copy' } else { 'symlink' }
$InstallHooks = -not $NoHooks

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

# ============== 注册 hooks 到 ~/.claude/settings.json ==============
# 策略：合并式写入 — 保留用户的 permissions / mcpServers 等其他段
# 工具降级：python3 → node → PowerShell 原生 ConvertFrom-Json / ConvertTo-Json
# 失败回滚：先备份再修改
function Register-Hooks {
    $SettingsPath = Join-Path $env:USERPROFILE '.claude\settings.json'
    $HooksFile = Join-Path $RepoDir 'hooks\hooks.json'
    $HooksInstallDir = Join-Path $SkillsDir 'mcpowers\hooks'  # symlink 后的路径

    if (-not (Test-Path $HooksFile)) {
        Write-Host "  ✗ hooks 配置不存在: $HooksFile" -ForegroundColor Red
        return
    }

    # 1. 备份已有 settings.json
    $Backup = $null
    if (Test-Path $SettingsPath) {
        $Backup = "$SettingsPath.bak.mcpowers.$PID"
        try {
            Copy-Item $SettingsPath $Backup -Force
        } catch {
            Write-Host '  ⚠ 备份 settings.json 失败，继续（不阻塞）' -ForegroundColor Yellow
            $Backup = $null
        }
    }

    # 2. 渲染 hooks.json（替换 __HOOKS_DIR__ 占位符）
    $RenderedHooks = [System.IO.Path]::GetTempFileName()
    try {
        $hooksContent = Get-Content $HooksFile -Raw -Encoding UTF8
        $hooksContent = $hooksContent.Replace('__HOOKS_DIR__', $HooksInstallDir)
        [System.IO.File]::WriteAllText($RenderedHooks, $hooksContent, [System.Text.Encoding]::UTF8)
    } catch {
        Write-Host "  ✗ 渲染 hooks.json 失败: $_" -ForegroundColor Red
        if ($Backup) { Copy-Item $Backup $SettingsPath -Force; Remove-Item $Backup -Force }
        Remove-Item $RenderedHooks -Force -ErrorAction SilentlyContinue
        return
    }

    # 3. 合并写入 settings.json
    $mergeOk = $false
    $settingsDir = Split-Path $SettingsPath
    if (-not (Test-Path $settingsDir)) { New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null }

    if (-not (Test-Path $SettingsPath)) {
        # settings.json 不存在 → 直接复制
        try {
            Copy-Item $RenderedHooks $SettingsPath -Force
            $mergeOk = $true
        } catch {
            Write-Host "  ✗ 写入 settings.json 失败: $_" -ForegroundColor Red
        }
    } else {
        # 优先 python3，回退 python（Windows 默认安装为 python）
        $python3 = (Get-Command python3 -ErrorAction SilentlyContinue)
        $python = (Get-Command python -ErrorAction SilentlyContinue)
        $pyBin = if ($python3) { 'python3' } elseif ($python) { 'python' } else { $null }
        $node = (Get-Command node -ErrorAction SilentlyContinue)

        if ($pyBin) {
            try {
                $settingsEsc = $SettingsPath -replace '\\', '\\'
                $renderedEsc = $RenderedHooks -replace '\\', '\\'
                $pyScript = @"
import json, sys
try:
    with open(r'$settingsEsc', 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(r'$renderedEsc', 'r', encoding='utf-8') as f:
        hooks = json.load(f)
    data['hooks'] = hooks['hooks']
    data['_mcpowers_marker'] = hooks.get('_mcpowers_marker', True)
    with open(r'$settingsEsc', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
"@
                $pyResult = & $pyBin -c $pyScript 2>&1
                if ($LASTEXITCODE -eq 0) { $mergeOk = $true }
            } catch {
                Write-Host "  ⚠ python3 合并失败: $_" -ForegroundColor Yellow
            }
        }

        # 降级到 node
        if (-not $mergeOk -and $node) {
            try {
                $settingsEsc = $SettingsPath -replace '\\', '\\'
                $renderedEsc = $RenderedHooks -replace '\\', '\\'
                $nodeScript = @"
const fs = require('fs');
try {
  const data = JSON.parse(fs.readFileSync('$settingsEsc', 'utf8'));
  const hooks = JSON.parse(fs.readFileSync('$renderedEsc', 'utf8'));
  data.hooks = hooks.hooks;
  data._mcpowers_marker = hooks._mcpowers_marker || true;
  fs.writeFileSync('$settingsEsc', JSON.stringify(data, null, 2));
} catch (e) {
  console.error(e.message);
  process.exit(1);
}
"@
                $nodeResult = & node -e $nodeScript 2>&1
                if ($LASTEXITCODE -eq 0) { $mergeOk = $true }
            } catch {
                Write-Host "  ⚠ node 合并失败: $_" -ForegroundColor Yellow
            }
        }

        # 降级到 PowerShell 原生
        if (-not $mergeOk) {
            try {
                $settingsData = Get-Content $SettingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
                $hooksData = Get-Content $RenderedHooks -Raw -Encoding UTF8 | ConvertFrom-Json
                # 转为 hashtable 操作（保留所有字段）
                $hash = @{}
                $settingsData.PSObject.Properties | ForEach-Object { $hash[$_.Name] = $_.Value }
                $hash['hooks'] = $hooksData.hooks
                $hash['_mcpowers_marker'] = $hooksData._mcpowers_marker
                $hash | ConvertTo-Json -Depth 10 | Set-Content $SettingsPath -Encoding UTF8
                $mergeOk = $true
            } catch {
                Write-Host "  ⚠ PowerShell 原生合并失败: $_" -ForegroundColor Yellow
            }
        }
    }

    Remove-Item $RenderedHooks -Force -ErrorAction SilentlyContinue

    # 4. 结果处理
    if ($mergeOk) {
        Write-Host "  ✓ hooks 已注册到 $SettingsPath" -ForegroundColor Green
        if ($Backup) { Remove-Item $Backup -Force -ErrorAction SilentlyContinue }
    } else {
        Write-Host "  ✗ hooks 合并失败" -ForegroundColor Red
        if ($Backup -and (Test-Path $Backup)) {
            Copy-Item $Backup $SettingsPath -Force
            Write-Host '  ↻ 已从备份回滚' -ForegroundColor Yellow
            Remove-Item $Backup -Force -ErrorAction SilentlyContinue
        }
    }
}

# ============== 1. 主入口 ==============
Write-Host '[1/4] 安装主入口 mcpowers/' -ForegroundColor Cyan
Install-Item -Src "$RepoDir\mcpowers" -Dst "$SkillsDir\mcpowers" -Name "mcpowers"

# ============== 2. 18 个技能（扁平化） ==============
Write-Host '[2/4] 安装技能（scene + method，共 18 个）' -ForegroundColor Cyan
$skillDirs = @()
$skillDirs += Get-ChildItem "$RepoDir\skills\scene" -Directory
$skillDirs += Get-ChildItem "$RepoDir\skills\method" -Directory
foreach ($skillDir in $skillDirs) {
    $name = $skillDir.Name
    Install-Item -Src $skillDir.FullName -Dst "$SkillsDir\$name" -Name $name
}

# ============== 3. 规范库 ==============
Write-Host '[3/4] 安装规范库 mcpowers-shared/' -ForegroundColor Cyan
Install-Item -Src "$RepoDir\mcpowers-shared" -Dst "$SkillsDir\mcpowers-shared" -Name "mcpowers-shared"

# ============== 4. 注册 Claude Code Hooks ==============
if ($InstallHooks) {
    Write-Host '[4/4] 注册 Claude Code Hooks 到 ~/.claude/settings.json' -ForegroundColor Cyan
    Register-Hooks
} else {
    Write-Host '[4/4] 跳过 hooks 注册（-NoHooks）' -ForegroundColor Cyan
}

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
if ($InstallHooks) {
    Write-Host 'Hooks: SessionStart + PreToolUse(Bash) 已注册，重启后生效' -ForegroundColor Green
    Write-Host '  跳过: .\install.ps1 -NoHooks'
}
