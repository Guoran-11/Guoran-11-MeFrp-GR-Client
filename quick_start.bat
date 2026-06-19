@echo off
chcp 65001 >nul
title ME Frp WebUI 启动器

echo ========================================
echo    ME Frp WebUI 启动器
echo ========================================
echo.

cd /d "%~dp0"

:: 使用 Python 的 -m 参数确保正确的路径导入
set PYTHONPATH=%CD%\python_portable\Lib\site-packages;%PYTHONPATH%

echo [启动] ME Frp WebUI...
echo 访问地址: http://127.0.0.1:5000
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

:: 延迟打开浏览器
start /B "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000"

:: 运行应用
python_portable\python.exe app.py

echo.
echo [提示] 程序已停止
pause