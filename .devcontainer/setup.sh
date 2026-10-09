#!/usr/bin/env bash
# Installs system + project dependencies for the media platform.
set -euo pipefail
cd "$(dirname "$0")/../media-platform"

if ! command -v ffmpeg >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y --no-install-recommends ffmpeg
fi

python3 -m pip install --user -r backend/requirements.txt
(cd frontend && npm install)
mkdir -p backend/data
