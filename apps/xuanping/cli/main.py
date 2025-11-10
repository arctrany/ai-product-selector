#!/usr/bin/env python3
"""
选评自动化CLI应用主入口

提供命令行界面来启动和管理选评自动化任务
"""

import sys
import os
import argparse
import logging
import time
import signal
import threading
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.xuanping.cli.models import UIStateManager, AppState, LogLevel, UIConfig
from apps.xuanping.cli.task_controller import TaskController
from apps.xuanping.cli.preset_manager import PresetManager
from apps.xuanping.cli.log_manager import LogManager
from apps.xuanping.common.config import GoodStoreSelectorConfig
from apps.xuanping.common.task_control import TaskControlInterface
from apps.xuanping.common.logging_config import setup_logging

def _handle_interactive_exit():
    """处理任务完成后的交互式退出"""
    print("\n" + "="*60)
    print("🎉 任务执行完成！")
    print("="*60)

    # 使用线程来实现超时功能
    user_input = [None]  # 使用列表来在闭包中修改值
    input_received = threading.Event()

    def get_user_input():
        try:
            user_input[0] = input("\n💡 按 Enter 键退出程序，或输入任意内容后按 Enter 继续等待: ").strip()
            input_received.set()
        except (EOFError, KeyboardInterrupt):
            input_received.set()

    # 启动输入线程
    input_thread = threading.Thread(target=get_user_input, daemon=True)
    input_thread.start()

    # 等待用户输入或超时
    timeout_seconds = 60
    print(f"⏰ 程序将在 {timeout_seconds} 秒后自动退出...")

    if input_received.wait(timeout=timeout_seconds):
        # 用户有输入
        if user_input[0] is not None and user_input[0] != "":
            print(f"📝 收到输入: {user_input[0]}")
            print("⏸️ 程序将保持运行状态，您可以手动关闭...")
            # 无限等待，直到用户手动关闭
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 用户手动中断，程序退出")
                return 0
        else:
            print("✅ 用户确认退出")
            return 0
    else:
        # 超时自动退出
        print(f"\n⏰ {timeout_seconds} 秒超时，程序自动退出")
        return 0


def setup_cli_logging(log_level: LogLevel = LogLevel.INFO):
    """设置CLI日志配置"""
    level_map = {
        LogLevel.DEBUG: "DEBUG",
        LogLevel.INFO: "INFO",
        LogLevel.WARNING: "WARNING",
        LogLevel.ERROR: "ERROR"
    }

    # 使用新的日志配置系统
    logger = setup_logging(
        log_level=level_map[log_level],
        max_bytes=100 * 1024 * 1024,  # 100MB
        backup_count=30,
        console_output=True
    )

    return logger


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='选评自动化CLI应用',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s start --data user_data.json --config system_config.json  # 使用用户数据和系统配置启动
  %(prog)s start --data user_data.json                              # 使用用户数据和默认系统配置启动
  %(prog)s start --dryrun --data user_data.json                     # 试运行模式
  %(prog)s status                                                    # 查看当前任务状态
  %(prog)s stop                                                      # 停止当前任务
  %(prog)s logs --export csv                                         # 导出日志为CSV格式

参数文件格式:
  --data (用户输入数据):
  {
    "good_shop_file": "/path/to/excel.xlsx",
    "item_collect_file": "/path/to/collect.xlsx", 
    "margin_calculator": "/path/to/calculator.xlsx",
    "margin": 0.1,
    "item_created_days": 150,
    "follow_buy_cnt": 37,
    "max_monthly_sold": 0,
    "monthly_sold_min": 100,
    "item_min_weight": 0,
    "item_max_weight": 1000,
    "g01_item_min_price": 0,
    "g01_item_max_price": 1000,
    "max_products_per_store": 50,
    "output_format": "xlsx",
    "output_path": "/path/to/output/"
  }

  --config (系统配置):
  {
    "scraping": {
      "browser_type": "chrome",
      "headless": false,
      "timeout_seconds": 30
    },
    "performance": {
      "max_concurrent_tasks": 5,
      "retry_count": 3
    }
  }
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # start命令
    start_parser = subparsers.add_parser('start', help='启动选评任务')
    start_parser.add_argument(
        '--data', '-d',
        required=True,
        help='用户输入数据文件路径（JSON格式）'
    )
    start_parser.add_argument(
        '--config', '-c',
        help='系统配置文件路径（JSON格式，可选）'
    )
    start_parser.add_argument(
        '--dryrun',
        action='store_true',
        help='试运行模式：只显示将要执行的操作，不实际修改文件'
    )

    # status命令
    subparsers.add_parser('status', help='查看任务状态')
    
    # stop命令
    subparsers.add_parser('stop', help='停止当前任务')
    
    # pause命令
    subparsers.add_parser('pause', help='暂停当前任务')
    
    # resume命令
    subparsers.add_parser('resume', help='恢复暂停的任务')
    
    # logs命令
    logs_parser = subparsers.add_parser('logs', help='日志管理')
    logs_parser.add_argument(
        '--export',
        choices=['txt', 'csv', 'json', 'html'],
        help='导出日志格式'
    )
    logs_parser.add_argument(
        '--output', '-o',
        help='输出文件路径'
    )
    logs_parser.add_argument(
        '--level',
        choices=['debug', 'info', 'warning', 'error'],
        help='过滤日志级别'
    )
    
    # preset命令
    preset_parser = subparsers.add_parser('preset', help='配置预设管理')
    preset_subparsers = preset_parser.add_subparsers(dest='preset_action')
    
    save_parser = preset_subparsers.add_parser('save', help='保存当前配置为预设')
    save_parser.add_argument('name', help='预设名称')
    
    load_parser = preset_subparsers.add_parser('load', help='加载配置预设')
    load_parser.add_argument('name', help='预设名称')
    
    preset_subparsers.add_parser('list', help='列出所有预设')
    
    delete_parser = preset_subparsers.add_parser('delete', help='删除预设')
    delete_parser.add_argument('name', help='预设名称')
    
    # 全局选项
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error'],
        default='info',
        help='日志级别 (默认: info)'
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='选评自动化CLI v1.0.0'
    )
    
    return parser


def load_user_data(data_path: str) -> UIConfig:
    """加载用户输入数据"""
    try:
        if not os.path.exists(data_path):
            print(f"❌ 用户数据文件不存在: {data_path}")
            sys.exit(1)

        import json
        with open(data_path, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)

        # 创建UIConfig对象
        ui_config = UIConfig(
            good_shop_file=data_dict.get('good_shop_file', ''),
            item_collect_file=data_dict.get('item_collect_file', ''),
            margin_calculator=data_dict.get('margin_calculator', ''),
            margin=data_dict.get('margin', 0.1),
            item_created_days=data_dict.get('item_created_days', 150),
            follow_buy_cnt=data_dict.get('follow_buy_cnt', 37),
            max_monthly_sold=data_dict.get('max_monthly_sold', 0),
            monthly_sold_min=data_dict.get('monthly_sold_min', 100),
            item_min_weight=data_dict.get('item_min_weight', 0),
            item_max_weight=data_dict.get('item_max_weight', 1000),
            g01_item_min_price=data_dict.get('g01_item_min_price', 0),
            g01_item_max_price=data_dict.get('g01_item_max_price', 1000),
            max_products_per_store=data_dict.get('max_products_per_store', 50),
            output_format=data_dict.get('output_format', 'xlsx'),
            output_path=data_dict.get('output_path', ''),
            remember_settings=data_dict.get('remember_settings', False),
            dryrun=False  # 这个由命令行参数控制
        )

        print(f"✓ 已加载用户数据: {data_path}")
        return ui_config

    except json.JSONDecodeError as e:
        print(f"❌ 用户数据JSON格式错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 加载用户数据失败: {e}")
        sys.exit(1)

def load_system_config(config_path: str = None) -> GoodStoreSelectorConfig:
    """加载系统配置文件"""
    try:
        if config_path and os.path.exists(config_path):
            config = GoodStoreSelectorConfig.from_json_file(config_path)
            print(f"✓ 已加载系统配置文件: {config_path}")
            return config
        elif config_path:
            print(f"⚠ 系统配置文件不存在，使用默认配置: {config_path}")
            return GoodStoreSelectorConfig()
        else:
            print("✓ 使用默认系统配置")
            return GoodStoreSelectorConfig()
    except Exception as e:
        print(f"✗ 加载系统配置文件失败: {e}")
        print("使用默认系统配置")
        return GoodStoreSelectorConfig()


def handle_start_command(args):
    """处理start命令"""
    if args.dryrun:
        print("🧪 启动选评自动化任务（试运行模式）...")
        print("📝 注意：试运行模式下不会实际修改任何文件，只会显示执行日志")
    else:
        print("🚀 启动选评自动化任务...")
    
    # 加载用户数据
    ui_config = load_user_data(args.data)

    # 加载系统配置
    system_config = load_system_config(args.config)

    # 应用dryrun模式
    if args.dryrun:
        ui_config.dryrun = True
        system_config.dryrun = True
        print("🧪 试运行模式已启用")

    # 显示将要执行的配置
    print("📋 将要执行的配置:")
    print(f"   • Excel文件: {ui_config.good_shop_file}")
    print(f"   • 输出路径: {ui_config.output_path}")
    print(f"   • 利润率: {ui_config.margin * 100}%")
    print(f"   • 每店最大商品数: {ui_config.max_products_per_store}")
    print(f"   • 浏览器类型: {system_config.scraping.browser_type}")
    print(f"   • 无头模式: {'是' if system_config.scraping.headless else '否'}")

    if args.dryrun:
        print("📝 试运行模式下不会实际修改任何文件")

    # 验证必需的用户数据
    if not ui_config.good_shop_file:
        print("❌ 错误: 用户数据中缺少good_shop_file字段")
        return 1

    if not os.path.exists(ui_config.good_shop_file):
        print(f"❌ 错误: Excel文件不存在: {ui_config.good_shop_file}")
        return 1

    if not ui_config.output_path:
        print("❌ 错误: 用户数据中缺少output_path字段")
        return 1

    # 初始化状态管理器
    state_manager = UIStateManager()
    state_manager.set_state(AppState.RUNNING)

    # 创建任务控制器
    task_controller = TaskController()

    try:
        # 启动实际任务（无论是否为dryrun模式）
        print("📊 开始处理Excel文件...")
        task_controller.start_task(ui_config)

        if args.dryrun:
            print("🧪 试运行模式：执行抓取但不写入文件，不调用1688接口")

        print("✅ 选评任务已启动")
        print("💡 使用 Ctrl+C 停止任务")
        print("💡 使用另一个终端运行 'python -m apps.xuanping.cli.main status' 查看进度")

        # 等待任务完成或用户中断
        try:
            while True:
                current_state = state_manager.state

                if current_state == AppState.COMPLETED:
                    print("🎉 选评任务已完成！")
                    # 任务完成后的交互式退出
                    return _handle_interactive_exit()
                elif current_state == AppState.ERROR:
                    print("❌ 任务执行出错")
                    return 1
                elif current_state == AppState.IDLE:
                    print("⏹ 任务已停止")
                    break

                # 显示进度信息
                progress = state_manager.progress
                if progress and hasattr(progress, 'current_store') and progress.current_store:
                    print(f"📈 正在处理: {progress.current_store} ({progress.processed_stores}/{progress.total_stores})")

                # 等待一段时间再检查
                time.sleep(5)

        except KeyboardInterrupt:
            print("\n🛑 用户中断，正在停止任务...")
            task_controller.stop_task()
            print("✅ 任务已停止")
            return 0
        
    except Exception as e:
        print(f"✗ 启动任务失败: {e}")
        state_manager.set_state(AppState.ERROR)
        return 1
    
    return 0


def handle_status_command(args):
    """处理status命令"""
    status_data = TaskControlInterface.get_task_status()

    if status_data.get("status") == "IDLE":
        print(f"📊 当前状态: IDLE")
        print(f"💡 {status_data.get('message', '没有运行中的任务')}")
    elif status_data.get("status") == "ERROR":
        print(f"📊 当前状态: ERROR")
        print(f"❌ {status_data.get('message', '获取状态失败')}")
    else:
        # 显示详细状态
        task_status = status_data.get("status", "UNKNOWN")
        current_step = status_data.get("current_step", "未知")
        progress = status_data.get("progress", {})

        print(f"📊 当前状态: {task_status.upper()}")
        print(f"🔄 当前步骤: {current_step}")

        if progress:
            current = progress.get("current", 0)
            total = progress.get("total", 0)
            percentage = progress.get("percentage", 0.0)

            if total > 0:
                print(f"📈 进度: {current}/{total} ({percentage:.1f}%)")

            # 显示其他进度信息
            for key, value in progress.items():
                if key not in ["current", "total", "percentage"] and value is not None:
                    print(f"   • {key}: {value}")

        # 显示时间信息
        created_time = status_data.get("created_time")
        updated_time = status_data.get("updated_time")
        pause_time = status_data.get("pause_time")

        if created_time:
            print(f"⏰ 创建时间: {created_time}")
        if updated_time:
            print(f"🔄 更新时间: {updated_time}")
        if pause_time:
            print(f"⏸️ 暂停时间: {pause_time}")

    return 0


def handle_stop_command(args):
    """处理stop命令"""
    print("🛑 停止选评任务...")

    success = TaskControlInterface.stop_task()
    return 0 if success else 1

def handle_pause_command(args):
    """处理pause命令"""
    print("⏸️ 暂停选评任务...")

    success = TaskControlInterface.pause_task()
    return 0 if success else 1

def handle_resume_command(args):
    """处理resume命令"""
    print("▶️ 恢复选评任务...")

    success = TaskControlInterface.resume_task()
    return 0 if success else 1


def handle_logs_command(args):
    """处理logs命令"""
    log_manager = LogManager()
    
    if args.export:
        # 如果没有指定输出路径，使用用户数据目录
        if args.output:
            output_file = args.output
        else:
            from apps.xuanping.common.logging_config import xuanping_logger
            data_dir = xuanping_logger.get_data_directory()
            output_file = str(data_dir / f"xuanping_logs.{args.export}")

        try:
            if args.export == 'txt':
                success = log_manager.export_logs_txt(output_file, args.level)
            elif args.export == 'csv':
                success = log_manager.export_logs_csv(output_file, args.level)
            elif args.export == 'json':
                success = log_manager.export_logs_json(output_file, args.level)
            elif args.export == 'html':
                success = log_manager.export_logs_html(output_file, args.level)
            else:
                print(f"✗ 不支持的导出格式: {args.export}")
                return 1

            if success:
                print(f"✅ 日志已导出到: {output_file}")
                if args.level:
                    print(f"📊 过滤级别: {args.level.upper()}")
            else:
                print("✗ 导出日志失败")
                return 1
        except Exception as e:
            print(f"✗ 导出日志失败: {e}")
            return 1
    else:
        # 显示最近的日志
        try:
            logs = log_manager.get_recent_logs(limit=20, level_filter=args.level)
            if logs:
                print("📋 最近的日志:")
                if args.level:
                    print(f"📊 过滤级别: {args.level.upper()}")
                print("-" * 80)
                for log in logs:
                    timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    level = log.level.value.upper()
                    print(f"[{timestamp}] [{level}] {log.message}")
                    if log.store_id:
                        print(f"    店铺ID: {log.store_id}")
                    if log.step:
                        print(f"    步骤: {log.step}")
                print("-" * 80)
                print(f"📊 共显示 {len(logs)} 条日志")

                # 显示日志文件信息
                from apps.xuanping.common.logging_config import xuanping_logger
                log_files = xuanping_logger.list_log_files()
                if log_files:
                    print(f"\n📁 日志文件位置: {xuanping_logger.get_log_directory()}")
                    print("📄 可用日志文件:")
                    for file_info in log_files[:5]:  # 只显示前5个
                        print(f"  • {file_info['name']} ({file_info['size_mb']}MB)")
            else:
                print("📋 暂无日志记录")
                from apps.xuanping.common.logging_config import xuanping_logger
                print(f"💡 日志文件位置: {xuanping_logger.get_log_directory()}")
        except Exception as e:
            print(f"✗ 读取日志失败: {e}")
            return 1
    
    return 0


def handle_preset_command(args):
    """处理preset命令"""
    preset_manager = PresetManager()
    
    if args.preset_action == 'save':
        try:
            # 这里需要获取当前配置，简化处理
            config = GoodStoreSelectorConfig()
            preset_manager.save_preset(args.name, config)
            print(f"✅ 预设 '{args.name}' 已保存")
        except Exception as e:
            print(f"✗ 保存预设失败: {e}")
            return 1
    
    elif args.preset_action == 'load':
        try:
            config = preset_manager.load_preset(args.name)
            print(f"✅ 预设 '{args.name}' 已加载")
            # 这里可以将配置保存为当前配置文件
        except Exception as e:
            print(f"✗ 加载预设失败: {e}")
            return 1
    
    elif args.preset_action == 'list':
        presets = preset_manager.list_presets()
        if presets:
            print("📋 可用预设:")
            for preset in presets:
                print(f"  • {preset}")
        else:
            print("📋 暂无保存的预设")
    
    elif args.preset_action == 'delete':
        try:
            preset_manager.delete_preset(args.name)
            print(f"✅ 预设 '{args.name}' 已删除")
        except Exception as e:
            print(f"✗ 删除预设失败: {e}")
            return 1
    
    return 0


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 设置日志级别
    log_level_map = {
        'debug': LogLevel.DEBUG,
        'info': LogLevel.INFO,
        'warning': LogLevel.WARNING,
        'error': LogLevel.ERROR
    }
    logger = setup_cli_logging(log_level_map[args.log_level])
    
    # 如果没有提供命令，显示帮助
    if not args.command:
        parser.print_help()
        return 0
    
    # 分发命令处理
    try:
        if args.command == 'start':
            return handle_start_command(args)
        elif args.command == 'status':
            return handle_status_command(args)
        elif args.command == 'stop':
            return handle_stop_command(args)
        elif args.command == 'pause':
            return handle_pause_command(args)
        elif args.command == 'resume':
            return handle_resume_command(args)
        elif args.command == 'logs':
            return handle_logs_command(args)
        elif args.command == 'preset':
            return handle_preset_command(args)
        else:
            print(f"✗ 未知命令: {args.command}")
            return 1
    
    except KeyboardInterrupt:
        print("\n⚠ 用户中断操作")
        return 130
    except Exception as e:
        print(f"✗ 执行命令时发生错误: {e}")
        logging.exception("命令执行异常")
        return 1


if __name__ == '__main__':
    sys.exit(main())