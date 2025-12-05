#!/usr/bin/env python3
"""
AI选品自动化系统 - 跨平台构建脚本
支持 Windows、macOS、Linux 平台的 PyInstaller 打包
"""

import os
import sys
import platform
import subprocess
import shutil
import argparse
from pathlib import Path
import json

class BuildManager:
    """构建管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.build_dir = self.project_root / "dist"
        self.spec_file = self.project_root / "build.spec"
        self.requirements_file = self.project_root / "requirements.txt"
        
    def get_platform_info(self):
        """获取平台信息"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        platform_map = {
            'windows': 'win',
            'darwin': 'macos',
            'linux': 'linux'
        }
        
        arch_map = {
            'x86_64': 'x64',
            'amd64': 'x64',
            'arm64': 'arm64',
            'aarch64': 'arm64',
            'i386': 'x86',
            'i686': 'x86'
        }
        
        platform_name = platform_map.get(system, system)
        arch_name = arch_map.get(machine, machine)
        
        return platform_name, arch_name, f"{platform_name}-{arch_name}"
    
    def check_dependencies(self):
        """检查构建依赖"""
        print("🔍 检查构建依赖...")
        
        # 检查 Python 版本
        python_version = sys.version_info
        if python_version < (3, 8):
            raise RuntimeError(f"需要 Python 3.8+，当前版本: {python_version.major}.{python_version.minor}")
        print(f"✓ Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查必需文件
        required_files = [
            self.spec_file,
            self.requirements_file,
            self.project_root / "cli" / "main.py"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                raise FileNotFoundError(f"缺少必需文件: {file_path}")
            print(f"✓ 找到文件: {file_path.name}")
    
    def install_dependencies(self, force_reinstall=False):
        """安装项目依赖"""
        print("📦 安装项目依赖...")
        
        # 安装 Python 依赖
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)]
        if force_reinstall:
            cmd.append("--force-reinstall")
        
        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print("✓ Python 依赖安装完成")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"安装 Python 依赖失败: {e}")
        
        # 安装 Playwright 浏览器
        print("🌐 安装 Playwright 浏览器...")
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                         check=True, cwd=self.project_root)
            print("✓ Playwright 浏览器安装完成")
        except subprocess.CalledProcessError as e:
            print(f"⚠ Playwright 浏览器安装失败: {e}")
            print("  请手动运行: playwright install chromium")
    
    def clean_build(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        
        dirs_to_clean = [
            self.build_dir,
            self.project_root / "build",
            self.project_root / "__pycache__"
        ]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"✓ 清理目录: {dir_path}")
    
    def run_pyinstaller(self, debug=False):
        """运行 PyInstaller 构建"""
        print("🔨 开始 PyInstaller 构建...")
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            str(self.spec_file),
            "--clean",
            "--noconfirm"
        ]
        
        if debug:
            cmd.extend(["--debug", "all"])
        
        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print("✓ PyInstaller 构建完成")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PyInstaller 构建失败: {e}")
    
    def create_distribution_package(self, platform_tag):
        """创建分发包"""
        print("📦 创建分发包...")
        
        # 确定可执行文件路径
        platform_name, arch_name, _ = self.get_platform_info()
        
        if platform_name == "win":
            exe_name = "ai-product-selector.exe"
        elif platform_name == "macos":
            exe_name = "AI Product Selector.app"
        else:
            exe_name = "ai-product-selector"
        
        exe_path = self.build_dir / exe_name
        
        if not exe_path.exists():
            raise FileNotFoundError(f"构建的可执行文件不存在: {exe_path}")
        
        # 创建分发目录
        dist_name = f"ai-product-selector-{platform_tag}"
        dist_dir = self.build_dir / dist_name
        dist_dir.mkdir(exist_ok=True)
        
        # 复制可执行文件
        if platform_name == "macos" and exe_path.is_dir():
            # macOS 应用包
            shutil.copytree(exe_path, dist_dir / exe_name)
        else:
            # 单文件可执行程序
            shutil.copy2(exe_path, dist_dir / exe_name)
        
        # 复制必要的配置文件
        config_files = [
            "config.json",
            "example_config.json"
        ]
        
        for config_file in config_files:
            src_path = self.project_root / config_file
            if src_path.exists():
                shutil.copy2(src_path, dist_dir / config_file)
        
        # 创建使用说明
        readme_content = f"""# AI选品自动化系统

## 使用方法

### 1. 准备配置文件
复制 `example_config.json` 为 `user_config.json` 并根据需要修改配置。

### 2. 运行程序
"""
        
        if platform_name == "win":
            readme_content += """
```cmd
ai-product-selector.exe start --data user_data.json --config user_config.json
```
"""
        elif platform_name == "macos":
            readme_content += """
```bash
./AI\\ Product\\ Selector.app/Contents/MacOS/ai-product-selector start --data user_data.json --config user_config.json
```

或者双击应用图标启动。
"""
        else:
            readme_content += """
```bash
./ai-product-selector start --data user_data.json --config user_config.json
```
"""
        
        readme_content += """
### 3. 查看帮助
"""
        
        if platform_name == "win":
            readme_content += "```cmd\nai-product-selector.exe --help\n```"
        elif platform_name == "macos":
            readme_content += "```bash\n./AI\\ Product\\ Selector.app/Contents/MacOS/ai-product-selector --help\n```"
        else:
            readme_content += "```bash\n./ai-product-selector --help\n```"
        
        readme_content += f"""

## 系统要求
- 操作系统: {platform.system()} {platform.release()}
- 架构: {platform.machine()}

## 版本信息
- 构建时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 平台标签: {platform_tag}
"""
        
        with open(dist_dir / "README.txt", "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        # 创建压缩包
        if platform_name == "win":
            archive_format = "zip"
        else:
            archive_format = "gztar"
        
        archive_path = self.build_dir / f"{dist_name}.{'zip' if archive_format == 'zip' else 'tar.gz'}"
        shutil.make_archive(str(archive_path.with_suffix('')), archive_format, self.build_dir, dist_name)
        
        print(f"✓ 分发包已创建: {archive_path}")
        return archive_path
    
    def build(self, clean=True, debug=False, force_reinstall=False):
        """执行完整构建流程"""
        try:
            platform_name, arch_name, platform_tag = self.get_platform_info()
            print(f"🚀 开始构建 AI选品自动化系统 ({platform_tag})")
            
            # 检查依赖
            self.check_dependencies()
            
            # 安装依赖
            self.install_dependencies(force_reinstall)
            
            # 清理构建目录
            if clean:
                self.clean_build()
            
            # 运行 PyInstaller
            self.run_pyinstaller(debug)
            
            # 创建分发包
            archive_path = self.create_distribution_package(platform_tag)
            
            print(f"🎉 构建成功完成!")
            print(f"📦 分发包: {archive_path}")
            print(f"📁 构建目录: {self.build_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ 构建失败: {e}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI选品自动化系统构建脚本")
    parser.add_argument("--no-clean", action="store_true", help="不清理构建目录")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--force-reinstall", action="store_true", help="强制重新安装依赖")
    
    args = parser.parse_args()
    
    builder = BuildManager()
    success = builder.build(
        clean=not args.no_clean,
        debug=args.debug,
        force_reinstall=args.force_reinstall
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
