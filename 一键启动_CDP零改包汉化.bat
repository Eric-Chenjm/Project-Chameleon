@echo off
chcp 65001 >nul
title 变色龙 Project Chameleon v3.0 - 零改包 CDP 动态汉化
cd /d "%~dp0"
if exist "E:\miniconda3\envs\pytorch\python.exe" (
  "E:\miniconda3\envs\pytorch\python.exe" chameleon.py --cdp
) else (
  python chameleon.py --cdp
)
pause
