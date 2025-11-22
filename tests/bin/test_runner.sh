#!/bin/bash

# ================================================================
# AI产品选择器测试运行脚本
# 
# 功能：运行 ./xp start 命令指定时间，然后杀掉进程并分析输出
# 使用：./test_runner.sh [分钟数] [可选：日志文件路径]
# 
# 示例：
#   ./test_runner.sh 5                    # 运行5分钟
#   ./test_runner.sh 10 /tmp/test.log     # 运行10分钟，输出到指定日志
# ================================================================

set -euo pipefail

# 默认配置
DEFAULT_MINUTES=5
DEFAULT_LOG_DIR="$(dirname "$0")/logs"
TEST_DATA_PATH="/Users/haowu/IdeaProjects/ai-product-selector3/tests/test_data/test_user_data.json"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

# 显示使用说明
usage() {
    cat << EOF
使用方法: $0 [分钟数] [日志文件路径]

参数:
  分钟数          运行时长（分钟），默认: $DEFAULT_MINUTES
  日志文件路径    输出日志文件路径，默认: $DEFAULT_LOG_DIR/test_run_YYYYMMDD_HHMMSS.log

示例:
  $0 5                          # 运行5分钟
  $0 10 /tmp/test.log          # 运行10分钟，输出到指定文件
  $0 --help                    # 显示此帮助信息

功能:
  1. 运行命令: ./xp start --dryrun --select-shops --data $TEST_DATA_PATH
  2. 监控指定时间后自动杀掉进程
  3. 分析输出日志，诊断错误和告警
  4. 生成问题诊断报告

EOF
}

# 检查参数
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

# 解析参数
MINUTES=${1:-$DEFAULT_MINUTES}
if ! [[ "$MINUTES" =~ ^[0-9]+$ ]] || [ "$MINUTES" -lt 1 ]; then
    log_error "无效的分钟数: $MINUTES。必须是正整数。"
    usage
    exit 1
fi

# 创建日志目录
mkdir -p "$DEFAULT_LOG_DIR"

# 生成日志文件名
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
DEFAULT_LOG_FILE="$DEFAULT_LOG_DIR/test_run_$TIMESTAMP.log"
LOG_FILE=${2:-$DEFAULT_LOG_FILE}

# 验证项目环境
log_info "验证项目环境..."
if [ ! -f "$PROJECT_ROOT/xp" ]; then
    log_error "找不到 xp 执行文件: $PROJECT_ROOT/xp"
    exit 1
fi

if [ ! -f "$TEST_DATA_PATH" ]; then
    log_error "找不到测试数据文件: $TEST_DATA_PATH"
    exit 1
fi

# 确保 xp 可执行
chmod +x "$PROJECT_ROOT/xp"

log_success "环境验证通过"

# 浏览器进程冲突检测和清理
log_info "检测浏览器进程冲突..."
cleanup_browser_processes() {
    local killed_any=false
    local browser_detected=false

    # 检测并杀掉Microsoft Edge进程
    local edge_pids=$(pgrep -f "Microsoft Edge" 2>/dev/null || true)
    if [ -n "$edge_pids" ]; then
        browser_detected=true
        log_warn "检测到Microsoft Edge进程 ($(echo "$edge_pids" | wc -w | tr -d ' ')个): $(echo "$edge_pids" | tr '\n' ' ')"
        for pid in $edge_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                log_info "  └─ 终止Microsoft Edge进程: $pid"
                kill -TERM "$pid" 2>/dev/null || true
                killed_any=true
            fi
        done
    fi

    # 检测并杀掉Chrome进程
    local chrome_pids=$(pgrep -f "Google Chrome" 2>/dev/null || true)
    if [ -n "$chrome_pids" ]; then
        browser_detected=true
        log_warn "检测到Google Chrome进程 ($(echo "$chrome_pids" | wc -w | tr -d ' ')个): $(echo "$chrome_pids" | tr '\n' ' ')"
        for pid in $chrome_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                log_info "  └─ 终止Google Chrome进程: $pid"
                kill -TERM "$pid" 2>/dev/null || true
                killed_any=true
            fi
        done
    fi

    # 检测并杀掉Safari进程（可能影响自动化）
    local safari_pids=$(pgrep -f "Safari" 2>/dev/null || true)
    if [ -n "$safari_pids" ]; then
        browser_detected=true
        log_warn "检测到Safari进程 ($(echo "$safari_pids" | wc -w | tr -d ' ')个): $(echo "$safari_pids" | tr '\n' ' ')"
        for pid in $safari_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                log_info "  └─ 终止Safari进程: $pid"
                kill -TERM "$pid" 2>/dev/null || true
                killed_any=true
            fi
        done
    fi

    # 检测并杀掉Playwright相关进程
    local playwright_pids=$(pgrep -f "playwright" 2>/dev/null || true)
    if [ -n "$playwright_pids" ]; then
        browser_detected=true
        log_warn "检测到Playwright相关进程 ($(echo "$playwright_pids" | wc -w | tr -d ' ')个): $(echo "$playwright_pids" | tr '\n' ' ')"
        for pid in $playwright_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                log_info "  └─ 终止Playwright进程: $pid"
                kill -TERM "$pid" 2>/dev/null || true
                killed_any=true
            fi
        done
    fi

    # 检测并杀掉其他可能的自动化相关进程
    local selenium_pids=$(pgrep -f "selenium\|webdriver\|chromedriver\|geckodriver" 2>/dev/null || true)
    if [ -n "$selenium_pids" ]; then
        browser_detected=true
        log_warn "检测到自动化驱动进程 ($(echo "$selenium_pids" | wc -w | tr -d ' ')个): $(echo "$selenium_pids" | tr '\n' ' ')"
        for pid in $selenium_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                log_info "  └─ 终止自动化驱动进程: $pid"
                kill -TERM "$pid" 2>/dev/null || true
                killed_any=true
            fi
        done
    fi

    # 等待进程完全退出
    if [ "$killed_any" = true ]; then
        log_info "等待浏览器进程完全退出..."
        sleep 3

        # 验证进程是否已退出，强制杀死仍在运行的进程
        local remaining_pids=""
        remaining_pids+="$(pgrep -f "Microsoft Edge" 2>/dev/null || true) "
        remaining_pids+="$(pgrep -f "Google Chrome" 2>/dev/null || true) "
        remaining_pids+="$(pgrep -f "Safari" 2>/dev/null || true) "
        remaining_pids+="$(pgrep -f "playwright" 2>/dev/null || true) "
        remaining_pids+="$(pgrep -f "selenium\|webdriver\|chromedriver\|geckodriver" 2>/dev/null || true) "

        local force_killed=false
        for pid in $remaining_pids; do
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                log_warn "  ⚡ 强制终止顽固进程: $pid"
                kill -KILL "$pid" 2>/dev/null || true
                force_killed=true
            fi
        done

        if [ "$force_killed" = true ]; then
            sleep 1
        fi

        log_success "浏览器进程清理完成"
    elif [ "$browser_detected" = true ]; then
        log_info "检测到浏览器进程但无需清理"
    else
        log_success "未检测到浏览器进程冲突"
    fi

    # 清理可能遗留的用户数据锁文件
    cleanup_browser_locks() {
        local locks_cleaned=false
        local edge_profile_path="$HOME/Library/Application Support/Microsoft Edge"
        local chrome_profile_path="$HOME/Library/Application Support/Google/Chrome"

        # 清理Edge锁文件
        if [ -d "$edge_profile_path" ]; then
            find "$edge_profile_path" -name "SingletonLock" -type f 2>/dev/null | while read lock_file; do
                if [ -f "$lock_file" ]; then
                    rm -f "$lock_file" 2>/dev/null && log_info "  └─ 清理Edge锁文件: $lock_file" && locks_cleaned=true
                fi
            done
        fi

        # 清理Chrome锁文件
        if [ -d "$chrome_profile_path" ]; then
            find "$chrome_profile_path" -name "SingletonLock" -type f 2>/dev/null | while read lock_file; do
                if [ -f "$lock_file" ]; then
                    rm -f "$lock_file" 2>/dev/null && log_info "  └─ 清理Chrome锁文件: $lock_file" && locks_cleaned=true
                fi
            done
        fi

        if [ "$locks_cleaned" = true ]; then
            log_info "浏览器锁文件清理完成"
        fi
    }

    cleanup_browser_locks
}

# 执行浏览器进程清理
cleanup_browser_processes

# 构建命令
CMD="./xp start --dryrun --select-shops --data $TEST_DATA_PATH"

log_info "准备执行命令: $CMD"
log_info "运行时长: $MINUTES 分钟"
log_info "日志文件: $LOG_FILE"
log_info "开始时间: $(date)"

# 创建日志文件目录
mkdir -p "$(dirname "$LOG_FILE")"

# 启动命令并记录输出
cd "$PROJECT_ROOT"

# 确保日志目录存在
log_dir=$(dirname "$LOG_FILE")
mkdir -p "$log_dir"

{
    echo "================================================================"
    echo "AI产品选择器测试运行报告"
    echo "================================================================"
    echo "开始时间: $(date)"
    echo "运行命令: $CMD"
    echo "运行时长: $MINUTES 分钟"
    echo "项目目录: $PROJECT_ROOT"
    echo "测试数据: $TEST_DATA_PATH"
    echo "================================================================"
    echo ""
} > "$LOG_FILE"

# 启动进程并记录PID
log_info "启动进程..."
$CMD >> "$LOG_FILE" 2>&1 &
PROCESS_PID=$!

log_info "进程PID: $PROCESS_PID"

# 监控函数
monitor_process() {
    local pid=$1
    local duration=$2
    local start_time=$(date +%s)
    local end_time=$((start_time + duration * 60))
    
    log_info "开始监控进程 ${pid}，运行时长: ${duration}分钟"

    while [ $(date +%s) -lt $end_time ]; do
        if ! kill -0 ${pid} 2>/dev/null; then
            log_warn "进程已提前结束"
            return 1  # 返回状态表示进程提前结束
        fi
        sleep 5  # 减少检查间隔，更及时响应
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        local remaining=$((end_time - current_time))
        log_info "运行中... 已用时: ${elapsed}s, 剩余: ${remaining}s"
    done

    log_info "⏰ 监控时间到达，准备终止进程"
    return 0  # 返回状态表示正常到时间
}

# 设置信号处理
cleanup() {
    log_info "收到中断信号，正在清理..."
    if kill -0 $PROCESS_PID 2>/dev/null; then
        log_info "终止进程: $PROCESS_PID"
        kill -TERM $PROCESS_PID 2>/dev/null || true
        sleep 2
        if kill -0 $PROCESS_PID 2>/dev/null; then
            log_warn "进程未响应TERM信号，使用KILL信号"
            kill -KILL $PROCESS_PID 2>/dev/null || true
        fi
    fi
    
    echo "" >> "$LOG_FILE"
    echo "================================================================" >> "$LOG_FILE"
    echo "测试结束时间: $(date)" >> "$LOG_FILE"
    echo "================================================================" >> "$LOG_FILE"
    
    analyze_logs
    exit 0
}

trap cleanup SIGINT SIGTERM

# 监控进程
monitor_result=0
monitor_process $PROCESS_PID $MINUTES
monitor_result=$?

# 根据监控结果决定是否需要终止进程
if [ $monitor_result -eq 0 ]; then
    # 正常到时间，需要终止进程
    if kill -0 $PROCESS_PID 2>/dev/null; then
        log_info "⏰ 时间到，正在终止进程..."
        kill -TERM $PROCESS_PID 2>/dev/null || true
        sleep 3
        if kill -0 $PROCESS_PID 2>/dev/null; then
            log_warn "进程未响应TERM信号，使用KILL信号"
            kill -KILL $PROCESS_PID 2>/dev/null || true
            sleep 1
        fi
        log_success "✅ 进程已成功终止"
    else
        log_info "进程已自然结束"
    fi
else
    # 进程提前结束，无需终止
    log_info "进程已提前结束，无需手动终止"
fi

# 等待进程完全结束（设置超时避免无限等待）
timeout 10 sh -c "
    while kill -0 $PROCESS_PID 2>/dev/null; do
        sleep 0.5
    done
" 2>/dev/null || log_warn "等待进程结束超时，但继续执行后续操作"

{
    echo ""
    echo "================================================================"
    echo "测试结束时间: $(date)"
    echo "================================================================"
} >> "$LOG_FILE"

log_success "进程已终止，开始分析日志..."

# 日志分析函数
analyze_logs() {
    log_info "正在分析日志文件: $LOG_FILE"
    
    local analysis_file="${LOG_FILE%.log}_analysis.txt"
    
    {
        echo "================================================================"
        echo "AI产品选择器日志分析报告"
        echo "================================================================"
        echo "生成时间: $(date)"
        echo "日志文件: $LOG_FILE"
        echo ""
        
        # 错误统计
        echo "【错误统计】"
        local error_count=$(grep -c "ERROR" "$LOG_FILE" 2>/dev/null || echo "0")
        local warn_count=$(grep -c "WARNING\|WARN" "$LOG_FILE" 2>/dev/null || echo "0")
        local success_count=$(grep -c "SUCCESS" "$LOG_FILE" 2>/dev/null || echo "0")
        local info_count=$(grep -c "INFO" "$LOG_FILE" 2>/dev/null || echo "0")
        
        echo "错误 (ERROR): $error_count"
        echo "警告 (WARNING): $warn_count"
        echo "成功 (SUCCESS): $success_count"
        echo "信息 (INFO): $info_count"
        echo ""
        
        # 详细错误信息
        if [ "$error_count" -gt 0 ]; then
            echo "【错误详情】"
            grep "ERROR" "$LOG_FILE" | head -20
            echo ""
        fi
        
        # 详细警告信息
        if [ "$warn_count" -gt 0 ]; then
            echo "【警告详情】"
            grep "WARNING\|WARN" "$LOG_FILE" | head -20
            echo ""
        fi
        
        # 常见问题诊断
        echo "【问题诊断】"
        
        # 检查配置文件问题
        if grep -q "配置文件.*不存在\|配置文件.*错误\|JSON.*格式错误" "$LOG_FILE"; then
            echo "🔍 配置文件问题: 检测到配置文件相关错误"
        fi
        
        # 检查Excel文件问题
        if grep -q "Excel.*不存在\|xlsx.*不存在\|文件.*不存在" "$LOG_FILE"; then
            echo "🔍 文件缺失问题: 检测到文件不存在错误"
        fi
        
        # 检查网络/页面问题
        if grep -q "页面验证失败\|无法提取.*数据\|连接.*失败\|超时" "$LOG_FILE"; then
            echo "🔍 网络/页面问题: 检测到页面访问或数据提取问题"
        fi
        
        # 检查任务执行问题
        if grep -q "任务.*异常\|执行.*失败\|进程.*错误" "$LOG_FILE"; then
            echo "🔍 任务执行问题: 检测到任务执行异常"
        fi
        
        # 检查权限问题
        if grep -q "权限.*拒绝\|Permission.*denied\|访问.*被拒绝" "$LOG_FILE"; then
            echo "🔍 权限问题: 检测到权限相关错误"
        fi
        
        # 检查浏览器进程冲突问题
        if grep -q "Target page.*has been closed\|正在现有浏览器会话中打开\|kill EPERM\|BrowserType.launch_persistent_context" "$LOG_FILE"; then
            echo "🔍 浏览器进程冲突: 检测到浏览器启动冲突或进程管理问题"
        fi

        echo ""
        echo "【建议修复措施】"
        
        if [ "$error_count" -gt 0 ]; then
            echo "• 优先修复ERROR级别的问题"
            echo "• 检查配置文件格式和路径"
            echo "• 验证所需文件是否存在"
            echo "• 检查网络连接和页面可访问性"
            echo "• 如发现浏览器冲突，关闭现有浏览器实例后重试"
            echo "• 考虑使用独立的浏览器Profile避免冲突"
        fi
        
        if [ "$warn_count" -gt 0 ]; then
            echo "• 关注WARNING级别的问题，可能影响功能"
            echo "• 检查数据提取逻辑"
            echo "• 优化页面元素选择器"
        fi
        
        if [ "$error_count" -eq 0 ] && [ "$warn_count" -eq 0 ]; then
            echo "• 未发现明显错误，功能运行正常"
            echo "• 可以考虑从试运行模式切换到正式运行"
        fi
        
        echo ""
        echo "================================================================"
        echo "分析完成时间: $(date)"
        echo "================================================================"
        
    } > "$analysis_file"
    
    log_success "日志分析完成，报告保存至: $analysis_file"
    
    # 显示关键分析结果
    echo ""
    log_info "=== 关键分析结果 ==="
    grep -A 10 "【错误统计】" "$analysis_file"
    
    if grep -q "【问题诊断】" "$analysis_file"; then
        echo ""
        log_info "=== 问题诊断 ==="
        sed -n '/【问题诊断】/,/【建议修复措施】/p' "$analysis_file" | head -n -1
    fi
}

# 执行日志分析
analyze_logs

log_success "测试运行完成！"
log_info "日志文件: $LOG_FILE"
log_info "分析报告: ${LOG_FILE%.log}_analysis.txt"
