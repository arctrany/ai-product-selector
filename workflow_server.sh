#!/bin/bash

# Workflow Engine Server Control Script
# Usage: ./workflow_server.sh [start|stop|restart|status]

PROJECT_DIR="/Users/haowu/IdeaProjects/ai-product-selector3"
SERVER_MODULE="workflow_engine.api.server"
PID_FILE="$PROJECT_DIR/.workflow_server.pid"
LOG_FILE="$PROJECT_DIR/workflow_server.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if server is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the server
start_server() {
    if is_running; then
        print_warning "Server is already running (PID: $(cat $PID_FILE))"
        return 1
    fi

    print_status "Starting Workflow Engine Server..."
    
    # Kill any processes using ports 8000, 8888, 8001, 8889
    print_status "Cleaning up ports 8000, 8888, 8001, 8889..."
    lsof -ti:8000,8888,8001,8889 2>/dev/null | xargs kill -9 2>/dev/null || true
    
    # Change to project directory and start server
    cd "$PROJECT_DIR/src_new"
    
    # Start server in background
    nohup python3 -m "$SERVER_MODULE" > "$LOG_FILE" 2>&1 &
    local server_pid=$!
    
    # Save PID
    echo "$server_pid" > "$PID_FILE"
    
    # Wait a moment and check if server started successfully
    sleep 3
    
    if is_running; then
        print_status "Server started successfully (PID: $server_pid)"
        print_status "Server running on: http://0.0.0.0:8889"
        print_status "Log file: $LOG_FILE"
        return 0
    else
        print_error "Failed to start server"
        print_error "Check log file: $LOG_FILE"
        return 1
    fi
}

# Function to stop the server
stop_server() {
    if ! is_running; then
        print_warning "Server is not running"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    print_status "Stopping server (PID: $pid)..."
    
    # Try graceful shutdown first
    kill "$pid" 2>/dev/null
    
    # Wait for graceful shutdown
    local count=0
    while [ $count -lt 10 ] && ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        print_warning "Forcing server shutdown..."
        kill -9 "$pid" 2>/dev/null
    fi
    
    # Clean up
    rm -f "$PID_FILE"
    
    # Also clean up any remaining processes on our ports
    lsof -ti:8000,8888,8001,8889 2>/dev/null | xargs kill -9 2>/dev/null || true
    
    print_status "Server stopped"
}

# Function to restart the server
restart_server() {
    print_status "Restarting Workflow Engine Server..."
    stop_server
    sleep 2
    start_server
}

# Function to show server status
show_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_status "Server is running (PID: $pid)"
        print_status "Server URL: http://0.0.0.0:8889"
        print_status "Apps page: http://localhost:8889/apps"
        
        # Show port usage
        echo ""
        echo "Port usage:"
        lsof -i:8889 2>/dev/null || echo "Port 8889: Not in use"
        
        # Show recent log entries
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "Recent log entries:"
            tail -n 5 "$LOG_FILE"
        fi
    else
        print_warning "Server is not running"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_status "Showing server logs (Press Ctrl+C to exit):"
        tail -f "$LOG_FILE"
    else
        print_error "Log file not found: $LOG_FILE"
    fi
}

# Function to open apps page
open_apps() {
    if is_running; then
        print_status "Opening apps page in browser..."
        open "http://localhost:8889/apps" 2>/dev/null || {
            print_status "Please open: http://localhost:8889/apps"
        }
    else
        print_error "Server is not running. Start it first with: $0 start"
    fi
}

# Function to test apps
test_apps() {
    if ! is_running; then
        print_error "Server is not running. Start it first with: $0 start"
        return 1
    fi
    
    print_status "Testing application pages..."
    
    # Test main endpoints
    local base_url="http://localhost:8889"
    
    print_status "Testing endpoints:"
    echo "  Main page: $base_url/"
    echo "  Apps list: $base_url/apps"
    echo "  Sample app: $base_url/apps/sample_app"
    echo "  Sample console: $base_url/console/sample_app"
    echo "  API docs: $base_url/docs"
    
    # Open key pages in browser
    print_status "Opening key pages in browser..."
    open "$base_url/apps" 2>/dev/null || true
    sleep 1
    open "$base_url/apps/sample_app" 2>/dev/null || true
    sleep 1
    open "$base_url/console/sample_app" 2>/dev/null || true
}

# Main script logic
case "${1:-}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    apps)
        open_apps
        ;;
    test)
        test_apps
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|apps|test}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the workflow engine server"
        echo "  stop    - Stop the workflow engine server"
        echo "  restart - Restart the workflow engine server"
        echo "  status  - Show server status"
        echo "  logs    - Show server logs (real-time)"
        echo "  apps    - Open apps page in browser"
        echo "  test    - Test and open all app pages"
        echo ""
        echo "Server will run on: http://0.0.0.0:8889"
        echo "Apps page: http://localhost:8889/apps"
        exit 1
        ;;
esac