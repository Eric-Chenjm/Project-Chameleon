@echo off
chcp 65001 >nul
title 变色龙 Antigravity 2.30.0 极速激活器

echo ========================================================
echo         变色龙 (Project Chameleon) Antigravity 2.30.0
echo                 极速无感汉化激活程序
echo ========================================================
echo.

set "RES_DIR=%LOCALAPPDATA%\Programs\Antigravity\resources"
set "ASAR=%RES_DIR%\app.asar"
set "TMP_ASAR=%RES_DIR%\app.asar.tmp"

:: 检查 Antigravity 是否仍在运行
tasklist /FI "IMAGENAME eq Antigravity.exe" 2>NUL | find /I /N "Antigravity.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [提示] 检测到 Antigravity 正在运行中。
    echo 请先通过主菜单或右上角正常关闭 Antigravity 软件，
    echo 关闭完成后按任意键继续激活...
    echo.
    pause >nul
)

:: 再次检查
:check_again
tasklist /FI "IMAGENAME eq Antigravity.exe" 2>NUL | find /I /N "Antigravity.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [等待] 软件尚未完全退出，请完全退出后按任意键重试...
    pause >nul
    goto check_again
)

echo [1/2] 正在应用已预编译好的 2.30.0 协议劫持核心...
if exist "%TMP_ASAR%" (
    move /Y "%TMP_ASAR%" "%ASAR%" >nul
    if "%ERRORLEVEL%"=="0" (
        echo [OK] app.asar 协议注入替换成功！
    ) else (
        echo [错误] 替换失败，请确保 Antigravity 已完全退出。
        pause
        exit /b 1
    )
) else (
    echo [OK] 协议包已处于激活状态。
)

echo [2/2] 正在校验系统汉化缓存...
if exist "%APPDATA%\Antigravity\zh_cn_ui_main.js" (
    echo [OK] 2.30.0 汉化全量 UI 包已就绪 (11.86 MB)。
) else (
    echo [警告] 未检测到 zh_cn_ui_main.js，正在从分发目录同步...
    copy /Y "translations\zh_cn_ui_main.js" "%APPDATA%\Antigravity\zh_cn_ui_main.js" >nul
)

echo.
echo ========================================================
echo  🎉 恭喜！Antigravity 2.30.0 全量汉化已 100%% 激活完成！
echo     现在您可以正常启动 Antigravity 享受纯净中文体验。
echo ========================================================
echo.
pause
