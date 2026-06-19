@echo off
chcp 65001 >nul
title 修复 MEFrpLib 导入问题

echo ========================================
echo    修复 MEFrpLib 导入问题
echo ========================================
echo.

cd /d "%~dp0"

:: 检查 Python 是否存在
if not exist "python_portable\python.exe" (
    echo [错误] 找不到 Python！
    echo 请先运行 start.bat 进行初始化设置
    pause
    exit /b 1
)

echo [1/4] 检查 MEFrpLib 安装状态...
python_portable\python.exe -c "import MEFrpLib" 2>nul
if errorlevel 1 (
    echo [警告] MEFrpLib 导入失败，正在修复...
) else (
    echo [✓] MEFrpLib 已正常工作
    goto :test_other
)

echo.
echo [2/4] 确保 site 模块已启用...
if exist "python_portable\python312._pth" (
    findstr /C:"import site" python_portable\python312._pth >nul
    if errorlevel 1 (
        echo.>> python_portable\python312._pth
        echo import site>> python_portable\python312._pth
        echo [✓] 已启用 site 模块
    ) else (
        echo [✓] site 模块已启用
    )
)

echo.
echo [3/4] 重新安装 MEFrpLib...
python_portable\Scripts\pip.exe uninstall MEFrpLib -y >nul 2>&1
python_portable\Scripts\pip.exe install MEFrpLib -i https://pypi.tuna.tsinghua.edu.cn/simple

if errorlevel 1 (
    echo [错误] 安装失败！
    pause
    exit /b 1
)

echo.
echo [4/4] 测试导入...
python_portable\python.exe -c "import MEFrpLib; print('MEFrpLib 版本:', MEFrpLib.__version__ if hasattr(MEFrpLib, '__version__') else '未知')"
if errorlevel 1 (
    echo [错误] 导入仍然失败！
    pause
    exit /b 1
)

:test_other
echo.
echo ========================================
echo    测试其他依赖
echo ========================================
echo.

:: 测试 Flask
python_portable\python.exe -c "import flask; print('✓ Flask 版本:', flask.__version__)"
if errorlevel 1 (
    echo [警告] Flask 导入失败，正在修复...
    python_portable\Scripts\pip.exe install flask -i https://pypi.tuna.tsinghua.edu.cn/simple
)

:: 测试 requests
python_portable\python.exe -c "import requests; print('✓ requests 版本:', requests.__version__)"
if errorlevel 1 (
    echo [警告] requests 导入失败，正在修复...
    python_portable\Scripts\pip.exe install requests -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo ========================================
echo    启动 WebUI
echo ========================================
echo.
echo 所有依赖已修复完成！
echo 访问地址: http://127.0.0.1:5000
echo 按 Ctrl+C 停止服务
echo.

:: 延迟打开浏览器
start /B "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000"

python_portable\python.exe app.py

echo.
echo [提示] 程序已停止
pause