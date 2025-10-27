#!/bin/bash

# Enhanced Workflow Engine Server Control Script for macOS/Linux
# Usage: ./workflow_server.sh [start|stop|restart|status|install|logs|apps|test]

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment variables from .env file if it exists
load_environment_variables() {
    local env_file="$SCRIPT_DIR/.env"
    if [ -f "$env_file" ]; then
        echo "✓ Loading environment variables from $env_file"
        # Source the .env file, but only set variables that aren't already set
        while IFS='=' read -r key value; do
            # Skip empty lines and comments
            if [[ -n "$key" && ! "$key" =~ ^[[:space:]]*# ]]; then
                # Remove quotes from value
                value=$(echo "$value" | sed 's/^["'\'']\|["'\'']$//g')
                # Only set if not already set
                if [ -z "${!key}" ]; then
                    export "$key"="$value"
                fi
            fi
        done < "$env_file"

        # Expand variables that reference other variables
        expand_environment_variables
    else
        echo "ℹ No .env file found at $env_file"
    fi
}

# Expand environment variables that reference other variables
expand_environment_variables() {
    # Expand WORKFLOW_DATA_DIR first (handle ~ expansion)
    if [[ "$WORKFLOW_DATA_DIR" =~ ^~ ]]; then
        WORKFLOW_DATA_DIR="${WORKFLOW_DATA_DIR/#\~/$HOME}"
        export WORKFLOW_DATA_DIR
    fi

    # Then expand variables that depend on WORKFLOW_DATA_DIR
    if [[ "$WORKFLOW_CACHE_DIR" == *'${WORKFLOW_DATA_DIR}'* ]]; then
        WORKFLOW_CACHE_DIR=$(eval echo "$WORKFLOW_CACHE_DIR")
        export WORKFLOW_CACHE_DIR
    fi

    if [[ "$WORKFLOW_UPLOAD_DIR" == *'${WORKFLOW_DATA_DIR}'* ]]; then
        WORKFLOW_UPLOAD_DIR=$(eval echo "$WORKFLOW_UPLOAD_DIR")
        export WORKFLOW_UPLOAD_DIR
    fi

    if [[ "$WORKFLOW_TEMP_DIR" == *'${WORKFLOW_DATA_DIR}'* ]]; then
        WORKFLOW_TEMP_DIR=$(eval echo "$WORKFLOW_TEMP_DIR")
        export WORKFLOW_TEMP_DIR
    fi

    if [[ "$WORKFLOW_LOG_DIR" == *'${WORKFLOW_DATA_DIR}'* ]]; then
        WORKFLOW_LOG_DIR=$(eval echo "$WORKFLOW_LOG_DIR")
        export WORKFLOW_LOG_DIR
    fi
}

# Load environment variables
load_environment_variables

SERVER_MODULE="src_new.workflow_engine.api.server"
PID_FILE="$PROJECT_DIR/.workflow_server.pid"
LOG_FILE="${WORKFLOW_LOG_DIR:-$PROJECT_DIR}/workflow_server.log"
SRC_DIR="$PROJECT_DIR/${WORKFLOW_SOURCE_DIR:-src_new}"
REQUIREMENTS_FILE="$SRC_DIR/requirements.txt"
SERVER_PORT="${WORKFLOW_PORT:-8889}"

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

# Function to install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."

    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        print_error "Please install Python 3.8+ from https://python.org or your package manager"
        return 1
    fi

    # Check Python version
    local python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    local major=$(echo "$python_version" | cut -d. -f1)
    local minor=$(echo "$python_version" | cut -d. -f2)

    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 8 ]); then
        print_error "Python 3.8+ is required (found $python_version)"
        return 1
    fi

    # Check if pip is available
    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip is not available"
        return 1
    fi

    # Check if requirements file exists
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_error "Requirements file not found: $REQUIREMENTS_FILE"
        return 1
    fi

    # Install requirements
    print_status "Installing from requirements.txt..."
    if ! python3 -m pip install -r "$REQUIREMENTS_FILE"; then
        print_error "Failed to install dependencies"
        return 1
    fi

    # Install Playwright browsers
    print_status "Installing Playwright browsers..."
    if ! python3 -m playwright install; then
        print_warning "Failed to install Playwright browsers automatically"
        print_status "You may need to run 'python3 -m playwright install' manually"
    fi

    print_status "Dependencies installed successfully"
    return 0
}

# Function to kill processes on specific ports
kill_port_processes() {
    local ports=(8000 8888 8001 8889)
    print_status "Cleaning up ports ${ports[*]}..."

    for port in "${ports[@]}"; do
        # Use lsof to find processes using the port
        local pids=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
    done
}

# Function to start the server
start_server() {
    if is_running; then
        print_warning "Server is already running (PID: $(cat $PID_FILE))"
        return 1
    fi

    print_status "Starting Workflow Engine Server..."

    # Create log directory if it doesn't exist
    local log_dir=$(dirname "$LOG_FILE")
    if [ ! -d "$log_dir" ]; then
        mkdir -p "$log_dir"
        print_status "Created log directory: $log_dir"
    fi

    # Kill any processes using our ports
    kill_port_processes

    # Check if source directory exists
    if [ ! -d "$SRC_DIR" ]; then
        print_error "Source directory not found: $SRC_DIR"
        return 1
    fi

    # Change to project directory (not src_new) and start server
    cd "$PROJECT_DIR"

    # Determine Python command
    local python_cmd="python3"
    if ! command -v python3 &> /dev/null; then
        if command -v python &> /dev/null; then
            python_cmd="python"
        else
            print_error "Python not found"
            return 1
        fi
    fi

    # Start server in background
    nohup $python_cmd -m "$SERVER_MODULE" > "$LOG_FILE" 2>&1 &
    local server_pid=$!

    # Save PID
    echo "$server_pid" > "$PID_FILE"

    # Wait a moment and check if server started successfully
    sleep 3

    if is_running; then
        print_status "Server started successfully (PID: $server_pid)"
        print_status "Server running on: http://0.0.0.0:$SERVER_PORT"
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
    kill_port_processes

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
        print_status "Server URL: http://0.0.0.0:$SERVER_PORT"
        print_status "Apps page: http://localhost:$SERVER_PORT/apps"

        # Show port usage
        echo ""
        echo "Port usage:"
        lsof -i:$SERVER_PORT 2>/dev/null || echo "Port $SERVER_PORT: Not in use"

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

        # Try different commands to open browser
        if command -v open &> /dev/null; then
            # macOS
            open "http://localhost:$SERVER_PORT/apps" 2>/dev/null
        elif command -v xdg-open &> /dev/null; then
            # Linux
            xdg-open "http://localhost:$SERVER_PORT/apps" 2>/dev/null
        else
            print_status "Please open: http://localhost:$SERVER_PORT/apps"
        fi
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
    local base_url="http://localhost:$SERVER_PORT"

    print_status "Testing endpoints:"
    echo "  Main page: $base_url/"
    echo "  Apps list: $base_url/apps"
    echo "  Sample app: $base_url/apps/sample_app"
    echo "  Sample console: $base_url/console/sample_app"
    echo "  API docs: $base_url/docs"

    # Open key pages in browser
    print_status "Opening key pages in browser..."

    local urls=(
        "$base_url/apps"
        "$base_url/apps/sample_app"
        "$base_url/console/sample_app"
    )

    for url in "${urls[@]}"; do
        if command -v open &> /dev/null; then
            # macOS
            open "$url" 2>/dev/null
        elif command -v xdg-open &> /dev/null; then
            # Linux
            xdg-open "$url" 2>/dev/null
        fi
        sleep 1
    done
}

# Function to use Python script as fallback
use_python_script() {
    local python_script="$SCRIPT_DIR/workflow_server.py"

    if [ -f "$python_script" ]; then
        print_status "Using Python script for enhanced functionality..."

        # Determine Python command
        local python_cmd="python3"
        if ! command -v python3 &> /dev/null; then
            if command -v python &> /dev/null; then
                python_cmd="python"
            else
                print_error "Python not found"
                return 1
            fi
        fi
        
        # Execute Python script with same arguments
        exec "$python_cmd" "$python_script" "$@"
    else
        print_error "Python script not found: $python_script"
        return 1
    fi
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
    install)
        install_dependencies
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
    python)
        # Use Python script for enhanced functionality
        shift
        use_python_script "$@"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|install|logs|apps|test|python}"
        echo ""
        echo "Commands:"
        echo "  install - Install Python dependencies and Playwright browsers"
        echo "  start   - Start the workflow engine server"
        echo "  stop    - Stop the workflow engine server"
        echo "  restart - Restart the workflow engine server"
        echo "  status  - Show server status"
        echo "  logs    - Show server logs (real-time)"
        echo "  apps    - Open apps page in browser"
        echo "  test    - Test and open all app pages"
        echo "  python  - Use Python script for enhanced functionality"
        echo ""
        echo "Server will run on: http://0.0.0.0:$SERVER_PORT"
        echo "Apps page: http://localhost:$SERVER_PORT/apps"
        echo ""
        echo "First time setup: $0 install"
        echo "Enhanced mode: $0 python [command]"
        exit 1
        ;;
esac