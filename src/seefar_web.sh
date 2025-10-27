#!/bin/bash

# Seefar Web服务启动脚本
# 用于启动基于Flask的Seefar店铺信息抓取Web界面
# 支持 start/stop/restart 命令

# PID文件路径
PID_FILE=".seefar_web.pid"
# 日志文件路径
LOG_FILE="seefar_web.log"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到项目根目录
cd "$SCRIPT_DIR"

# 检查Python3是否可用
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "❌ 错误: 未找到 python3 命令"
        echo "请确保已安装 Python 3"
        exit 1
    fi
}

# 检查必要文件是否存在
check_files() {
    if [ ! -f "src/playweight/scenes/web/seerfar_web.py" ]; then
        echo "❌ 错误: 未找到 seerfar_web.py 文件"
        echo "请确保在正确的项目目录中运行此脚本"
        exit 1
    fi
}

# 安装Python依赖
install_dependencies() {
    echo "📦 检查并安装Python依赖..."
    if [ -f "src/playweight/requirements.txt" ]; then
        echo "📋 找到 requirements.txt，正在安装依赖..."
        if ! python3 -m pip install -r src/playweight/requirements.txt; then
            echo "❌ 错误: 依赖安装失败"
            echo "请确保已安装 pip 并具有网络连接"
            exit 1
        fi
        echo "✅ 依赖安装完成"
    else
        echo "⚠️  警告: 未找到 requirements.txt 文件"
    fi
}

# 启动Web服务
start_service() {
    # 检查是否已在运行
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️  Seefar Web 服务已在运行 (PID: $PID)"
            exit 1
        else
            echo "🧹 清理残留的PID文件..."
            rm -f "$PID_FILE"
        fi
    fi

    check_python
    check_files
    install_dependencies

    echo "📍 项目目录: $SCRIPT_DIR"
    echo "🔧 设置 PYTHONPATH=src"
    echo "🌐 启动 Flask 服务..."
    echo ""

    # 导出PYTHONPATH并在后台启动服务
    export PYTHONPATH=src
    python3 src/playweight/scenes/web/seerfar_web.py > "$LOG_FILE" 2>&1 &
    PID=$!

    # 保存PID到文件
    echo $PID > "$PID_FILE"

    echo "✅ Seefar Web 服务已启动 (PID: $PID)"
    echo "📄 日志文件: $LOG_FILE"
    echo "📍 访问地址: http://127.0.0.1:7788"
    echo "🔍 查看实时日志: ./start_seefar_web.sh logs"
}

# 停止Web服务
stop_service() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  Seefar Web 服务未在运行 (PID文件不存在)"
        exit 1
    fi

    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🛑 正在停止 Seefar Web 服务 (PID: $PID)..."
        kill "$PID"

        # 等待进程终止（最多10秒）
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        # 如果进程仍未终止，强制杀死
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️  进程未正常终止，强制杀死..."
            kill -9 "$PID"
        fi

        # 清理PID文件
        rm -f "$PID_FILE"
        echo "✅ Seefar Web 服务已停止"
    else
        echo "⚠️  Seefar Web 服务未在运行 (PID文件存在但进程不存在)"
        rm -f "$PID_FILE"
    fi
}

# 重启Web服务
restart_service() {
    echo "🔄 重启 Seefar Web 服务..."
    if [ -f "$PID_FILE" ]; then
        stop_service
        sleep 2
    fi
    start_service
}

# 查看实时日志
view_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "⚠️  日志文件不存在: $LOG_FILE"
        echo "可能服务还未启动或日志文件被删除"
        exit 1
    fi

    echo "🔍 正在查看 Seefar Web 服务实时日志..."
    echo "📄 日志文件: $LOG_FILE"
    echo "💡 按 Ctrl+C 退出日志查看"
    echo ""

    # 使用 tail -f 查看实时日志
    tail -f "$LOG_FILE"
}

# 显示使用帮助
show_help() {
    echo "Seefar Web 服务管理脚本"
    echo ""
    echo "用法: $0 [start|stop|restart|logs|status]"
    echo ""
    echo "命令:"
    echo "  start    启动 Web 服务"
    echo "  stop     停止 Web 服务"
    echo "  restart  重启 Web 服务"
    echo "  logs     查看实时日志"
    echo "  status   显示服务状态"
    echo "  (无参数) 启动 Web 服务（默认行为）"
    echo ""
    echo "文件:"
    echo "  PID文件: $PID_FILE"
    echo "  日志文件: $LOG_FILE"
}

# 显示服务状态
show_status() {
    if [ ! -f "$PID_FILE" ]; then
        echo "🔴 Seefar Web 服务状态: 未运行"
    else
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "🟢 Seefar Web 服务状态: 运行中 (PID: $PID)"
        else
            echo "🟡 Seefar Web 服务状态: 异常 (PID文件存在但进程不存在)"
        fi
    fi

    # 显示日志文件信息
    if [ -f "$LOG_FILE" ]; then
        LOG_SIZE=$(du -h "$LOG_FILE" 2>/dev/null | cut -f1)
        echo "📄 日志文件: $LOG_FILE ($LOG_SIZE)"
    else
        echo "📄 日志文件: $LOG_FILE (不存在)"
    fi
}

# 主逻辑
case "${1:-start}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    logs)
        view_logs
        ;;
    status)
        show_status
        ;;
    *)
        show_help
        exit 1
        ;;
esac