param(
  [int]$Port = 23456,
  [string]$Bridge = "D:\pycharm_wenjian\dsh\hmbridge\hm_bridge.tcl"
)
$ErrorActionPreference = "Stop"
$hw = "D:\Hyperwork2022\hwdesktop\hw\bin\win64\hw.exe"
if (-not (Test-Path $hw)) { throw "hw.exe not found: $hw" }
if (-not (Test-Path $Bridge)) { throw "bridge tcl not found: $Bridge" }
$env:HM_BRIDGE_PORT = "$Port"
$argsList = @("/clientconfig","hwfepre.dat","-tcl",$Bridge)
Write-Host "Launching HyperMesh 2022 with bridge on 127.0.0.1:$Port ..."
Start-Process -FilePath $hw -ArgumentList $argsList -WorkingDirectory "$env:USERPROFILE\Documents"
Write-Host "Started. Wait for the HyperMesh window, then use: python hmc.py ping"
