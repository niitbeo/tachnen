@echo off
chcp 65001 >nul
setlocal
set PYTHONIOENCODING=utf-8
set PYTHONNOUSERSITE=1
cd /d "%~dp0"

rem Uu tien Python di kem trong goi; khong co thi dung Python cua may
if exist "%~dp0python\python.exe" (
  set "PY=%~dp0python\python.exe"
) else (
  set "PY=python"
)

if "%~1"=="" (
  echo.
  echo   Keo tha anh ^(hoac ca thu muc anh^) vao tep nay de tach nen.
  echo.
  echo   Muon doi nen thi mo Command Prompt va go:
  echo     "%PY%" tachnen.py anh.jpg --bg trang
  echo.
  pause
  exit /b
)

:loop
if "%~1"=="" goto done
echo.
echo === %~nx1 ===
"%PY%" tachnen.py "%~1" --maxsize 2500
shift
goto loop

:done
echo.
echo Xong. Ket qua nam canh anh goc, ten co duoi _tachnen.png
echo.
pause
