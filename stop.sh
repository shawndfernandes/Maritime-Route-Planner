#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "Stopping existing Maritime Route Engine processes..."
pkill -f "uvicorn backend.main:app.*8002" 2>/dev/null || true
pkill -f "http.server 3002" 2>/dev/null || true
sleep 1


