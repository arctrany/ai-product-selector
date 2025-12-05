#!/bin/bash
# AI选品自动化系统 - Linux 构建脚本
# 使用 PyInstaller 打包为 Linux 可执行文件

set -e  # 遇到错误立即退出

echo "========================================"
echo "AI选品自动化系统 - Linux 构建"
echo "========================================"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python 3.8+"
    echo "💡 Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "💡 CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "💡 Fedora: sudo dnf install python3 python3-pip"
    echo "💡 Arch: sudo pacman -S python python-pip"
    exit 1
fi

# 显示 Python 版本
echo "🐍 Python 版本:"
python3 --version

# 检查系统信息
echo "🖥️ 系统信息:"
echo "   发行版: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")"
echo "   内核: $(uname -r)"
echo "   架构: $(uname -m)"

# 检查必需文件
required_files=("requirements.txt" "build.spec" "cli/main.py")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ 错误: 未找到 $file 文件"
        exit 1
    fi
done
echo "✓ 必需文件检查通过"

# 检查系统依赖
echo "🔍 检查系统依赖..."
missing_deps=()

# 检查必需的系统包
if ! dpkg -l | grep -q python3-dev 2>/dev/null && ! rpm -q python3-devel &>/dev/null; then
    missing_deps+=("python3-dev/python3-devel")
fi

if ! command -v gcc &> /dev/null; then
    missing_deps+=("gcc")
fi

if [[ ${#missing_deps[@]} -gt 0 ]]; then
    echo "⚠ 警告: 缺少以下系统依赖:"
    for dep in "${missing_deps[@]}"; do
        echo "   - $dep"
    done
    echo "💡 请安装缺少的依赖后重试"
    echo "💡 Ubuntu/Debian: sudo apt install python3-dev gcc"
    echo "💡 CentOS/RHEL: sudo yum install python3-devel gcc"
    echo "💡 Fedora: sudo dnf install python3-devel gcc"
fi

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
    echo "⚠ 警告: Playwright 浏览器安装失败"
    echo "💡 请手动运行: playwright install chromium"
    echo "💡 或安装系统依赖: playwright install-deps"
}

# 清理旧的构建文件
echo "🧹 清理构建目录..."
rm -rf dist build
echo "✓ 构建目录已清理"

# 运行 PyInstaller
echo "🔨 开始 PyInstaller 构建..."
python3 -m PyInstaller build.spec --clean --noconfirm

# 检查构建结果
if [[ ! -f "dist/ai-product-selector" ]]; then
    echo "❌ 错误: 构建的可执行文件不存在"
    exit 1
fi

# 确定平台标签
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        PLATFORM_TAG="linux-x64"
        ;;
    aarch64|arm64)
        PLATFORM_TAG="linux-arm64"
        ;;
    armv7l)
        PLATFORM_TAG="linux-armv7"
        ;;
    i386|i686)
        PLATFORM_TAG="linux-x86"
        ;;
    *)
        PLATFORM_TAG="linux-$ARCH"
        ;;
esac

DIST_NAME="ai-product-selector-$PLATFORM_TAG"
DIST_DIR="dist/$DIST_NAME"

echo "📦 创建分发包..."
mkdir -p "$DIST_DIR"

# 复制可执行文件
cp "dist/ai-product-selector" "$DIST_DIR/"
chmod +x "$DIST_DIR/ai-product-selector"

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
# AI选品自动化系统 - Linux 版本

## 使用方法

### 1. 准备配置文件
复制 example_config.json 为 user_config.json 并根据需要修改配置。

### 2. 运行程序
\`\`\`bash
./ai-product-selector start --data user_data.json --config user_config.json
\`\`\`

### 3. 查看帮助
\`\`\`bash
./ai-product-selector --help
\`\`\`

## 系统要求
- Linux 发行版 (Ubuntu 18.04+, CentOS 7+, 等)
- 架构: $ARCH
- 无需安装 Python 环境

## 权限设置
如果遇到权限问题，请运行：
\`\`\`bash
chmod +x ai-product-selector
\`\`\`

## 故障排除

### 1. 缺少共享库
如果出现 "error while loading shared libraries" 错误，请安装相应的系统库：

Ubuntu/Debian:
\`\`\`bash
sudo apt update
sudo apt install libc6 libgcc-s1 libstdc++6
\`\`\`

CentOS/RHEL:
\`\`\`bash
sudo yum install glibc libgcc libstdc++
\`\`\`

### 2. 浏览器问题
如果 Playwright 浏览器无法启动，请安装浏览器依赖：
\`\`\`bash
# 下载并运行依赖安装脚本
wget https://playwright.azureedge.net/builds/driver/playwright-1.40.0-linux.tar.gz
tar -xzf playwright-1.40.0-linux.tar.gz
./playwright-1.40.0-linux/playwright.sh install-deps chromium
\`\`\`

## 版本信息
- 构建时间: $(date)
- 平台: $PLATFORM_TAG
- 发行版: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")
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

# 检查可执行权限
if [[ ! -x "ai-product-selector" ]]; then
    echo "🔧 设置可执行权限..."
    chmod +x ai-product-selector
fi

# 启动应用程序
echo "🚀 启动 AI选品自动化系统..."
./ai-product-selector start --data user_data.json --config user_config.json
EOF

chmod +x "$DIST_DIR/start.sh"

# 创建安装脚本
cat > "$DIST_DIR/install.sh" << 'EOF'
#!/bin/bash
# AI选品自动化系统安装脚本

set -e

INSTALL_DIR="/opt/ai-product-selector"
BIN_DIR="/usr/local/bin"

echo "🚀 安装 AI选品自动化系统..."

# 检查权限
if [[ $EUID -ne 0 ]]; then
    echo "❌ 错误: 需要 root 权限安装到系统目录"
    echo "💡 请使用: sudo ./install.sh"
    exit 1
fi

# 创建安装目录
echo "📁 创建安装目录: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 复制文件
echo "📋 复制程序文件..."
cp ai-product-selector "$INSTALL_DIR/"
cp *.json "$INSTALL_DIR/" 2>/dev/null || true
cp README.txt "$INSTALL_DIR/"

# 设置权限
chmod +x "$INSTALL_DIR/ai-product-selector"

# 创建符号链接
echo "🔗 创建命令行链接..."
ln -sf "$INSTALL_DIR/ai-product-selector" "$BIN_DIR/ai-product-selector"

echo "✅ 安装完成！"
echo "💡 现在可以在任何位置运行: ai-product-selector --help"
echo "📁 程序安装在: $INSTALL_DIR"
EOF

chmod +x "$DIST_DIR/install.sh"

# 创建 tar.gz 压缩包
echo "📦 创建 tar.gz 压缩包..."
cd dist
tar -czf "$DIST_NAME.tar.gz" "$DIST_NAME"
cd ..

# 显示构建结果
echo
echo "========================================"
echo "🎉 Linux 构建完成！"
echo "========================================"
echo "📁 构建目录: dist/$DIST_NAME"
echo "📦 压缩包: dist/$DIST_NAME.tar.gz"
echo "🚀 可执行文件: $DIST_NAME/ai-product-selector"
echo
echo "💡 使用方法:"
echo "   cd dist/$DIST_NAME"
echo "   ./start.sh"
echo "   或 ./ai-product-selector --help"
echo
echo "💡 系统安装:"
echo "   sudo ./install.sh"
echo

# 停用虚拟环境
if [[ "$CREATE_VENV" == true ]]; then
    deactivate
    echo "✓ 虚拟环境已停用"
fi

echo "构建完成！"
