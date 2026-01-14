#!/bin/bash

# Kill all Uvicorn processes safely
# Usage: ./kill_server.sh [port]

PORT=${1:-8000}

echo "🔍 Checking for processes on port $PORT..."

# Find processes using the port
PIDS=$(lsof -ti :$PORT 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo "✓ No processes found on port $PORT"
    exit 0
fi

echo "Found processes:"
lsof -i :$PORT

echo ""
read -p "Kill these processes? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Killing processes: $PIDS"
    echo "$PIDS" | xargs kill -9 2>/dev/null
    sleep 1
    
    # Verify
    if lsof -ti :$PORT >/dev/null 2>&1; then
        echo "⚠️  Some processes may still be running"
        lsof -i :$PORT
    else
        echo "✓ All processes on port $PORT have been terminated"
    fi
else
    echo "Cancelled"
fi
