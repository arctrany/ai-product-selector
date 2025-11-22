# -*- mode: python ; coding: utf-8 -*-
"""
AI选品自动化系统 PyInstaller 构建规格文件 - 启动速度优化版本
优化策略：
1. 使用 onedir 模式提升启动速度
2. 精简 hiddenimports，只保留运行时必需的模块
3. 扩展 excludes，排除更多开发依赖
4. 优化资源文件，只包含运行时必需的配置
"""

import sys
import os
from pathlib import Path

# 项目根目录
project_root = Path.cwd()

# 数据文件和资源文件配置 - 只包含运行时必需的文件
datas = [
    # 核心配置文件
    ('config.json', '.'),
    ('example_config.json', '.'),
    ('common/config.py', 'common/'),
    ('common/config/ozon_selectors_default.json', 'common/config/'),
    
    # 移除非必需的文档和规范文件以减小体积
    # ('docs', 'docs'),  # 开发时文档，运行时不需要
    # ('openspec', 'openspec'),  # 开发规范，运行时不需要
]

# 精简的隐藏导入 - 只保留运行时真正需要的模块
hiddenimports = [
    # 核心应用模块
    'cli.main',
    'cli.models', 
    'cli.task_controller',
    'cli.log_manager',
    'common.config',
    'common.logging_config',
    'common.task_control',
    
    # 业务逻辑模块
    'common.business.pricing_calculator',
    'common.business.profit_evaluator', 
    'common.business.source_matcher',
    'common.business.store_evaluator',
    
    # 爬虫模块
    'common.scrapers.ozon_scraper',
    'common.scrapers.seerfar_scraper',
    'common.scrapers.competitor_scraper',
    'common.scrapers.xuanping_browser_service',
    
    # RPA浏览器模块
    'rpa.browser.browser_service',
    
    # 核心依赖 - 只保留必需的
    'playwright.async_api',
    'openpyxl',
    'requests',
    'PIL.Image',
    
    # 系统模块
    'asyncio',
    'json',
    'pathlib',
    'tempfile',
    
    # 移除大型可选依赖
    # 'cv2',  # OpenCV - 如果图像处理不是核心功能可以移除
    # 'skimage',  # scikit-image - 大型库，按需加载
    # 'imagehash',  # 图像哈希 - 按需加载
    # 'numpy',  # NumPy - 如果不直接使用可以移除
]

# 扩展的排除模块 - 减少打包大小和启动时间
excludes = [
    # GUI 框架
    'tkinter',
    'PyQt5', 'PyQt6',
    'PySide2', 'PySide6',
    'wx',
    
    # 科学计算库（如果不需要）
    'matplotlib',
    'scipy',
    'sympy',
    'pandas',
    'seaborn',
    'plotly',
    
    # 开发工具
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
    'unittest',
    'doctest',
    'pdb',
    'cProfile',
    'profile',
    
    # 大型可选依赖
    'tensorflow',
    'torch',
    'transformers',
    'sklearn',
    'lightgbm',
    'xgboost',
    
    # 网络服务器
    'flask',
    'django',
    'fastapi',
    'tornado',
    
    # 数据库
    'sqlalchemy',
    'pymongo',
    'redis',
    
    # 其他大型库
    'babel',
    'jinja2',
    'markupsafe',
    'click',
]

# 二进制文件排除
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
    noarchive=False,  # 保持为 False 以获得更好的性能
)

# PYZ 配置 - Python 字节码归档
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE 配置 - 使用 onedir 模式提升启动速度
exe = EXE(
    pyz,
    a.scripts,
    [],  # 空列表表示使用 onedir 模式
    exclude_binaries=True,  # onedir 模式需要设置为 True
    name='ai-product-selector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用 UPX 压缩
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# COLLECT 配置 - onedir 模式必需
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ai-product-selector'
)

# 平台特定配置
if sys.platform == 'darwin':  # macOS
    # macOS 应用包配置 - 可选
    app = BUNDLE(
        coll,  # 注意这里使用 coll 而不是 exe
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
