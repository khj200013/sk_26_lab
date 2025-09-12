@echo off
chcp 65001 >nul
setlocal
set "ROOT=%~dp0"
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY (
  echo Python not found. Install Python 3 and add to PATH.
  pause & exit /b 1
)
REM Optional first run:
REM %PY% -m pip install --upgrade pip
REM %PY% -m pip install plyer win10toast
%PY% "%ROOT%src\daemon.py" --interval 15 --threshold 50 --debug
pause
