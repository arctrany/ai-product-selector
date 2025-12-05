# 跨平台使用指南

本文档介绍如何在不同操作系统上使用 AI 选品自动化系统。

## 快速开始

### Linux / macOS

```bash
# 克隆项目
git clone <repository-url>
cd ai-product-selector3

# 添加执行权限（首次）
chmod +x xp

# 运行
./xp --help
```

### Windows

```cmd
REM 克隆项目
git clone <repository-url>
cd ai-product-selector3

REM 运行
xp.bat --help
```

## 自动依赖管理

系统会在首次运行时自动检测并安装缺失的依赖：

1. **Python 版本检测** - 需要 Python 3.8+
2. **pip 可用性检测** - 需要 pip 包管理器
3. **系统浏览器检测** - 需要安装 Chrome 或 Edge 浏览器
4. **依赖包安装** - 自动安装 requirements.txt 中的依赖
5. **Playwright 浏览器** - 自动安装 Chromium 浏览器驱动

### 跳过依赖检查

如果你确定依赖已安装，可以跳过检查以加快启动速度：

```bash
# Linux / macOS
XP_SKIP_DEP_CHECK=1 ./xp start

# Windows
set XP_SKIP_DEP_CHECK=1
xp.bat start
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `XP_SKIP_DEP_CHECK` | 跳过依赖检查 (1/true/yes) | 空（不跳过） |

## 虚拟环境（推荐）

建议使用虚拟环境来隔离项目依赖：

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
# Linux / macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
python -m playwright install chromium

# 运行
./xp start  # 或 xp.bat start
```

## 常见问题

### Python 未找到

**问题**: 运行 `xp` 或 `xp.bat` 时提示找不到 Python

**解决方案**:
1. 确保已安装 Python 3.8+
2. 将 Python 添加到系统 PATH
3. Windows 用户安装时勾选 "Add Python to PATH"

### 依赖安装失败

**问题**: 自动安装依赖时失败

**可能原因**:
- 网络问题
- 权限不足
- pip 版本过低

**解决方案**:
```bash
# 手动安装
pip install --upgrade pip
pip install -r requirements.txt
```

### 未检测到 Chrome 或 Edge 浏览器

**问题**: 系统没有安装 Chrome 或 Edge 浏览器

**解决方案**:
- 安装 Google Chrome: https://www.google.com/chrome/
- 安装 Microsoft Edge: https://www.microsoft.com/edge/

注意：系统必须安装 Chrome 或 Edge 之一才能正常运行。

### Playwright 浏览器安装失败

**问题**: Playwright 浏览器驱动安装失败

**解决方案**:
```bash
# 手动安装
python -m playwright install chromium

# 如果需要系统依赖（Linux）
sudo python -m playwright install-deps
```

## 平台特定说明

### macOS

- 使用 `./xp` 运行
- 首次运行可能需要授权网络访问

### Windows

- 使用 `xp.bat` 运行
- 如果安装了 Python Launcher (py)，会自动使用
- 中文输出可能需要终端支持 UTF-8

### Linux

- 使用 `./xp` 运行
- 可能需要安装系统依赖: `sudo apt install libnss3 libatk-bridge2.0-0`

## 依赖检测工具

可以单独运行依赖检测工具来诊断问题：

```bash
# 只检测，不安装
python cli/dependency_checker.py --no-install

# 静默模式
python cli/dependency_checker.py --quiet
```
