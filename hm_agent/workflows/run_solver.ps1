# 运行 OptiStruct 求解器 (已验证环境配置)
# 用法: powershell -ExecutionPolicy Bypass -File topology/run_solver.ps1 <deck.fem>
param([string]$Deck = "D:\pycharm_wenjian\dsh\hmbridge\topology\topo_run.fem")
$ErrorActionPreference = "Continue"
$env:ALTAIR_HOME = "D:/Hyperwork2022/hwdesktop"
$env:NOLICENSECHECK = "true"
$env:PATH = "D:\Hyperwork2022\hwsolvers\common\bin\win64;D:\Hyperwork2022\hwsolvers\optistruct\bin\win64;D:\Hyperwork2022\hwdesktop\hw\bin\win64;D:\Hyperwork2022\common\python\python3.5\win64\DLLs;" + $env:PATH
$deck = (Resolve-Path $Deck).Path
$dir = Split-Path $deck
Set-Location $dir
Write-Host "Running OptiStruct on $deck ..."
& "D:\Hyperwork2022\hwsolvers\optistruct\bin\win64\optistruct_2022_win64.exe" $deck 2>&1 | Select-Object -Last 30
Write-Host "OS exit=$LASTEXITCODE"
