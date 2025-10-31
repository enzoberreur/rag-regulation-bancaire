#!/bin/bash
# Script to run the backend server

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/backend"

echo -e "${BLUE}📦 Starting backend server...${NC}\n"

# Check if backend directory exists
if [ ! -d "." ]; then
    echo -e "${YELLOW}❌ Backend directory not found${NC}"
    exit 1
fi

# Start backend
uv run python run.py

