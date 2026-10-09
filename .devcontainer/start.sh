#!/usr/bin/env bash
# Starts the Flask backend (:5000) and Vite dev server (:5173) in the background.
cd "$(dirname "$0")/../media-platform"
LOG=/tmp/media-platform
mkdir -p "$LOG"

if ! (echo > /dev/tcp/127.0.0.1/5000) 2>/dev/null; then
  HOST=0.0.0.0 PORT=5000 nohup python3 backend/app.py > "$LOG/backend.log" 2>&1 &
fi
if ! (echo > /dev/tcp/127.0.0.1/5173) 2>/dev/null; then
  (cd frontend && nohup npm run dev -- --host 0.0.0.0 --port 5173 > "$LOG/frontend.log" 2>&1 &)
fi
