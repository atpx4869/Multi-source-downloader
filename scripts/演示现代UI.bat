@echo off
chcp 65001 >nul
title 现代化UI演示
color 0A

echo.
echo ╔════════════════════════════════════════╗
echo ║      现代化UI组件演示程序启动          ║
echo ╚════════════════════════════════════════╝
echo.
echo [√] 正在启动现代化UI演示...
echo.

REM 切换到项目根目录
cd /d "%~dp0.."

REM 检查虚拟环境
if exist .venv\Scripts\python.exe (
    echo [√] 使用虚拟环境
    echo [√] 当前目录: %CD%
    .venv\Scripts\python.exe app\modern_ui_demo.py
) else if exist WinPython-3.11.9\python.exe (
    echo [√] 使用WinPython
    echo [√] 当前目录: %CD%
    WinPython-3.11.9\python.exe app\modern_ui_demo.py
) else (
    echo [√] 使用系统Python
    echo [√] 当前目录: %CD%
    python app\modern_ui_demo.py
)

if errorlevel 1 (
    echo.
    echo [×] 启动失败！
    echo.
    echo 可能的原因:
    echo 1. Python未安装或未添加到PATH
    echo 2. 缺少依赖包 (PySide6)
    echo.
    echo 解决方案:
    echo 1. 运行: scripts\首次安装.bat
    echo 2. 或手动安装: pip install PySide6
    echo.
    pause
    exit /b 1
)

echo.
echo [√] 程序已关闭
pause
