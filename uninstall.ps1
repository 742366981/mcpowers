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

# ============== 清理 ~/.claude/settings.json 中的 mcpowers hooks ==============
# 逻辑：
#   - settings.json 不存在 → 无需清理
#   - 顶层 _mcpowers_marker: true → mcpowers 是唯一 hooks 来源 → 删除整个 hooks 段
#   - 顶层 _mcpowers_marker 不存在但 hooks 段存在 → 只清理 mcpowers 标记的子项
#   - 失败时回滚备份
function Cleanup-Hooks {
    $SettingsPath = Join-Path $env:USERPROFILE '.claude\settings.json'

    if (-not (Test-Path $SettingsPath)) {
        Write-Host '  ⊘ ~/.claude/settings.json 不存在，跳过' -ForegroundColor DarkGray
        return
    }

    # 1. 备份
    $Backup = "$SettingsPath.bak.mcpowers.uninstall.$PID"
    try {
        Copy-Item $SettingsPath $Backup -Force
    } catch {
        Write-Host "  ✗ 备份 settings.json 失败，跳过清理: $_" -ForegroundColor Red
        return
    }

    # 2. 合并式清理（优先 python3 → node → PowerShell 原生）
    $ok = $false

    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    $python = Get-Command python -ErrorAction SilentlyContinue
    $pyBin = if ($python3) { 'python3' } elseif ($python) { 'python' } else { $null }
    $node = Get-Command node -ErrorAction SilentlyContinue

    if ($pyBin) {
        try {
            $settingsEsc = $SettingsPath -replace '\\', '\\'
            $pyScript = @"
import json, sys
try:
    with open(r'$settingsEsc', 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        sys.exit(0)
    is_owner = data.get('_mcpowers_marker') is True
    if is_owner:
        data.pop('hooks', None)
        data.pop('_mcpowers_marker', None)
    elif 'hooks' in data:
        if isinstance(data['hooks'], dict):
            for event_name in list(data['hooks'].keys()):
                groups = data['hooks'][event_name]
                if not isinstance(groups, list):
                    continue
                filtered = []
                for g in groups:
                    if not isinstance(g, dict):
                        filtered.append(g); continue
                    hks = g.get('hooks', [])
                    if not isinstance(hks, list):
                        filtered.append(g); continue
                    new_hks = [h for h in hks
                              if not (
                                  isinstance(h, dict) and
                                  isinstance(h.get('command'), str) and
                                  'mcpowers' in h['command']
                              )]
                    if new_hks:
                        g['hooks'] = new_hks
                        filtered.append(g)
                if filtered:
                    data['hooks'][event_name] = filtered
                else:
                    del data['hooks'][event_name]
            if not data['hooks']:
                data.pop('hooks')
    with open(r'$settingsEsc', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
except Exception as e:
    print('err: ' + str(e), file=sys.stderr)
    sys.exit(1)
"@
            $pyResult = & $pyBin -c $pyScript 2>&1
            if ($LASTEXITCODE -eq 0) { $ok = $true }
        } catch {
            Write-Host "  ⚠ python3 清理失败: $_" -ForegroundColor Yellow
        }
    }

    if (-not $ok -and $node) {
        try {
            $settingsEsc = $SettingsPath -replace '\\', '\\'
            $nodeScript = @"
const fs = require('fs');
try {
  const data = JSON.parse(fs.readFileSync('$settingsEsc', 'utf8'));
  const isOwner = data._mcpowers_marker === true;
  if (isOwner) {
    delete data.hooks;
    delete data._mcpowers_marker;
  } else if (data.hooks) {
    for (const eventName of Object.keys(data.hooks)) {
      const groups = data.hooks[eventName];
      if (!Array.isArray(groups)) continue;
      const filtered = groups.map(g => {
        if (!g || !Array.isArray(g.hooks)) return g;
        g.hooks = g.hooks.filter(h =>
          !(h && typeof h.command === 'string' && h.command.includes('mcpowers'))
        );
        return g;
      }).filter(g => g && Array.isArray(g.hooks) && g.hooks.length > 0);
      if (filtered.length > 0) {
        data.hooks[eventName] = filtered;
      } else {
        delete data.hooks[eventName];
      }
    }
    if (Object.keys(data.hooks).length === 0) {
      delete data.hooks;
    }
  }
  fs.writeFileSync('$settingsEsc', JSON.stringify(data, null, 2));
} catch (e) {
  console.error('err: ' + e.message);
  process.exit(1);
}
"@
            $nodeResult = & node -e $nodeScript 2>&1
            if ($LASTEXITCODE -eq 0) { $ok = $true }
        } catch {
            Write-Host "  ⚠ node 清理失败: $_" -ForegroundColor Yellow
        }
    }

    # 降级到 PowerShell 原生
    if (-not $ok) {
        try {
            $rawJson = Get-Content $SettingsPath -Raw -Encoding UTF8
            $settingsData = $rawJson | ConvertFrom-Json
            $hash = @{}
            $settingsData.PSObject.Properties | ForEach-Object { $hash[$_.Name] = $_.Value }

            $isOwner = $hash['_mcpowers_marker'] -eq $true
            if ($isOwner) {
                $hash.Remove('hooks')
                $hash.Remove('_mcpowers_marker')
            } elseif ($hash.ContainsKey('hooks')) {
                $hooksObj = $hash['hooks']
                foreach ($eventName in @($hooksObj.PSObject.Properties.Name)) {
                    $groups = $hooksObj.$eventName
                    $newGroups = @()
                    foreach ($g in $groups) {
                        $newHks = @()
                        foreach ($h in $g.hooks) {
                            if ($h.command -and $h.command -like '*mcpowers*') {
                                # skip - mcpowers 自己的
                            } else {
                                $newHks += $h
                            }
                        }
                        if ($newHks.Count -gt 0) {
                            $g.hooks = $newHks
                            $newGroups += $g
                        }
                    }
                    if ($newGroups.Count -gt 0) {
                        $hooksObj.$eventName = $newGroups
                    } else {
                        $hooksObj.PSObject.Properties.Remove($eventName)
                    }
                }
                if ($hooksObj.PSObject.Properties.Count -eq 0) {
                    $hash.Remove('hooks')
                } else {
                    $hash['hooks'] = $hooksObj
                }
            }

            $hash | ConvertTo-Json -Depth 10 | Set-Content $SettingsPath -Encoding UTF8
            $ok = $true
        } catch {
            Write-Host "  ⚠ PowerShell 原生清理失败: $_" -ForegroundColor Yellow
        }
    }

    # 3. 结果
    if ($ok) {
        Write-Host "  ✓ hooks 已从 settings.json 清理" -ForegroundColor Green
        Remove-Item $Backup -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "  ✗ 清理失败，从备份回滚" -ForegroundColor Red
        if (Test-Path $Backup) {
            Copy-Item $Backup $SettingsPath -Force
            Remove-Item $Backup -Force
            Write-Host '  ↻ 已从备份回滚' -ForegroundColor Yellow
        }
    }
}

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

# ============== 清理 ~/.claude/settings.json 中的 mcpowers hooks ==============
Write-Host '=== 清理 Claude Code Hooks ===' -ForegroundColor Cyan
Cleanup-Hooks
Write-Host ''
Write-Host '如需重装: .\install.ps1'
