# ============================================================
# Trae 每日签到 - Windows 任务计划程序一键配置脚本
# ============================================================
#
# 使用方法：
#   1. 把整个 /workspace 目录（或至少 trae_checkin.py 和本脚本）
#      复制到你的 Windows 电脑上任意位置，例如:
#         C:\TraeCheckin\
#
#   2. 右键点击 setup_task.ps1 → 使用 PowerShell 运行
#      如果被执行策略拦截，先以管理员身份运行 PowerShell 再执行：
#         Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#
#   3. 脚本会自动：
#      - 查找已安装的 Python（避开 WindowsApps 假别名）
#      - 创建每天 07:00 运行的计划任务
#      - 显示任务状态，供你验证
#
#   4. 可选：首次配置好后，手动运行一次 trae_checkin.py 验证可用性
#
# 卸载：
#   在 PowerShell 中运行: schtasks /Delete /TN "Trae 每日签到" /F
#
# ============================================================

$ErrorActionPreference = "Stop"

# ---------- 1. 定位脚本自身所在目录（作为基准路径） ----------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyScript  = Join-Path $ScriptDir "trae_checkin.py"
$CalibrateScript = Join-Path $ScriptDir "calibrate.py"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Trae 每日签到 - 任务计划配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 验证签到脚本存在
if (-not (Test-Path $PyScript)) {
    Write-Host "[错误] 找不到 trae_checkin.py" -ForegroundColor Red
    Write-Host "脚本路径应为: $PyScript"
    exit 1
}
Write-Host "[OK] 签到脚本: $PyScript" -ForegroundColor Green

# ---------- 2. 查找 Python 解释器 ----------
Write-Host ""
Write-Host "正在查找 Python..." -ForegroundColor Yellow

$PythonExe = $null

# 方法 A: py launcher (Windows 官方推荐)
try {
    $pyVer = py --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $PythonExe = "py -3"
        Write-Host "[OK] 使用 py launcher: $pyVer" -ForegroundColor Green
    }
} catch {}

# 方法 B: where.exe python
if (-not $PythonExe) {
    $pyPaths = where.exe python 2>$null
    if ($pyPaths) {
        foreach ($p in $pyPaths) {
            # 跳过 WindowsApps 假别名 (0 字节的重解析点)
            try {
                $fileInfo = Get-Item $p
                if ($fileInfo.Length -gt 0 -and $fileInfo.FullName -notmatch "WindowsApps") {
                    $PythonExe = "`"$($fileInfo.FullName)`""
                    Write-Host "[OK] 找到 Python: $($fileInfo.FullName)" -ForegroundColor Green
                    break
                }
            } catch {}
        }
    }
}

# 方法 C: 检查常见安装路径
if (-not $PythonExe) {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe",
        "$env:ProgramFiles\Python3*\python.exe",
        "$env:ProgramFiles (x86)\Python3*\python.exe",
        "$env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe"
    )
    foreach ($pattern in $candidates) {
        $found = Get-Item $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found -and $found.Length -gt 0 -and $found.FullName -notmatch "WindowsApps") {
            $PythonExe = "`"$($found.FullName)`""
            Write-Host "[OK] 找到 Python: $($found.FullName)" -ForegroundColor Green
            break
        }
    }
}

if (-not $PythonExe) {
    Write-Host "[错误] 未找到有效的 Python 安装" -ForegroundColor Red
    Write-Host "请从 https://www.python.org/downloads/ 安装 Python 3"
    Write-Host "安装时勾选 'Add Python to PATH'"
    exit 1
}

# ---------- 3. 检查依赖 ----------
Write-Host ""
Write-Host "正在检查依赖..." -ForegroundColor Yellow

# 生成临时脚本来检查依赖
$depCheck = Join-Path $env:TEMP "trae_dep_check.py"
Set-Content -Path $depCheck -Value @"
import importlib
missing = []
for mod in ['pyautogui', 'PIL', 'win32gui', 'win32con']:
    try:
        importlib.import_module(mod)
    except ImportError:
        missing.append(mod)
if missing:
    print('MISSING:' + ','.join(missing))
else:
    print('OK')
"@

$depResult = & cmd /c "$PythonExe `"$depCheck`"" 2>&1
Remove-Item $depCheck -Force -ErrorAction SilentlyContinue

if ($depResult -match "^MISSING:(.+)$") {
    $missingList = $Matches[1] -split ","
    Write-Host "[缺失] 依赖库未安装: $($missingList -join ', ')" -ForegroundColor Yellow
    Write-Host "正在自动安装..." -ForegroundColor Yellow
    $pipCmd = "$PythonExe -m pip install pyautogui pillow pywin32"
    Write-Host "  $pipCmd"
    & cmd /c $pipCmd
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[警告] pip 安装可能失败，手动执行: pip install pyautogui pillow pywin32" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] 依赖安装完成" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] 所有依赖已就绪" -ForegroundColor Green
}

# ---------- 4. 检查脚本配置状态（坐标是否已填写） ----------
Write-Host ""
Write-Host "正在检查签到脚本配置..." -ForegroundColor Yellow

$configContent = Get-Content $PyScript -Raw
$needsCalibrate = $false
if ($configContent -match '"avatar_button": None') {
    Write-Host "[提示] 头像按钮坐标未配置" -ForegroundColor Yellow
    $needsCalibrate = $true
}
if ($configContent -match '"checkin_button": None') {
    Write-Host "[提示] 签到按钮坐标未配置" -ForegroundColor Yellow
    $needsCalibrate = $true
}

if ($needsCalibrate -and (Test-Path $CalibrateScript)) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  ⚠️  坐标未校准！" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "在计划任务能正常工作之前，你需要先校准坐标："
    Write-Host ""
    Write-Host "  1. 打开 Trae 桌面端"
    Write-Host "  2. 运行（复制到 PowerShell）：" -ForegroundColor Cyan
    Write-Host "     $PythonExe `"$CalibrateScript`"" -ForegroundColor Cyan
    Write-Host "  3. F1 = 头像按钮, F2 = 签到按钮, ESC = 完成"
    Write-Host "  4. 把输出的坐标填回 trae_checkin.py 的 CONFIG 区"
    Write-Host ""

    $continue = Read-Host "是否仍要先创建计划任务？(Y/N)"
    if ($continue -notmatch "^[Yy]") {
        Write-Host "好的，校准完坐标后再回来运行本脚本。" -ForegroundColor Cyan
        exit 0
    }
}

# ---------- 5. 创建计划任务 ----------
$TaskName = "Trae 每日签到"

Write-Host ""
Write-Host "正在创建计划任务: $TaskName" -ForegroundColor Yellow

# 如果任务已存在，先删除
$existing = schtasks /Query /TN $TaskName 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[提示] 已存在同名任务，先删除旧任务..." -ForegroundColor Yellow
    schtasks /Delete /TN $TaskName /F | Out-Null
}

# 构造命令
# /TR: 要运行的命令
# /SC DAILY: 每天
# /ST 07:00: 7 点
# /RL HIGHEST: 最高权限
# /RU SYSTEM: 系统账户（无论用户是否登录都能运行，但 GUI 操作受限）
#   => 改为当前用户 + 勾选"不管用户是否登录都要运行"，让 GUI 操作能进行

$actionCmd = "$PythonExe `"$PyScript`""

# 使用 PowerShell 的 ScheduledTask 模块，更灵活
$action  = New-ScheduledTaskAction -Execute ($PythonExe -replace '^"|"$','') -Argument "`"$PyScript`"" -WorkingDirectory $ScriptDir
$trigger = New-ScheduledTaskTrigger -Daily -At 07:00AM
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "每天 7:00 自动运行 Trae 桌面端签到" `
        -Force `
        | Out-Null

    Write-Host "[OK] 计划任务创建成功！" -ForegroundColor Green
} catch {
    Write-Host "[错误] Register-ScheduledTask 失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "尝试用 schtasks 命令行方式..." -ForegroundColor Yellow

    # 回退方案：使用 schtasks.exe
    $cmdArgs = "/Create /TN `"$TaskName`" /TR `"$actionCmd`" /SC DAILY /ST 07:00 /RL HIGHEST /F"
    $result = & cmd /c "schtasks $cmdArgs" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] schtasks 创建成功" -ForegroundColor Green
    } else {
        Write-Host "[错误] schtasks 也失败了: $result" -ForegroundColor Red
        Write-Host ""
        Write-Host "请手动操作："
        Write-Host "  1. Win+S 搜索 '任务计划程序'"
        Write-Host "  2. 创建基本任务 → 名称 'Trae 每日签到'"
        Write-Host "  3. 每天 07:00"
        Write-Host "  4. 启动程序 → 程序 $($PythonExe -replace '^"|"$','') 参数 `"$PyScript`" 起始位置 `"$ScriptDir`""
        exit 1
    }
}

# ---------- 6. 验证并显示 ----------
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ 配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 查询任务显示详情
try {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "任务名称:   $TaskName"
        Write-Host "触发器:     每天 07:00"
        Write-Host "执行程序:   $($task.Actions.Execute)"
        Write-Host "参数:       $($task.Actions.Arguments)"
        Write-Host "工作目录:   $ScriptDir"
        Write-Host "上次运行:   $($task.LastRunTime)"
        Write-Host "下次运行:   $($task.NextRunTime)"
    }
} catch {
    # schtasks 查询
    schtasks /Query /TN $TaskName /V /FO LIST
}

Write-Host ""
Write-Host "--- 快速验证 ---" -ForegroundColor Cyan
Write-Host "手动运行一次："
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看日志："
Write-Host "  Get-Content `"$ScriptDir\checkin.log`" -Tail 20" -ForegroundColor Cyan
Write-Host ""
Write-Host "删除任务："
Write-Host "  schtasks /Delete /TN `"$TaskName`" /F" -ForegroundColor Cyan
Write-Host ""
