#!/bin/bash

# Improved Chrome User Data Directory Detector
# Cross-platform script to detect Chrome processes and their user data directories

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Improved Chrome User Data Directory Detector${NC}"
echo "=========================================="

# Detect OS
OS="$(uname -s)"
echo "Detected OS: $OS"

# Function to safely extract user data directory from process args
extract_user_data_dir() {
    local args="$1"
    # Handle quoted paths and unquoted paths
    if echo "$args" | grep -q '\--user-data-dir='; then
        # Extract path after --user-data-dir=
        echo "$args" | sed -E 's/.*\--user-data-dir=("[^"]*"|[^ ]*).*/\1/' | sed 's/"//g'
        return 0
    elif echo "$args" | grep -q '\--user-data-dir '; then
        # Extract path after --user-data-dir (space separated)
        echo "$args" | sed -E 's/.*\--user-data-dir (("[^"]*")|([^ ]*)).*/\1/' | sed 's/"//g'
        return 0
    fi
    return 1
}

# Function to detect Chrome processes on macOS
detect_macos() {
    echo -e "\n${GREEN}Searching for Chrome processes on macOS...${NC}"
    
    # Find all Chrome processes
    CHROME_PROCESSES=$(ps -ax -o pid,ppid,comm,args | grep "Google Chrome" | grep -v grep || true)
    
    if [ -z "$CHROME_PROCESSES" ]; then
        echo "No Chrome processes found."
        return
    fi
    
    # Separate main and child processes
    MAIN_PROCESSES=$(echo "$CHROME_PROCESSES" | grep -v "(Renderer)" | grep -v Helper | grep -v crashpad || true)
    CHILD_PROCESSES=$(echo "$CHROME_PROCESSES" | grep -E "(Renderer|Helper)" | grep -v crashpad || true)
    
    # Display main processes
    echo -e "\n${YELLOW}Main Chrome Processes:${NC}"
    if [ -n "$MAIN_PROCESSES" ]; then
        echo "$MAIN_PROCESSES" | while read -r line; do
            echo "  $line"
        done
    else
        echo "  No main Chrome processes found"
    fi
    
    # Display child processes
    echo -e "\n${YELLOW}Child Chrome Processes:${NC}"
    if [ -n "$CHILD_PROCESSES" ]; then
        # Count by type
        RENDERER_COUNT=$(echo "$CHILD_PROCESSES" | grep -c "(Renderer)" || true)
        HELPER_COUNT=$(echo "$CHILD_PROCESSES" | grep -c "Helper" || true)
        echo "  Renderer processes: $RENDERER_COUNT"
        echo "  Helper processes: $HELPER_COUNT"
    else
        echo "  No child Chrome processes found"
    fi
    
    # Extract user data directories
    echo -e "\n${YELLOW}User Data Directories:${NC}"
    USER_DATA_DIRS=""
    
    # Check all processes for --user-data-dir parameter
    echo "$CHROME_PROCESSES" | while read -r line; do
        DIR=$(extract_user_data_dir "$line" 2>/dev/null || true)
        if [ -n "$DIR" ] && [ "$DIR" != "$line" ]; then
            echo "  $DIR"
            USER_DATA_DIRS="$USER_DATA_DIRS $DIR"
        fi
    done
    
    # If no custom directories found, use default
    if [ -z "$USER_DATA_DIRS" ]; then
        DEFAULT_DIR="$HOME/Library/Application Support/Google/Chrome"
        echo "  Using default directory: $DEFAULT_DIR"
        USER_DATA_DIRS="$DEFAULT_DIR"
    fi
    
    # Show profile structure for each directory
    echo -e "\n${YELLOW}Profile Structure:${NC}"
    for dir in $USER_DATA_DIRS; do
        echo "  Profiles in $dir:"
        if [ -d "$dir" ]; then
            # List profile directories only
            (cd "$dir" && ls -la | grep "^d" | awk '{print $9}' | grep -E "^(Profile [0-9]+|Default|Guest)" || echo "    No profile directories found")
        else
            echo "    Directory does not exist"
        fi
    done
}

# Function to detect Chrome processes on Linux
detect_linux() {
    echo -e "\n${GREEN}Searching for Chrome processes on Linux...${NC}"
    
    # Find all Chrome processes
    CHROME_PROCESSES=$(ps -eo pid,ppid,comm,args | grep -E "(chrome|chromium)" | grep -v grep || true)
    
    if [ -z "$CHROME_PROCESSES" ]; then
        echo "No Chrome processes found."
        return
    fi
    
    # Separate main and child processes
    MAIN_PROCESSES=$(echo "$CHROME_PROCESSES" | grep -v "\-\-type=" || true)
    CHILD_PROCESSES=$(echo "$CHROME_PROCESSES" | grep "\-\-type=" || true)
    
    # Display main processes
    echo -e "\n${YELLOW}Main Chrome Processes:${NC}"
    if [ -n "$MAIN_PROCESSES" ]; then
        echo "$MAIN_PROCESSES" | while read -r line; do
            echo "  $line"
        done
    else
        echo "  No main Chrome processes found"
    fi
    
    # Display child processes
    echo -e "\n${YELLOW}Child Chrome Processes:${NC}"
    if [ -n "$CHILD_PROCESSES" ]; then
        # Count by type
        TYPE_COUNTS=$(echo "$CHILD_PROCESSES" | grep -oE "\-\-type=[^ ]*" | sort | uniq -c)
        echo "$TYPE_COUNTS" | while read -r count type; do
            echo "  ${type#--type=}: $count"
        done
    else
        echo "  No child Chrome processes found"
    fi
    
    # Extract user data directories
    echo -e "\n${YELLOW}User Data Directories:${NC}"
    USER_DATA_DIRS=""
    
    # Check all processes for --user-data-dir parameter
    echo "$CHROME_PROCESSES" | while read -r line; do
        DIR=$(extract_user_data_dir "$line" 2>/dev/null || true)
        if [ -n "$DIR" ] && [ "$DIR" != "$line" ]; then
            echo "  $DIR"
            USER_DATA_DIRS="$USER_DATA_DIRS $DIR"
        fi
    done
    
    # If no custom directories found, use default
    if [ -z "$USER_DATA_DIRS" ]; then
        DEFAULT_DIR="$HOME/.config/google-chrome"
        echo "  Using default directory: $DEFAULT_DIR"
        USER_DATA_DIRS="$DEFAULT_DIR"
    fi
    
    # Show profile structure for each directory
    echo -e "\n${YELLOW}Profile Structure:${NC}"
    for dir in $USER_DATA_DIRS; do
        echo "  Profiles in $dir:"
        if [ -d "$dir" ]; then
            # List profile directories only
            (cd "$dir" && ls -la | grep "^d" | awk '{print $9}' | grep -E "^(Profile [0-9]+|Default|Guest)" || echo "    No profile directories found")
        else
            echo "    Directory does not exist"
        fi
    done
}

# Function to detect Chrome processes on Windows (using PowerShell)
detect_windows() {
    echo -e "\n${GREEN}Searching for Chrome processes on Windows...${NC}"
    
    # Check if we're in WSL or actual Windows
    if command -v powershell.exe >/dev/null 2>&1; then
        # We're likely in WSL
        echo "Running in WSL environment"
        
        # Use PowerShell to get Chrome processes
        echo -e "\n${YELLOW}Chrome Processes:${NC}"
        powershell.exe -Command "Get-Process chrome -ErrorAction SilentlyContinue | Select-Object Id, Name, Path | Format-Table -AutoSize" 2>/dev/null || echo "Failed to get process info"
        
        # Get command line arguments for Chrome processes
        echo -e "\n${YELLOW}Chrome Process Details:${NC}"
        powershell.exe -Command "Get-WmiObject Win32_Process -Filter \"Name='chrome.exe'\" | Select-Object ProcessId, CommandLine | Format-Table -AutoSize" 2>/dev/null || echo "Failed to get command line info"
        
        # Extract user data directories
        echo -e "\n${YELLOW}User Data Directories:${NC}"
        USER_DATA_DIRS=$(powershell.exe -Command "Get-WmiObject Win32_Process -Filter \"Name='chrome.exe'\" | ForEach-Object { if (\$_.CommandLine -match '--user-data-dir=([^ ]+)') { \$matches[1] } }" 2>/dev/null | tr -d '\r')
        
        if [ -n "$USER_DATA_DIRS" ]; then
            echo "$USER_DATA_DIRS" | while read -r dir; do
                echo "  $dir"
            done
        else
            # Default directory
            echo "  Using default directory: %LOCALAPPDATA%\\Google\\Chrome\\User Data"
        fi
    else
        # Pure Windows environment (if this script could run there)
        echo "Note: This script is designed for Unix-like environments"
        echo "For Windows, use PowerShell directly:"
        echo "  Get-Process chrome"
        echo "  Get-WmiObject Win32_Process -Filter \"Name='chrome.exe'\""
    fi
}

# Main detection logic
case "$OS" in
    Darwin*)
        detect_macos
        ;;
    Linux*)
        detect_linux
        ;;
    MINGW*|MSYS*|CYGWIN*)
        detect_windows
        ;;
    *)
        echo -e "${RED}Unsupported operating system: $OS${NC}"
        echo "This script supports macOS (Darwin), Linux, and Windows Subsystem for Linux (WSL)"
        exit 1
        ;;
esac

echo -e "\n${GREEN}Detection complete.${NC}"
