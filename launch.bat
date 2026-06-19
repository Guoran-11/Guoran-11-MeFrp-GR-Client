@echo off
chcp 65001 >nul
title MEFrp WebUI

echo.
echo ========================================
echo     MEFrp WebUI 启动器
echo ========================================
echo.

:: 检查 Python 便携版
if not exist "python_portable\python.exe" (
    echo [错误] 未找到 Python 便携版！
    echo 请先运行 start.bat 下载 Python
    pause
    exit /b 1
)

:: 检查依赖
echo [检查] 验证依赖...
python_portable\python.exe -c "import flask; import requests" 2>nul

if errorlevel 1 (
    echo [安装] 安装依赖...
    python_portable\python.exe -m pip install flask requests -q
    if errorlevel 1 (
        echo [错误] 安装依赖失败！
        pause
        exit /b 1
    )
)

:: 安装 MEFrpLib（如果未安装）
python_portable\python.exe -c "import MEFrpLib" 2>nul
if errorlevel 1 (
    echo [安装] 安装 MEFrpLib...
    python_portable\python.exe -m pip install MEFrpLib -q
)

echo.
echo [启动] 正在启动 WebUI...
echo.
echo ========================================
echo 访问地址：http://127.0.0.1:5000
echo 端口：5000
echo ========================================
echo.
echo 提示：使用 launch_production.bat 可获得更稳定的生产模式
echo.
echo 按 Ctrl+C 停止服务
echo.

:: 启动 WebUI
python_portable\python.exe app.py
pause
