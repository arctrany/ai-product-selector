#!/usr/bin/env python3
"""
智能选品系统命令行控制工具

支持命令行方式控制任务的启动、暂停、取消、恢复，以及配置管理、进度和日志查看

使用方式:
    python xp_cli.py start --config config.json    # 启动任务
    python xp_cli.py pause                         # 暂停任务
    python xp_cli.py resume                        # 恢复任务
    python xp_cli.py stop                          # 停止任务
    python xp_cli.py status                        # 查看状态
    python xp_cli.py config list                   # 列出配置
    python xp_cli.py config set key=value          # 设置配置
    python xp_cli.py logs                          # 查看日志
    python xp_cli.py progress                      # 查看进度
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__)
sys.path.insert(0, str(project_root))

try:
    from cli import UIConfig, AppState, ui_state_manager
    from cli import task_controller
    from cli import log_manager
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块都已正确安装")
    sys.exit(1)


class XuanpingCLIController:
    """智能选品系统命令行控制器"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".xp" / "configs"
        self.config_file = self.config_dir / "last_config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self, config_path: Optional[str] = None) -> UIConfig:
        """加载配置"""
        if config_path and Path(config_path).exists():
            return UIConfig.from_config_file(config_path)
        elif self.config_file.exists():
            return UIConfig.from_config_file(str(self.config_file))
        else:
            return UIConfig()
    
    def save_config(self, config: UIConfig):
        """保存配置"""
        config.save_to_file(str(self.config_file))
    
    def start_task(self, config_path: Optional[str] = None) -> bool:
        """启动任务"""
        try:
            config = self.load_config(config_path)
            
            # 验证配置
            if not config.good_shop_file:
                print("❌ 错误: 请先设置好店模版文件")
                return False
            
            if not config.output_path:
                print("❌ 错误: 请先设置输出路径")
                return False
            
            if not Path(config.good_shop_file).exists():
                print(f"❌ 错误: 好店模版文件不存在: {config.good_shop_file}")
                return False
            
            if not Path(config.output_path).exists():
                print(f"❌ 错误: 输出路径不存在: {config.output_path}")
                return False
            
            # 启动任务
            success = task_controller.start_task(config)
            if success:
                print("✅ 任务已启动")
                self.save_config(config)
                return True
            else:
                print("❌ 任务启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 启动任务时出错: {e}")
            return False
    
    def pause_task(self) -> bool:
        """暂停任务"""
        try:
            success = task_controller.pause_task()
            if success:
                print("✅ 任务已暂停")
                return True
            else:
                print("❌ 任务暂停失败")
                return False
        except Exception as e:
            print(f"❌ 暂停任务时出错: {e}")
            return False
    
    def resume_task(self) -> bool:
        """恢复任务"""
        try:
            success = task_controller.resume_task()
            if success:
                print("✅ 任务已恢复")
                return True
            else:
                print("❌ 任务恢复失败")
                return False
        except Exception as e:
            print(f"❌ 恢复任务时出错: {e}")
            return False
    
    def stop_task(self) -> bool:
        """停止任务"""
        try:
            success = task_controller.stop_task()
            if success:
                print("✅ 任务已停止")
                return True
            else:
                print("❌ 任务停止失败")
                return False
        except Exception as e:
            print(f"❌ 停止任务时出错: {e}")
            return False
    
    def show_status(self):
        """显示任务状态"""
        try:
            state = ui_state_manager.state
            progress = ui_state_manager.progress
            
            state_text = {
                AppState.IDLE: "等待开始",
                AppState.RUNNING: "运行中",
                AppState.PAUSED: "已暂停",
                AppState.STOPPING: "正在停止",
                AppState.COMPLETED: "已完成",
                AppState.ERROR: "出错"
            }.get(state, "未知")
            
            print(f"📊 任务状态: {state_text}")
            print(f"📈 进度: {progress.processed_stores}/{progress.total_stores} 店铺")
            print(f"⏱️  耗时: {getattr(progress, 'elapsed_time', 0):.1f}秒")
            
            if progress.current_store:
                print(f"🏪 当前店铺: {progress.current_store}")
            
            error_msg = getattr(progress, 'error_message', None)
            if error_msg:
                print(f"❌ 错误信息: {error_msg}")
                
        except Exception as e:
            print(f"❌ 获取状态时出错: {e}")
    
    def show_progress(self):
        """显示详细进度"""
        try:
            progress = ui_state_manager.progress
            
            print("📈 详细进度信息:")
            print(f"  当前步骤: {progress.current_step}")
            print(f"  总店铺数: {progress.total_stores}")
            print(f"  已处理: {progress.processed_stores}")
            print(f"  好店数量: {progress.good_stores}")
            print(f"  进度: {progress.percentage:.1f}%" if hasattr(progress, 'percentage') else f"  进度: {progress.processed_stores/progress.total_stores*100:.1f}%" if progress.total_stores > 0 else "  进度: 0%")
            print(f"  步骤耗时: {progress.step_duration:.1f}秒" if hasattr(progress, 'step_duration') else "  步骤耗时: 0.0秒")
            
            if progress.current_store:
                print(f"  当前店铺: {progress.current_store}")
                
        except Exception as e:
            print(f"❌ 获取进度时出错: {e}")
    
    def show_logs(self, lines: int = 50):
        """显示日志"""
        try:
            # 从ui_state_manager获取日志
            all_logs = ui_state_manager.logs
            logs = all_logs[-lines:] if len(all_logs) > lines else all_logs
            
            print(f"📝 最近 {len(logs)} 条日志:")
            print("-" * 80)
            
            for log_entry in logs:
                timestamp = log_entry.get('timestamp', '')
                level = log_entry.get('level', 'INFO')
                message = log_entry.get('message', '')
                
                level_icon = {
                    'DEBUG': '🔍',
                    'INFO': 'ℹ️',
                    'WARNING': '⚠️',
                    'ERROR': '❌',
                    'CRITICAL': '🚨'
                }.get(level, 'ℹ️')
                
                print(f"{level_icon} [{timestamp}] {level}: {message}")
                
        except Exception as e:
            print(f"❌ 获取日志时出错: {e}")
    
    def list_configs(self):
        """列出配置"""
        try:
            config = self.load_config()
            config_dict = config.to_dict()
            
            print("⚙️ 当前配置:")
            print("-" * 50)
            
            for key, value in config_dict.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            print(f"❌ 获取配置时出错: {e}")
    
    def set_config(self, key: str, value: str):
        """设置配置项"""
        try:
            config = self.load_config()
            config_dict = config.to_dict()
            
            if key not in config_dict:
                print(f"❌ 未知的配置项: {key}")
                print("可用的配置项:")
                for k in config_dict.keys():
                    print(f"  - {k}")
                return False
            
            # 类型转换
            original_value = config_dict[key]
            if isinstance(original_value, bool):
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(original_value, int):
                value = int(value)
            elif isinstance(original_value, float):
                value = float(value)
            
            # 设置新值
            setattr(config, key, value)
            self.save_config(config)
            
            print(f"✅ 配置已更新: {key} = {value}")
            return True
            
        except ValueError as e:
            print(f"❌ 配置值格式错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 设置配置时出错: {e}")
            return False


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="智能选品系统命令行控制工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s start --config config.json    # 使用配置文件启动任务
  %(prog)s start                         # 使用默认配置启动任务
  %(prog)s pause                         # 暂停当前任务
  %(prog)s resume                        # 恢复暂停的任务
  %(prog)s stop                          # 停止当前任务
  %(prog)s status                        # 查看任务状态
  %(prog)s progress                      # 查看详细进度
  %(prog)s logs --lines 100              # 查看最近100条日志
  %(prog)s config list                   # 列出所有配置
  %(prog)s config set margin=0.2         # 设置利润率为20%%
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # start 命令
    start_parser = subparsers.add_parser('start', help='启动任务')
    start_parser.add_argument('--config', '-c', help='配置文件路径')
    
    # pause 命令
    subparsers.add_parser('pause', help='暂停任务')
    
    # resume 命令
    subparsers.add_parser('resume', help='恢复任务')
    
    # stop 命令
    subparsers.add_parser('stop', help='停止任务')
    
    # status 命令
    subparsers.add_parser('status', help='查看任务状态')
    
    # progress 命令
    subparsers.add_parser('progress', help='查看详细进度')
    
    # logs 命令
    logs_parser = subparsers.add_parser('logs', help='查看日志')
    logs_parser.add_argument('--lines', '-n', type=int, default=50, help='显示的日志行数 (默认: 50)')
    
    # config 命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_subparsers = config_parser.add_subparsers(dest='config_action', help='配置操作')
    
    config_subparsers.add_parser('list', help='列出所有配置')
    
    set_parser = config_subparsers.add_parser('set', help='设置配置项')
    set_parser.add_argument('assignment', help='配置赋值 (格式: key=value)')
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    controller = XuanpingCLIController()
    
    try:
        if args.command == 'start':
            success = controller.start_task(args.config)
            sys.exit(0 if success else 1)
            
        elif args.command == 'pause':
            success = controller.pause_task()
            sys.exit(0 if success else 1)
            
        elif args.command == 'resume':
            success = controller.resume_task()
            sys.exit(0 if success else 1)
            
        elif args.command == 'stop':
            success = controller.stop_task()
            sys.exit(0 if success else 1)
            
        elif args.command == 'status':
            controller.show_status()
            
        elif args.command == 'progress':
            controller.show_progress()
            
        elif args.command == 'logs':
            controller.show_logs(args.lines)
            
        elif args.command == 'config':
            if args.config_action == 'list':
                controller.list_configs()
            elif args.config_action == 'set':
                if '=' not in args.assignment:
                    print("❌ 错误: 配置赋值格式应为 key=value")
                    sys.exit(1)
                
                key, value = args.assignment.split('=', 1)
                success = controller.set_config(key.strip(), value.strip())
                sys.exit(0 if success else 1)
            else:
                parser.parse_args(['config', '--help'])
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n⚠️ 操作被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()