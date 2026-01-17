#!/bin/bash

# AI Anti-Spam Shield - Backend Server Startup Script
# This script starts the Node.js Express backend server

echo "=========================================="
echo "  AI Anti-Spam Shield - Backend Server"
echo "=========================================="

# Configuration
PROJECT_ROOT="/opt/school-project/ai-anti-spam-shield"
BACKEND_DIR="$PROJECT_ROOT/ai-anti-spam-shield-backend"
PORT=3000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to backend directory
cd "$BACKEND_DIR" || {
    echo -e "${RED}Error: Could not navigate to $BACKEND_DIR${NC}"
    exit 1
}

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    yarn install || npm install
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}Please update .env with your configuration.${NC}"
    else
        echo -e "${YELLOW}Warning: No .env file found.${NC}"
    fi
fi

# Kill any existing process on the port
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}Killing existing process on port $PORT...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

echo -e "${GREEN}Starting Backend Server...${NC}"
echo "Port: $PORT"
echo "API Base: http://localhost:$PORT/api/v1"
echo "Swagger Docs: http://localhost:$PORT/api-docs"
echo "Health Check: http://localhost:$PORT/health"
echo "=========================================="

# Start the server
yarn dev
