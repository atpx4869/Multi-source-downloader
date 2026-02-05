@echo off
chcp 65001 >nul
title 重启Web前端
color 0C

echo.
echo ========================================
echo      强制重启前端开发服务器
echo ========================================
echo.

cd /d "%~dp0.."
cd web_app\frontend

echo [1/3] 清理Vite缓存...
if exist .vite (
    rmdir /s /q .vite
    echo [√] Vite缓存已清理
) else (
    echo [!] 无需清理缓存
)

echo.
echo [2/3] 清理node_modules缓存...
if exist node_modules\.vite (
    rmdir /s /q node_modules\.vite
    echo [√] node_modules缓存已清理
) else (
    echo [!] 无需清理node_modules缓存
)

echo.
echo [3/3] 启动开发服务器（强制重新构建）...
echo.
echo ========================================
echo   前端地址: http://localhost:5173
echo   按 Ctrl+C 停止服务器
echo ========================================
echo.

npm run dev -- --force

pause
