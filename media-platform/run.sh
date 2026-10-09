#!/usr/bin/env bash
# One-step build & run: ./run.sh  -> http://127.0.0.1:5000
set -e
cd "$(dirname "$0")"
python3 -m pip install -r backend/requirements.txt
(cd frontend && npm install && npm run build)
python3 backend/app.py
