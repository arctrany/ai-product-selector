#!/bin/bash

# Prefect 工作流引擎环境设置脚本
# 用于自动创建虚拟环境并安装依赖

set -e  # 遇到错误时退出

echo "🚀 开始设置 Prefect 工作流环境..."

# 检查 Python 是否已安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.8+"
    exit 1
fi

# 检查 pip 是否已安装
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: 未找到 pip3，请先安装 pip"
    exit 1
fi

echo "✅ Python 和 pip 已安装"

# 进入 src_new 目录
cd "$(dirname "$0")"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "🔧 创建 Python 虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "🔧 升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "🔧 安装依赖包..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ 依赖包安装完成"
else
    echo "⚠️  未找到 requirements.txt 文件"
fi

# 验证安装
echo "🔧 验证 Prefect 安装..."
if python -c "import prefect; print('✅ Prefect 版本:', prefect.__version__)" &> /dev/null; then
    echo "✅ Prefect 安装验证通过"
else
    echo "❌ Prefect 安装验证失败"
    exit 1
fi

echo ""
echo "🎉 环境设置完成!"
echo "使用方法:"
echo "  1. 激活环境: source venv/bin/activate"
echo "  2. 运行基础工作流: cd workflows && python basic_workflow.py"
echo "  3. 运行暂停/恢复演示: cd workflows && python pause_resume_workflow.py"
echo "  4. 使用 API 控制工具: cd utils && python control_api.py list"
echo ""
echo "💡 提示: 要退出虚拟环境，运行: deactivate"
