@echo off
chcp 65001 >nul
pushd %~dp0

echo.
echo ============================================================
echo    标准号批量处理工具 - Web版
echo ============================================================
echo.

REM 检查是否已安装依赖
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [1/2] 正在安装依赖包...
    pip install -r requirements_web.txt
    echo.
) else (
    echo [✓] 依赖已安装
)

echo [2/2] 启动Web服务...
echo.
echo ============================================================
echo 🚀 服务器已启动！
echo.
echo 📍 请在浏览器中访问: http://127.0.0.1:5000
echo.
echo 💡 提示:
echo    - 使用 Ctrl+C 停止服务
echo    - 保持此窗口打开以继续使用
echo ============================================================
echo.

python web_app.py

popd
pause
