@echo off
chcp 65001 >nul
title MEFrp WebUI - Production Mode

echo.
echo ========================================
echo    MEFrp WebUI 生产模式启动器
echo ========================================
echo.

:: 检查 Python 便携版
if not exist "python_portable\python.exe" (
    echo [错误] 未找到 Python 便携版！
    echo 请先运行 start.bat 下载 Python
    pause
    exit /b 1
)

:: 安装 waitress（生产级 WSGI 服务器）
echo [1/2] 安装生产级服务器...
python_portable\python.exe -m pip install waitress -q

if errorlevel 1 (
    echo [错误] 安装 waitress 失败！
    echo 正在尝试使用开发模式启动...
    goto :dev_mode
)

:: 启动生产模式
echo.
echo [2/2] 启动 WebUI（生产模式）...
echo.
echo 访问地址：http://127.0.0.1:5000
echo 按 Ctrl+C 停止服务
echo.

:: 使用 waitress 作为 WSGI 服务器
python_portable\python.exe -c "from waitress import serve; from app import app; serve(app, host='0.0.0.0', port=5000)"

goto :end

:dev_mode
echo.
echo 启动开发模式...
echo.
echo 访问地址：http://127.0.0.1:5000
echo 按 Ctrl+C 停止服务
echo.
python_portable\python.exe app.py

:end
pause
