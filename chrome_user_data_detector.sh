#!/bin/bash

# Chrome User Data Directory Detector
# Cross-platform script to detect Chrome processes and their user data directories

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Chrome User Data Directory Detector${NC}"
echo "=================================="

# Detect OS
OS="$(uname -s)"
echo "Detected OS: $OS"

# Function to detect Chrome processes on macOS
detect_macos() {
    echo -e "\n${GREEN}Searching for Chrome processes on macOS...${NC}"
    
    # Find main Chrome processes (without --type parameter)
    echo -e "\n${YELLOW}Main Chrome Processes:${NC}"
    ps -ax -o pid,ppid,comm,args | grep -E "Google Chrome" | grep -v "(Renderer)" | grep -v Helper | grep -v crashpad | grep -v grep || echo "No main Chrome processes found"
    
    # Find child processes
    echo -e "\n${YELLOW}Child Chrome Processes:${NC}"
    ps -ax -o pid,ppid,comm,args | grep -E "Google Chrome.*--type=" | grep -v grep || echo "No child Chrome processes found"
    
    # Extract user data directories
    echo -e "\n${YELLOW}User Data Directories:${NC}"
    USER_DATA_DIRS=$(ps -ax -o args | grep "Google Chrome" | grep -v grep | grep -oE '--user-data-dir[= ][^ ]+' | sed 's/--user-data-dir[= ]//g' | sort | uniq)
    
    if [ -n "$USER_DATA_DIRS" ]; then
        echo "$USER_DATA_DIRS"
    else
        # Default directory
        DEFAULT_DIR="$HOME/Library/Application Support/Google/Chrome"
        echo "Using default directory: $DEFAULT_DIR"
        if [ -d "$DEFAULT_DIR" ]; then
            echo -e "${GREEN}Directory exists and is accessible${NC}"
        else
            echo -e "${RED}Directory does not exist${NC}"
        fi
    fi
    
    # Show profile structure
    echo -e "\n${YELLOW}Profile Structure:${NC}"
    if [ -n "$USER_DATA_DIRS" ]; then
        for dir in $USER_DATA_DIRS; do
            echo "Profiles in $dir:"
            if [ -d "$dir" ]; then
                ls -la "$dir" | grep -E "^(Profile [0-9]+|Default|Guest)" || echo "No profile directories found"
            else
                echo "Directory does not exist"
            fi
        done
    else
        DEFAULT_DIR="$HOME/Library/Application Support/Google/Chrome"
        if [ -d "$DEFAULT_DIR" ]; then
            echo "Profiles in $DEFAULT_DIR:"
            ls -la "$DEFAULT_DIR" | grep -E "^(Profile [0-9]+|Default|Guest)" || echo "No profile directories found"
        fi
    fi
}

# Function to detect Chrome processes on Linux
detect_linux() {
    echo -e "\n${GREEN}Searching for Chrome processes on Linux...${NC}"
    
    # Find main Chrome processes (without --type parameter)
    echo -e "\n${YELLOW}Main Chrome Processes:${NC}"
    ps -eo pid,ppid,comm,args | grep -E "(chrome|chromium)" | grep -v "\-\-type=" | grep -v grep || echo "No main Chrome processes found"
    
    # Find child processes
    echo -e "\n${YELLOW}Child Chrome Processes:${NC}"
    ps -eo pid,ppid,comm,args | grep -E "(chrome|chromium).*\-\-type=" | grep -v grep || echo "No child Chrome processes found"
    
    # Extract user data directories
    echo -e "\n${YELLOW}User Data Directories:${NC}"
    USER_DATA_DIRS=$(ps -eo args | grep -E "(chrome|chromium)" | grep -v grep | grep -oE '\-\-user\-data\-dir[= ][^ ]+' | sed 's/\-\-user\-data\-dir[= ]//g' | sort | uniq)
    
    if [ -n "$USER_DATA_DIRS" ]; then
        echo "$USER_DATA_DIRS"
    else
        # Default directory
        DEFAULT_DIR="$HOME/.config/google-chrome"
        echo "Using default directory: $DEFAULT_DIR"
        if [ -d "$DEFAULT_DIR" ]; then
            echo -e "${GREEN}Directory exists and is accessible${NC}"
        else
            echo -e "${RED}Directory does not exist${NC}"
        fi
    fi
    
    # Show profile structure
    echo -e "\n${YELLOW}Profile Structure:${NC}"
    if [ -n "$USER_DATA_DIRS" ]; then
        for dir in $USER_DATA_DIRS; do
            echo "Profiles in $dir:"
            if [ -d "$dir" ]; then
                ls -la "$dir" | grep -E "^(Profile [0-9]+|Default|Guest)" || echo "No profile directories found"
            else
                echo "Directory does not exist"
            fi
        done
    else
        DEFAULT_DIR="$HOME/.config/google-chrome"
        if [ -d "$DEFAULT_DIR" ]; then
            echo "Profiles in $DEFAULT_DIR:"
            ls -la "$DEFAULT_DIR" | grep -E "^(Profile [0-9]+|Default|Guest)" || echo "No profile directories found"
        fi
    fi
}

# Function to detect Chrome processes on Windows (using PowerShell)
detect_windows() {
    echo -e "\n${GREEN}Searching for Chrome processes on Windows...${NC}"
    
    # Use PowerShell to get Chrome processes
    powershell.exe -Command "Get-Process chrome -ErrorAction SilentlyContinue | Select-Object Id, Name, Path | Format-Table -AutoSize"
    
    # Get command line arguments for Chrome processes
    echo -e "\n${YELLOW}Chrome Process Details:${NC}"
    powershell.exe -Command "Get-WmiObject Win32_Process -Filter \"Name='chrome.exe'\" | Select-Object ProcessId, CommandLine | Format-Table -AutoSize"
    
    # Extract user data directories
    echo -e "\n${YELLOW}User Data Directories:${NC}"
    USER_DATA_DIRS=$(powershell.exe -Command "Get-WmiObject Win32_Process -Filter \"Name='chrome.exe'\" | ForEach-Object { if (\$_.CommandLine -match '--user-data-dir=([^ ]+)') { \$matches[1] } }" 2>/dev/null)
    
    if [ -n "$USER_DATA_DIRS" ]; then
        echo "$USER_DATA_DIRS"
    else
        # Default directory
        DEFAULT_DIR="$LOCALAPPDATA\\Google\\Chrome\\User Data"
        echo "Using default directory: $DEFAULT_DIR"
        # Note: We can't easily check directory existence from WSL
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
        exit 1
        ;;
esac

echo -e "\n${GREEN}Detection complete.${NC}"
