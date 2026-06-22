@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title MeFrp-GR-Client 一键打包工具

echo.
echo ===============================================================
echo            MeFrp-GR-Client  一键打包为 EXE
echo ===============================================================
echo.
echo   本脚本会：
echo     1) 检查 Python 环境
echo     2) 安装 PyInstaller 与依赖
echo     3) 调用 build.spec 生成 dist\MeFrp-GR-Client\
echo.
echo   默认配置：双击 .exe 弹出 **原生 tkinter 桌面控制台窗口**
echo             （不打开浏览器，不需要任何浏览器引擎）
echo.
echo   命令行参数（双击运行时直接透传）：
echo     --no-gui / --web-only   仅启动 Web 后端（不弹 GUI）
echo     --open-browser          启动后自动打开浏览器
echo     --port 8080             修改端口
echo     --help                  查看所有参数
echo.
echo ===============================================================
echo.

:: 1) 查找 Python
set "PYTHON_EXE="
if exist "python_portable\python.exe" (
    set "PYTHON_EXE=python_portable\python.exe"
    echo [1/4] 检测到便携版 Python：!PYTHON_EXE!
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
        echo [1/4] 检测到系统 Python：python
    ) else (
        echo [错误] 未找到 Python！
        echo        请先运行 稳定启动.bat 自动下载便携版 Python
        pause
        exit /b 1
    )
)
echo.

:: 2) 安装 PyInstaller
echo [2/4] 检查/安装 PyInstaller ...
!PYTHON_EXE! -m pip show pyinstaller >nul 2>&1
if !errorlevel! neq 0 (
    echo        正在安装 PyInstaller ...
    !PYTHON_EXE! -m pip install pyinstaller
    if !errorlevel! neq 0 (
        echo [错误] PyInstaller 安装失败！
        pause
        exit /b 1
    )
) else (
    echo        PyInstaller 已安装
)
echo.

:: 安装项目依赖
echo        检查/安装项目依赖 ...
!PYTHON_EXE! -m pip install -q -r requirements.txt
!PYTHON_EXE! -m pip install -q waitress
echo.

:: 3) 打包
echo [3/4] 开始打包（这可能需要 1-3 分钟）...
echo.
!PYTHON_EXE! -m PyInstaller build.spec --clean --noconfirm
if !errorlevel! neq 0 (
    echo.
    echo [错误] 打包失败！请查看上方日志
    pause
    exit /b 1
)
echo.

:: 4) 检查产物
set "EXE_PATH=dist\MeFrp-GR-Client\MeFrp-GR-Client.exe"
if not exist "%EXE_PATH%" (
    echo [错误] 未找到打包产物：%EXE_PATH%
    pause
    exit /b 1
)

echo [4/4] 打包完成！
echo.
echo ===============================================================
echo   产物位置：%EXE_PATH%
echo.
echo   双击运行：弹出原生桌面控制台窗口
echo   命令行可选参数：
echo             --no-gui / --web-only   改为仅启动 Web 后端
echo             --open-browser          同时打开浏览器
echo             --port 8080             修改端口
echo ===============================================================
echo.

set /p RUN_NOW="是否立即启动试运行？(Y/N，默认N): "
if /i "%RUN_NOW%"=="Y" (
    echo.
    echo [试运行] 启动 %EXE_PATH% ...
    start "" "%EXE_PATH%"
)

echo.
echo 打包脚本执行完毕。
pause
endlocal
