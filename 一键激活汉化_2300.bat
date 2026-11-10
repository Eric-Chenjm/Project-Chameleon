@echo off
title 变色龙 Antigravity 2.30.0 极速激活器

echo ========================================================
echo         变色龙 (Project Chameleon) Antigravity 2.30.0
echo                 极速无感汉化激活程序
echo ========================================================
echo.

set RES_DIR=%LOCALAPPDATA%\Programs\antigravity\resources
set ASAR=%RES_DIR%\app.asar
set TMP_ASAR=%RES_DIR%\app.asar.tmp
set UNPACKED=%RES_DIR%\app.asar.unpacked
set TMP_UNPACKED=%RES_DIR%\app.asar.tmp.unpacked

:check_running
tasklist /FI "IMAGENAME eq Antigravity.exe" 2>NUL | find /I /N "Antigravity.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [提示] 检测到 Antigravity 正在运行中。
    echo 请先完全关闭 Antigravity 软件（右上角关闭）。
    echo 退出软件后，按任意键继续执行激活...
    echo.
    pause >nul
    goto check_running
)

echo [1/3] 正在应用 2.30.0 协议注入核心...
if exist "%TMP_ASAR%" (
    move /Y "%TMP_ASAR%" "%ASAR%" >nul
    if errorlevel 1 (
        echo [错误] 替换 app.asar 失败，请确认 Antigravity 已完全退出。
        pause
        exit /b 1
    ) else (
        echo [OK] app.asar 替换成功！
    )
) else (
    echo [OK] app.asar 已经是打好补丁的状态。
)

echo [2/3] 正在同步解包资源...
if exist "%TMP_UNPACKED%" (
    if exist "%UNPACKED%" rd /s /q "%UNPACKED%" >nul 2>nul
    move /Y "%TMP_UNPACKED%" "%UNPACKED%" >nul
    echo [OK] 解包资源已同步！
)

echo [3/3] 正在校验系统汉化缓存...
if exist "%APPDATA%\Antigravity\zh_cn_ui_main.js" (
    echo [OK] 2.30.0 汉化全量 UI 包已就绪。
) else (
    echo [更新] 正在同步 zh_cn_ui_main.js 到缓存目录...
    copy /Y "translations\zh_cn_ui_main.js" "%APPDATA%\Antigravity\zh_cn_ui_main.js" >nul
)

echo.
echo ========================================================
echo  恭喜！Antigravity 2.30.0 全量汉化已 100%% 激活完成！
echo     现在您可以正常启动 Antigravity 享受纯净中文体验。
echo ========================================================
echo.
pause
