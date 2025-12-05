#!/bin/bash
# AI选品自动化系统 - macOS 构建脚本
# 使用 PyInstaller 打包为 macOS 应用程序

set -e  # 遇到错误立即退出

echo "========================================"
echo "AI选品自动化系统 - macOS 构建"
echo "========================================"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 显示 Python 版本
echo "🐍 Python 版本:"
python3 --version

# 检查必需文件
required_files=("requirements.txt" "build.spec" "cli/main.py")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ 错误: 未找到 $file 文件"
        exit 1
    fi
done
echo "✓ 必需文件检查通过"

# 检查是否使用虚拟环境
CREATE_VENV=false
if [[ "$1" == "--venv" ]]; then
    CREATE_VENV=true
fi

if [[ "$CREATE_VENV" == true ]]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv build-env
    source build-env/bin/activate
    echo "✓ 虚拟环境已激活"
fi

# 升级 pip
echo "📦 升级 pip..."
python3 -m pip install --upgrade pip

# 安装依赖
echo "📦 安装项目依赖..."
python3 -m pip install -r requirements.txt

# 安装 Playwright 浏览器
echo "🌐 安装 Playwright 浏览器..."
python3 -m playwright install chromium || {
    echo "⚠ 警告: Playwright 浏览器安装失败，请手动运行: playwright install chromium"
}

# 清理旧的构建文件
echo "🧹 清理构建目录..."
rm -rf dist build
echo "✓ 构建目录已清理"

# 运行 PyInstaller
echo "🔨 开始 PyInstaller 构建..."
python3 -m PyInstaller build.spec --clean --noconfirm

# 检查构建结果
if [[ ! -d "dist/AI Product Selector.app" ]]; then
    echo "❌ 错误: 构建的应用程序不存在"
    exit 1
fi

# 确定平台标签
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        PLATFORM_TAG="macos-x64"
        ;;
    arm64)
        PLATFORM_TAG="macos-arm64"
        ;;
    *)
        PLATFORM_TAG="macos-$ARCH"
        ;;
esac

DIST_NAME="ai-product-selector-$PLATFORM_TAG"
DIST_DIR="dist/$DIST_NAME"

echo "📦 创建分发包..."
mkdir -p "$DIST_DIR"

# 复制应用程序
cp -R "dist/AI Product Selector.app" "$DIST_DIR/"

# 复制配置文件
if [[ -f "config.json" ]]; then
    cp "config.json" "$DIST_DIR/"
fi
if [[ -f "example_config.json" ]]; then
    cp "example_config.json" "$DIST_DIR/"
fi

# 创建使用说明
echo "创建使用说明..."
cat > "$DIST_DIR/README.txt" << EOF
# AI选品自动化系统 - macOS 版本

## 使用方法

### 1. 准备配置文件
复制 example_config.json 为 user_config.json 并根据需要修改配置。

### 2. 运行程序

#### 方法一：双击应用图标
直接双击 "AI Product Selector.app" 启动应用程序。

#### 方法二：命令行运行
\`\`\`bash
./AI\\ Product\\ Selector.app/Contents/MacOS/ai-product-selector start --data user_data.json --config user_config.json
\`\`\`

### 3. 查看帮助
\`\`\`bash
./AI\\ Product\\ Selector.app/Contents/MacOS/ai-product-selector --help
\`\`\`

## 系统要求
- macOS 10.15+ (Catalina 或更高版本)
- 架构: $ARCH
- 无需安装 Python 环境

## 安全提示
首次运行时，macOS 可能会显示安全警告。请按以下步骤操作：
1. 右键点击应用程序，选择"打开"
2. 在弹出的对话框中点击"打开"
3. 或者在"系统偏好设置" > "安全性与隐私"中允许运行

## 版本信息
- 构建时间: $(date)
- 平台: $PLATFORM_TAG
EOF

# 创建启动脚本
cat > "$DIST_DIR/start.sh" << 'EOF'
#!/bin/bash
# AI选品自动化系统启动脚本

cd "$(dirname "$0")"

# 检查配置文件
if [[ ! -f "user_data.json" ]]; then
    echo "❌ 错误: 未找到 user_data.json 配置文件"
    echo "💡 请复制 example_config.json 为 user_data.json 并修改配置"
    exit 1
fi

# 启动应用程序
echo "🚀 启动 AI选品自动化系统..."
./AI\ Product\ Selector.app/Contents/MacOS/ai-product-selector start --data user_data.json --config user_config.json
EOF

chmod +x "$DIST_DIR/start.sh"

# 创建 tar.gz 压缩包
echo "📦 创建 tar.gz 压缩包..."
cd dist
tar -czf "$DIST_NAME.tar.gz" "$DIST_NAME"
cd ..

# 显示构建结果
echo
echo "========================================"
echo "🎉 macOS 构建完成！"
echo "========================================"
echo "📁 构建目录: dist/$DIST_NAME"
echo "📦 压缩包: dist/$DIST_NAME.tar.gz"
echo "🚀 应用程序: $DIST_NAME/AI Product Selector.app"
echo
echo "💡 使用方法:"
echo "   cd dist/$DIST_NAME"
echo "   ./start.sh"
echo "   或双击 AI Product Selector.app"
echo

# 停用虚拟环境
if [[ "$CREATE_VENV" == true ]]; then
    deactivate
    echo "✓ 虚拟环境已停用"
fi

echo "构建完成！"
