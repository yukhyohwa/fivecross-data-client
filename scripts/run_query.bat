@echo off
set PROJECT_DIR=%~dp0..
cd /d %PROJECT_DIR%

echo ========================================
echo   FiveCross Unified Data Client
echo ========================================
echo.
echo [FiveCross] Executing Scheduled Multi-Tasks...
echo Tasks file: tasks\scheduled_multi_tasks.json
echo.

:: Using the explicit Python path from your working environment
"C:\ProgramData\miniconda3\python.exe" main.py --task tasks/scheduled_multi_tasks.json

echo.
echo ========================================
echo   Process Finished.
echo ========================================
pause
