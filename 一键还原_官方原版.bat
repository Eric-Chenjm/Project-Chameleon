@echo off
chcp 65001 >nul
title 变色龙 Project Chameleon v3.0 - 一键还原官方原版
cd /d "%~dp0"
if exist "E:\miniconda3\envs\pytorch\python.exe" (
  "E:\miniconda3\envs\pytorch\python.exe" chameleon.py --restore
) else (
  python chameleon.py --restore
)
pause
