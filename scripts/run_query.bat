@echo off
set PROJECT_DIR=%~dp0..
cd /d %PROJECT_DIR%

echo ========================================
echo   FiveCross Unified Data Client
echo ========================================
echo.
echo Select Engine:
echo 1. ThinkingData (TA)
echo 2. AliCloud ODPS
echo 3. AliCloud Hologres
echo.

set /p choice="Enter choice (1-3, default 1): "

if "%choice%"=="2" (
    echo [FiveCross] Running AliCloud ODPS Report...
    python main.py --engine odps
) else if "%choice%"=="3" (
    echo [FiveCross] Running AliCloud Hologres Report...
    python main.py --engine holo
) else (
    echo [FiveCross] Running ThinkingData Report...
    python main.py --engine ta
)

echo.
echo Task Completed.
pause
