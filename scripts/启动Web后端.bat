@echo off
chcp 65001 >nul
title 启动Web应用后端
color 0A

echo.
echo ========================================
echo      标准文献检索系统 - 后端API
echo ========================================
echo.

cd /d "%~dp0.."

REM 检测Python环境
set PYTHON_CMD=

if exist WinPython-3.11.9\python.exe (
    echo [√] 使用WinPython 3.11.9
    set PYTHON_CMD=WinPython-3.11.9\python.exe
) else if exist .venv\Scripts\python.exe (
    echo [√] 使用虚拟环境
    set PYTHON_CMD=.venv\Scripts\python.exe
) else (
    echo [×] 未找到Python环境！
    echo.
    echo 请先运行: scripts\首次安装.bat
    pause
    exit /b 1
)

echo.
echo [1/2] 安装依赖...
%PYTHON_CMD% -m pip install -q -r web_app\backend\requirements.txt
if errorlevel 1 (
    echo [×] 依赖安装失败！
    pause
    exit /b 1
)

echo [√] 依赖安装完成
echo.

echo [2/2] 启动FastAPI服务器...
echo.
echo ========================================
echo   后端API: http://localhost:8000
echo   API文档: http://localhost:8000/api/docs
echo   按 Ctrl+C 停止服务器
echo ========================================
echo.

REM 直接在项目根目录运行，使用完整路径
%PYTHON_CMD% -m uvicorn web_app.backend.main:app --reload --host 0.0.0.0 --port 8000

pause
