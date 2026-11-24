@echo off
chcp 65001 >nul
title 变色龙 Project Chameleon v3.0 - 增量无损 ASAR 补丁安装
cd /d "%~dp0"
if exist "E:\miniconda3\envs\pytorch\python.exe" (
  "E:\miniconda3\envs\pytorch\python.exe" chameleon.py --patch
) else (
  python chameleon.py --patch
)
pause
