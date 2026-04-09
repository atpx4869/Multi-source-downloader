@echo off
chcp 65001 >nul
title 标准文献检索系统 - 一键更新
color 0B

echo.
echo ╔════════════════════════════════════════╗
echo ║       标准文献检索系统 - 一键更新      ║
echo ╚════════════════════════════════════════╝
echo.
echo [!] 注意: 此操作将从 GitHub 拉取最新代码，并可能覆盖本地未提交的修改。
echo.
pause

REM 切换到项目根目录
cd /d "%~dp0.."

echo.
echo [√] 当前目录: %CD%
echo.

REM 检查是否安装了 git
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [×] 错误: 未找到 Git 命令！
    echo [!] 请确保已安装 Git 并将其添加到了系统环境变量中。
    echo.
    pause
    exit /b 1
)

echo [>] 正在获取最新代码状态...
git fetch origin
if %ERRORLEVEL% neq 0 (
    echo [×] 错误: 无法连接到 GitHub，请检查网络连接！
    echo.
    pause
    exit /b 1
)

echo [>] 正在拉取并合并最新代码...
git pull origin main
if %ERRORLEVEL% neq 0 (
    echo [!] 尝试强制更新当前分支...
    git reset --hard origin/main
    git pull origin main
    if %ERRORLEVEL% neq 0 (
        echo [×] 错误: 代码更新失败！
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [√] 代码更新成功！
echo.

echo [>] 正在检查并更新依赖...

REM 检查虚拟环境并更新依赖
if exist .venv\Scripts\python.exe (
    echo [√] 发现虚拟环境，正在更新 Python 依赖...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
) else if exist WinPython-3.11.9\python.exe (
    echo [√] 发现便携版 WinPython，正在更新 Python 依赖...
    WinPython-3.11.9\python.exe -m pip install -r requirements.txt
) else (
    echo [√] 使用系统 Python 更新依赖...
    python -m pip install -r requirements.txt
)

echo.
echo [>] 正在检查前端依赖 (如果存在)...
if exist web_app\frontend\package.json (
    where npm >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        echo [√] 发现前端项目，正在更新 npm 依赖...
        cd web_app\frontend
        call npm install
        cd /d "%~dp0.."
    ) else (
        echo [!] 未找到 npm 命令，跳过前端依赖更新。
    )
)

echo.
echo ╔════════════════════════════════════════╗
echo ║             更新流程全部完成           ║
echo ╚════════════════════════════════════════╝
echo.
echo [√] 您现在可以关闭此窗口，或运行启动脚本启动最新版本的系统了！
echo.
pause
