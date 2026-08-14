#!/bin/bash
cd "$(dirname "$0")"
python3 server.py &
SERVER_PID=$!
sleep 1
xdg-open "http://127.0.0.1:5001/admin.html" >/dev/null 2>&1
wait $SERVER_PID
