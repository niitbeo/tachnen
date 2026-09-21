@echo off
chcp 65001 >nul
setlocal
set PYTHONIOENCODING=utf-8
set PYTHONNOUSERSITE=1
cd /d "%~dp0"

if exist "%~dp0python\python.exe" (
  set "PY=%~dp0python\python.exe"
) else (
  set "PY=python"
)

"%PY%" web.py
echo.
echo Da tat. Bam phim bat ky de dong.
pause >nul
