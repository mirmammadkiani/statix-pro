@echo off
chcp 65001 > nul
title STATIX PRO Desktop App
echo ====================================================================
echo   STATIX PRO - نسخه دسکتاپ بومی (Native Desktop Window)
echo ====================================================================
echo در حال باز کردن پنجره اختصاصی نرم‌افزار دسکتاپ...

set PYTHON_CMD="C:\Users\AmirMohammad\AppData\Local\Programs\Python\Python314\python.exe"
if exist %PYTHON_CMD% (
    %PYTHON_CMD% desktop_app.py
    goto end
)

py -3 desktop_app.py
if %ERRORLEVEL% EQU 0 goto end

python desktop_app.py

:end
