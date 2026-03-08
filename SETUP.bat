@echo off
title Reboot Launcher — First-Time Setup
color 0A

echo.
echo  =====================================================
echo   Reboot Launcher — First-Time Setup
echo  =====================================================
echo.
echo  This script will install the required Visual C++
echo  Redistributable so that the launcher works correctly.
echo.

:: Check for the redistributable installer
set "REDIST_PATH=%~dp0dependencies\redist\VC_redist.x64.exe"

if not exist "%REDIST_PATH%" (
    echo  [!] VC_redist.x64.exe not found at:
    echo      %REDIST_PATH%
    echo.
    echo  Please download it manually from:
    echo  https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo  and run it before starting the launcher.
    echo.
    pause
    exit /b 1
)

echo  Installing Visual C++ Redistributable...
echo  (You may see a UAC prompt — click Yes to continue)
echo.
"%REDIST_PATH%" /install /quiet /norestart
if %errorlevel% equ 0 (
    echo  [OK] Visual C++ Redistributable installed successfully.
) else if %errorlevel% equ 1638 (
    echo  [OK] Visual C++ Redistributable is already installed.
) else (
    echo  [!] Installation may have failed (exit code: %errorlevel%).
    echo      Try running VC_redist.x64.exe manually.
)

echo.
echo  =====================================================
echo   Setup complete! You can now run reboot_launcher.exe
echo  =====================================================
echo.
echo  Quick-start guide:
echo    - Solo play  : Open launcher, go to Play tab, click Launch Fortnite.
echo    - Host LAN   : Go to Host tab, start hosting, share your LAN IP.
echo    - Join LAN   : Go to Backend tab, switch to Remote, click Scan LAN for Host.
echo.
pause
