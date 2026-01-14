#!/bin/bash

# Development server startup script
# Safely starts Uvicorn with port conflict detection

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Configuration
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Issue Tracker API Development Server"
echo "================================================"

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}✗ Port $PORT is already in use${NC}"
    echo ""
    echo "Processes using port $PORT:"
    lsof -i :$PORT
    echo ""
    read -p "Kill existing processes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Killing processes on port $PORT...${NC}"
        lsof -ti :$PORT | xargs kill -9 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✓ Port $PORT is now free${NC}"
    else
        echo -e "${RED}✗ Cannot start server. Port $PORT is in use.${NC}"
        echo "Try running on a different port: PORT=8001 ./start_dev.sh"
        exit 1
    fi
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start the server
echo ""
echo -e "${GREEN}Starting server on http://$HOST:$PORT${NC}"
echo "API Documentation: http://$HOST:$PORT/docs"
echo "Press CTRL+C to stop"
echo ""

# Use exec to replace shell with uvicorn (cleaner process management)
exec uvicorn app.main:app \
    --reload \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level info \
    --access-log
