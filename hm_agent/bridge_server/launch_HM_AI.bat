@echo off
rem HyperMesh 2022 AI collaboration launcher (loads hm_bridge.tcl on port 23456)
set HM_BRIDGE_PORT=23456
cd /d "%USERPROFILE%\Documents"

rem 1. Check custom environment variable ALTAIR_HOME
if defined ALTAIR_HOME (
    if exist "%ALTAIR_HOME%\hwdesktop\hw\bin\win64\hw.exe" (
        set "HW_EXE=%ALTAIR_HOME%\hwdesktop\hw\bin\win64\hw.exe"
        goto launch
    )
)

rem 2. Search common default installation paths
if exist "D:\Hyperwork2022\hwdesktop\hw\bin\win64\hw.exe" (
    set "HW_EXE=D:\Hyperwork2022\hwdesktop\hw\bin\win64\hw.exe"
    goto launch
)
if exist "C:\Altair\2022\hwdesktop\hw\bin\win64\hw.exe" (
    set "HW_EXE=C:\Altair\2022\hwdesktop\hw\bin\win64\hw.exe"
    goto launch
)
if exist "C:\Program Files\Altair\2022\hwdesktop\hw\bin\win64\hw.exe" (
    set "HW_EXE=C:\Program Files\Altair\2022\hwdesktop\hw\bin\win64\hw.exe"
    goto launch
)
if exist "C:\Program Files\Altair\2021\hwdesktop\hw\bin\win64\hw.exe" (
    set "HW_EXE=C:\Program Files\Altair\2021\hwdesktop\hw\bin\win64\hw.exe"
    goto launch
)

echo [WARNING] Could not automatically locate hw.exe in standard Altair paths.
echo Please set the ALTAIR_HOME environment variable or launch HyperMesh manually and run mount_bridge.tcl.
pause
exit /b 1

:launch
echo Found HyperMesh at: %HW_EXE%
start "" "%HW_EXE%" /clientconfig hwfepre.dat -tcl "%~dp0hm_bridge.tcl"
echo HyperMesh launching with AI bridge (port 23456)...
