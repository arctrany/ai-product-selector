#!/usr/bin/env python3
"""
Windows 兼容性检查和修复工具
检查并修复工作流引擎在 Windows 下的兼容性问题
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any
import json
import shutil

def check_platform():
    """检查当前平台"""
    system = platform.system()
    print(f"🖥️  当前操作系统: {system}")
    print(f"📋 系统版本: {platform.version()}")
    print(f"🏗️  架构: {platform.machine()}")
    return system

def check_python_version():
    """检查 Python 版本兼容性"""
    version = sys.version_info
    print(f"🐍 Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 版本过低，建议使用 Python 3.8+")
        return False
    else:
        print("✅ Python 版本兼容")
        return True

def check_path_separators():
    """检查路径分隔符使用"""
    issues = []
    
    # 检查硬编码的路径分隔符
    problematic_files = []
    
    # 扫描 Python 文件中的硬编码路径
    for root, dirs, files in os.walk('..'):
        # 跳过一些目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # 检查硬编码的 Unix 路径分隔符
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        # 跳过注释和字符串中的URL
                        if ('http://' in line or 'https://' in line or 
                            line.strip().startswith('#') or 
                            line.strip().startswith('"""') or
                            line.strip().startswith("'''")):
                            continue
                            
                        # 检查可能有问题的路径
                        if ('/' in line and 
                            not line.strip().startswith('from ') and
                            not line.strip().startswith('import ') and
                            '\\' not in line and
                            'os.path' not in line and
                            'Path(' not in line and
                            'pathlib' not in line):
                            
                            # 进一步检查是否真的是路径
                            if any(keyword in line for keyword in [
                                'dir', 'path', 'file', 'folder', 'directory',
                                '.json', '.txt', '.csv', '.xlsx', '.py'
                            ]):
                                problematic_files.append((file_path, i, line.strip()))
                                
                except Exception as e:
                    continue
    
    if problematic_files:
        print("⚠️  发现可能的路径兼容性问题:")
        for file_path, line_num, line in problematic_files[:10]:  # 只显示前10个
            print(f"   📁 {file_path}:{line_num} - {line[:80]}...")
        if len(problematic_files) > 10:
            print(f"   ... 还有 {len(problematic_files) - 10} 个问题")
        issues.extend(problematic_files)
    else:
        print("✅ 路径分隔符使用检查通过")
    
    return issues

def check_shell_scripts():
    """检查 shell 脚本兼容性"""
    issues = []
    
    # 查找 shell 脚本
    shell_scripts = []
    for root, dirs, files in os.walk('..'):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith(('.sh', '.bash')):
                shell_scripts.append(os.path.join(root, file))
    
    if shell_scripts:
        print("⚠️  发现 Shell 脚本，在 Windows 下可能无法直接运行:")
        for script in shell_scripts:
            print(f"   📜 {script}")
            issues.append(('shell_script', script))
        
        print("💡 建议:")
        print("   1. 使用 Git Bash 或 WSL 运行 shell 脚本")
        print("   2. 创建对应的 .bat 或 .ps1 脚本")
        print("   3. 使用 Python 脚本替代")
    else:
        print("✅ 未发现 shell 脚本")
    
    return issues

def check_file_permissions():
    """检查文件权限相关代码"""
    issues = []
    
    # 检查使用了 Unix 特定权限的代码
    permission_patterns = [
        'chmod', 'os.chmod', 'stat.S_I', 'os.access',
        'os.X_OK', 'os.R_OK', 'os.W_OK'
    ]
    
    problematic_files = []
    for root, dirs, files in os.walk('..'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern in permission_patterns:
                        if pattern in content:
                            problematic_files.append((file_path, pattern))
                            break
                            
                except Exception:
                    continue
    
    if problematic_files:
        print("⚠️  发现文件权限相关代码，可能在 Windows 下有兼容性问题:")
        for file_path, pattern in problematic_files:
            print(f"   📁 {file_path} - 使用了 {pattern}")
        issues.extend(problematic_files)
    else:
        print("✅ 文件权限检查通过")
    
    return issues

def check_environment_variables():
    """检查环境变量使用"""
    issues = []
    
    # 检查 Unix 特定的环境变量
    unix_env_vars = ['HOME', 'USER', 'SHELL', 'PWD']
    
    problematic_files = []
    for root, dirs, files in os.walk('..'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for env_var in unix_env_vars:
                        if f"'{env_var}'" in content or f'"{env_var}"' in content:
                            problematic_files.append((file_path, env_var))
                            
                except Exception:
                    continue
    
    if problematic_files:
        print("⚠️  发现 Unix 特定环境变量使用:")
        for file_path, env_var in problematic_files:
            print(f"   📁 {file_path} - 使用了 {env_var}")
        issues.extend(problematic_files)
    else:
        print("✅ 环境变量使用检查通过")
    
    return issues

def check_dependencies():
    """检查依赖包兼容性"""
    issues = []
    
    # 检查 requirements.txt
    req_files = ['requirements.txt', 'src_new/requirements.txt']
    
    for req_file in req_files:
        if os.path.exists(req_file):
            print(f"📦 检查依赖文件: {req_file}")
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    requirements = f.read()
                
                # 检查可能有 Windows 兼容性问题的包
                problematic_packages = [
                    'uvloop',  # Unix only
                    'fcntl',   # Unix only
                ]
                
                for package in problematic_packages:
                    if package in requirements:
                        print(f"   ⚠️  发现可能不兼容的包: {package}")
                        issues.append(('dependency', package))
                
                print(f"   ✅ 依赖文件检查完成")
                
            except Exception as e:
                print(f"   ❌ 读取依赖文件失败: {e}")
                issues.append(('dependency_read_error', req_file))
    
    return issues

def check_process_management():
    """检查进程管理代码"""
    issues = []
    
    # 检查 Unix 特定的进程管理
    unix_process_patterns = [
        'os.fork', 'os.kill', 'signal.SIGTERM', 'signal.SIGKILL',
        'subprocess.Popen.*shell=True', 'os.system'
    ]
    
    problematic_files = []
    for root, dirs, files in os.walk('..'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern in unix_process_patterns:
                        if pattern.replace('.*', '') in content:
                            problematic_files.append((file_path, pattern))
                            
                except Exception:
                    continue
    
    if problematic_files:
        print("⚠️  发现进程管理相关代码，可能在 Windows 下有兼容性问题:")
        for file_path, pattern in problematic_files:
            print(f"   📁 {file_path} - 使用了 {pattern}")
        issues.extend(problematic_files)
    else:
        print("✅ 进程管理检查通过")
    
    return issues

def create_windows_batch_files():
    """创建 Windows 批处理文件"""
    print("🔧 创建 Windows 兼容的启动脚本...")
    
    # 创建工作流服务器启动脚本
    batch_content = """@echo off
REM Workflow Engine Server Startup Script for Windows
echo Starting Workflow Engine Server...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Set environment variables
set PYTHONPATH=%CD%
set WORKFLOW_HOST=0.0.0.0
set WORKFLOW_PORT=8889

REM Start the server
echo Starting server on http://localhost:8889
python -m src_new.workflow_engine.api.server

pause
"""
    
    with open('start_workflow_server.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print("   ✅ 创建了 start_workflow_server.bat")
    
    # 创建环境检查脚本
    check_content = """@echo off
REM Environment Check Script for Windows
echo Checking environment...

echo.
echo Python Version:
python --version

echo.
echo Python Path:
python -c "import sys; print('\\n'.join(sys.path))"

echo.
echo Environment Variables:
echo PYTHONPATH=%PYTHONPATH%
echo PATH=%PATH%

echo.
echo Checking required packages...
python -c "
import sys
packages = ['fastapi', 'uvicorn', 'pathlib', 'asyncio']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} - OK')
    except ImportError:
        print(f'❌ {pkg} - Missing')
"

pause
"""
    
    with open('check_environment.bat', 'w', encoding='utf-8') as f:
        f.write(check_content)
    
    print("   ✅ 创建了 check_environment.bat")

def create_windows_fixes():
    """创建 Windows 兼容性修复"""
    print("🔧 创建 Windows 兼容性修复...")
    
    # 创建跨平台路径工具
    path_utils_content = '''"""
Windows 兼容性路径工具
提供跨平台的路径处理功能
"""

import os
import platform
from pathlib import Path
from typing import Union

def normalize_path(path: Union[str, Path]) -> Path:
    """标准化路径，确保跨平台兼容"""
    if isinstance(path, str):
        # 将 Unix 风格路径转换为当前平台路径
        path = path.replace('/', os.sep)
    return Path(path).resolve()

def ensure_directory(path: Union[str, Path]) -> Path:
    """确保目录存在，跨平台兼容"""
    path = normalize_path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_app_data_dir(app_name: str = "workflow_engine") -> Path:
    """获取应用数据目录，跨平台兼容"""
    system = platform.system().lower()
    
    if system == "windows":
        # Windows: %LOCALAPPDATA%\\AppName
        app_data = os.environ.get('LOCALAPPDATA')
        if not app_data:
            app_data = Path.home() / "AppData" / "Local"
        return Path(app_data) / app_name
        
    elif system == "darwin":  # macOS
        # macOS: ~/Library/Application Support/AppName
        return Path.home() / "Library" / "Application Support" / app_name
        
    else:  # Linux and other Unix-like systems
        # Linux: ~/.local/share/AppName
        xdg_data_home = os.environ.get('XDG_DATA_HOME')
        if xdg_data_home:
            return Path(xdg_data_home) / app_name
        else:
            return Path.home() / ".local" / "share" / app_name

def is_windows() -> bool:
    """检查是否为 Windows 系统"""
    return platform.system().lower() == "windows"

def get_executable_extension() -> str:
    """获取可执行文件扩展名"""
    return ".exe" if is_windows() else ""

def fix_command_for_windows(command: str) -> str:
    """修复命令以适配 Windows"""
    if is_windows():
        # 将 Unix 命令转换为 Windows 命令
        command_map = {
            'ls': 'dir',
            'cat': 'type',
            'rm': 'del',
            'cp': 'copy',
            'mv': 'move',
            'mkdir': 'mkdir',
            'rmdir': 'rmdir',
        }
        
        for unix_cmd, win_cmd in command_map.items():
            if command.startswith(unix_cmd + ' '):
                command = command.replace(unix_cmd + ' ', win_cmd + ' ', 1)
    
    return command
'''
    
    os.makedirs('../src_new/utils', exist_ok=True)
    with open('../src_new/utils/windows_compat.py', 'w', encoding='utf-8') as f:
        f.write(path_utils_content)
    
    print("   ✅ 创建了 Windows 兼容性工具模块")

def generate_compatibility_report(all_issues: List):
    """生成兼容性报告"""
    print("\n" + "="*80)
    print("📋 WINDOWS 兼容性检查报告")
    print("="*80)

    if not all_issues:
        print("🎉 恭喜！未发现 Windows 兼容性问题")
        print("✅ 您的工作流引擎应该可以在 Windows 下正常运行")
    else:
        print(f"⚠️  发现 {len(all_issues)} 个潜在的兼容性问题")

        # 按类型分组问题
        issue_groups = {}
        for issue in all_issues:
            if isinstance(issue, tuple) and len(issue) >= 2:
                issue_type, details = issue[0], issue[1]
            else:
                issue_type, details = 'unknown', str(issue)

            if issue_type not in issue_groups:
                issue_groups[issue_type] = []
            issue_groups[issue_type].append(details)
        
        print("\n📊 问题分类统计:")
        for issue_type, issues in issue_groups.items():
            print(f"   • {issue_type}: {len(issues)} 个问题")
        
        print("\n🔧 修复建议:")
        
        if 'shell_script' in issue_groups:
            print("   📜 Shell 脚本问题:")
            print("      - 使用 Git Bash 或 WSL 运行 .sh 脚本")
            print("      - 使用创建的 .bat 文件替代")
            print("      - 考虑将脚本逻辑移植到 Python")
        
        if 'dependency' in issue_groups:
            print("   📦 依赖包问题:")
            print("      - 检查包的 Windows 兼容性")
            print("      - 使用条件导入处理平台特定包")
            print("      - 寻找跨平台替代方案")
        
        if any('path' in str(issue) for issue in all_issues):
            print("   📁 路径问题:")
            print("      - 使用 pathlib.Path 而不是字符串拼接")
            print("      - 使用 os.path.join() 或 Path() / 操作符")
            print("      - 避免硬编码路径分隔符")
        
        print("\n💡 通用建议:")
        print("   1. 使用 pathlib.Path 处理所有路径操作")
        print("   2. 使用 platform.system() 检测操作系统")
        print("   3. 为平台特定功能提供条件实现")
        print("   4. 测试时使用 Windows 虚拟机或 WSL")
    
    print("\n🚀 快速启动 (Windows):")
    print("   1. 双击运行 start_workflow_server.bat")
    print("   2. 或在命令提示符中运行:")
    print("      python -m src_new.workflow_engine.api.server")
    print("   3. 访问 http://localhost:8889")

def main():
    """主函数"""
    print("🔍 Windows 兼容性检查工具")
    print("="*60)
    
    # 检查当前平台
    current_system = check_platform()
    print()
    
    # 检查 Python 版本
    if not check_python_version():
        return
    print()
    
    all_issues = []
    
    # 执行各项检查
    print("🔍 开始兼容性检查...")
    print("-" * 40)
    
    all_issues.extend(check_path_separators())
    print()
    
    all_issues.extend(check_shell_scripts())
    print()
    
    all_issues.extend(check_file_permissions())
    print()
    
    all_issues.extend(check_environment_variables())
    print()
    
    all_issues.extend(check_dependencies())
    print()
    
    all_issues.extend(check_process_management())
    print()
    
    # 创建 Windows 兼容性文件
    if current_system == "Windows" or True:  # 总是创建，以备将来使用
        create_windows_batch_files()
        print()
        
        create_windows_fixes()
        print()
    
    # 生成报告
    generate_compatibility_report(all_issues)

if __name__ == "__main__":
    main()