@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem Windows 專用虛擬環境。.venv 可能是 Linux 建的（bin/ 而非 Scripts/），不共用。
set "VENV=.venv-win"
set "PY=%VENV%\Scripts\python.exe"

if exist "%PY%" goto :have_venv

rem 找可用的 Python：優先 py launcher，其次 PATH 上的 python。
rem 注意 python.exe 可能是 Microsoft Store 的空殼別名，所以要實際執行一次確認。
set "BOOTPY="
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 set "BOOTPY=py -3"
if not defined BOOTPY (
  python -c "import sys" >nul 2>&1
  if not errorlevel 1 set "BOOTPY=python"
)

if not defined BOOTPY (
  echo.
  echo [錯誤] 找不到可用的 Python。
  echo.
  echo 這台電腦沒有安裝 Python，或 PATH 上只有 Microsoft Store 的空殼別名。
  echo 請安裝 Python 3.12：
  echo.
  echo     winget install --id Python.Python.3.12 -e --scope machine
  echo.
  echo 或到 https://www.python.org/downloads/ 下載安裝，
  echo 安裝時務必勾選 "Add python.exe to PATH"，裝完重開這個視窗再試。
  echo.
  pause
  exit /b 1
)

echo 未找到 %VENV%，建立虛擬環境中...
%BOOTPY% -m venv "%VENV%" || goto :fail
"%PY%" -m pip install --upgrade pip || goto :fail
call :install_deps || goto :fail

:have_venv
rem 套件缺漏時（例如安裝到一半中斷）補裝
"%PY%" -c "import flask, PIL, edge_tts, pydub" 2>nul
if errorlevel 1 (
  echo 套件不完整，重新安裝中...
  call :install_deps || goto :fail
)

where ffmpeg >nul 2>&1 || echo 警告：未安裝 ffmpeg，音檔生成的靜音修剪/音量正規化會失敗（winget install Gyan.FFmpeg）

rem 等 server 起來再開瀏覽器；關掉這個視窗即停止 server。
start "" /min cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5001/"
"%PY%" server.py
goto :eof

:install_deps
"%PY%" -m pip install flask pillow edge-tts pydub || exit /b 1
rem Python 3.13 移除了 stdlib 的 audioop，pydub 需要 audioop-lts 補回
"%PY%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)"
if not errorlevel 1 "%PY%" -m pip install audioop-lts
exit /b 0

:fail
echo.
echo [錯誤] 環境準備失敗，請看上面的訊息。
pause
exit /b 1
