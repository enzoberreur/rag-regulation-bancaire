#!/bin/bash
# Script to run both backend and frontend together

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 Starting LLMOPS Product Application...${NC}\n"

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo -e "${YELLOW}❌ Backend directory not found${NC}"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping servers...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
    wait $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Servers stopped${NC}"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${BLUE}📦 Starting backend...${NC}"
cd backend
uv run python run.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 2

# Start frontend
echo -e "${BLUE}🎨 Starting frontend...${NC}"
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait a bit for frontend to start
sleep 3

echo -e "\n${GREEN}✅ Application started!${NC}\n"
echo -e "${GREEN}📍 Backend:${NC} http://localhost:8000"
echo -e "${GREEN}📍 Frontend:${NC} http://localhost:3000"
echo -e "${GREEN}📍 API Docs:${NC} http://localhost:8000/docs\n"
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}\n"

# Tail logs
tail -f backend.log frontend.log 2>/dev/null || {
    # If tail fails, just wait
    wait $BACKEND_PID $FRONTEND_PID
}

