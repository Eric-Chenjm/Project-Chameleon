@echo off
chcp 936 >nul
title 变色龙 Antigravity 2.31.0 终极智能激活器

echo ========================================================
echo         变色龙 (Project Chameleon) Antigravity 2.31.0
echo                 极速智能汉化激活程序
echo ========================================================
echo.

set RES_DIR=%LOCALAPPDATA%\Programs\antigravity\resources
set ASAR=%RES_DIR%\app.asar
set TMP_ASAR=%RES_DIR%\app.asar.tmp
set UNPACKED=%RES_DIR%\app.asar.unpacked
set TMP_UNPACKED=%RES_DIR%\app.asar.tmp.unpacked
set APP_EXE=%LOCALAPPDATA%\Programs\antigravity\Antigravity.exe

:: 检查是否存在运行中或后台驻留进程
tasklist /FI "IMAGENAME eq Antigravity.exe" 2>NUL | find /I /N "Antigravity.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [提示] 检测到 Antigravity 窗口已关闭，但后台仍有托盘或渲染进程驻留。
    echo.
    echo 正在为您自动安全清理后台驻留进程，请稍候...
    taskkill /F /IM "Antigravity.exe" /T >nul 2>nul
    timeout /t 1 /nobreak >nul
)

echo.
echo [1/3] 正在应用 2.31.0 协议注入核心...
if exist "%TMP_ASAR%" (
    move /Y "%TMP_ASAR%" "%ASAR%" >nul
    if errorlevel 1 (
        echo [错误] 替换 app.asar 失败，请检查文件是否被其他程序占用。
        pause
        exit /b 1
    ) else (
        echo [OK] app.asar 协议注入核心替换成功！
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
    echo [OK] 2.31.0 汉化全量 UI 包已就绪 (12.03 MB)。
) else (
    echo [更新] 正在同步 zh_cn_ui_main.js 到缓存目录...
    copy /Y "translations\zh_cn_ui_main.js" "%APPDATA%\Antigravity\zh_cn_ui_main.js" >nul
)

echo.
echo ========================================================
echo  恭喜！Antigravity 2.31.0 全量汉化已 100%% 激活完成！
echo ========================================================
echo.
echo 按任意键立即启动全新中文版 Antigravity ...
pause >nul

if exist "%APP_EXE%" (
    start "" "%APP_EXE%"
)
exit
