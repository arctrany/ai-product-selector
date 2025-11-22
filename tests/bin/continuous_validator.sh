#!/bin/bash

# =================================================================
# AI产品选择器持续验证脚本
# 功能：不断运行测试，发现并记录项目中的错误
# 作者：AI助手
# 版本：1.0
# =================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置参数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs/continuous_validation"
RESULTS_DIR="$PROJECT_ROOT/validation_results"
MAX_ITERATIONS=${MAX_ITERATIONS:-100}  # 默认运行100轮
TEST_DURATION=${TEST_DURATION:-2}      # 每轮测试2分钟
SLEEP_BETWEEN_TESTS=${SLEEP_BETWEEN_TESTS:-30}  # 测试间隔30秒

# 创建必要的目录
mkdir -p "$LOG_DIR"
mkdir -p "$RESULTS_DIR"

# 时间处理函数
convert_to_seconds() {
    local duration="$1"
    # 如果是整数，直接返回秒数
    if [[ "$duration" =~ ^[0-9]+$ ]]; then
        echo $((duration * 60))
    # 如果包含小数点，使用bc或awk处理
    elif [[ "$duration" =~ ^[0-9]*\.[0-9]+$ ]]; then
        # 使用awk进行浮点数计算，转换为秒
        echo "$duration" | awk '{printf "%.0f", $1 * 60}'
    else
        # 默认返回120秒（2分钟）
        echo 120
    fi
}

# 时间处理函数
convert_to_seconds() {
    local duration="$1"
    # 如果是整数，直接返回秒数
    if [[ "$duration" =~ ^[0-9]+$ ]]; then
        echo $((duration * 60))
    # 如果包含小数点，使用bc或awk处理
    elif [[ "$duration" =~ ^[0-9]*\.[0-9]+$ ]]; then
        # 使用awk进行浮点数计算，转换为秒
        echo "$duration" | awk '{printf "%.0f", $1 * 60}'
    else
        # 默认返回120秒（2分钟）
        echo 120
    fi
}

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_highlight() {
    echo -e "${PURPLE}[HIGHLIGHT]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
AI产品选择器持续验证脚本

用法: $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -i, --iterations NUM    设置运行轮数 (默认: 100)
    -d, --duration NUM      设置每轮测试时长(分钟) (默认: 2)
    -s, --sleep NUM         设置测试间隔(秒) (默认: 30)
    -c, --continuous        持续运行模式（无限循环）
    -q, --quick             快速模式（每轮30秒，间隔5秒）
    --clean-logs            清理历史日志后开始

示例:
    $0                      # 运行100轮，每轮2分钟
    $0 -i 50 -d 1           # 运行50轮，每轮1分钟
    $0 -c                   # 持续运行模式
    $0 -q                   # 快速验证模式
    $0 --clean-logs -i 20   # 清理日志后运行20轮

环境变量:
    MAX_ITERATIONS          最大迭代次数
    TEST_DURATION           测试持续时间(分钟)
    SLEEP_BETWEEN_TESTS     测试间隔时间(秒)
EOF
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -i|--iterations)
                MAX_ITERATIONS="$2"
                shift 2
                ;;
            -d|--duration)
                TEST_DURATION="$2"
                shift 2
                ;;
            -s|--sleep)
                SLEEP_BETWEEN_TESTS="$2"
                shift 2
                ;;
            -c|--continuous)
                MAX_ITERATIONS=999999
                shift
                ;;
            -q|--quick)
                TEST_DURATION="0.5"
                SLEEP_BETWEEN_TESTS=5
                shift
                ;;
            --clean-logs)
                CLEAN_LOGS=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 清理历史日志
clean_logs() {
    if [[ "$CLEAN_LOGS" == "true" ]]; then
        log_info "清理历史验证日志..."
        rm -rf "$LOG_DIR"/*
        rm -rf "$RESULTS_DIR"/*
        log_success "历史日志清理完成"
    fi
}

# 初始化环境
initialize_environment() {
    log_info "初始化持续验证环境..."
    
    # 检查项目结构
    if [[ ! -f "$PROJECT_ROOT/xp" ]]; then
        log_error "未找到主程序脚本: $PROJECT_ROOT/xp"
        exit 1
    fi
    
    if [[ ! -f "$PROJECT_ROOT/tests/bin/test_runner.sh" ]]; then
        log_error "未找到测试运行脚本: $PROJECT_ROOT/tests/bin/test_runner.sh"
        exit 1
    fi
    
    # 设置执行权限
    chmod +x "$PROJECT_ROOT/tests/bin/test_runner.sh"
    
    log_success "环境初始化完成"
}

# 运行单轮测试
run_single_test() {
    local iteration=$1
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local test_log="$LOG_DIR/test_${iteration}_${timestamp}.log"
    local analysis_log="$LOG_DIR/analysis_${iteration}_${timestamp}.txt"
    
    log_highlight "🚀 开始第 $iteration 轮测试 (时长: ${TEST_DURATION}分钟)"
    
    # 记录测试开始信息
    {
        echo "================================================================"
        echo "持续验证测试报告 - 第 $iteration 轮"
        echo "================================================================"
        echo "开始时间: $(date)"
        echo "测试时长: ${TEST_DURATION} 分钟"
        echo "项目路径: $PROJECT_ROOT"
        echo "================================================================"
        echo ""
    } > "$test_log"
    
    # 运行测试
    cd "$PROJECT_ROOT"
    local test_seconds=$(convert_to_seconds "$TEST_DURATION")
    local timeout_seconds=$((test_seconds + 30))
    if timeout "$timeout_seconds" "$PROJECT_ROOT/tests/bin/test_runner.sh" "$TEST_DURATION" >> "$test_log" 2>&1; then
        log_success "✅ 第 $iteration 轮测试完成"
    else
        log_warning "⚠️ 第 $iteration 轮测试可能存在问题"
    fi
    
    # 分析测试结果
    analyze_test_results "$test_log" "$analysis_log" "$iteration"
    
    return 0
}

# 分析测试结果
analyze_test_results() {
    local test_log="$1"
    local analysis_log="$2"
    local iteration="$3"
    
    if [[ ! -f "$test_log" ]]; then
        log_error "测试日志文件不存在: $test_log"
        return 1
    fi
    
    log_info "🔍 分析第 $iteration 轮测试结果..."
    
    # 统计错误信息
    local error_count=$(grep -c "ERROR" "$test_log" 2>/dev/null | tr -d '\n\r\t ' || echo "0")
    local warning_count=$(grep -c "WARNING\|WARN" "$test_log" 2>/dev/null | tr -d '\n\r\t ' || echo "0")
    local success_count=$(grep -c "SUCCESS" "$test_log" 2>/dev/null | tr -d '\n\r\t ' || echo "0")
    local timeout_count=$(grep -c "timeout\|Timeout\|TIMEOUT" "$test_log" 2>/dev/null | tr -d '\n\r\t ' || echo "0")
    local crash_count=$(grep -c "crash\|Crash\|CRASH\|segmentation fault" "$test_log" 2>/dev/null | tr -d '\n\r\t ' || echo "0")
    
    # 生成分析报告
    {
        echo "================================================================"
        echo "第 $iteration 轮测试结果分析"
        echo "================================================================"
        echo "分析时间: $(date)"
        echo "测试日志: $test_log"
        echo ""
        echo "【统计结果】"
        echo "错误 (ERROR): $error_count"
        echo "警告 (WARNING): $warning_count"
        echo "成功 (SUCCESS): $success_count"
        echo "超时 (TIMEOUT): $timeout_count"
        echo "崩溃 (CRASH): $crash_count"
        echo ""
        
        # 详细错误信息
        if [[ "$error_count" -gt 0 ]]; then
            echo "【错误详情】"
            grep -n "ERROR" "$test_log" | head -10
            echo ""
        fi
        
        # 超时问题
        if [[ "$timeout_count" -gt 0 ]]; then
            echo "【超时问题】"
            grep -n -i "timeout" "$test_log" | head -5
            echo ""
        fi
        
        # 崩溃问题
        if [[ "$crash_count" -gt 0 ]]; then
            echo "【崩溃问题】"
            grep -n -i "crash\|segmentation fault" "$test_log" | head -5
            echo ""
        fi
        
        # 性能指标
        echo "【性能指标】"
        local total_time=$(grep "运行中... 已用时:" "$test_log" | tail -1 | grep -o "已用时: [0-9]*s" | grep -o "[0-9]*" || echo "N/A")
        echo "实际运行时间: ${total_time}s"
        echo ""
        
        echo "================================================================"
        
    } > "$analysis_log"
    
    # 输出关键统计信息
    if [[ "$error_count" -gt 0 ]] || [[ "$crash_count" -gt 0 ]]; then
        log_error "❌ 第 $iteration 轮发现严重问题: $error_count 个错误, $crash_count 个崩溃"
    elif [[ "$warning_count" -gt 5 ]]; then
        log_warning "⚠️ 第 $iteration 轮发现较多警告: $warning_count 个"
    else
        log_success "✅ 第 $iteration 轮测试状态良好: $success_count 个成功操作"
    fi
    
    log_info "📊 统计: ERROR:$error_count, WARNING:$warning_count, SUCCESS:$success_count, TIMEOUT:$timeout_count"
}

# 生成汇总报告
generate_summary_report() {
    local summary_file="$RESULTS_DIR/continuous_validation_summary_$(date '+%Y%m%d_%H%M%S').txt"
    
    log_info "📋 生成汇总报告..."
    
    {
        echo "================================================================"
        echo "AI产品选择器持续验证汇总报告"
        echo "================================================================"
        echo "报告生成时间: $(date)"
        echo "验证轮数: 已完成的轮数"
        echo "项目路径: $PROJECT_ROOT"
        echo ""
        
        echo "【总体统计】"
        local total_errors=0
        local total_warnings=0
        local total_successes=0
        local total_timeouts=0
        local total_crashes=0
        
        # 统计所有日志
        for log_file in "$LOG_DIR"/test_*.log; do
            if [[ -f "$log_file" ]]; then
                local file_errors=$(grep -c "ERROR" "$log_file" 2>/dev/null | tr -d '\n\r\t ' || echo "0")
                local file_warnings=$(grep -c "WARNING\|WARN" "$log_file" 2>/dev/null | tr -d '\n\r\t ' || echo "0")
                local file_successes=$(grep -c "SUCCESS" "$log_file" 2>/dev/null | tr -d '\n\r\t ' || echo "0")
                local file_timeouts=$(grep -c "timeout\|Timeout\|TIMEOUT" "$log_file" 2>/dev/null | tr -d '\n\r\t ' || echo "0")
                local file_crashes=$(grep -c "crash\|Crash\|CRASH" "$log_file" 2>/dev/null | tr -d '\n\r\t ' || echo "0")

                total_errors=$((total_errors + file_errors))
                total_warnings=$((total_warnings + file_warnings))
                total_successes=$((total_successes + file_successes))
                total_timeouts=$((total_timeouts + file_timeouts))
                total_crashes=$((total_crashes + file_crashes))
            fi
        done
        
        echo "总错误数: $total_errors"
        echo "总警告数: $total_warnings"
        echo "总成功数: $total_successes"
        echo "总超时数: $total_timeouts"
        echo "总崩溃数: $total_crashes"
        echo ""
        
        echo "【问题分析】"
        if [[ "$total_crashes" -gt 0 ]]; then
            echo "🔴 严重: 发现 $total_crashes 次崩溃，需要立即修复"
        fi
        
        if [[ "$total_errors" -gt 10 ]]; then
            echo "🔴 严重: 发现 $total_errors 个错误，建议优先修复"
        elif [[ "$total_errors" -gt 0 ]]; then
            echo "🟡 注意: 发现 $total_errors 个错误，建议关注"
        fi
        
        if [[ "$total_timeouts" -gt 5 ]]; then
            echo "🟡 注意: 发现 $total_timeouts 次超时，可能存在性能问题"
        fi
        
        if [[ "$total_warnings" -gt 50 ]]; then
            echo "🟡 注意: 警告数量较多 ($total_warnings)，建议优化"
        fi
        
        if [[ "$total_errors" -eq 0 ]] && [[ "$total_crashes" -eq 0 ]] && [[ "$total_timeouts" -lt 3 ]]; then
            echo "🟢 良好: 系统运行稳定，未发现严重问题"
        fi
        
        echo ""
        echo "【建议措施】"
        if [[ "$total_crashes" -gt 0 ]] || [[ "$total_errors" -gt 10 ]]; then
            echo "1. 立即检查错误日志，定位问题根源"
            echo "2. 检查系统资源使用情况"
            echo "3. 验证配置文件和依赖项"
            echo "4. 考虑回滚到稳定版本"
        else
            echo "1. 定期检查警告信息，进行预防性维护"
            echo "2. 持续监控系统性能指标"
            echo "3. 保持代码质量和测试覆盖率"
        fi
        
        echo ""
        echo "================================================================"
        
    } > "$summary_file"
    
    log_success "📊 汇总报告已生成: $summary_file"
    
    # 显示关键统计信息
    log_highlight "🎯 验证完成统计: ERROR:$total_errors, WARNING:$total_warnings, SUCCESS:$total_successes"
}

# 信号处理
cleanup() {
    log_info "收到终止信号，正在清理..."
    
    # 杀掉可能的子进程
    pkill -P $$ 2>/dev/null || true
    
    # 生成最终报告
    generate_summary_report
    
    log_success "持续验证已停止"
    exit 0
}

# 主函数
main() {
    # 设置信号处理
    trap cleanup SIGINT SIGTERM
    
    # 解析参数
    parse_arguments "$@"
    
    # 显示配置信息
    log_highlight "🎯 持续验证配置"
    log_info "最大轮数: $MAX_ITERATIONS"
    log_info "每轮时长: ${TEST_DURATION} 分钟"
    log_info "测试间隔: ${SLEEP_BETWEEN_TESTS} 秒"
    log_info "日志目录: $LOG_DIR"
    log_info "结果目录: $RESULTS_DIR"
    echo ""
    
    # 清理历史日志
    clean_logs
    
    # 初始化环境
    initialize_environment
    
    # 开始持续验证
    log_highlight "🚀 开始持续验证循环..."
    
    for ((i=1; i<=MAX_ITERATIONS; i++)); do
        log_highlight "🔄 第 $i/$MAX_ITERATIONS 轮验证"
        
        # 运行测试
        run_single_test "$i"
        
        # 检查是否需要继续
        if [[ $i -lt $MAX_ITERATIONS ]]; then
            log_info "⏸️ 等待 ${SLEEP_BETWEEN_TESTS} 秒后开始下一轮..."
            sleep "$SLEEP_BETWEEN_TESTS"
        fi
    done
    
    # 生成最终报告
    generate_summary_report
    
    log_success "🎉 持续验证完成！"
}

# 执行主函数
main "$@"
