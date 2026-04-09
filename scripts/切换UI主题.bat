@echo off
chcp 65001 >nul
title UI主题切换工具
color 0A

echo.
echo ╔════════════════════════════════════════╗
echo ║      标准文献检索系统 - 主题切换      ║
echo ╚════════════════════════════════════════╝
echo.
echo 请选择您喜欢的UI主题:
echo.
echo  [1] 原始主题 - 经典商务风格
echo      └─ 蓝色 · 稳重专业 · 适合办公
echo.
echo  [2] 深色主题 - 现代科技风格 ⭐ 推荐
echo      └─ 紫蓝渐变 · 护眼炫酷 · 适合夜间
echo.
echo  [3] 扁平化主题 - 活力清新风格
echo      └─ 珊瑚红 · 色彩鲜明 · 视觉冲击
echo.
echo  [0] 退出
echo.
set /p choice=请输入数字 (0-3): 

if "%choice%"=="0" (
    echo 已取消切换
    timeout /t 1 >nul
    exit /b
)

if "%choice%"=="1" (
    echo.
    echo [√] 正在切换到原始主题...
    cd ..
    powershell -Command "$content = Get-Content 'app\desktop_app_impl.py' -Encoding UTF8; $content = $content -replace 'from app import ui_styles(_dark|_flat)? as ui_styles', 'from app import ui_styles'; $content | Set-Content 'app\desktop_app_impl.py' -Encoding UTF8"
    echo [√] 切换成功！主题: 原始主题
)

if "%choice%"=="2" (
    echo.
    echo [√] 正在切换到深色主题...
    cd ..
    powershell -Command "$content = Get-Content 'app\desktop_app_impl.py' -Encoding UTF8; $content = $content -replace 'from app import ui_styles(_dark|_flat)?( as ui_styles)?', 'from app import ui_styles_dark as ui_styles'; $content | Set-Content 'app\desktop_app_impl.py' -Encoding UTF8"
    echo [√] 切换成功！主题: 深色主题 (紫蓝渐变)
)

if "%choice%"=="3" (
    echo.
    echo [√] 正在切换到扁平化主题...
    cd ..
    powershell -Command "$content = Get-Content 'app\desktop_app_impl.py' -Encoding UTF8; $content = $content -replace 'from app import ui_styles(_dark|_flat)?( as ui_styles)?', 'from app import ui_styles_flat as ui_styles'; $content | Set-Content 'app\desktop_app_impl.py' -Encoding UTF8"
    echo [√] 切换成功！主题: 扁平化主题 (珊瑚红)
)

if not "%choice%"=="1" if not "%choice%"=="2" if not "%choice%"=="3" if not "%choice%"=="0" (
    echo.
    echo [×] 无效选择，请输入 0-3 之间的数字
    timeout /t 2 >nul
    goto :eof
)

echo.
echo ════════════════════════════════════════
echo  提示: 请重启应用以查看新主题效果
echo ════════════════════════════════════════
echo.
pause
