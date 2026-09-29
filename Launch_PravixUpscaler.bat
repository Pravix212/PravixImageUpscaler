@echo off
cd /d "%~dp0"
if exist "%~dp0dist\PravixUpscaler_Portable.exe" (
    start "" "%~dp0dist\PravixUpscaler_Portable.exe"
) else (
    python desktop_app.py
)
