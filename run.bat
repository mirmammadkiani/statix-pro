@echo off
chcp 65001 > nul
title STATIX PRO - Engineering Statics Suite
echo ====================================================================
echo   STATIX PRO - سامانه جامع تحلیل استاتیک مهندسی عمران (بیر جانسون)
echo ====================================================================
echo در حال راه‌اندازی سرور محاسباتی و باز کردن مرورگر...

set PYTHON_CMD="C:\Users\AmirMohammad\AppData\Local\Programs\Python\Python314\python.exe"
if exist %PYTHON_CMD% (
    %PYTHON_CMD% run.py
    goto end
)

py -3 run.py
if %ERRORLEVEL% EQU 0 goto end

python run.py

:end
pause
