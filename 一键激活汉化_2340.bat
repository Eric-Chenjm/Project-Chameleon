@echo off
chcp 65001 >nul
title 变色龙 Antigravity 2.34.0 纯净手动汉化激活器

echo ========================================================
echo         变色龙 (Project Chameleon) Antigravity 2.34.0
echo               纯净安全手动汉化激活程序
echo ========================================================
echo.

cd /d "%~dp0"

:check_running
tasklist /FI "IMAGENAME eq Antigravity.exe" 2>NUL | find /I /N "Antigravity.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [提示] 检测到 Antigravity.exe 正在运行中！
    echo 为防止 app.asar 被占用锁定或引发闪退，请先【手动完全退出】 Antigravity 软件（含系统托盘）。
    echo 确认软件已完全退出后，按任意键重新检测并继续...
    echo.
    pause >nul
    goto check_running
)

set "PY_CMD="
if exist "E:\miniconda3\envs\pytorch\python.exe" (
    set "PY_CMD=E:\miniconda3\envs\pytorch\python.exe"
) else (
    where python >nul 2>nul
    if "%ERRORLEVEL%"=="0" (
        set "PY_CMD=python"
    )
)

if "%PY_CMD%"=="" (
    echo [错误] 未检测到可用的 Python 解释器，请先安装 Python 或配置环境后重试。
    pause
    exit /b 1
)

echo [1/2] 正在调用 smart_patch.py 执行 2.34.0 白名单校验与纯净注入...
"%PY_CMD%" "%~dp0smart_patch.py" --skip-process-check
if errorlevel 1 (
    echo.
    echo [错误] 汉化注入流程未完成，请查看上方提示信息。
    pause
    exit /b 1
)

echo.
echo [2/2] 正在校验系统汉化缓存...
if exist "%APPDATA%\Antigravity\zh_cn_ui_main.js" (
    echo [OK] 2.34.0 汉化全量 UI 包已就绪: %APPDATA%\Antigravity\zh_cn_ui_main.js
) else (
    echo [警告] 未在 %APPDATA%\Antigravity 找到 zh_cn_ui_main.js，请手动检查 translations\zh_cn_ui_main.js。
)

echo.
echo ========================================================
echo  恭喜！Antigravity 2.34.0 全量汉化已激活完成！
echo  请手动启动 Antigravity 软件体验中文界面（严禁强杀进程）。
echo ========================================================
echo.
pause
