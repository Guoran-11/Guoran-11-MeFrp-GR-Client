@echo off
chcp 65001 >nul
title ME Frp WebUI 一键启动器

echo ========================================
echo    ME Frp WebUI 智能启动器
echo ========================================
echo.

cd /d "%~dp0"

:: 检查是否存在打包好的 EXE
if exist "dist\mefrp_webui.exe" (
    echo [检测] 发现打包版本，直接启动...
    start "" "dist\mefrp_webui.exe"
    echo.
    echo 程序已启动！请查看新打开的窗口
    pause
    exit /b 0
)

echo [提示] 未找到打包版本，尝试使用便携版 Python...
echo.

:: 检查便携版 Python 目录
set PORTABLE_PYTHON=python_portable\python.exe

if exist "%PORTABLE_PYTHON%" (
    echo [✓] 找到便携版 Python
    goto :run_with_python
)

echo [提示] 便携版 Python 不存在，正在设置...
echo.

:: 创建便携版 Python 目录
if not exist "python_portable" mkdir python_portable
cd python_portable

:: 下载 Python embeddable package
echo [1/3] 下载 Python 便携版...
set PYTHON_URL=https://www.python.org/ftp/python/3.12.9/python-3.12.9-embed-amd64.zip
set PYTHON_ZIP=python-embed.zip

if not exist "%PYTHON_ZIP%" (
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_ZIP%'}"
    if errorlevel 1 (
        echo [错误] 下载失败！
        echo 请手动下载: %PYTHON_URL%
        echo 解压到当前目录的 python_portable 文件夹
        pause
        exit /b 1
    )
)

:: 解压
echo [2/3] 解压 Python...
powershell -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '.' -Force"
if errorlevel 1 (
    echo [错误] 解压失败！
    pause
    exit /b 1
)

:: 配置 Python 路径
echo [3/3] 配置 Python...
echo.>> python312._pth
echo ..\Lib>> python312._pth
echo import site>> python312._pth

:: 安装 pip
echo [4/4] 安装 pip...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
python.exe get-pip.py --no-warn-script-location

cd ..
echo.
echo [✓] 便携版 Python 设置完成！

:run_with_python
echo.
echo [安装依赖] 检查并安装所需库...
cd python_portable
python.exe -m pip show MEFrpLib >nul 2>&1
if errorlevel 1 (
    echo 正在安装 MEFrpLib...
    python.exe -m pip install MEFrpLib -i https://pypi.tuna.tsinghua.edu.cn/simple
)
python.exe -m pip show flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装 Flask...
    python.exe -m pip install flask -i https://pypi.tuna.tsinghua.edu.cn/simple
)
cd ..

echo.
echo [启动] 启动 ME Frp WebUI...
echo.
echo 访问地址: http://127.0.0.1:5000
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

:: 延迟打开浏览器
start /B "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:5000"

:: 运行应用
python_portable\python.exe app.py

echo.
echo [提示] 程序已停止
pause