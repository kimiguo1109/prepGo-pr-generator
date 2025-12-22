#!/bin/bash

# PrepGo Practice Generator Start Script
# Frontend: http://44.236.240.72:28020 or http://pr-generator.prepgo.com
# Backend: http://44.236.240.72:28021

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PID files
BACKEND_PID_FILE=".backend.pid"
FRONTEND_PID_FILE=".frontend.pid"

# Log files
BACKEND_LOG="logs/backend.log"
FRONTEND_LOG="logs/frontend.log"

# Create logs directory
mkdir -p logs

# Load .env file if exists
load_env() {
    local env_file="$1"
    if [ -f "$env_file" ]; then
        echo -e "${BLUE}Loading environment from $env_file${NC}"
        set -a
        source "$env_file"
        set +a
    fi
}

# Load backend .env file
if [ -f "backend/.env" ]; then
    load_env "backend/.env"
elif [ -f ".env" ]; then
    load_env ".env"
fi

# Function to check if a process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to stop processes
stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    
    if is_running "$BACKEND_PID_FILE"; then
        local pid=$(cat "$BACKEND_PID_FILE")
        echo -e "  Stopping backend (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        rm -f "$BACKEND_PID_FILE"
    fi
    
    if is_running "$FRONTEND_PID_FILE"; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        echo -e "  Stopping frontend (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        rm -f "$FRONTEND_PID_FILE"
    fi
    
    # Also kill any processes on our ports (frontend: 28020, backend: 28021)
    fuser -k 28020/tcp 2>/dev/null || true
    fuser -k 28021/tcp 2>/dev/null || true
    
    echo -e "${GREEN}Services stopped.${NC}"
}

# Function to start backend
start_backend() {
    echo -e "${BLUE}Starting backend...${NC}"
    
    cd backend
    
    # Check for virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Install dependencies if needed
    if [ ! -d "venv" ] && [ -f "requirements.txt" ]; then
        echo -e "  Installing backend dependencies..."
        pip install -r requirements.txt -q
    fi
    
    # Check for GEMINI_API_KEY
    if [ -z "$GEMINI_API_KEY" ]; then
        echo -e "${YELLOW}Warning: GEMINI_API_KEY not set. Generation will fail without it.${NC}"
    fi
    
    # Start backend on port 28021
    nohup uvicorn app.main:app --host 0.0.0.0 --port 28021 --reload > "../$BACKEND_LOG" 2>&1 &
    local pid=$!
    echo $pid > "../$BACKEND_PID_FILE"
    
    cd ..
    
    echo -e "${GREEN}  Backend started (PID: $pid)${NC}"
    echo -e "  Backend URL: http://44.236.240.72:28021"
    echo -e "  API Docs: http://44.236.240.72:28021/docs"
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}Starting frontend...${NC}"
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo -e "  Installing frontend dependencies..."
        npm install --silent
    fi
    
    # Start frontend on port 28020
    nohup npm run dev -- --host 0.0.0.0 --port 28020 > "../$FRONTEND_LOG" 2>&1 &
    local pid=$!
    echo $pid > "../$FRONTEND_PID_FILE"
    
    cd ..
    
    echo -e "${GREEN}  Frontend started (PID: $pid)${NC}"
    echo -e "  Frontend URL: http://pr-generator.prepgo.com"
}

# Function to show status
show_status() {
    echo -e "\n${BLUE}=== PrepGo Practice Generator ===${NC}"
    
    if is_running "$BACKEND_PID_FILE"; then
        echo -e "Backend:  ${GREEN}Running${NC} (PID: $(cat $BACKEND_PID_FILE))"
    else
        echo -e "Backend:  ${RED}Stopped${NC}"
    fi
    
    if is_running "$FRONTEND_PID_FILE"; then
        echo -e "Frontend: ${GREEN}Running${NC} (PID: $(cat $FRONTEND_PID_FILE))"
    else
        echo -e "Frontend: ${RED}Stopped${NC}"
    fi
    
    echo -e "\nURLs:"
    echo -e "  Frontend: http://pr-generator.prepgo.com"
    echo -e "  Backend:  http://44.236.240.72:28021"
    echo -e "  API Docs: http://pr-generator.prepgo.com/docs"
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}=== Backend Logs ===${NC}"
    tail -50 "$BACKEND_LOG" 2>/dev/null || echo "No backend logs yet"
    
    echo -e "\n${BLUE}=== Frontend Logs ===${NC}"
    tail -50 "$FRONTEND_LOG" 2>/dev/null || echo "No frontend logs yet"
}

# Main command handling
case "${1:-start}" in
    start)
        stop_services
        sleep 1
        start_backend
        start_frontend
        sleep 2
        show_status
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 1
        start_backend
        start_frontend
        sleep 2
        show_status
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    backend)
        if is_running "$BACKEND_PID_FILE"; then
            echo "Backend already running"
        else
            start_backend
        fi
        ;;
    frontend)
        if is_running "$FRONTEND_PID_FILE"; then
            echo "Frontend already running"
        else
            start_frontend
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|backend|frontend}"
        exit 1
        ;;
esac

