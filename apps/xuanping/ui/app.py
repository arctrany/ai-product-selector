"""
智能选品系统应用程序入口

检测到GUI兼容性问题，自动重定向到CLI版本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    """主函数 - 重定向到CLI版本"""
    print("智能选品系统")
    print("=" * 50)
    print("检测到GUI兼容性问题，正在启动命令行界面版本...")
    print()
    
    try:
        from apps.xuanping.cli.cli_app import XuanpingCLI
        
        # 创建并运行CLI应用
        app = XuanpingCLI()
        app.run()
        
    except ImportError as e:
        print(f"导入CLI模块失败: {e}")
        print("请确保所有依赖模块都已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"启动CLI应用失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()