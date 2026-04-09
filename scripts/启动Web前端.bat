@echo off
chcp 65001 >nul
title 启动Web前端
color 0A

echo.
echo ========================================
echo      标准文献检索系统 - 前端界面
echo ========================================
echo.

cd /d "%~dp0.."
cd web_app\frontend

echo [1/1] 启动开发服务器...
echo.
echo ========================================
echo   前端地址: http://localhost:5173
echo   确保后端已启动: http://localhost:8000
echo   按 Ctrl+C 停止服务器
echo ========================================
echo.

npm run dev

pause
