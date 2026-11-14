#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ -x "backend/venv/bin/uvicorn" ]; then
  UVICORN_BIN="backend/venv/bin/uvicorn"
elif [ -x "../flight-forecast-engine/backend/venv/bin/uvicorn" ]; then
  UVICORN_BIN="../flight-forecast-engine/backend/venv/bin/uvicorn"
else
  echo "Error: uvicorn virtual environment not found. Please run ./setup.sh first."
  exit 1
fi

echo "Stopping existing Maritime Route Engine processes..."
pkill -f "uvicorn backend.main:app.*8002" 2>/dev/null || true
pkill -f "http.server 3002" 2>/dev/null || true
sleep 1

echo "Starting Maritime Route Engine API on http://localhost:8002 using ${UVICORN_BIN} ..."
PYTHONPATH=backend "${UVICORN_BIN}" backend.main:app --host 0.0.0.0 --port 8002 --reload &

echo "Starting Maritime Route Engine UI on http://localhost:3002 ..."
python3 -m http.server 3002 --directory frontend &

echo "Maritime Route Engine ready at http://localhost:3002"
