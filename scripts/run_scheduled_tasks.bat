@echo off
:: run_scheduled_tasks.bat
:: 用于 Windows 计划任务的启动脚本

cd /d "%~dp0.."

:: 检查并激活虚拟环境 (如果有)
if exist venv\Scripts\activate (
    call venv\Scripts\activate
)

echo [%date% %time%] Starting scheduled data tasks...

:: 运行主程序加载定时任务 JSON
:: 注意：main.py 现在会自动根据文件名在 tasks/configs 下搜索
python main.py fetch --task scheduled_multi_tasks.json

echo [%date% %time%] Tasks completed.
pause
