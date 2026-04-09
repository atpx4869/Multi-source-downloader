@echo off
chcp 65001 >nul
title 标准文献检索系统 - Web应用
color 0A

echo.
echo ========================================
echo      标准文献检索系统 - Web应用
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
echo [1/3] 安装后端依赖...
%PYTHON_CMD% -m pip install -q -r web_app\backend\requirements.txt
if errorlevel 1 (
    echo [×] 后端依赖安装失败！
    pause
    exit /b 1
)
echo [√] 后端依赖安装完成

echo.
echo [2/3] 启动后端服务器...
start "后端API服务器" cmd /k "%PYTHON_CMD% -m uvicorn web_app.backend.main:app --reload --host 0.0.0.0 --port 8000"

REM 等待后端启动
timeout /t 3 /nobreak >nul

echo [√] 后端服务器已启动
echo     后端地址: http://localhost:8000
echo     API文档: http://localhost:8000/api/docs

echo.
echo [3/3] 启动前端开发服务器...
cd web_app\frontend
start "前端开发服务器" cmd /k "npm run dev"

REM 等待前端启动
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   ✓ 应用启动完成！
echo.
echo   前端地址: http://localhost:5173
echo   后端地址: http://localhost:8000
echo   API文档: http://localhost:8000/api/docs
echo.
echo   两个窗口已打开：
echo   - 后端API服务器
echo   - 前端开发服务器
echo.
echo   关闭此窗口不会停止服务
echo   要停止服务，请关闭对应的窗口
echo ========================================
echo.

pause
