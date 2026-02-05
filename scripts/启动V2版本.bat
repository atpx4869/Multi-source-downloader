@echo off
chcp 65001 >nul
title 标准文献检索系统 V2
color 0A

echo.
echo ╔════════════════════════════════════════╗
echo ║     标准文献检索系统 V2 - 启动        ║
echo ╚════════════════════════════════════════╝
echo.
echo [√] 正在启动全新V2版本...
echo.

REM 切换到项目根目录
cd /d "%~dp0.."

echo [√] 当前目录: %CD%
echo.

REM 检查虚拟环境
if exist .venv\Scripts\python.exe (
    echo [√] 使用虚拟环境
    .venv\Scripts\python.exe app_v2\main.py
) else if exist WinPython-3.11.9\python.exe (
    echo [√] 使用WinPython
    WinPython-3.11.9\python.exe app_v2\main.py
) else (
    echo [√] 使用系统Python
    python app_v2\main.py
)

if errorlevel 1 (
    echo.
    echo [×] 启动失败！
    echo.
    pause
    exit /b 1
)

echo.
echo [√] 程序已关闭
pause
