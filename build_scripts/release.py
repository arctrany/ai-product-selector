#!/usr/bin/env python3
"""
AI选品自动化系统 - 发布管理脚本
自动化构建、打包和分发流程
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ReleaseManager:
    """发布管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.packaging_dir = self.project_root / "packaging"
        self.dist_dir = self.project_root / "dist"
        self.version_file = self.project_root / "version.json"
        
    def get_version_info(self) -> Dict:
        """获取版本信息"""
        if self.version_file.exists():
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认版本信息
            return {
                "version": "1.0.0",
                "build": 1,
                "release_date": datetime.now().isoformat(),
                "description": "AI选品自动化系统"
            }
    
    def update_version(self, version: Optional[str] = None, increment_build: bool = True) -> Dict:
        """更新版本信息"""
        version_info = self.get_version_info()
        
        if version:
            version_info["version"] = version
        
        if increment_build:
            version_info["build"] = version_info.get("build", 0) + 1
        
        version_info["release_date"] = datetime.now().isoformat()
        
        # 保存版本信息
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=2, ensure_ascii=False)
        
        return version_info
    
    def create_version_file_for_build(self, version_info: Dict):
        """为构建创建版本信息文件"""
        version_py_content = f'''"""
AI选品自动化系统版本信息
自动生成，请勿手动修改
"""

VERSION = "{version_info['version']}"
BUILD = {version_info['build']}
RELEASE_DATE = "{version_info['release_date']}"
DESCRIPTION = "{version_info['description']}"

def get_version_string():
    """获取完整版本字符串"""
    return f"{{VERSION}}.{{BUILD}}"

def get_full_version_info():
    """获取完整版本信息"""
    return {{
        "version": VERSION,
        "build": BUILD,
        "release_date": RELEASE_DATE,
        "description": DESCRIPTION,
        "full_version": get_version_string()
    }}
'''
        
        version_py_path = self.project_root / "version.py"
        with open(version_py_path, 'w', encoding='utf-8') as f:
            f.write(version_py_content)
        
        return version_py_path
    
    def run_build_script(self, platform: str = "auto", debug: bool = False) -> bool:
        """运行构建脚本"""
        print(f"🔨 开始构建 ({platform} 平台)...")
        
        try:
            if platform == "auto":
                # 自动检测平台并使用 Python 构建脚本
                build_script = self.packaging_dir / "build.py"
                cmd = [sys.executable, str(build_script)]
            elif platform == "windows":
                build_script = self.packaging_dir / "build-windows.bat"
                cmd = [str(build_script)]
            elif platform == "macos":
                build_script = self.packaging_dir / "build-macos.sh"
                cmd = ["bash", str(build_script)]
            elif platform == "linux":
                build_script = self.packaging_dir / "build-linux.sh"
                cmd = ["bash", str(build_script)]
            else:
                raise ValueError(f"不支持的平台: {platform}")
            
            if debug:
                cmd.append("--debug")
            
            # 执行构建
            result = subprocess.run(cmd, cwd=self.project_root, check=True)
            print("✅ 构建完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 构建失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 构建错误: {e}")
            return False
    
    def create_release_notes(self, version_info: Dict) -> Path:
        """创建发布说明"""
        release_notes_content = f"""# AI选品自动化系统 v{version_info['version']}.{version_info['build']}

## 发布信息
- **版本**: {version_info['version']}.{version_info['build']}
- **发布日期**: {datetime.fromisoformat(version_info['release_date']).strftime('%Y-%m-%d %H:%M:%S')}
- **描述**: {version_info['description']}

## 新增功能
- ✅ PyInstaller 单文件打包支持
- ✅ 跨平台构建 (Windows/macOS/Linux)
- ✅ 自动依赖管理和 Playwright 浏览器安装
- ✅ 资源文件路径自动处理
- ✅ 完整的构建和分发流程

## 系统要求
- **Windows**: Windows 10/11 (x64/ARM64)
- **macOS**: macOS 10.15+ (Intel/Apple Silicon)
- **Linux**: Ubuntu 18.04+, CentOS 7+, 或其他主流发行版

## 安装方法

### 1. 下载预编译版本
从 Releases 页面下载对应平台的压缩包，解压后即可使用。

### 2. 从源码构建
```bash
# 克隆仓库
git clone <repository-url>
cd ai-product-selector3

# 安装依赖
pip install -r requirements.txt

# 构建 (自动检测平台)
python packaging/build.py

# 或使用平台特定脚本
# Windows: packaging/build-windows.bat
# macOS: bash packaging/build-macos.sh  
# Linux: bash packaging/build-linux.sh
```

## 使用方法

### 基本用法
```bash
# 查看帮助
./ai-product-selector --help

# 启动任务
./ai-product-selector start --data user_data.json --config user_config.json

# 查看状态
./ai-product-selector status
```

### 配置文件
1. 复制 `example_config.json` 为 `user_config.json`
2. 根据需要修改配置参数
3. 准备用户数据文件 `user_data.json`

## 技术架构
- **核心框架**: Python 3.8+
- **浏览器自动化**: Playwright
- **Excel 处理**: openpyxl
- **图像处理**: PIL, OpenCV, scikit-image
- **打包工具**: PyInstaller
- **支持平台**: Windows, macOS, Linux

## 故障排除

### 常见问题
1. **浏览器启动失败**: 运行 `playwright install chromium`
2. **权限错误**: 确保可执行文件有执行权限
3. **依赖缺失**: 检查系统是否安装必要的运行库

### 获取帮助
- 查看 README.txt 文件
- 运行 `./ai-product-selector --help` 查看命令帮助
- 检查日志文件获取详细错误信息

---
*构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        release_notes_path = self.dist_dir / f"RELEASE_NOTES_v{version_info['version']}.{version_info['build']}.txt"
        self.dist_dir.mkdir(exist_ok=True)
        
        with open(release_notes_path, 'w', encoding='utf-8') as f:
            f.write(release_notes_content)
        
        return release_notes_path
    
    def create_checksums(self, files: List[Path]) -> Path:
        """创建校验和文件"""
        import hashlib
        
        checksums_content = []
        checksums_content.append("# AI选品自动化系统 - 文件校验和")
        checksums_content.append(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        checksums_content.append("")
        
        for file_path in files:
            if file_path.exists() and file_path.is_file():
                # 计算 SHA256 校验和
                sha256_hash = hashlib.sha256()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)
                
                checksum = sha256_hash.hexdigest()
                file_size = file_path.stat().st_size
                
                checksums_content.append(f"{checksum}  {file_path.name}  ({file_size} bytes)")
        
        checksums_path = self.dist_dir / "checksums.txt"
        with open(checksums_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(checksums_content))
        
        return checksums_path
    
    def collect_build_artifacts(self) -> List[Path]:
        """收集构建产物"""
        artifacts = []
        
        if self.dist_dir.exists():
            # 查找压缩包文件
            for pattern in ["*.zip", "*.tar.gz", "*.tgz"]:
                artifacts.extend(self.dist_dir.glob(pattern))
            
            # 查找可执行文件目录
            for item in self.dist_dir.iterdir():
                if item.is_dir() and item.name.startswith("ai-product-selector-"):
                    artifacts.append(item)
        
        return artifacts
    
    def create_release_package(self, version_info: Dict, include_source: bool = False) -> Path:
        """创建完整的发布包"""
        version_string = f"{version_info['version']}.{version_info['build']}"
        release_package_name = f"ai-product-selector-release-{version_string}"
        release_package_dir = self.dist_dir / release_package_name
        
        # 清理并创建发布包目录
        if release_package_dir.exists():
            shutil.rmtree(release_package_dir)
        release_package_dir.mkdir(parents=True)
        
        # 收集构建产物
        artifacts = self.collect_build_artifacts()
        
        # 复制构建产物
        for artifact in artifacts:
            if artifact.is_file():
                shutil.copy2(artifact, release_package_dir / artifact.name)
            elif artifact.is_dir():
                shutil.copytree(artifact, release_package_dir / artifact.name)
        
        # 创建发布说明
        release_notes = self.create_release_notes(version_info)
        shutil.copy2(release_notes, release_package_dir / "RELEASE_NOTES.txt")
        
        # 创建校验和文件
        package_files = list(release_package_dir.glob("*"))
        checksums = self.create_checksums(package_files)
        
        # 复制重要文档
        docs_to_copy = [
            "README.md",
            "LICENSE",
            "requirements.txt"
        ]
        
        for doc_file in docs_to_copy:
            src_path = self.project_root / doc_file
            if src_path.exists():
                shutil.copy2(src_path, release_package_dir / doc_file)
        
        # 包含源码（可选）
        if include_source:
            source_dir = release_package_dir / "source"
            source_dir.mkdir()
            
            # 复制源码文件
            source_patterns = ["*.py", "*.json", "*.md", "*.txt", "*.spec"]
            for pattern in source_patterns:
                for src_file in self.project_root.glob(pattern):
                    shutil.copy2(src_file, source_dir / src_file.name)
            
            # 复制源码目录
            source_dirs = ["cli", "common", "rpa", "utils", "packaging"]
            for src_dir_name in source_dirs:
                src_dir = self.project_root / src_dir_name
                if src_dir.exists():
                    shutil.copytree(src_dir, source_dir / src_dir_name)
        
        # 创建最终压缩包
        final_archive = self.dist_dir / f"{release_package_name}.zip"
        shutil.make_archive(str(final_archive.with_suffix('')), 'zip', self.dist_dir, release_package_name)
        
        print(f"📦 发布包已创建: {final_archive}")
        return final_archive
    
    def release(self, version: Optional[str] = None, platform: str = "auto", 
                debug: bool = False, include_source: bool = False) -> bool:
        """执行完整发布流程"""
        try:
            print("🚀 开始发布流程...")
            
            # 更新版本信息
            version_info = self.update_version(version)
            print(f"📋 版本信息: v{version_info['version']}.{version_info['build']}")
            
            # 创建构建版本文件
            version_py = self.create_version_file_for_build(version_info)
            print(f"✅ 版本文件已创建: {version_py}")
            
            # 执行构建
            if not self.run_build_script(platform, debug):
                return False
            
            # 创建发布包
            release_package = self.create_release_package(version_info, include_source)
            
            # 清理临时文件
            if version_py.exists():
                version_py.unlink()
            
            print("🎉 发布流程完成！")
            print(f"📦 发布包: {release_package}")
            
            # 显示构建产物
            artifacts = self.collect_build_artifacts()
            if artifacts:
                print("\n📋 构建产物:")
                for artifact in artifacts:
                    if artifact.is_file():
                        size_mb = artifact.stat().st_size / (1024 * 1024)
                        print(f"   📄 {artifact.name} ({size_mb:.1f} MB)")
                    else:
                        print(f"   📁 {artifact.name}/")
            
            return True
            
        except Exception as e:
            print(f"❌ 发布失败: {e}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI选品自动化系统发布管理")
    parser.add_argument("--version", help="指定版本号 (如: 1.0.0)")
    parser.add_argument("--platform", choices=["auto", "windows", "macos", "linux"], 
                       default="auto", help="目标平台")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--include-source", action="store_true", help="包含源码")
    parser.add_argument("--build-only", action="store_true", help="仅构建，不创建发布包")
    
    args = parser.parse_args()
    
    manager = ReleaseManager()
    
    if args.build_only:
        # 仅构建
        success = manager.run_build_script(args.platform, args.debug)
    else:
        # 完整发布流程
        success = manager.release(
            version=args.version,
            platform=args.platform,
            debug=args.debug,
            include_source=args.include_source
        )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
