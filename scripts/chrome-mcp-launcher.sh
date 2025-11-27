#!/bin/bash
# Chrome MCP Launcher Script for macOS/Linux
# 启动Chrome浏览器，配置用户目录和调试端口，供Chrome DevTools MCP连接
# 
# 使用方法:
# ./chrome-mcp-launcher.sh [options]
#
# 选项:
#   --port PORT          设置调试端口 (默认: 9222)
#   --profile PATH       设置用户目录路径 (默认: 自动检测)
#   --headless          无头模式启动
#   --help              显示帮助信息

set -e

# 默认配置
DEBUG_PORT=9222
HEADLESS_MODE=false
CUSTOM_PROFILE=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/chrome-mcp.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# 帮助信息
show_help() {
    cat << EOF
Chrome MCP Launcher - 为Chrome DevTools MCP启动Chrome浏览器

用法: $0 [选项]

选项:
    --port PORT          设置调试端口 (默认: 9222)
    --profile PATH       设置用户目录路径 (默认: 自动检测)
    --headless          启用无头模式
    --help              显示此帮助信息

示例:
    $0                                    # 使用默认配置启动
    $0 --port 9223 --headless            # 无头模式，自定义端口
    $0 --profile ~/my-chrome-profile      # 指定用户目录

连接方法:
    npx chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:9222

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --port)
                if [[ -n $2 && $2 =~ ^[0-9]+$ ]]; then
                    DEBUG_PORT="$2"
                    shift 2
                else
                    log_error "端口号必须是数字"
                    exit 1
                fi
                ;;
            --profile)
                if [[ -n $2 ]]; then
                    CUSTOM_PROFILE="$2"
                    shift 2
                else
                    log_error "请提供用户目录路径"
                    exit 1
                fi
                ;;
            --headless)
                HEADLESS_MODE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# 查找Chrome可执行文件
find_chrome_executable() {
    local os=$(detect_os)
    local chrome_paths=()
    
    case $os in
        "macos")
            chrome_paths=(
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                "/Applications/Chromium.app/Contents/MacOS/Chromium"
                "/opt/homebrew/bin/google-chrome"
                "/usr/local/bin/google-chrome"
            )
            ;;
        "linux")
            chrome_paths=(
                "/usr/bin/google-chrome"
                "/usr/bin/google-chrome-stable"
                "/usr/bin/chromium-browser"
                "/usr/bin/chromium"
                "/snap/bin/chromium"
                "/opt/google/chrome/chrome"
            )
            ;;
        *)
            log_error "不支持的操作系统: $OSTYPE"
            exit 1
            ;;
    esac
    
    for chrome_path in "${chrome_paths[@]}"; do
        if [[ -x "$chrome_path" ]]; then
            echo "$chrome_path"
            return 0
        fi
    done
    
    log_error "未找到Chrome可执行文件"
    exit 1
}

# 获取默认用户目录
get_default_profile() {
    local os=$(detect_os)
    local profile_dir=""
    
    case $os in
        "macos")
            profile_dir="$HOME/Library/Application Support/Google/Chrome/Default"
            ;;
        "linux")
            profile_dir="$HOME/.config/google-chrome/Default"
            ;;
    esac
    
    # 如果默认目录不存在，创建一个MCP专用目录
    if [[ ! -d "$profile_dir" ]]; then
        profile_dir="$HOME/.chrome-mcp-profile"
        log_warn "默认Chrome目录不存在，将使用: $profile_dir"
    fi
    
    echo "$profile_dir"
}

# 检查端口是否被占用
check_port() {
    if command -v lsof >/dev/null 2>&1; then
        if lsof -Pi :$DEBUG_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warn "端口 $DEBUG_PORT 已被占用"
            return 1
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -an | grep -q ":$DEBUG_PORT.*LISTEN"; then
            log_warn "端口 $DEBUG_PORT 已被占用"
            return 1
        fi
    fi
    return 0
}

# 构建Chrome启动参数
build_chrome_args() {
    local profile_dir="$1"
    local args=(
        "--remote-debugging-port=$DEBUG_PORT"
        "--user-data-dir=$profile_dir"
        "--no-first-run"
        "--no-default-browser-check"
        "--disable-extensions-file-access-check"
        "--disable-extensions-except"
        "--disable-sync"
        "--disable-translate"
        "--disable-background-timer-throttling"
        "--disable-backgrounding-occluded-windows"
        "--disable-renderer-backgrounding"
        "--disable-field-trial-config"
        "--disable-ipc-flooding-protection"
        "--disable-hang-monitor"
        "--disable-prompt-on-repost"
        "--disable-client-side-phishing-detection"
        "--disable-component-extensions-with-background-pages"
        "--disable-default-apps"
        "--disable-dev-shm-usage"
        "--disable-features=TranslateUI"
        "--disable-blink-features=AutomationControlled"
        "--exclude-switches=enable-automation"
        "--no-sandbox"
    )
    
    if [[ "$HEADLESS_MODE" == "true" ]]; then
        args+=("--headless" "--disable-gpu" "--virtual-time-budget=5000")
        log_info "启用无头模式"
    fi
    
    printf '%s\n' "${args[@]}"
}

# 启动Chrome
launch_chrome() {
    local chrome_executable="$1"
    local profile_dir="$2"
    
    log_info "Chrome可执行文件: $chrome_executable"
    log_info "用户数据目录: $profile_dir"
    log_info "调试端口: $DEBUG_PORT"
    
    # 确保用户目录存在
    mkdir -p "$profile_dir"
    
    # 构建启动参数
    local chrome_args
    readarray -t chrome_args < <(build_chrome_args "$profile_dir")
    
    log_info "正在启动Chrome浏览器..."
    log_info "日志文件: $LOG_FILE"
    
    # 启动Chrome（后台运行）
    nohup "$chrome_executable" "${chrome_args[@]}" >> "$LOG_FILE" 2>&1 &
    local chrome_pid=$!
    
    # 等待Chrome启动
    sleep 3
    
    # 验证Chrome是否成功启动
    if kill -0 $chrome_pid 2>/dev/null; then
        log_info "Chrome已成功启动 (PID: $chrome_pid)"
        
        # 测试调试端口连接
        if command -v curl >/dev/null 2>&1; then
            if curl -s "http://127.0.0.1:$DEBUG_PORT/json/version" >/dev/null; then
                log_info "调试端口连接测试成功"
                echo
                log_info "${GREEN}🎉 Chrome MCP连接就绪！${NC}"
                echo
                log_info "连接命令:"
                echo -e "${BLUE}npx chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:$DEBUG_PORT${NC}"
                echo
                log_info "或者在IDE中配置MCP连接到: http://127.0.0.1:$DEBUG_PORT"
                echo
            else
                log_warn "调试端口连接测试失败，请稍后重试"
            fi
        fi
        
        # 保存PID用于后续管理
        echo $chrome_pid > "$SCRIPT_DIR/chrome-mcp.pid"
        log_info "进程ID已保存到: $SCRIPT_DIR/chrome-mcp.pid"
        
    else
        log_error "Chrome启动失败，请检查日志: $LOG_FILE"
        exit 1
    fi
}

# 主函数
main() {
    log_info "Chrome MCP Launcher 启动中..."
    echo "日志时间: $(date)" >> "$LOG_FILE"
    
    # 解析命令行参数
    parse_args "$@"
    
    # 检查端口
    if ! check_port; then
        log_error "端口 $DEBUG_PORT 已被占用，请使用 --port 指定其他端口"
        exit 1
    fi
    
    # 查找Chrome可执行文件
    local chrome_executable
    chrome_executable=$(find_chrome_executable)
    
    # 确定用户目录
    local profile_dir
    if [[ -n "$CUSTOM_PROFILE" ]]; then
        profile_dir="$CUSTOM_PROFILE"
    else
        profile_dir=$(get_default_profile)
    fi
    
    # 启动Chrome
    launch_chrome "$chrome_executable" "$profile_dir"
}

# 脚本入口
main "$@"
