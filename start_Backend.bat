@echo off
title Backend BandungAJa
echo ========================================
echo   Menjalankan Backend BandungAJa
echo ========================================
echo.

venv\Scripts\activate

uvicorn main:app --reload

pause