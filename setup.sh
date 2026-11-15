#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=== 1. Setting up Python Virtual Environment (backend/venv) ==="
python3 -m venv backend/venv
./backend/venv/bin/pip install --upgrade pip
./backend/venv/bin/pip install -r backend/requirements.txt

echo "=== 2. Setting up CesiumJS (frontend/cesium) ==="
chmod +x setup_cesium.sh restart.sh stop.sh
./setup_cesium.sh

echo "Setup complete! Run ./restart.sh to start Ground Route Engine on http://localhost:3001"
