#!/usr/bin/env python3
"""
PyInstaller 资源路径处理工具
解决打包后资源文件访问路径问题
"""

import os
import sys
from pathlib import Path
from typing import Union, Optional

def get_resource_path(relative_path: Union[str, Path]) -> Path:
    """
    获取资源文件的正确路径
    
    在开发环境中，返回相对于项目根目录的路径
    在 PyInstaller 打包环境中，返回临时目录中的资源路径
    
    Args:
        relative_path: 相对于项目根目录的资源文件路径
        
    Returns:
        Path: 资源文件的绝对路径
        
    Example:
        >>> config_path = get_resource_path("config.json")
        >>> selectors_path = get_resource_path("common/config/ozon_selectors_default.json")
    """
    relative_path = Path(relative_path)
    
    # 检查是否在 PyInstaller 打包环境中
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包环境：使用临时目录
        base_path = Path(sys._MEIPASS)
        resource_path = base_path / relative_path
        
        # 如果资源文件不存在，尝试在当前工作目录查找
        if not resource_path.exists():
            fallback_path = Path.cwd() / relative_path
            if fallback_path.exists():
                return fallback_path
                
        return resource_path
    else:
        # 开发环境：使用项目根目录
        # 尝试从当前文件位置推断项目根目录
        current_file = Path(__file__).resolve()
        
        # 向上查找项目根目录（包含 cli/main.py 的目录）
        project_root = None
        for parent in current_file.parents:
            if (parent / "cli" / "main.py").exists():
                project_root = parent
                break
        
        if project_root is None:
            # 如果找不到项目根目录，使用当前工作目录
            project_root = Path.cwd()
            
        resource_path = project_root / relative_path
        return resource_path

def ensure_resource_exists(relative_path: Union[str, Path]) -> Optional[Path]:
    """
    确保资源文件存在，如果不存在返回 None
    
    Args:
        relative_path: 相对于项目根目录的资源文件路径
        
    Returns:
        Optional[Path]: 如果文件存在返回路径，否则返回 None
    """
    resource_path = get_resource_path(relative_path)
    
    if resource_path.exists():
        return resource_path
    else:
        return None

def get_config_path(config_name: str = "config.json") -> Path:
    """
    获取配置文件路径
    
    Args:
        config_name: 配置文件名，默认为 "config.json"
        
    Returns:
        Path: 配置文件路径
    """
    return get_resource_path(config_name)

def get_selectors_config_path(selector_file: str = "ozon_selectors_default.json") -> Path:
    """
    获取选择器配置文件路径
    
    Args:
        selector_file: 选择器配置文件名
        
    Returns:
        Path: 选择器配置文件路径
    """
    return get_resource_path(f"common/config/{selector_file}")

def get_data_directory() -> Path:
    """
    获取数据目录路径
    
    在开发环境中，返回项目根目录
    在打包环境中，返回可执行文件所在目录
    
    Returns:
        Path: 数据目录路径
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包环境：使用可执行文件所在目录
        if hasattr(sys, 'executable'):
            return Path(sys.executable).parent
        else:
            return Path.cwd()
    else:
        # 开发环境：使用项目根目录
        current_file = Path(__file__).resolve()
        
        # 向上查找项目根目录
        for parent in current_file.parents:
            if (parent / "cli" / "main.py").exists():
                return parent
                
        return Path.cwd()

def get_output_directory(output_path: Optional[str] = None) -> Path:
    """
    获取输出目录路径
    
    Args:
        output_path: 用户指定的输出路径，如果为 None 则使用默认路径
        
    Returns:
        Path: 输出目录路径
    """
    if output_path:
        output_dir = Path(output_path)
        if output_dir.is_absolute():
            return output_dir
        else:
            # 相对路径：相对于数据目录
            return get_data_directory() / output_dir
    else:
        # 默认输出目录：数据目录下的 output 文件夹
        return get_data_directory() / "output"

def create_user_config_template(target_path: Optional[Path] = None) -> Path:
    """
    创建用户配置文件模板
    
    Args:
        target_path: 目标路径，如果为 None 则使用数据目录
        
    Returns:
        Path: 创建的配置文件路径
    """
    if target_path is None:
        target_path = get_data_directory() / "user_config.json"
    
    # 读取示例配置文件
    example_config_path = ensure_resource_exists("example_config.json")
    
    if example_config_path and example_config_path.exists():
        # 复制示例配置文件
        import shutil
        shutil.copy2(example_config_path, target_path)
        return target_path
    else:
        # 创建基本配置文件
        import json
        
        basic_config = {
            "scraping": {
                "browser_type": "chrome",
                "headless": False,
                "timeout_seconds": 30
            },
            "performance": {
                "max_concurrent_tasks": 5,
                "retry_count": 3
            }
        }
        
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(basic_config, f, indent=2, ensure_ascii=False)
            
        return target_path

def list_available_resources() -> dict:
    """
    列出所有可用的资源文件
    
    Returns:
        dict: 资源文件信息
    """
    resources = {
        "config_files": [],
        "selector_files": [],
        "docs": [],
        "other": []
    }
    
    # 配置文件
    config_files = ["config.json", "example_config.json", "test_system_config.json", "test_user_data.json"]
    for config_file in config_files:
        path = ensure_resource_exists(config_file)
        if path:
            resources["config_files"].append({
                "name": config_file,
                "path": str(path),
                "exists": True
            })
    
    # 选择器配置文件
    selector_files = ["ozon_selectors_default.json"]
    for selector_file in selector_files:
        path = ensure_resource_exists(f"common/config/{selector_file}")
        if path:
            resources["selector_files"].append({
                "name": selector_file,
                "path": str(path),
                "exists": True
            })
    
    # 文档文件
    docs_path = ensure_resource_exists("docs")
    if docs_path and docs_path.is_dir():
        for doc_file in docs_path.rglob("*.md"):
            resources["docs"].append({
                "name": doc_file.name,
                "path": str(doc_file),
                "relative_path": str(doc_file.relative_to(docs_path))
            })
    
    return resources

def validate_packaging_resources() -> dict:
    """
    验证打包资源的完整性
    
    Returns:
        dict: 验证结果
    """
    validation_result = {
        "success": True,
        "missing_files": [],
        "found_files": [],
        "warnings": []
    }
    
    # 必需的资源文件
    required_files = [
        "config.json",
        "example_config.json",
        "common/config/ozon_selectors_default.json"
    ]
    
    for file_path in required_files:
        resource_path = ensure_resource_exists(file_path)
        if resource_path:
            validation_result["found_files"].append(file_path)
        else:
            validation_result["missing_files"].append(file_path)
            validation_result["success"] = False
    
    # 可选的资源文件
    optional_files = [
        "test_system_config.json",
        "test_user_data.json"
    ]
    
    for file_path in optional_files:
        resource_path = ensure_resource_exists(file_path)
        if not resource_path:
            validation_result["warnings"].append(f"可选文件缺失: {file_path}")
    
    # 检查文档目录
    docs_path = ensure_resource_exists("docs")
    if not docs_path:
        validation_result["warnings"].append("文档目录缺失: docs/")
    
    return validation_result

if __name__ == "__main__":
    """测试资源路径处理功能"""
    print("🔍 资源路径处理工具测试")
    print("=" * 50)
    
    # 测试基本路径获取
    print("📁 基本路径测试:")
    print(f"   项目根目录: {get_data_directory()}")
    print(f"   配置文件: {get_config_path()}")
    print(f"   选择器配置: {get_selectors_config_path()}")
    print()
    
    # 测试资源文件存在性
    print("📋 资源文件验证:")
    validation = validate_packaging_resources()
    
    if validation["success"]:
        print("✅ 所有必需资源文件都存在")
    else:
        print("❌ 缺少必需资源文件:")
        for missing_file in validation["missing_files"]:
            print(f"   - {missing_file}")
    
    if validation["warnings"]:
        print("⚠️ 警告:")
        for warning in validation["warnings"]:
            print(f"   - {warning}")
    
    print(f"\n✅ 找到的文件: {len(validation['found_files'])}")
    for found_file in validation["found_files"]:
        print(f"   - {found_file}")
    
    # 列出所有可用资源
    print("\n📚 可用资源文件:")
    resources = list_available_resources()
    
    for category, files in resources.items():
        if files:
            print(f"   {category}:")
            for file_info in files:
                print(f"     - {file_info['name']}")
