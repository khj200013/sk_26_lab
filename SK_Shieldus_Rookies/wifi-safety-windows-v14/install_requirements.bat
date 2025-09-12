@echo off
chcp 65001 >nul
setlocal
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY (
  echo Python not found. Install Python 3 and add to PATH.
  pause & exit /b 1
)
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
pause
