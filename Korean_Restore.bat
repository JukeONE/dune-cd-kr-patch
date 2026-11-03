@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0kopatch\kopatch.ps1" -Restore
pause
