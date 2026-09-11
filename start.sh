#!/bin/bash
set -e
cd "$(dirname "$0")"

VENV=".venv"
PY="$VENV/bin/python"

# 首次執行（或重灌系統後）自動建立虛擬環境並安裝套件
if [ ! -x "$PY" ]; then
  echo "未找到 $VENV，建立虛擬環境中..."
  python3 -m venv "$VENV"
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install flask pillow edge-tts pydub
fi

# 套件缺漏時（例如安裝到一半中斷）補裝
if ! "$PY" -c "import flask, PIL, edge_tts, pydub" 2>/dev/null; then
  echo "套件不完整，重新安裝中..."
  "$PY" -m pip install flask pillow edge-tts pydub
fi

command -v ffmpeg >/dev/null || echo "警告：未安裝 ffmpeg，音檔生成的靜音修剪/音量正規化會失敗（sudo apt install ffmpeg）"

"$PY" server.py &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null' EXIT INT TERM
sleep 1
xdg-open "http://127.0.0.1:5001/" >/dev/null 2>&1
wait $SERVER_PID
