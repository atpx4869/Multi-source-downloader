@echo off
setlocal
chcp 65001 >nul
title One-Click Update
color 0B

echo.
echo ==========================================
echo  One-Click Update (GitHub Sync)
echo ==========================================
echo.
echo This will update code from GitHub and may discard local uncommitted changes.
echo.
pause

cd /d "%~dp0.."
echo.
echo Current dir: %CD%
echo.

git --version >nul 2>nul
if errorlevel 1 (
  echo ERROR: Git not found. Please install Git and add it to PATH.
  echo.
  pause
  exit /b 1
)

echo Fetching latest...
git fetch origin
if errorlevel 1 (
  echo ERROR: git fetch failed. Check your network / GitHub access.
  echo.
  pause
  exit /b 1
)

echo Pulling latest...
git pull origin main
if errorlevel 1 (
  echo Pull failed. Trying hard reset to origin/main...
  git reset --hard origin/main
  if errorlevel 1 (
    echo ERROR: git reset failed.
    echo.
    pause
    exit /b 1
  )
  git pull origin main
  if errorlevel 1 (
    echo ERROR: git pull still failed.
    echo.
    pause
    exit /b 1
  )
)

echo.
echo Code update OK.
echo.

echo Updating Python dependencies...
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -m pip install -r requirements.txt
) else if exist WinPython-3.11.9\python.exe (
  WinPython-3.11.9\python.exe -m pip install -r requirements.txt
) else (
  python -m pip install -r requirements.txt
)

echo.
echo Updating frontend dependencies (if any)...
if exist web_app\frontend\package.json (
  npm --version >nul 2>nul
  if errorlevel 1 (
    echo npm not found. Skip frontend install.
  ) else (
    cd web_app\frontend
    call npm install
    cd /d "%~dp0.."
  )
)

echo.
echo ==========================================
echo Update completed.
echo ==========================================
echo.
pause
