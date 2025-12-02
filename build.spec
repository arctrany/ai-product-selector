# -*- mode: python ; coding: utf-8 -*-
"""
AI选品自动化系统 PyInstaller 构建规格文件
支持跨平台打包为单文件可执行程序
"""

import sys
import os
from pathlib import Path

# 项目根目录
project_root = Path.cwd()

# 数据文件和资源文件配置
datas = []

# 只包含运行时必需的配置文件
config_files = [
    'config.json',
    'example_config.json',
    'common/config/ozon_selectors_default.json'
]

for config_file in config_files:
    config_path = project_root / config_file
    if config_path.exists():
        if config_file.startswith('common/'):
            datas.append((config_file, os.path.dirname(config_file)))
        else:
            datas.append((config_file, '.'))

# CI环境可能需要的版本信息文件
version_file = project_root / 'version.py'
if version_file.exists():
    datas.append(('version.py', '.'))

# 隐藏导入 - 确保所有必需模块被包含
hiddenimports = [
    # 核心模块
    'cli',
    'cli.main',
    'cli.models',
    'cli.task_controller',
    'cli.preset_manager',
    'cli.log_manager',
    'common',
    'common.config',
    'common.business',
    'common.scrapers',
    'rpa',
    'rpa.browser',
    'utils',
    
    # Playwright 相关
    'playwright',
    'playwright.async_api',
    'playwright._impl',
    
    # Excel 处理
    'openpyxl',
    'openpyxl.workbook',
    'openpyxl.worksheet',
    
    # 图像处理
    'PIL',
    'PIL.Image',
    'cv2',
    'skimage',
    'imagehash',
    'numpy',
    
    # HTTP 和网络
    'requests',
    'urllib3',
    'certifi',
    
    # 异步编程
    'asyncio',
    'concurrent.futures',
    
    # JSON 和数据处理
    'json',
    'csv',
    'sqlite3',
    
    # 系统和路径
    'pathlib',
    'tempfile',
    'shutil',
]

# 排除的模块 - 减少打包大小
excludes = [
    'tkinter',
    'matplotlib',
    'IPython',
    'jupyter',
    'notebook',
    'pandas',  # 项目中未使用
    'scipy',   # 如果未使用
    'sympy',
    'pytest',
    'unittest',
]

# 二进制文件排除 - 避免不必要的依赖
binaries = []

# 分析配置
a = Analysis(
    ['cli/main.py'],  # 主入口文件
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ 配置 - Python 字节码归档
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE 配置 - 可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ai-product-selector',  # 可执行文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用 UPX 压缩（如果可用）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 控制台应用
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
    version_file=None,  # 可以添加版本信息文件
)

# 平台特定配置
if sys.platform == 'darwin':  # macOS
    # macOS 应用包配置
    app = BUNDLE(
        exe,
        name='AI Product Selector.app',
        icon=None,
        bundle_identifier='com.example.ai-product-selector',
        info_plist={
            'CFBundleDisplayName': 'AI Product Selector',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
